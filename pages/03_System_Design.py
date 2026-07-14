from pathlib import Path
import copy
import csv
from html import escape
import io
import re

import pandas as pd
import streamlit as st
from config import APP_VERSION, DATA_VERSION
from feedback import render_report_button
from ui_helpers import render_card_title

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.unit_model_defaults import cost_input_rows, technical_input_rows
from tea_models.water_quality import (
    apply_removal_overrides,
    calculate_brine_quality,
    collect_feedwater_quality,
    get_default_removal_efficiencies,
    make_stream,
)


st.set_page_config(page_title="03_System_Design", layout="wide")

st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

st.markdown("""
<style>
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        letter-spacing: -0.5px;
        margin-top: 0;
    }
    .main {
        background-color: #FAFAFA;
    }
    [data-testid="stContainer"] {
        border-radius: 12px;
    }
    .assumption-table {
        border: 1px solid #D9E2EC;
        border-radius: 8px;
        padding: 14px 16px 16px;
        background: #FFFFFF;
    }
    .assumption-title {
        font-weight: 700;
        margin-bottom: 12px;
    }
    .assumption-header {
        color: #5F6C7B;
        font-size: 0.82rem;
        font-weight: 700;
        border-bottom: 1px solid #E6ECF2;
        padding-bottom: 6px;
        margin-bottom: 4px;
    }
    .feed-quality-tab {
        background: #1F6FEB;
        color: #FFFFFF;
        font-weight: 700;
        border-radius: 8px 8px 0 0;
        padding: 8px 12px;
        margin-top: 18px;
        margin-bottom: 0;
    }
    div[data-testid="stNumberInput"] button {
        display: none;
    }
    div[data-testid="stNumberInput"] input[type="number"]::-webkit-outer-spin-button,
    div[data-testid="stNumberInput"] input[type="number"]::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    div[data-testid="stNumberInput"] input[type="number"] {
        -moz-appearance: textfield;
    }
</style>
""", unsafe_allow_html=True)


APP_ROOT = Path(__file__).resolve().parents[1]
TECHNICAL_INPUT_PATH = APP_ROOT / "data" / "input_tables" / "technical_inputs.csv"
COST_INPUT_PATH = APP_ROOT / "data" / "input_tables" / "cost_inputs.csv"
RESULTS_OUTPUT_PATH = APP_ROOT / "data" / "results" / "tea_results.csv"
BBL_TO_M3 = 0.158987294928
M3_TO_BBL = 1 / BBL_TO_M3
DEFAULT_INVESTMENT_FACTOR = 2.5
REMOVAL_EFFICIENCY_EXCLUDED_PARAMETERS = {"pH"}
INPUT_METADATA_COLUMNS = ["source", "data_type"]
HIDDEN_COST_OUTPUTS = {
    "flow_capacity_equipment_capital_cost",
    "power_capacity_capital_cost",
    "land_capital_cost",
    "liner_capital_cost",
}

COST_INPUT_FALLBACKS = {
    "MVC": [
        ("Capital", "capex_per_flow", 1104.0, "$/(m3/day)", "Equipment MVC capital cost per unit daily capacity"),
        ("Fixed O&M", "fixed_opex_fraction", 0.05, "fraction/yr", "Annual fixed OPEX as fraction of installed MVC CAPEX"),
        ("Variable O&M", "variable_opex_per_m3", 0.0, "$/m3", "Variable MVC operating cost per cubic meter treated"),
    ],
    "Saltwater disposal well": [
        ("Capital", "capex_per_flow", 48.0, "$/(m3/day)", "Equipment surface facilities capital per unit daily disposal capacity"),
        ("Capital", "capex_per_well", 600000.0, "$/well", "Equipment capital cost per disposal well"),
        ("Fixed O&M", "fixed_opex_fraction", 0.04, "fraction/yr", "Annual fixed OPEX as fraction of installed disposal well CAPEX"),
        ("Variable O&M", "variable_opex_per_m3", 11.4, "$/m3", "Variable disposal cost per cubic meter injected"),
    ],
}


def safe_project_filename(project_name):
    """Return a filesystem-friendly filename prefix for project outputs."""
    cleaned = []
    for char in project_name.strip():
        if char.isalnum():
            cleaned.append(char)
        else:
            cleaned.append("_")
    filename = "_".join(part for part in "".join(cleaned).split("_") if part)
    return filename or "tea_project"


def calculate_crf(discount_rate_percent, project_life_years):
    """Return the capital recovery factor matching Excel PMT rate logic."""
    project_life_years = max(float(project_life_years or 0.0), 1.0)
    rate = float(discount_rate_percent or 0.0) / 100.0
    if abs(rate) < 1e-12:
        return 1.0 / project_life_years
    factor = (1.0 + rate) ** project_life_years
    return rate * factor / (factor - 1.0)


def display_flow_value(flow_m3_day, display_unit):
    """Return flow in the same daily unit selected by the user."""
    if display_unit == "bbl/day":
        return float(flow_m3_day) * M3_TO_BBL
    return float(flow_m3_day)


def feed_lcow_unit(display_unit):
    """Return the LCOW unit for feed-volume normalization."""
    if display_unit == "bbl/day":
        return "$/bbl feed"
    return "$/m3 feed"


def format_lcow(value, unit):
    """Format LCOW as a currency value with its feed-normalized denominator."""
    if str(unit).startswith("$/"):
        return f"${value:,.2f}/{str(unit)[2:]}"
    return f"${value:,.2f} {unit}"


def sync_feed_flow_display_unit():
    """Convert the displayed feed-flow value when the user switches units."""
    current_unit = st.session_state.get("tea_feed_flow_unit", "bbl/day")
    previous_unit = st.session_state.get("tea_previous_feed_flow_unit", current_unit)
    current_value = float(st.session_state.get("tea_feed_flow_value", 25000.0) or 0.0)

    if current_unit != previous_unit:
        if current_unit == "m3/day" and previous_unit == "bbl/day":
            st.session_state.tea_feed_flow_value = current_value * BBL_TO_M3
        elif current_unit == "bbl/day" and previous_unit == "m3/day":
            st.session_state.tea_feed_flow_value = current_value * M3_TO_BBL
        st.session_state.tea_previous_feed_flow_unit = current_unit


def get_ordered_unit_processes(train):
    """Flatten the page 02 treatment train into the execution order for page 03."""
    brine_units = train.get("brine", [])
    if isinstance(brine_units, str):
        brine_units = [brine_units]

    sections = [
        ("Pretreatment", train.get("pretreatment", [])),
        ("Desalination", train.get("desalination", [])),
        ("Post-treatment", train.get("posttreatment", [])),
        (f"Brine management - {train.get('brine_category', 'Brine management')}", brine_units),
    ]

    ordered_units = []
    sequence = 1
    for section, units in sections:
        for unit_process in units:
            # Migrate treatment trains saved before the generic RO placeholder
            # was replaced by the explicit BWRO model.
            if unit_process == "RO":
                unit_process = "BWRO"
            elif unit_process in {"MD", "VMD"}:
                unit_process = "Vacuum membrane distillation (VMD)"
            ordered_units.append({
                "sequence": sequence,
                "section": section,
                "unit_process": unit_process,
            })
            sequence += 1

    return ordered_units


def load_input_table(path):
    """Load an editable input table template."""
    table = pd.read_csv(path)
    if "sub_section" not in table.columns:
        table.insert(1, "sub_section", "General")
    for column in INPUT_METADATA_COLUMNS:
        if column not in table.columns:
            table[column] = ""
        table[column] = table[column].fillna("")
    table["value"] = pd.to_numeric(table["value"], errors="coerce").fillna(0.0)
    return table


def get_inputs_for_unit(table, unit_process, fallback_map=None):
    """Return unit-specific rows when present, otherwise use DEFAULT rows."""
    output_columns = [
        "unit_process",
        "sub_section",
        "parameter",
        "value",
        "unit",
        "description",
        *INPUT_METADATA_COLUMNS,
    ]
    default_rows = table[table["unit_process"] == "DEFAULT"].copy()
    unit_rows = table[table["unit_process"] == unit_process].copy()

    if unit_rows.empty:
        fallback_rows = (fallback_map or {}).get(unit_process)
        if fallback_rows is None:
            if "technical" in str(table.attrs.get("input_table_kind", "")):
                fallback_rows = technical_input_rows(unit_process)
            elif "cost" in str(table.attrs.get("input_table_kind", "")):
                fallback_rows = cost_input_rows(unit_process)
        if fallback_rows:
            records = []
            for fallback_row in fallback_rows:
                sub_section, parameter, value, unit, description, *metadata = fallback_row
                source = metadata[0] if len(metadata) >= 1 else ""
                data_type = metadata[1] if len(metadata) >= 2 else ""
                records.append({
                    "unit_process": unit_process,
                    "sub_section": sub_section,
                    "parameter": parameter,
                    "value": value,
                    "unit": unit,
                    "description": description,
                    "source": source,
                    "data_type": data_type,
                })
            return pd.DataFrame(records)
        rows = default_rows
        rows["unit_process"] = unit_process
        return rows.reset_index(drop=True)[output_columns]

    return unit_rows.reset_index(drop=True)[output_columns]


def input_row_tooltip(row):
    """Build the tooltip text for one technical/cost input row."""
    def clean_text(value):
        if pd.isna(value):
            return ""
        return str(value or "").strip()

    source = clean_text(row.get("source", ""))
    data_type = clean_text(row.get("data_type", ""))
    if data_type and source:
        return f"{data_type}: {source}"
    if data_type:
        return f"{data_type}: source not provided"
    if source:
        return f"Source: {source}"
    return "Metadata: not provided"


def input_key_fragment(value):
    """Return a stable widget-key fragment for table section and parameter names."""
    return re.sub(r"[^a-zA-Z0-9_]+", "_", str(value)).strip("_") or "input"


def render_grouped_input_tables(rows, key_prefix):
    """Render one unit's input rows with per-item tooltips and return edited rows."""
    edited_sections = []
    subsection_names = rows["sub_section"].fillna("General").drop_duplicates().tolist()
    st.markdown(
        """
        <style>
            .input-row-info {
                align-items: center;
                border: 1.3px solid #8A8F98;
                border-radius: 999px;
                color: #6B7280;
                cursor: help;
                display: inline-flex;
                font-size: 0.68rem;
                font-weight: 750;
                height: 16px;
                justify-content: center;
                line-height: 1;
                margin-top: 0.35rem;
                position: relative;
                width: 16px;
            }
            .input-row-info:hover::after {
                background: #111827;
                border-radius: 4px;
                bottom: calc(100% + 8px);
                color: #FFFFFF;
                content: attr(data-tooltip);
                font-size: 0.78rem;
                font-weight: 500;
                left: 0;
                line-height: 1.35;
                padding: 0.42rem 0.55rem;
                position: absolute;
                text-align: left;
                white-space: pre-line;
                width: 260px;
                z-index: 9999;
            }
            .input-row-info:hover::before {
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #111827;
                bottom: calc(100% + 2px);
                content: "";
                left: 2px;
                position: absolute;
                z-index: 9999;
            }
            .input-row-description {
                color: #102A43;
                font-size: 0.92rem;
                line-height: 1.25;
                padding-top: 0.38rem;
            }
            .input-row-unit {
                color: #52606D;
                font-size: 0.88rem;
                line-height: 1.25;
                padding-top: 0.48rem;
            }
            .input-row-header {
                border-bottom: 1px solid #E6ECF2;
                color: #5F6C7B;
                font-size: 0.78rem;
                font-weight: 750;
                margin-bottom: 0.15rem;
                padding-bottom: 0.25rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    for sub_section in subsection_names:
        subsection_rows = rows[rows["sub_section"].fillna("General") == sub_section].copy()
        st.markdown(f"_{sub_section}_")
        header_cols = st.columns([3.0, 0.24, 1.15, 0.85], vertical_alignment="top")
        header_cols[0].markdown('<div class="input-row-header">Input</div>', unsafe_allow_html=True)
        header_cols[2].markdown('<div class="input-row-header">Value</div>', unsafe_allow_html=True)
        header_cols[3].markdown('<div class="input-row-header">Unit</div>', unsafe_allow_html=True)
        merged_rows = subsection_rows.reset_index(drop=True).copy()
        for index, row in merged_rows.iterrows():
            row_cols = st.columns([3.0, 0.24, 1.15, 0.85], vertical_alignment="top")
            with row_cols[0]:
                st.markdown(
                    f'<div class="input-row-description">{escape(str(row.get("description", "")))}</div>',
                    unsafe_allow_html=True,
                )
            with row_cols[1]:
                st.markdown(
                    (
                        f'<span class="input-row-info" '
                        f'data-tooltip="{escape(input_row_tooltip(row))}">i</span>'
                    ),
                    unsafe_allow_html=True,
                )
            with row_cols[2]:
                merged_rows.at[index, "value"] = st.number_input(
                    str(row.get("description", row.get("parameter", "Input"))),
                    value=float(row.get("value", 0.0) or 0.0),
                    key=(
                        f"{key_prefix}_{input_key_fragment(sub_section)}_"
                        f"{input_key_fragment(row.get('parameter', index))}_{index}"
                    ),
                    label_visibility="collapsed",
                )
            with row_cols[3]:
                st.markdown(
                    f'<div class="input-row-unit">{escape(str(row.get("unit", "")))}</div>',
                    unsafe_allow_html=True,
                )
        edited_sections.append(merged_rows)

    if not edited_sections:
        return rows

    return pd.concat(edited_sections, ignore_index=True)


def table_to_input_dict(table):
    """Convert edited table rows into the dictionary expected by unit models."""
    values = {}
    for _, row in table.iterrows():
        parameter = row.get("parameter")
        if not parameter:
            continue
        values[str(parameter)] = float(row.get("value", 0.0) or 0.0)
    return values


def current_removal_efficiencies(unit, feedwater_quality):
    """Return editable constituent removals for one unit process."""
    quality = feedwater_quality.get("water_quality", {})
    defaults = get_default_removal_efficiencies(unit["unit_process"], quality)
    if not defaults:
        return {}

    override_store = st.session_state.setdefault("unit_removal_overrides", {})
    sequence_key = str(unit["sequence"])
    current_overrides = override_store.get(sequence_key, {})
    merged = apply_removal_overrides(defaults, current_overrides)
    return {
        parameter: value
        for parameter, value in merged.items()
        if parameter not in REMOVAL_EFFICIENCY_EXCLUDED_PARAMETERS
    }


@st.dialog("Removal efficiencies")
def show_removal_efficiency_dialog(unit, feedwater_quality):
    """Edit removal efficiencies in a modal dialog."""
    quality = feedwater_quality.get("water_quality", {})
    defaults = get_default_removal_efficiencies(unit["unit_process"], quality)
    merged = current_removal_efficiencies(unit, feedwater_quality)
    override_store = st.session_state.setdefault("unit_removal_overrides", {})
    sequence_key = str(unit["sequence"])

    st.markdown(f"**{unit['sequence']}. {unit['unit_process']}**")
    removal_rows = pd.DataFrame([
        {
            "parameter": parameter,
            "removal_efficiency": merged.get(parameter, 0.0),
        }
        for parameter in quality
        if parameter in defaults
        and parameter not in REMOVAL_EFFICIENCY_EXCLUDED_PARAMETERS
    ])
    edited = st.data_editor(
        removal_rows,
        key=f"removal_efficiencies_{unit['sequence']}_{unit['unit_process']}",
        hide_index=True,
        disabled=["parameter"],
        num_rows="fixed",
        use_container_width=True,
    )
    edited_values = {
        str(row["parameter"]): max(0.0, min(float(row["removal_efficiency"] or 0.0), 1.0))
        for _, row in edited.iterrows()
    }
    override_store[sequence_key] = edited_values


def result_value(result, name, default=0.0):
    """Read a numeric value from a model result entry with value/unit fields."""
    entry = result.get(name, {})
    if isinstance(entry, dict):
        return float(entry.get("value", default) or default)
    return float(entry or default)


def result_unit(result, name):
    """Read a unit string from a model result entry with value/unit fields."""
    entry = result.get(name, {})
    if isinstance(entry, dict):
        return entry.get("unit", "")
    return ""


def energy_basis_flow_m3_day(technical_result, intensity_unit):
    """Select the flow basis that matches an energy-intensity unit."""
    unit_text = str(intensity_unit or "").lower()
    if "product" in unit_text or "permeate" in unit_text:
        return result_value(technical_result, "outlet_flow")
    if "disposed" in unit_text:
        return result_value(
            technical_result,
            "disposed_flow",
            result_value(technical_result, "inlet_flow"),
        )
    return result_value(technical_result, "inlet_flow")


def unit_energy_summary(technical_result, intensity_name, train_feed_bbl_day):
    """Summarize unit energy use as daily energy, power, and train-feed intensity."""
    intensity = result_value(technical_result, intensity_name)
    intensity_unit = result_unit(technical_result, intensity_name)
    if intensity <= 0.0 or train_feed_bbl_day <= 0.0:
        return {
            "intensity": 0.0,
            "intensity_unit": intensity_unit,
            "energy_kwh_day": 0.0,
            "power_kw": 0.0,
            "kwh_per_bbl_feed": 0.0,
        }

    basis_flow_m3_day = energy_basis_flow_m3_day(technical_result, intensity_unit)
    energy_kwh_day = intensity * basis_flow_m3_day
    return {
        "intensity": intensity,
        "intensity_unit": intensity_unit,
        "energy_kwh_day": energy_kwh_day,
        "power_kw": energy_kwh_day / 24.0,
        "kwh_per_bbl_feed": energy_kwh_day / train_feed_bbl_day,
    }


def flatten_model_results(sequence, section, unit_process, model_type, model_results):
    """Convert nested model outputs into rows for the results CSV."""
    rows = []
    for result_name, result in model_results.items():
        if not isinstance(result, dict) or "value" not in result:
            continue
        rows.append({
            "sequence": sequence,
            "section": section,
            "unit_process": unit_process,
            "model_type": model_type,
            "result_name": result_name,
            "value": result.get("value"),
            "unit": result.get("unit", ""),
        })
    return rows


def build_results_csv_rows(results):
    """Create a long-form results table with units for download and export."""
    rows = []
    for unit_result in results["unit_results"]:
        rows.extend(flatten_model_results(
            unit_result["sequence"],
            unit_result["section"],
            unit_result["unit_process"],
            "technical",
            unit_result["technical_results"],
        ))
        rows.extend(flatten_model_results(
            unit_result["sequence"],
            unit_result["section"],
            unit_result["unit_process"],
            "cost",
            unit_result["cost_results"],
        ))

    project_rows = [
        ("total_capital_cost", results["total_capital_cost"], "USD"),
        ("annualized_capital_cost", results["annualized_capital_cost"], "USD/year"),
        ("total_annual_operating_cost", results["total_annual_operating_cost"], "USD/year"),
        ("total_annual_cost", results["total_annual_cost"], "USD/year"),
        ("final_product_flow", results["final_product_flow"], results["final_product_flow_unit"]),
        (
            "electricity_intensity",
            results.get("electricity_intensity_kwh_per_bbl_feed", 0.0),
            "kWh/bbl feed",
        ),
        (
            "electricity_power_requirement",
            results.get("electricity_power_requirement_kw", 0.0),
            "kW",
        ),
        (
            "thermal_energy_intensity",
            results.get("thermal_energy_intensity_kwh_per_bbl_feed", 0.0),
            "kWh/bbl feed",
        ),
        (
            "thermal_power_requirement",
            results.get("thermal_power_requirement_kw", 0.0),
            "kW",
        ),
        ("levelized_cost_of_water", results["levelized_cost_of_water"], results["levelized_cost_unit"]),
    ]
    for result_name, value, unit in project_rows:
        rows.append({
            "sequence": "",
            "section": "Project",
            "unit_process": "Overall system",
            "model_type": "project_summary",
            "result_name": result_name,
            "value": value,
            "unit": unit,
        })

    return rows


def _csv_number(value):
    """Return a stable compact numeric value for CSV output."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return value
    if pd.isna(numeric_value):
        return ""
    return f"{numeric_value:.6g}"


def unit_scaling_summary(unit_result):
    """Return a concise scaling summary for one unit's outlet water quality."""
    if str(unit_result.get("section", "")).startswith("Brine management"):
        return "Not applied", ""

    water_quality = unit_result.get("technical_results", {}).get("water_quality_out", {})
    if not water_quality:
        return "No data", ""

    try:
        from tea_models.scaling_tendency import calculate_scaling_tendency

        scaling_result = calculate_scaling_tendency(water_quality)
    except Exception as exc:
        return "Calculation unavailable", str(exc)

    minerals = scaling_result.get("minerals", [])
    likely = []
    near = []
    for mineral in minerals:
        tendency = mineral.get("tendency", "")
        mineral_name = mineral.get("mineral", "")
        omega = mineral.get("scaling_tendency")
        si = mineral.get("saturation_index")
        mineral_label = mineral_name
        if omega is not None and si is not None:
            mineral_label = (
                f"{mineral_name} "
                f"(Omega={_csv_number(omega)}, SI={_csv_number(si)})"
            )
        if tendency == "Scaling likely":
            likely.append(mineral_label)
        elif tendency == "Near saturation":
            near.append(mineral_label)

    if likely:
        return "Scaling likely", "; ".join(likely)
    if near:
        return "Near saturation", "; ".join(near)
    return "No scaling expected", ""


def build_unit_summary_csv_rows(results):
    """Build one summary row per unit process for the download CSV."""
    rows = []
    for unit_result in sorted(results["unit_results"], key=lambda row: row["sequence"]):
        scaling_tendency, scaling_minerals = unit_scaling_summary(unit_result)
        rows.append({
            "Sequence": unit_result.get("sequence", ""),
            "Section": unit_result.get("section", ""),
            "Unit process": unit_result.get("unit_process", ""),
            "Inlet flow": _csv_number(unit_result.get("inlet_flow", "")),
            "Inlet flow unit": unit_result.get("inlet_flow_unit", ""),
            "Outlet flow": _csv_number(unit_result.get("outlet_flow", "")),
            "Outlet flow unit": unit_result.get("outlet_flow_unit", ""),
            "Water recovery": _csv_number(unit_result.get("water_recovery", "")),
            "Water recovery unit": unit_result.get("water_recovery_unit", ""),
            "Installed CAPEX": _csv_number(unit_result.get("installed_capital_cost", "")),
            "Installed CAPEX unit": unit_result.get("installed_capital_cost_unit", "USD"),
            "Annualized CAPEX": _csv_number(unit_result.get("annualized_capital_cost", "")),
            "Annualized CAPEX unit": unit_result.get("annualized_capital_cost_unit", "USD/year"),
            "Annual OPEX": _csv_number(unit_result.get("total_annual_operating_cost", "")),
            "Annual OPEX unit": unit_result.get("total_annual_operating_cost_unit", "USD/year"),
            "CAPEX LCOW contribution": _csv_number(unit_result.get("capital_lcow_contribution", "")),
            "CAPEX LCOW unit": unit_result.get("capital_lcow_contribution_unit", ""),
            "OPEX LCOW contribution": _csv_number(unit_result.get("opex_lcow_contribution", "")),
            "OPEX LCOW unit": unit_result.get("opex_lcow_contribution_unit", ""),
            "Electricity consumption": _csv_number(unit_result.get("electricity_consumption_kwh_day", "")),
            "Electricity consumption unit": "kWh/day",
            "Electricity intensity": _csv_number(unit_result.get("electricity_intensity_kwh_per_bbl_feed", "")),
            "Electricity intensity unit": "kWh/bbl feed",
            "Electricity power": _csv_number(unit_result.get("electricity_power_requirement_kw", "")),
            "Electricity power unit": "kW",
            "Thermal energy consumption": _csv_number(unit_result.get("thermal_energy_consumption_kwh_day", "")),
            "Thermal energy consumption unit": "kWh/day",
            "Thermal energy intensity": _csv_number(unit_result.get("thermal_energy_intensity_kwh_per_bbl_feed", "")),
            "Thermal energy intensity unit": "kWh/bbl feed",
            "Thermal power": _csv_number(unit_result.get("thermal_power_requirement_kw", "")),
            "Thermal power unit": "kW",
            "Scaling tendency": scaling_tendency,
            "Scaling minerals": scaling_minerals,
        })
    return rows


def _quality_value_and_unit(water_quality, parameter):
    entry = water_quality.get(parameter, {})
    if isinstance(entry, dict):
        return _csv_number(entry.get("value", "")), entry.get("unit", "")
    return _csv_number(entry), ""


def build_water_quality_tracking_csv_rows(results):
    """Build a constituent-by-unit water quality tracking table."""
    unit_results = sorted(results.get("unit_results", []), key=lambda row: row["sequence"])
    feed_quality = {}
    trace = results.get("water_quality_trace", [])
    if trace:
        feed_quality = trace[0].get("water_quality", {}) or {}
    if not feed_quality and unit_results:
        feed_quality = unit_results[0].get("technical_results", {}).get("water_quality_in", {}) or {}

    parameters = list(feed_quality.keys())
    stage_columns = [("Influent", feed_quality)]
    for unit_result in unit_results:
        technical_results = unit_result.get("technical_results", {})
        stage_columns.append((
            f"{unit_result.get('sequence', '')}. {unit_result.get('unit_process', '')}",
            technical_results.get("water_quality_out", {}) or {},
        ))

    rows = []
    for parameter in parameters:
        _, unit = _quality_value_and_unit(feed_quality, parameter)
        row = {
            "Parameter": parameter,
            "Unit": unit,
        }
        for stage_name, water_quality in stage_columns:
            value, stage_unit = _quality_value_and_unit(water_quality, parameter)
            row[stage_name] = value
            if not row["Unit"] and stage_unit:
                row["Unit"] = stage_unit
        rows.append(row)
    return rows


def build_results_download_csv(results):
    """Create a sectioned CSV for summary, water quality, and detailed results."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    summary_rows = build_unit_summary_csv_rows(results)
    writer.writerow(["Unit process summary"])
    if summary_rows:
        summary_columns = list(summary_rows[0].keys())
        writer.writerow(summary_columns)
        for row in summary_rows:
            writer.writerow([row.get(column, "") for column in summary_columns])
    else:
        writer.writerow(["No unit results"])

    writer.writerow([])
    writer.writerow(["Water quality tracking"])
    water_quality_rows = build_water_quality_tracking_csv_rows(results)
    if water_quality_rows:
        water_quality_columns = list(water_quality_rows[0].keys())
        writer.writerow(water_quality_columns)
        for row in water_quality_rows:
            writer.writerow([row.get(column, "") for column in water_quality_columns])
    else:
        writer.writerow(["No water quality tracking data"])

    writer.writerow([])
    writer.writerow(["Detailed model results"])
    detailed_rows = results.get("results_csv_rows", [])
    if detailed_rows:
        detailed_columns = ["sequence", "section", "unit_process", "model_type", "result_name", "value", "unit"]
        writer.writerow(detailed_columns)
        for row in detailed_rows:
            if row.get("model_type") == "cost" and row.get("result_name") in HIDDEN_COST_OUTPUTS:
                continue
            writer.writerow([row.get(column, "") for column in detailed_columns])
    else:
        writer.writerow(["No detailed results"])

    return output.getvalue()


def transportation_extension_payload(context):
    payload = context.get("transportation_cost", {}) or {}
    try:
        annual_cost = float(payload.get("annual_transportation_cost", 0.0) or 0.0)
    except (TypeError, ValueError):
        annual_cost = 0.0
    payload["annual_transportation_cost"] = max(annual_cost, 0.0)
    return payload


def calculate_lcow(ordered_units, technical_tables, cost_tables, removal_tables, context, feedwater_quality):
    """Run the modular TEA calculation across all unit processes.

    Each unit process first calls a technical model from
    tea_models/technical_models, then passes that technical result into a cost
    model from tea_models/cost_models. If no unit-specific model exists, the
    default model in each folder is used.
    """
    stream = make_stream(feedwater_quality, context["feed_flow_m3_day"])
    brine_stream = None
    water_quality_trace = [{
        "sequence": 0,
        "section": "Feedwater",
        "unit_process": "Feedwater",
        "flow_m3_day": stream["flow_m3_day"],
        "water_quality": stream.get("water_quality", {}),
    }]
    unit_results = []
    total_capital_cost = 0.0
    total_annual_operating_cost = 0.0
    total_electricity_kwh_day = 0.0
    total_thermal_kwh_day = 0.0
    crf = float(context["capital_recovery_factor"])
    train_feed_bbl_day = max(float(context.get("feed_flow_bbl_day", 0.0) or 0.0), 1e-9)

    for unit in ordered_units:
        unit_process = unit["unit_process"]
        is_brine_management = unit["section"].startswith("Brine management")
        technical_inputs = table_to_input_dict(technical_tables[unit["sequence"]])
        technical_inputs["removal_efficiencies"] = removal_tables.get(unit["sequence"], {})
        cost_inputs = table_to_input_dict(cost_tables[unit["sequence"]])

        model_stream = brine_stream if is_brine_management and brine_stream is not None else stream
        technical_result = run_technical_model(unit_process, technical_inputs, model_stream)
        cost_result = run_cost_model(unit_process, technical_result, cost_inputs, context)

        capital_cost = result_value(cost_result, "installed_capital_cost")
        annualized_capital_cost = capital_cost * crf
        annual_operating_cost = result_value(cost_result, "total_annual_operating_cost")
        outlet_flow = result_value(technical_result, "outlet_flow")
        electricity_summary = unit_energy_summary(
            technical_result,
            "energy_intensity",
            train_feed_bbl_day,
        )
        thermal_summary = unit_energy_summary(
            technical_result,
            "thermal_energy_intensity",
            train_feed_bbl_day,
        )
        total_electricity_kwh_day += electricity_summary["energy_kwh_day"]
        total_thermal_kwh_day += thermal_summary["energy_kwh_day"]

        total_capital_cost += capital_cost
        total_annual_operating_cost += annual_operating_cost
        brine_flow = result_value(technical_result, "brine_flow")
        if brine_flow > 0.0 and unit["section"] == "Desalination":
            brine_quality = calculate_brine_quality(
                technical_result.get("water_quality_in", {}),
                technical_result.get("water_quality_out", {}),
                result_value(technical_result, "inlet_flow"),
                outlet_flow,
                brine_flow,
            )
            brine_stream = {
                "flow_m3_day": brine_flow,
                "water_quality": brine_quality,
            }
            technical_result["brine_water_quality"] = brine_quality
        if is_brine_management:
            brine_stream = technical_result.get("outlet_stream", {
                "flow_m3_day": outlet_flow,
                "water_quality": {},
            })
        else:
            stream = technical_result.get("outlet_stream", {
                "flow_m3_day": outlet_flow,
                "water_quality": stream.get("water_quality", {}),
            })
            water_quality_trace.append({
                "sequence": unit["sequence"],
                "section": unit["section"],
                "unit_process": unit_process,
                "flow_m3_day": outlet_flow,
                "water_quality": technical_result.get("water_quality_out", {}),
            })

        unit_results.append({
            "sequence": unit["sequence"],
            "section": unit["section"],
            "unit_process": unit_process,
            "inlet_flow": result_value(technical_result, "inlet_flow"),
            "inlet_flow_unit": result_unit(technical_result, "inlet_flow"),
            "outlet_flow": outlet_flow,
            "outlet_flow_unit": result_unit(technical_result, "outlet_flow"),
            "water_recovery": result_value(technical_result, "water_recovery"),
            "water_recovery_unit": result_unit(technical_result, "water_recovery"),
            "energy_intensity": result_value(technical_result, "energy_intensity"),
            "energy_intensity_unit": result_unit(technical_result, "energy_intensity"),
            "electricity_consumption_kwh_day": electricity_summary["energy_kwh_day"],
            "electricity_intensity_kwh_per_bbl_feed": electricity_summary["kwh_per_bbl_feed"],
            "electricity_power_requirement_kw": electricity_summary["power_kw"],
            "thermal_energy_consumption_kwh_day": thermal_summary["energy_kwh_day"],
            "thermal_energy_intensity_kwh_per_bbl_feed": thermal_summary["kwh_per_bbl_feed"],
            "thermal_power_requirement_kw": thermal_summary["power_kw"],
            "installed_capital_cost": capital_cost,
            "installed_capital_cost_unit": result_unit(cost_result, "installed_capital_cost"),
            "annualized_capital_cost": annualized_capital_cost,
            "annualized_capital_cost_unit": "USD/year",
            "total_annual_operating_cost": annual_operating_cost,
            "total_annual_operating_cost_unit": result_unit(cost_result, "total_annual_operating_cost"),
            "technical_results": technical_result,
            "cost_results": cost_result,
        })

    operating_days = float(context["operating_days_per_year"])
    flow_display_unit = context.get("feed_flow_display_unit", "m3/day")
    annual_feed_volume = (
        float(context["feed_flow_bbl_day"]) * operating_days
        if flow_display_unit == "bbl/day"
        else float(context["feed_flow_m3_day"]) * operating_days
    )
    transportation_cost = transportation_extension_payload(context)
    annual_transportation_cost = transportation_cost["annual_transportation_cost"]
    if annual_transportation_cost > 0.0:
        total_annual_operating_cost += annual_transportation_cost
        unit_results.append({
            "sequence": len(unit_results) + 1,
            "section": "Extension",
            "unit_process": "Transportation",
            "inlet_flow": 0.0,
            "inlet_flow_unit": "",
            "outlet_flow": 0.0,
            "outlet_flow_unit": "",
            "water_recovery": 0.0,
            "water_recovery_unit": "",
            "energy_intensity": 0.0,
            "energy_intensity_unit": "",
            "electricity_consumption_kwh_day": 0.0,
            "electricity_intensity_kwh_per_bbl_feed": 0.0,
            "electricity_power_requirement_kw": 0.0,
            "thermal_energy_consumption_kwh_day": 0.0,
            "thermal_energy_intensity_kwh_per_bbl_feed": 0.0,
            "thermal_power_requirement_kw": 0.0,
            "installed_capital_cost": 0.0,
            "installed_capital_cost_unit": "USD",
            "annualized_capital_cost": 0.0,
            "annualized_capital_cost_unit": "USD/year",
            "total_annual_operating_cost": annual_transportation_cost,
            "total_annual_operating_cost_unit": "USD/year",
            "technical_results": {
                "distance_miles": {
                    "value": float(transportation_cost.get("distance_miles", 0.0) or 0.0),
                    "unit": "mile",
                },
                "transported_volume": {
                    "value": float(
                        transportation_cost.get(
                            "annual_transported_volume_bbl",
                            transportation_cost.get("transported_volume_bbl_day", 0.0),
                        )
                        or 0.0
                    ),
                    "unit": (
                        "bbl/year"
                        if "annual_transported_volume_bbl" in transportation_cost
                        else "bbl/day"
                    ),
                },
            },
            "cost_results": {
                "cost_per_bbl_mile": {
                    "value": float(transportation_cost.get("cost_per_bbl_mile", 0.0) or 0.0),
                    "unit": "$/bbl-mile",
                },
                "total_annual_operating_cost": {
                    "value": annual_transportation_cost,
                    "unit": "USD/year",
                },
            },
        })

    annualized_capital_cost = total_capital_cost * crf
    total_annual_cost = annualized_capital_cost + total_annual_operating_cost
    annual_feed_volume = max(annual_feed_volume, 1e-9)
    lcow = total_annual_cost / annual_feed_volume

    for unit_result in unit_results:
        unit_result["capital_lcow_contribution"] = (
            unit_result["annualized_capital_cost"] / annual_feed_volume
        )
        unit_result["capital_lcow_contribution_unit"] = feed_lcow_unit(flow_display_unit)
        unit_result["opex_lcow_contribution"] = (
            unit_result["total_annual_operating_cost"] / annual_feed_volume
        )
        unit_result["opex_lcow_contribution_unit"] = feed_lcow_unit(flow_display_unit)

    product_flow = display_flow_value(stream["flow_m3_day"], flow_display_unit)

    results = {
        "total_capital_cost": total_capital_cost,
        "annualized_capital_cost": annualized_capital_cost,
        "total_annual_operating_cost": total_annual_operating_cost,
        "total_annual_cost": total_annual_cost,
        "final_product_flow": product_flow,
        "final_product_flow_unit": flow_display_unit,
        "electricity_intensity_kwh_per_bbl_feed": total_electricity_kwh_day / train_feed_bbl_day,
        "electricity_power_requirement_kw": total_electricity_kwh_day / 24.0,
        "thermal_energy_intensity_kwh_per_bbl_feed": total_thermal_kwh_day / train_feed_bbl_day,
        "thermal_power_requirement_kw": total_thermal_kwh_day / 24.0,
        "levelized_cost_of_water": lcow,
        "levelized_cost_unit": feed_lcow_unit(flow_display_unit),
        "unit_results": unit_results,
        "water_quality_trace": water_quality_trace,
        "transportation_cost": transportation_cost,
    }
    results["results_csv_rows"] = build_results_csv_rows(results)
    return results


title_col, report_col = st.columns([0.82, 0.18])
with title_col:
    st.header("System design & unit assumptions")
with report_col:
    render_report_button("System design and unit assumptions", use_container_width=True)

project_name = st.session_state.get("project_name", "TEA project")
st.caption(f"Project: {project_name}")

if "treatment_train" not in st.session_state:
    st.warning("Please save the Treatment Train on the previous page before proceeding.")
    st.stop()

train = st.session_state.treatment_train
ordered_units = get_ordered_unit_processes(train)

if not ordered_units:
    st.warning("No unit processes were found in the treatment train.")
    st.stop()

technical_template = load_input_table(TECHNICAL_INPUT_PATH)
cost_template = load_input_table(COST_INPUT_PATH)
technical_template.attrs["input_table_kind"] = "technical"
cost_template.attrs["input_table_kind"] = "cost"

st.markdown("Configure the system design assumptions and unit-specific inputs below. When you are ready, click the **Run TEA Calculation** button at the bottom to execute the models and calculate the levelized cost of water (LCOW) for your project.")

st.session_state.setdefault("tea_feed_flow_unit", "bbl/day")
st.session_state.setdefault("tea_previous_feed_flow_unit", st.session_state.tea_feed_flow_unit)
st.session_state.setdefault("tea_feed_flow_value", 25000.0)
sync_feed_flow_display_unit()

assumption_cols = st.columns(2)
with assumption_cols[0]:
    with st.container(border=True):
        render_card_title(
            "System assumptions",
            "Set project-wide operating assumptions used by every unit model and cost calculation.",
            key="help_system_assumptions",
            html='<div class="assumption-title">System assumptions</div>',
        )
        header_cols = st.columns([2.2, 1.2, 1.0])
        header_cols[0].markdown('<div class="assumption-header">Assumption</div>', unsafe_allow_html=True)
        header_cols[1].markdown('<div class="assumption-header">Value</div>', unsafe_allow_html=True)
        header_cols[2].markdown('<div class="assumption-header">Unit</div>', unsafe_allow_html=True)

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Feed flow rate")
        with row_cols[1]:
            feed_flow_value = st.number_input(
                "Feed flow rate value",
                min_value=0.0,
                value=float(st.session_state.tea_feed_flow_value),
                key="tea_feed_flow_value",
                label_visibility="collapsed",
            )
        with row_cols[2]:
            feed_flow_unit = st.selectbox(
                "Feed flow rate unit",
                ["bbl/day", "m3/day"],
                key="tea_feed_flow_unit",
                label_visibility="collapsed",
            )

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Operation time")
        with row_cols[1]:
            operation_time = st.number_input(
                "Operation time",
                min_value=0.0,
                max_value=100.0,
                value=90.0,
                key="tea_operation_time_percent",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("%")

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Project life")
        with row_cols[1]:
            project_life = st.number_input(
                "Project life",
                min_value=1.0,
                value=20.0,
                key="tea_project_life_years",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("yr")

        feed_flow_m3_day = (
            float(feed_flow_value) * BBL_TO_M3
            if feed_flow_unit == "bbl/day"
            else float(feed_flow_value)
        )
        feed_flow_bbl_day = (
            float(feed_flow_value)
            if feed_flow_unit == "bbl/day"
            else float(feed_flow_value) * M3_TO_BBL
        )

with assumption_cols[1]:
    with st.container(border=True):
        render_card_title(
            "Financial assumptions",
            "Set the financial factors used to annualize capital cost and calculate levelized cost.",
            key="help_financial_assumptions",
            html='<div class="assumption-title">Financial assumptions</div>',
        )
        header_cols = st.columns([2.2, 1.2, 1.0])
        header_cols[0].markdown('<div class="assumption-header">Assumption</div>', unsafe_allow_html=True)
        header_cols[1].markdown('<div class="assumption-header">Value</div>', unsafe_allow_html=True)
        header_cols[2].markdown('<div class="assumption-header">Unit</div>', unsafe_allow_html=True)

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Discount rate")
        with row_cols[1]:
            discount_rate = st.number_input(
                "Discount rate",
                min_value=0.0,
                value=8.0,
                key="tea_discount_rate_percent",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("%")

        calculated_crf = calculate_crf(discount_rate, project_life)
        previous_calculated_crf = st.session_state.get("tea_previous_calculated_crf")
        if (
            "tea_capital_recovery_factor" not in st.session_state
            or previous_calculated_crf is None
            or abs(float(st.session_state.tea_capital_recovery_factor) - previous_calculated_crf) < 1e-12
        ):
            st.session_state.tea_capital_recovery_factor = calculated_crf
        st.session_state.tea_previous_calculated_crf = calculated_crf

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("CRF")
        with row_cols[1]:
            capital_recovery_factor = st.number_input(
                "CRF",
                min_value=0.0,
                value=float(st.session_state.tea_capital_recovery_factor),
                format="%.6f",
                key="tea_capital_recovery_factor",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("")

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Investment factor")
        with row_cols[1]:
            investment_factor = st.number_input(
                "Investment factor",
                min_value=1.0,
                value=float(st.session_state.get("tea_investment_factor", DEFAULT_INVESTMENT_FACTOR)),
                step=0.1,
                format="%.2f",
                key="tea_investment_factor",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("")

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Base currency year")
        with row_cols[1]:
            base_currency_year = st.number_input(
                "Base currency year",
                min_value=2001,
                max_value=2024,
                value=2024,
                step=1,
                key="tea_base_currency_year",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("")

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Electricity price")
        with row_cols[1]:
            electricity_price = st.number_input(
                "Electricity price",
                min_value=0.0,
                value=0.1,
                key="tea_electricity_price",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("$/kWh")

        row_cols = st.columns([2.2, 1.2, 1.0])
        row_cols[0].markdown("Thermal energy price")
        with row_cols[1]:
            thermal_energy_price = st.number_input(
                "Thermal energy price",
                min_value=0.0,
                value=0.05,
                key="tea_thermal_energy_price",
                label_visibility="collapsed",
            )
        row_cols[2].markdown("$/kWh")

operating_days = 365.0 * float(operation_time) / 100.0

feedwater_quality = copy.deepcopy(
    st.session_state.get("feedwater_quality")
    or collect_feedwater_quality(st.session_state)
)
feedwater_quality["flow"] = {"value": float(feed_flow_bbl_day), "unit": "bbl/day"}
if feedwater_quality.get("water_quality"):
    st.markdown('<div class="feed-quality-tab">Feedwater quality</div>', unsafe_allow_html=True)
    with st.expander("View feedwater quality", expanded=False):
        st.dataframe(
            pd.DataFrame([
                {
                    "parameter": parameter,
                    "value": entry.get("value"),
                    "unit": entry.get("unit", ""),
                }
                for parameter, entry in feedwater_quality["water_quality"].items()
            ]),
            hide_index=True,
            use_container_width=True,
        )

technical_tables = {}
cost_tables = {}
removal_tables = {}

for unit in ordered_units:
    label = f"{unit['sequence']}. {unit['section']} - {unit['unit_process']}"
    is_brine_management = unit["section"].startswith("Brine management")
    title_col, removal_button_col = st.columns([4, 1])
    with title_col:
        st.subheader(label)
    with removal_button_col:
        if not is_brine_management and st.button("Removal efficiencies", key=f"show_removal_{unit['sequence']}", type="primary"):
            show_removal_efficiency_dialog(unit, feedwater_quality)
    tech_col, cost_col = st.columns(2)

    technical_rows = get_inputs_for_unit(technical_template, unit["unit_process"])
    cost_rows = get_inputs_for_unit(
        cost_template,
        unit["unit_process"],
        COST_INPUT_FALLBACKS,
    )

    with tech_col:
        st.markdown("**Technical input table**")
        technical_tables[unit["sequence"]] = render_grouped_input_tables(
            technical_rows,
            f"technical_inputs_{unit['sequence']}_{unit['unit_process']}",
        )
        removal_tables[unit["sequence"]] = current_removal_efficiencies(
            unit,
            feedwater_quality,
        )

    with cost_col:
        st.markdown("**Cost input table**")
        cost_tables[unit["sequence"]] = render_grouped_input_tables(
            cost_rows,
            f"cost_inputs_{unit['sequence']}_{unit['unit_process']}",
        )

context = {
    "feed_flow_bbl_day": feed_flow_bbl_day,
    "feed_flow_m3_day": feed_flow_m3_day,
    "feed_flow_display_value": feed_flow_value,
    "feed_flow_display_unit": feed_flow_unit,
    "operation_time_percent": operation_time,
    "operating_days_per_year": operating_days,
    "project_life_years": project_life,
    "discount_rate_percent": discount_rate,
    "capital_recovery_factor": capital_recovery_factor,
    "investment_factor": investment_factor,
    "base_currency_year": int(base_currency_year),
    "electricity_price": electricity_price,
    "thermal_energy_price": thermal_energy_price,
    "transportation_cost": st.session_state.get("transportation_cost", {}),
}

if st.button("Run TEA Calculation", type="primary"):
    results = calculate_lcow(
        ordered_units,
        technical_tables,
        cost_tables,
        removal_tables,
        context,
        feedwater_quality,
    )
    results_table = pd.DataFrame(results["results_csv_rows"])
    download_csv = build_results_download_csv(results)
    RESULTS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_filename = f"{safe_project_filename(project_name)}_tea_results.csv"
    (RESULTS_OUTPUT_PATH.parent / results_filename).write_text(download_csv, encoding="utf-8")
    st.session_state.tea_context = context
    st.session_state.feedwater_quality = feedwater_quality
    st.session_state.tea_unit_inputs = {
        "technical": {k: v.to_dict("records") for k, v in technical_tables.items()},
        "cost": {k: v.to_dict("records") for k, v in cost_tables.items()},
        "removal_efficiencies": removal_tables,
    }
    st.session_state.tea_results = results
    st.session_state.tea_results_csv = download_csv.encode("utf-8")
    st.session_state.tea_detailed_results_csv = results_table.to_csv(index=False).encode("utf-8")
    st.session_state.tea_results_filename = results_filename
    st.success("TEA calculation completed.")

if "tea_results" in st.session_state:
    results = st.session_state.tea_results
    st.markdown("**TEA calculation summary**")
    summary_table = pd.DataFrame([
        {"Result": "Total CAPEX", "Value": f"${results['total_capital_cost']:,.0f}"},
        {"Result": "Annual OPEX", "Value": f"${results['total_annual_operating_cost']:,.0f}/yr"},
        {
            "Result": "Product flow",
            "Value": (
                f"{results['final_product_flow']:,.1f} "
                f"{results.get('final_product_flow_unit', 'm3/day')}"
            ),
        },
        {
            "Result": "Electricity power requirement",
            "Value": f"{results.get('electricity_power_requirement_kw', 0.0):,.1f} kW",
        },
        {
            "Result": "Thermal power requirement",
            "Value": f"{results.get('thermal_power_requirement_kw', 0.0):,.1f} kW",
        },
        {
            "Result": "LCOW",
            "Value": format_lcow(
                results["levelized_cost_of_water"],
                results.get("levelized_cost_unit", "$/m3 feed"),
            ),
        },
    ])
    st.dataframe(summary_table, hide_index=True, use_container_width=True)

    if st.button("View TEA results", type="primary"):
        st.switch_page("pages/04_TEA_Results.py")

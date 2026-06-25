from pathlib import Path
import copy

import pandas as pd
import streamlit as st

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.water_quality import (
    apply_removal_overrides,
    calculate_brine_quality,
    collect_feedwater_quality,
    get_default_removal_efficiencies,
    make_stream,
)


st.set_page_config(page_title="03_System_Design", layout="wide")

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
REMOVAL_EFFICIENCY_EXCLUDED_PARAMETERS = {"pH"}

COST_INPUT_FALLBACKS = {
    "MVC": [
        ("Capital", "capex_per_flow", 2760.0, "$/(m3/day)", "Installed MVC capital cost per unit daily capacity"),
        ("Fixed O&M", "fixed_opex_fraction", 0.05, "fraction/yr", "Annual fixed OPEX as fraction of installed MVC CAPEX"),
        ("Variable O&M", "variable_opex_per_m3", 0.0, "$/m3", "Variable MVC operating cost per cubic meter treated"),
    ],
    "Saltwater disposal well": [
        ("Capital", "capex_per_flow", 120.0, "$/(m3/day)", "Installed surface facilities capital per unit daily disposal capacity"),
        ("Capital", "capex_per_well", 1500000.0, "$/well", "Installed capital cost per disposal well"),
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
    table["value"] = pd.to_numeric(table["value"], errors="coerce").fillna(0.0)
    return table


def get_inputs_for_unit(table, unit_process, fallback_map=None):
    """Return unit-specific rows when present, otherwise use DEFAULT rows."""
    default_rows = table[table["unit_process"] == "DEFAULT"].copy()
    unit_rows = table[table["unit_process"] == unit_process].copy()

    if unit_rows.empty:
        fallback_rows = (fallback_map or {}).get(unit_process)
        if fallback_rows:
            return pd.DataFrame([
                {
                    "unit_process": unit_process,
                    "sub_section": sub_section,
                    "parameter": parameter,
                    "value": value,
                    "unit": unit,
                    "description": description,
                }
                for sub_section, parameter, value, unit, description in fallback_rows
            ])
        rows = default_rows
        rows["unit_process"] = unit_process
        return rows.reset_index(drop=True)[
            ["unit_process", "sub_section", "parameter", "value", "unit", "description"]
        ]

    return unit_rows.reset_index(drop=True)[
        ["unit_process", "sub_section", "parameter", "value", "unit", "description"]
    ]


def render_grouped_input_tables(rows, key_prefix):
    """Render one unit's input rows as sub-section tables and return edited rows."""
    edited_sections = []
    subsection_names = rows["sub_section"].fillna("General").drop_duplicates().tolist()

    for sub_section in subsection_names:
        subsection_rows = rows[rows["sub_section"].fillna("General") == sub_section].copy()
        st.markdown(f"_{sub_section}_")
        display_rows = subsection_rows[["description", "value", "unit"]].copy()
        edited = st.data_editor(
            display_rows,
            key=f"{key_prefix}_{sub_section}",
            hide_index=True,
            disabled=["description", "unit"],
            num_rows="fixed",
            use_container_width=True,
        )
        merged_rows = subsection_rows.reset_index(drop=True).copy()
        merged_rows["value"] = edited["value"].reset_index(drop=True)
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
            "electricity_intensity_kwh_per_bbl_feed": electricity_summary["kwh_per_bbl_feed"],
            "electricity_power_requirement_kw": electricity_summary["power_kw"],
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


st.header("System design & unit assumptions")

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

st.markdown("Configure the system design assumptions and unit-specific inputs below. When you are ready, click the **Run TEA Calculation** button at the bottom to execute the models and calculate the levelized cost of water (LCOW) for your project.")

st.session_state.setdefault("tea_feed_flow_unit", "bbl/day")
st.session_state.setdefault("tea_previous_feed_flow_unit", st.session_state.tea_feed_flow_unit)
st.session_state.setdefault("tea_feed_flow_value", 25000.0)
sync_feed_flow_display_unit()

assumption_cols = st.columns(2)
with assumption_cols[0]:
    with st.container(border=True):
        st.markdown('<div class="assumption-title">System assumptions</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="assumption-title">Financial assumptions</div>', unsafe_allow_html=True)
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
    RESULTS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_filename = f"{safe_project_filename(project_name)}_tea_results.csv"
    results_table.to_csv(RESULTS_OUTPUT_PATH.parent / results_filename, index=False)
    st.session_state.tea_context = context
    st.session_state.feedwater_quality = feedwater_quality
    st.session_state.tea_unit_inputs = {
        "technical": {k: v.to_dict("records") for k, v in technical_tables.items()},
        "cost": {k: v.to_dict("records") for k, v in cost_tables.items()},
        "removal_efficiencies": removal_tables,
    }
    st.session_state.tea_results = results
    st.session_state.tea_results_csv = results_table.to_csv(index=False).encode("utf-8")
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

import csv
import io

import pandas as pd
import streamlit as st
from config import APP_VERSION, DATA_VERSION
from feedback import render_report_button
from tea_models.water_quality import calculate_brine_quality, water_quality_comparison_table
from treatment_config import ALL_WATER_QUALITY_PARAMS

try:
    from matplotlib import pyplot as plt
    from matplotlib.patches import Patch
except Exception as exc:  # Keep the results page usable when the runtime lacks matplotlib.
    plt = None
    Patch = None
    MATPLOTLIB_IMPORT_ERROR = exc
else:
    MATPLOTLIB_IMPORT_ERROR = None

try:
    from tea_models.scaling_tendency import calculate_scaling_tendency
except Exception as exc:  # Reaktoro is only needed for the optional scaling dialog.
    calculate_scaling_tendency = None
    SCALING_IMPORT_ERROR = exc
else:
    SCALING_IMPORT_ERROR = None


st.set_page_config(page_title="04_TEA_Results", layout="wide")

st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

BREAKDOWN_FIGSIZE = (7.2, 5.8)
BREAKDOWN_BAR_WIDTH = 0.22
BBL_PER_M3 = 6.289810770432
HIDDEN_COST_OUTPUTS = {
    "flow_capacity_equipment_capital_cost",
    "power_capacity_capital_cost",
    "land_capital_cost",
    "liner_capital_cost",
}

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
</style>
""", unsafe_allow_html=True)

title_col, report_col = st.columns([0.82, 0.18])
with title_col:
    st.header("TEA results")
with report_col:
    render_report_button("TEA results", use_container_width=True)

project_name = st.session_state.get("project_name", "TEA project")
st.caption(f"Project: {project_name}")


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


def format_lcow(value, unit):
    """Format LCOW as a currency value with its feed-normalized denominator."""
    if str(unit).startswith("$/"):
        return f"${value:,.2f}/{str(unit)[2:]}"
    return f"${value:,.2f} {unit}"


def product_lcow_bbl(results):
    """Return LCOW normalized by annual product-water volume in bbl."""
    product_flow = float(results.get("final_product_flow", 0.0) or 0.0)
    product_flow_unit = str(results.get("final_product_flow_unit", "m3/day")).lower()
    if product_flow_unit == "m3/day":
        product_flow_bbl_day = product_flow * BBL_PER_M3
    else:
        product_flow_bbl_day = product_flow

    operating_days = float(
        st.session_state.get("tea_context", {}).get("operating_days_per_year", 365.0)
        or 365.0
    )
    annual_product_volume = product_flow_bbl_day * operating_days
    if annual_product_volume <= 0.0:
        return 0.0
    return float(results.get("total_annual_cost", 0.0) or 0.0) / annual_product_volume


def export_csv_number(value):
    """Return a stable compact numeric value for CSV output."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return value
    if pd.isna(numeric_value):
        return ""
    return f"{numeric_value:.6g}"


def export_unit_scaling_summary(unit_result):
    """Return a concise scaling summary for one unit's outlet water quality."""
    if str(unit_result.get("section", "")).startswith("Brine management"):
        return "Not applied", ""

    water_quality = unit_result.get("technical_results", {}).get("water_quality_out", {})
    if not water_quality:
        return "No data", ""

    try:
        scaling_result = calculate_scaling_tendency(water_quality)
    except Exception as exc:
        return "Calculation unavailable", str(exc)

    likely = []
    near = []
    for mineral in scaling_result.get("minerals", []):
        tendency = mineral.get("tendency", "")
        mineral_name = mineral.get("mineral", "")
        omega = mineral.get("scaling_tendency")
        si = mineral.get("saturation_index")
        mineral_label = mineral_name
        if omega is not None and si is not None:
            mineral_label = (
                f"{mineral_name} "
                f"(Omega={export_csv_number(omega)}, SI={export_csv_number(si)})"
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


def export_unit_summary_rows(results):
    """Build one summary row per unit process for the download CSV."""
    rows = []
    for unit_result in sorted(results.get("unit_results", []), key=lambda row: row["sequence"]):
        scaling_tendency, scaling_minerals = export_unit_scaling_summary(unit_result)
        electricity_consumption = unit_result.get("electricity_consumption_kwh_day", "")
        if electricity_consumption == "":
            electricity_consumption = float(unit_result.get("electricity_power_requirement_kw", 0.0) or 0.0) * 24.0
        thermal_consumption = unit_result.get("thermal_energy_consumption_kwh_day", "")
        if thermal_consumption == "":
            thermal_consumption = float(unit_result.get("thermal_power_requirement_kw", 0.0) or 0.0) * 24.0
        rows.append({
            "Sequence": unit_result.get("sequence", ""),
            "Section": unit_result.get("section", ""),
            "Unit process": unit_result.get("unit_process", ""),
            "Inlet flow": export_csv_number(unit_result.get("inlet_flow", "")),
            "Inlet flow unit": unit_result.get("inlet_flow_unit", ""),
            "Outlet flow": export_csv_number(unit_result.get("outlet_flow", "")),
            "Outlet flow unit": unit_result.get("outlet_flow_unit", ""),
            "Water recovery": export_csv_number(unit_result.get("water_recovery", "")),
            "Water recovery unit": unit_result.get("water_recovery_unit", ""),
            "Installed CAPEX": export_csv_number(unit_result.get("installed_capital_cost", "")),
            "Installed CAPEX unit": unit_result.get("installed_capital_cost_unit", "USD"),
            "Annualized CAPEX": export_csv_number(unit_result.get("annualized_capital_cost", "")),
            "Annualized CAPEX unit": unit_result.get("annualized_capital_cost_unit", "USD/year"),
            "Annual OPEX": export_csv_number(unit_result.get("total_annual_operating_cost", "")),
            "Annual OPEX unit": unit_result.get("total_annual_operating_cost_unit", "USD/year"),
            "CAPEX LCOW contribution": export_csv_number(unit_result.get("capital_lcow_contribution", "")),
            "CAPEX LCOW unit": unit_result.get("capital_lcow_contribution_unit", ""),
            "OPEX LCOW contribution": export_csv_number(unit_result.get("opex_lcow_contribution", "")),
            "OPEX LCOW unit": unit_result.get("opex_lcow_contribution_unit", ""),
            "Electricity consumption": export_csv_number(electricity_consumption),
            "Electricity consumption unit": "kWh/day",
            "Electricity intensity": export_csv_number(unit_result.get("electricity_intensity_kwh_per_bbl_feed", "")),
            "Electricity intensity unit": "kWh/bbl feed",
            "Electricity power": export_csv_number(unit_result.get("electricity_power_requirement_kw", "")),
            "Electricity power unit": "kW",
            "Thermal energy consumption": export_csv_number(thermal_consumption),
            "Thermal energy consumption unit": "kWh/day",
            "Thermal energy intensity": export_csv_number(unit_result.get("thermal_energy_intensity_kwh_per_bbl_feed", "")),
            "Thermal energy intensity unit": "kWh/bbl feed",
            "Thermal power": export_csv_number(unit_result.get("thermal_power_requirement_kw", "")),
            "Thermal power unit": "kW",
            "Scaling tendency": scaling_tendency,
            "Scaling minerals": scaling_minerals,
        })
    return rows


def export_quality_value_and_unit(water_quality, parameter):
    entry = water_quality.get(parameter, {})
    if isinstance(entry, dict):
        return export_csv_number(entry.get("value", "")), entry.get("unit", "")
    return export_csv_number(entry), ""


def export_water_quality_tracking_rows(results):
    """Build a constituent-by-unit water quality tracking table."""
    unit_results = sorted(results.get("unit_results", []), key=lambda row: row["sequence"])
    trace = results.get("water_quality_trace", [])
    feed_quality = trace[0].get("water_quality", {}) if trace else {}
    if not feed_quality and unit_results:
        feed_quality = unit_results[0].get("technical_results", {}).get("water_quality_in", {}) or {}

    stage_columns = [("Influent", feed_quality)]
    for unit_result in unit_results:
        stage_columns.append((
            f"{unit_result.get('sequence', '')}. {unit_result.get('unit_process', '')}",
            unit_result.get("technical_results", {}).get("water_quality_out", {}) or {},
        ))

    rows = []
    for parameter in feed_quality:
        _, unit = export_quality_value_and_unit(feed_quality, parameter)
        row = {"Parameter": parameter, "Unit": unit}
        for stage_name, water_quality in stage_columns:
            value, stage_unit = export_quality_value_and_unit(water_quality, parameter)
            row[stage_name] = value
            if not row["Unit"] and stage_unit:
                row["Unit"] = stage_unit
        rows.append(row)
    return rows


def build_results_download_csv(results):
    """Create a sectioned CSV for summary, water quality, and detailed results."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    summary_rows = export_unit_summary_rows(results)
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
    water_quality_rows = export_water_quality_tracking_rows(results)
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


def render_summary_cells(summary_values):
    """Render key result values as a compact two-row summary."""
    st.markdown("""
    <style>
        .tea-summary-cell {
            border: 1px solid #D9E2EC;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        .tea-summary-label {
            align-items: center;
            background: #F7FAFC;
            border-bottom: 1px solid #D9E2EC;
            color: #334E68;
            display: flex;
            font-size: 0.96rem;
            font-weight: 750;
            height: 42px;
            justify-content: center;
            position: relative;
            text-align: center;
        }
        .tea-summary-help {
            align-items: center;
            border: 1px solid #CBD5E1;
            border-radius: 999px;
            color: #64748B;
            display: inline-flex;
            font-size: 0.72rem;
            height: 18px;
            justify-content: center;
            position: absolute;
            right: 8px;
            width: 18px;
        }
        .tea-summary-value {
            align-items: center;
            background: #FFFFFF;
            color: #102A43;
            display: flex;
            font-size: 1.16rem;
            font-weight: 800;
            height: 48px;
            justify-content: center;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    summary_cols = st.columns(len(summary_values), gap="small")
    for column, (name, value) in zip(summary_cols, summary_values.items()):
        with column:
            st.markdown(
                f"""
                <div class="tea-summary-cell">
                    <div class="tea-summary-label">
                        {name}
                        <span class="tea-summary-help" title="Quick summary metric from the current TEA calculation.">?</span>
                    </div>
                    <div class="tea-summary-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def model_results_table(model_results):
    """Convert model return dictionaries into display rows."""
    rows = []
    for result_name, result in model_results.items():
        if isinstance(result, dict):
            if "value" not in result:
                continue
            rows.append({
                "result_name": result_name,
                "value": result.get("value"),
                "unit": result.get("unit", ""),
            })
        else:
            rows.append({
                "result_name": result_name,
                "value": result,
                "unit": "",
            })
    return pd.DataFrame(rows)


def format_output_parameter(result_name):
    """Convert internal result keys into human-readable table labels."""
    words = str(result_name).replace("_", " ").replace("-", " ").split()
    return " ".join(word.capitalize() for word in words)


def format_model_value(value, mode, unit=""):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return value
    if pd.isna(numeric_value):
        return ""
    if str(unit).strip() in {"", "-"}:
        return f"{numeric_value:.3g}"
    if mode == "cost":
        if "/m3" in str(unit).lower():
            return f"{numeric_value:,.3f}"
        return f"{numeric_value:,.0f}"
    if abs(numeric_value) > 10:
        return f"{numeric_value:,.1f}"
    return f"{numeric_value:.3g}"


def format_output_table(table, mode="technical"):
    """Apply display-only labels and column names for model output tables."""
    if table.empty:
        return pd.DataFrame(columns=["Output parameters", "Value", "Unit"])

    output = table.copy()
    if mode == "cost":
        output = output[~output["result_name"].isin(HIDDEN_COST_OUTPUTS)].copy()
    output["result_name"] = output["result_name"].apply(format_output_parameter)
    output["value"] = output.apply(
        lambda row: format_model_value(row["value"], mode, row.get("unit", "")),
        axis=1,
    )
    return output.rename(columns={
        "result_name": "Output parameters",
        "value": "Value",
        "unit": "Unit",
    })


def display_height(table, min_height=150, max_height=700):
    """Size result tables so long model outputs are visible without hiding rows."""
    row_count = len(table.index)
    return min(max(38 + 35 * max(row_count, 1), min_height), max_height)


def unit_output_table(results_table, unit_result, model_type):
    """Read one unit/model output table from the exported long-form results."""
    if results_table.empty:
        return model_results_table(unit_result.get(f"{model_type}_results", {}))

    mask = (
        (results_table["sequence"].astype(str) == str(unit_result["sequence"]))
        & (results_table["unit_process"] == unit_result["unit_process"])
        & (results_table["model_type"] == model_type)
    )
    output = results_table.loc[mask, ["result_name", "value", "unit"]].copy()

    if output.empty:
        return model_results_table(unit_result.get(f"{model_type}_results", {}))
    return output.reset_index(drop=True)


def has_result(output_table, result_name):
    if output_table.empty or "result_name" not in output_table.columns:
        return False
    return result_name in set(output_table["result_name"].astype(str))


def technical_result_value(technical_results, result_name, default=0.0):
    result = technical_results.get(result_name, default)
    if isinstance(result, dict):
        result = result.get("value", default)
    try:
        return float(result)
    except (TypeError, ValueError):
        return default


def brine_water_quality_for_result(unit_result):
    technical_results = unit_result.get("technical_results", {})
    brine_water_quality = technical_results.get("brine_water_quality", {})
    if brine_water_quality:
        return brine_water_quality

    brine_flow = technical_result_value(technical_results, "brine_flow")
    if brine_flow <= 0.0:
        return {}

    return calculate_brine_quality(
        technical_results.get("water_quality_in", {}),
        technical_results.get("water_quality_out", {}),
        technical_result_value(technical_results, "inlet_flow"),
        technical_result_value(technical_results, "outlet_flow"),
        brine_flow,
    )


def format_water_quality_table(table):
    if table.empty:
        return pd.DataFrame(columns=[
            "Parameter",
            "Inlet value",
            "Outlet value",
            "Target value",
            "Unit",
            "Removal efficiency",
        ])
    output = table.copy()
    output["target_value"] = output["parameter"].apply(target_value_for_parameter)
    return output.rename(columns={
        "parameter": "Parameter",
        "inlet_value": "Inlet value",
        "outlet_value": "Outlet value",
        "target_value": "Target value",
        "unit": "Unit",
        "removal_efficiency": "Removal efficiency",
    })


def format_quality_value(value):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric_value):
        return ""
    if abs(numeric_value) < 10:
        return f"{numeric_value:.3g}"
    return f"{numeric_value:,.0f}"


def target_value_for_parameter(parameter):
    target_key = f"wq_target_{parameter}".replace(" ", "_")
    if target_key in st.session_state:
        return st.session_state[target_key]
    return ALL_WATER_QUALITY_PARAMS.get(parameter, {}).get("limit")


def highlight_outlet_exceedance(row):
    styles = [""] * len(row)
    try:
        outlet = float(str(row.get("Outlet value")).replace(",", ""))
        target = float(str(row.get("Target value")).replace(",", ""))
    except (TypeError, ValueError):
        return styles
    if outlet > target:
        outlet_index = list(row.index).index("Outlet value")
        styles[outlet_index] = "color: #b00020; font-weight: 700;"
    return styles


def format_scaling_value(value):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return ""
    if pd.isna(numeric_value):
        return ""
    if abs(numeric_value) >= 10:
        return f"{numeric_value:,.1f}"
    return f"{numeric_value:.3g}"


@st.dialog("Water quality")
def show_water_quality_dialog(
    unit_result,
    stream_name="Outlet",
    outlet_quality=None,
    removal_efficiencies=None,
):
    st.markdown(f"**{unit_result['sequence']}. {unit_result['unit_process']} - {stream_name}**")
    technical_results = unit_result.get("technical_results", {})
    if removal_efficiencies is None:
        removal_efficiencies = (
            technical_results.get("removal_efficiencies", {})
            if outlet_quality is None
            else {}
        )
    wq_table = water_quality_comparison_table(
        technical_results.get("water_quality_in", {}),
        outlet_quality if outlet_quality is not None else technical_results.get("water_quality_out", {}),
        removal_efficiencies,
    )
    if wq_table.empty:
        st.info("No water quality data is available for this unit.")
        return

    display_table = format_water_quality_table(wq_table)
    for column in ["Inlet value", "Outlet value", "Target value"]:
        if column in display_table.columns:
            display_table[column] = display_table[column].apply(format_quality_value)
    st.dataframe(
        display_table.style.apply(highlight_outlet_exceedance, axis=1),
        hide_index=True,
        use_container_width=True,
    )


@st.dialog("Scaling tendency")
def show_scaling_tendency_dialog(unit_result, stream_name="Outlet", water_quality=None):
    st.markdown(f"**{unit_result['sequence']}. {unit_result['unit_process']} - {stream_name}**")
    if unit_result["section"].startswith("Brine management"):
        st.info("Scaling tendency is not applied to brine management units yet.")
        return

    if calculate_scaling_tendency is None:
        st.error(
            "Scaling tendency is unavailable because Reaktoro is not installed in "
            "the Python environment running Streamlit."
        )
        st.caption(f"Reaktoro import error: {SCALING_IMPORT_ERROR}")
        return

    if water_quality is None:
        water_quality = unit_result.get("technical_results", {}).get("water_quality_out", {})
    if not water_quality:
        st.info(f"No {stream_name.lower()} water quality is available for this unit.")
        return

    try:
        scaling_result = calculate_scaling_tendency(water_quality)
    except Exception as exc:
        st.error(f"Scaling tendency calculation failed: {exc}")
        return

    scaling_table = pd.DataFrame(scaling_result["minerals"])
    if scaling_table.empty:
        st.info("No scaling tendency results were returned.")
        return

    display_table = scaling_table.rename(columns={
        "mineral": "Mineral",
        "saturation_index": "SI",
        "scaling_tendency": "Scaling tendency",
        "tendency": "Tendency",
    })
    for column in ["SI", "Scaling tendency"]:
        display_table[column] = display_table[column].apply(format_scaling_value)

    st.dataframe(display_table, hide_index=True, use_container_width=True)


def render_lcow_cost_breakdown(unit_results, lcow_unit):
    st.subheader("LCOW cost breakdown")
    cost_breakdown = unit_results.sort_values("sequence").copy()
    if plt is None or Patch is None:
        st.warning(
            "The chart could not be loaded because Matplotlib is unavailable in the "
            "Python environment running Streamlit. The same breakdown is shown below."
        )
        fallback = cost_breakdown.set_index(
            cost_breakdown.apply(
                lambda row: f"{int(row['sequence'])}. {row['unit_process']}", axis=1
            )
        )[["capital_lcow_contribution", "opex_lcow_contribution"]].rename(
            columns={
                "capital_lcow_contribution": "CAPEX contribution",
                "opex_lcow_contribution": "OPEX contribution",
            }
        )
        st.bar_chart(fallback)
        st.caption(f"Matplotlib import error: {MATPLOTLIB_IMPORT_ERROR}")
        return

    fig, ax = plt.subplots(figsize=BREAKDOWN_FIGSIZE)
    palette = [
        "#1f77b4",
        "#aec7e8",
        "#ff7f0e",
        "#ffbb78",
        "#2ca02c",
        "#98df8a",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#17becf",
    ]
    bottom = 0.0
    unit_handles = []
    bar_x = 0
    bar_width = BREAKDOWN_BAR_WIDTH

    for idx, (_, row) in enumerate(cost_breakdown.iterrows()):
        color = palette[idx % len(palette)]
        unit_label = f"{int(row['sequence'])}. {row['unit_process']}"
        capex_contribution = float(row["capital_lcow_contribution"])
        ax.bar(
            [bar_x],
            [capex_contribution],
            bottom=bottom,
            width=bar_width,
            color=color,
            edgecolor="white",
            linewidth=0.8,
        )
        bottom += capex_contribution
        unit_handles.append(Patch(facecolor=color, edgecolor="white", label=unit_label))

    for idx, (_, row) in enumerate(cost_breakdown.iterrows()):
        color = palette[idx % len(palette)]
        opex_contribution = float(row["opex_lcow_contribution"])
        ax.bar(
            [bar_x],
            [opex_contribution],
            bottom=bottom,
            width=bar_width,
            color=color,
            edgecolor="#333333",
            linewidth=0.8,
            hatch="///",
        )
        bottom += opex_contribution

    style_handles = [
        Patch(facecolor="#d9d9d9", edgecolor="white", label="CAPEX contribution"),
        Patch(facecolor="#d9d9d9", edgecolor="#333333", hatch="///", label="OPEX contribution"),
    ]

    ax.set_ylabel(f"LCOW contribution ({lcow_unit})")
    ax.set_xticks([bar_x])
    ax.set_xticklabels(["LCOW"])
    ax.set_xlim(-0.55, 0.55)
    ax.set_ylim(0, max(bottom * 1.12, 0.01))
    ax.grid(axis="y", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(
        handles=style_handles + unit_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
        fontsize=8,
    )
    fig.subplots_adjust(bottom=0.32)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_energy_breakdown(unit_results):
    st.subheader("Energy breakdown")
    required_columns = {
        "electricity_intensity_kwh_per_bbl_feed",
        "thermal_energy_intensity_kwh_per_bbl_feed",
    }
    if not required_columns.issubset(unit_results.columns):
        st.info("Run TEA Calculation again to generate energy breakdown results.")
        return

    energy_breakdown = unit_results.sort_values("sequence").copy()
    if plt is None or Patch is None:
        st.warning(
            "The chart could not be loaded because Matplotlib is unavailable in the "
            "Python environment running Streamlit. The same breakdown is shown below."
        )
        fallback = energy_breakdown.set_index(
            energy_breakdown.apply(
                lambda row: f"{int(row['sequence'])}. {row['unit_process']}", axis=1
            )
        )[
            [
                "electricity_intensity_kwh_per_bbl_feed",
                "thermal_energy_intensity_kwh_per_bbl_feed",
            ]
        ].rename(
            columns={
                "electricity_intensity_kwh_per_bbl_feed": "Electricity (kWh/bbl feed)",
                "thermal_energy_intensity_kwh_per_bbl_feed": "Thermal energy (kWh/bbl feed)",
            }
        )
        st.bar_chart(fallback)
        st.caption(f"Matplotlib import error: {MATPLOTLIB_IMPORT_ERROR}")
        return

    fig, ax = plt.subplots(figsize=BREAKDOWN_FIGSIZE)
    palette = [
        "#1f77b4",
        "#aec7e8",
        "#ff7f0e",
        "#ffbb78",
        "#2ca02c",
        "#98df8a",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#17becf",
    ]
    bar_x = 0
    bar_width = BREAKDOWN_BAR_WIDTH
    electricity_bottom = 0.0
    thermal_bottom = 0.0
    unit_handles = []

    for idx, (_, row) in enumerate(energy_breakdown.iterrows()):
        color = palette[idx % len(palette)]
        unit_label = f"{int(row['sequence'])}. {row['unit_process']}"
        electricity_intensity = float(row.get("electricity_intensity_kwh_per_bbl_feed", 0.0) or 0.0)
        thermal_intensity = float(row.get("thermal_energy_intensity_kwh_per_bbl_feed", 0.0) or 0.0)
        if electricity_intensity > 0.0:
            ax.bar(
                [bar_x],
                [electricity_intensity],
                bottom=electricity_bottom,
                width=bar_width,
                color=color,
                edgecolor="white",
                linewidth=0.8,
            )
            electricity_bottom += electricity_intensity
        if thermal_intensity > 0.0:
            ax.bar(
                [bar_x + bar_width * 1.25],
                [thermal_intensity],
                bottom=thermal_bottom,
                width=bar_width,
                color=color,
                edgecolor="#333333",
                linewidth=0.8,
                hatch="///",
            )
            thermal_bottom += thermal_intensity
        if electricity_intensity > 0.0 or thermal_intensity > 0.0:
            unit_handles.append(Patch(facecolor=color, edgecolor="white", label=unit_label))

    style_handles = [
        Patch(facecolor="#d9d9d9", edgecolor="white", label="Electricity"),
        Patch(facecolor="#d9d9d9", edgecolor="#333333", hatch="///", label="Thermal energy"),
    ]
    total_intensity = max(electricity_bottom, thermal_bottom, 0.01)

    ax.set_ylabel("Specific energy consumption (kWh/bbl feed)")
    ax.set_xticks([bar_x, bar_x + bar_width * 1.25])
    ax.set_xticklabels(["Electricity", "Thermal energy"])
    ax.set_xlim(-0.35, bar_x + bar_width * 1.25 + 0.35)
    ax.set_ylim(0, total_intensity * 1.12)
    ax.grid(axis="y", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(
        handles=style_handles + unit_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
        fontsize=8,
    )
    fig.subplots_adjust(bottom=0.32)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


if "tea_results" not in st.session_state:
    st.warning("Please run the TEA calculation on the System Design page first.")
    if st.button("Back to System Design"):
        st.switch_page("pages/03_System_Design.py")
    st.stop()

results = st.session_state.tea_results

summary_values = {
    "Total CAPEX": f"${results['total_capital_cost']:,.0f}",
    "Annual OPEX": f"${results['total_annual_operating_cost']:,.0f}/yr",
    "Electricity power": f"{results.get('electricity_power_requirement_kw', 0.0):,.1f} kW",
    "Thermal power": f"{results.get('thermal_power_requirement_kw', 0.0):,.1f} kW",
}
transportation_cost = results.get("transportation_cost", {})
annual_transportation_cost = float(transportation_cost.get("annual_transportation_cost", 0.0) or 0.0)
if annual_transportation_cost > 0.0:
    summary_values["Annual transportation cost"] = f"${annual_transportation_cost:,.0f}/yr"

summary_values.update({
    "Product flow": (
        f"{results['final_product_flow']:,.1f} "
        f"{results.get('final_product_flow_unit', 'm3/day')}"
    ),
    "LCOW": format_lcow(
        results["levelized_cost_of_water"],
        results.get("levelized_cost_unit", "$/m3 feed"),
    ),
    "LCOW product": format_lcow(product_lcow_bbl(results), "$/bbl product"),
})

render_summary_cells(summary_values)

unit_results = pd.DataFrame([
    {k: v for k, v in row.items() if k not in ["technical_results", "cost_results"]}
    for row in results["unit_results"]
])
results_table = pd.DataFrame(results.get("results_csv_rows", []))

breakdown_cols = st.columns(2)
with breakdown_cols[0]:
    render_lcow_cost_breakdown(unit_results, results.get("levelized_cost_unit", "$/m3 feed"))
with breakdown_cols[1]:
    render_energy_breakdown(unit_results)

st.subheader("Unit process modeling results")

for unit_result in sorted(results["unit_results"], key=lambda row: row["sequence"]):
    label = (
        f"{unit_result['sequence']}. "
        f"{unit_result['section']} - {unit_result['unit_process']}"
    )
    st.markdown(f"**{label}**")
    tech_col, cost_col = st.columns(2)

    with tech_col:
        st.markdown("_Technical outputs_")
        technical_outputs = unit_output_table(results_table, unit_result, "technical")
        if (
            unit_result["unit_process"] == "MVC"
            and not has_result(technical_outputs, "brine_salinity")
        ):
            st.warning(
                "MVC surrogate outputs are not in this saved result. "
                "Run TEA Calculation again on the System Design page."
            )
        st.dataframe(
            format_output_table(technical_outputs, mode="technical"),
            hide_index=True,
            height=display_height(technical_outputs),
            use_container_width=True,
        )

    with cost_col:
        st.markdown("_Cost outputs_")
        cost_outputs = unit_output_table(results_table, unit_result, "cost")
        st.dataframe(
            format_output_table(cost_outputs, mode="cost"),
            hide_index=True,
            height=display_height(cost_outputs),
            use_container_width=True,
        )

    if unit_result["section"] == "Desalination":
        brine_water_quality = brine_water_quality_for_result(unit_result)
        product_wq_col, product_scaling_col = st.columns([1, 1])
        with product_wq_col:
            wq_button_key = f"show_product_water_quality_{unit_result['sequence']}"
            if st.button("Show product water quality", key=wq_button_key, type="primary"):
                show_water_quality_dialog(unit_result, "Product water")
        with product_scaling_col:
            scaling_button_key = f"show_product_scaling_tendency_{unit_result['sequence']}"
            if st.button("Show product water scaling tendency", key=scaling_button_key, type="primary"):
                show_scaling_tendency_dialog(unit_result, "Product water")
        brine_wq_col, brine_scaling_col = st.columns([1, 1])
        with brine_wq_col:
            brine_wq_button_key = f"show_brine_water_quality_{unit_result['sequence']}"
            if st.button("Show brine water quality", key=brine_wq_button_key, type="primary"):
                show_water_quality_dialog(
                    unit_result,
                    "Brine water",
                    outlet_quality=brine_water_quality,
                )
        with brine_scaling_col:
            brine_scaling_button_key = f"show_brine_scaling_tendency_{unit_result['sequence']}"
            if st.button("Show brine scaling tendency", key=brine_scaling_button_key, type="primary"):
                show_scaling_tendency_dialog(
                    unit_result,
                    "Brine water",
                    water_quality=brine_water_quality,
                )
    else:
        wq_button_col, scaling_button_col = st.columns([1, 1])
        with wq_button_col:
            wq_button_key = f"show_water_quality_{unit_result['sequence']}"
            if st.button("Show outlet water quality", key=wq_button_key, type="primary"):
                show_water_quality_dialog(unit_result)
        with scaling_button_col:
            scaling_button_key = f"show_scaling_tendency_{unit_result['sequence']}"
            if st.button("Show scaling tendency", key=scaling_button_key, type="primary"):
                show_scaling_tendency_dialog(unit_result)

csv = build_results_download_csv(results).encode("utf-8")
st.session_state.tea_results_csv = csv
st.download_button(
    "Download TEA results CSV",
    csv,
    file_name=st.session_state.get("tea_results_filename", f"{safe_project_filename(project_name)}_tea_results.csv"),
    mime="text/csv",
)

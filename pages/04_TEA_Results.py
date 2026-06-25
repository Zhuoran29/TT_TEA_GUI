import pandas as pd
import streamlit as st
from config import APP_VERSION, DATA_VERSION
from matplotlib import pyplot as plt
from matplotlib.patches import Patch
from tea_models.scaling_tendency import calculate_scaling_tendency
from tea_models.water_quality import calculate_brine_quality, water_quality_comparison_table
from treatment_config import ALL_WATER_QUALITY_PARAMS


st.set_page_config(page_title="04_TEA_Results", layout="wide")

st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

BREAKDOWN_FIGSIZE = (7.2, 5.8)
BREAKDOWN_BAR_WIDTH = 0.22

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

st.header("TEA results")

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
            text-align: center;
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
                    <div class="tea-summary-label">{name}</div>
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


def format_model_value(value, mode):
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return value
    if pd.isna(numeric_value):
        return ""
    if mode == "cost":
        return f"{numeric_value:,.0f}"
    if abs(numeric_value) > 10:
        return f"{numeric_value:,.1f}"
    return f"{numeric_value:.3g}"


def format_output_table(table, mode="technical"):
    """Apply display-only labels and column names for model output tables."""
    if table.empty:
        return pd.DataFrame(columns=["Output parameters", "Value", "Unit"])

    output = table.copy()
    output["result_name"] = output["result_name"].apply(format_output_parameter)
    output["value"] = output["value"].apply(lambda value: format_model_value(value, mode))
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

csv = st.session_state.get(
    "tea_results_csv",
    results_table.to_csv(index=False).encode("utf-8"),
)
st.download_button(
    "Download TEA results CSV",
    csv,
    file_name=st.session_state.get("tea_results_filename", f"{safe_project_filename(project_name)}_tea_results.csv"),
    mime="text/csv",
)

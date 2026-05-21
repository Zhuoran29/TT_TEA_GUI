from pathlib import Path

import pandas as pd
import streamlit as st

from tea_models.registry import run_cost_model, run_technical_model


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
</style>
""", unsafe_allow_html=True)


APP_ROOT = Path(__file__).resolve().parents[1]
TECHNICAL_INPUT_PATH = APP_ROOT / "data" / "input_tables" / "technical_inputs.csv"
COST_INPUT_PATH = APP_ROOT / "data" / "input_tables" / "cost_inputs.csv"
RESULTS_OUTPUT_PATH = APP_ROOT / "data" / "results" / "tea_results.csv"
BBL_TO_M3 = 0.158987294928


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


def get_inputs_for_unit(table, unit_process):
    """Return unit-specific rows when present, otherwise use DEFAULT rows."""
    default_rows = table[table["unit_process"] == "DEFAULT"].copy()
    unit_rows = table[table["unit_process"] == unit_process].copy()

    if unit_rows.empty:
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


def flatten_model_results(sequence, section, unit_process, model_type, model_results):
    """Convert nested model outputs into rows for the results CSV."""
    rows = []
    for result_name, result in model_results.items():
        if not isinstance(result, dict):
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
        ("final_product_flow", results["final_product_flow"], "m3/day"),
        ("levelized_cost_of_water", results["levelized_cost_of_water"], "USD/m3"),
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


def calculate_lcow(ordered_units, technical_tables, cost_tables, context):
    """Run the modular TEA calculation across all unit processes.

    Each unit process first calls a technical model from
    tea_models/technical_models, then passes that technical result into a cost
    model from tea_models/cost_models. If no unit-specific model exists, the
    default model in each folder is used.
    """
    stream = {"flow_m3_day": float(context["feed_flow_m3_day"])}
    unit_results = []
    total_capital_cost = 0.0
    total_annual_operating_cost = 0.0
    project_life_years = float(context["project_life_years"])

    for unit in ordered_units:
        unit_process = unit["unit_process"]
        technical_inputs = table_to_input_dict(technical_tables[unit["sequence"]])
        cost_inputs = table_to_input_dict(cost_tables[unit["sequence"]])

        technical_result = run_technical_model(unit_process, technical_inputs, stream)
        cost_result = run_cost_model(unit_process, technical_result, cost_inputs, context)

        capital_cost = result_value(cost_result, "installed_capital_cost")
        annualized_capital_cost = capital_cost / project_life_years
        annual_operating_cost = result_value(cost_result, "total_annual_operating_cost")
        outlet_flow = result_value(technical_result, "outlet_flow")

        total_capital_cost += capital_cost
        total_annual_operating_cost += annual_operating_cost
        stream = {"flow_m3_day": outlet_flow}

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
    annualized_capital_cost = total_capital_cost / project_life_years
    total_annual_cost = annualized_capital_cost + total_annual_operating_cost
    annual_product_volume = max(stream["flow_m3_day"] * operating_days, 1e-9)
    lcow = total_annual_cost / annual_product_volume

    for unit_result in unit_results:
        unit_result["capital_lcow_contribution"] = (
            unit_result["annualized_capital_cost"] / annual_product_volume
        )
        unit_result["capital_lcow_contribution_unit"] = "USD/m3"
        unit_result["opex_lcow_contribution"] = (
            unit_result["total_annual_operating_cost"] / annual_product_volume
        )
        unit_result["opex_lcow_contribution_unit"] = "USD/m3"

    results = {
        "total_capital_cost": total_capital_cost,
        "annualized_capital_cost": annualized_capital_cost,
        "total_annual_operating_cost": total_annual_operating_cost,
        "total_annual_cost": total_annual_cost,
        "final_product_flow": stream["flow_m3_day"],
        "levelized_cost_of_water": lcow,
        "unit_results": unit_results,
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

st.markdown("Configure each unit process in order. Technical inputs and cost inputs are stored as editable tables and passed into modular unit-process models.")

feed_flow_bbl_day = st.number_input(
    "Feed flow rate (bbl/day)",
    min_value=0.0,
    value=float(st.session_state.get("wq_flow", 1000.0)),
    key="tea_feed_flow_bbl_day",
)

context_cols = st.columns(3)
with context_cols[0]:
    operating_days = st.number_input("Operating days/year", min_value=1, value=330, key="tea_operating_days")
with context_cols[1]:
    project_life = st.number_input("Project life (years)", min_value=1, value=10, key="tea_project_life")
with context_cols[2]:
    feed_flow_m3_day = feed_flow_bbl_day * BBL_TO_M3
    st.metric("Feed flow", f"{feed_flow_m3_day:,.1f} m3/day")

technical_tables = {}
cost_tables = {}

for unit in ordered_units:
    label = f"{unit['sequence']}. {unit['section']} - {unit['unit_process']}"
    st.subheader(label)
    tech_col, cost_col = st.columns(2)

    technical_rows = get_inputs_for_unit(technical_template, unit["unit_process"])
    cost_rows = get_inputs_for_unit(cost_template, unit["unit_process"])

    with tech_col:
        st.markdown("**Technical input table**")
        technical_tables[unit["sequence"]] = render_grouped_input_tables(
            technical_rows,
            f"technical_inputs_{unit['sequence']}_{unit['unit_process']}",
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
    "operating_days_per_year": operating_days,
    "project_life_years": project_life,
}

if st.button("Run TEA Calculation", type="primary"):
    results = calculate_lcow(ordered_units, technical_tables, cost_tables, context)
    results_table = pd.DataFrame(results["results_csv_rows"])
    RESULTS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_filename = f"{safe_project_filename(project_name)}_tea_results.csv"
    results_table.to_csv(RESULTS_OUTPUT_PATH.parent / results_filename, index=False)
    st.session_state.tea_context = context
    st.session_state.tea_unit_inputs = {
        "technical": {k: v.to_dict("records") for k, v in technical_tables.items()},
        "cost": {k: v.to_dict("records") for k, v in cost_tables.items()},
    }
    st.session_state.tea_results = results
    st.session_state.tea_results_csv = results_table.to_csv(index=False).encode("utf-8")
    st.session_state.tea_results_filename = results_filename
    st.success("TEA calculation completed.")

if "tea_results" in st.session_state:
    results = st.session_state.tea_results
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.metric("Total CAPEX", f"${results['total_capital_cost']:,.0f}")
    with metric_cols[1]:
        st.metric("Annual OPEX", f"${results['total_annual_operating_cost']:,.0f}/yr")
    with metric_cols[2]:
        st.metric("Product flow", f"{results['final_product_flow']:,.1f} m3/day")
    with metric_cols[3]:
        st.metric("LCOW", f"${results['levelized_cost_of_water']:,.2f}/m3")

    unit_summary = pd.DataFrame([
        {k: v for k, v in row.items() if k not in ["technical_results", "cost_results"]}
        for row in results["unit_results"]
    ])
    st.dataframe(unit_summary, use_container_width=True)

    st.download_button(
        "Download TEA results CSV",
        st.session_state.get("tea_results_csv", b""),
        file_name=st.session_state.get("tea_results_filename", f"{safe_project_filename(project_name)}_tea_results.csv"),
        mime="text/csv",
    )

    if st.button("TEA Results ->", type="secondary"):
        st.switch_page("pages/04_TEA_Results.py")

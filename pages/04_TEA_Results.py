import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt
from matplotlib.patches import Patch


st.set_page_config(page_title="04_TEA_Results", layout="wide")

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

if "tea_results" not in st.session_state:
    st.warning("Please run the TEA calculation on the System Design page first.")
    if st.button("Back to System Design"):
        st.switch_page("pages/03_System_Design.py")
    st.stop()

results = st.session_state.tea_results
context = st.session_state.get("tea_context", {})

metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("Total CAPEX", f"${results['total_capital_cost']:,.0f}")
with metric_cols[1]:
    st.metric("Annual OPEX", f"${results['total_annual_operating_cost']:,.0f}/yr")
with metric_cols[2]:
    st.metric("Product flow", f"{results['final_product_flow']:,.1f} m3/day")
with metric_cols[3]:
    st.metric("LCOW", f"${results['levelized_cost_of_water']:,.2f}/m3")

st.subheader("Calculation context")
st.dataframe(pd.DataFrame([context]), use_container_width=True)

st.subheader("Unit process results")
unit_results = pd.DataFrame([
    {k: v for k, v in row.items() if k not in ["technical_results", "cost_results"]}
    for row in results["unit_results"]
])
st.dataframe(unit_results, use_container_width=True)

st.subheader("LCOW cost breakdown")
cost_breakdown = unit_results.sort_values("sequence").copy()
fig, ax = plt.subplots(figsize=(12, 3.8))
palette = list(plt.get_cmap("tab20").colors)
bottom = 0.0
unit_handles = []

for idx, (_, row) in enumerate(cost_breakdown.iterrows()):
    color = palette[idx % len(palette)]
    unit_label = f"{int(row['sequence'])}. {row['unit_process']}"
    capex_contribution = float(row["capital_lcow_contribution"])
    ax.bar(
        ["LCOW"],
        [capex_contribution],
        bottom=bottom,
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
        ["LCOW"],
        [opex_contribution],
        bottom=bottom,
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

ax.set_ylabel("LCOW contribution (USD/m3)")
ax.set_ylim(0, max(bottom * 1.12, 0.01))
ax.grid(axis="y", alpha=0.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(
    handles=style_handles + unit_handles,
    loc="upper left",
    bbox_to_anchor=(1.01, 1.0),
    frameon=False,
)
fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)

st.subheader("Results CSV")
results_table = pd.DataFrame(results.get("results_csv_rows", []))
st.dataframe(results_table, use_container_width=True)

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

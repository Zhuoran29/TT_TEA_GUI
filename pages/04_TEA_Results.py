import pandas as pd
import streamlit as st


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
    file_name="tea_results.csv",
    mime="text/csv",
)

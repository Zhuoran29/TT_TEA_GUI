import streamlit as st
import pandas as pd

st.set_page_config(page_title="14_TEA_Results", layout="wide")

# Apple-style CSS
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

st.header("Step 4 — TEA results")

if "treatment_train" not in st.session_state:
    st.warning("Please complete the previous steps and save (Home -> Treatment Train -> System Design).")
else:
    flow = st.session_state.get("wq_flow", 1000.0)
    days_per_year = st.sidebar.number_input("Operating days/year", min_value=1, value=330, key="tea_days")
    amort_years = st.sidebar.number_input("Amortization (years)", min_value=1, value=10, key="tea_amort")

    train = st.session_state.treatment_train
    units = []
    total_capex = 0.0
    total_opex_annual = 0.0

    for section, us in [("Pretreatment", train["pretreatment"]), ("Desalination", train["desalination"]), ("Post‑treatment", train["posttreatment"]), ("Brine management", [train["brine"]])]:
        for u in us:
            key_prefix = f"unit_{section}_{u}".replace(" ", "_")
            capex_per_m3 = st.session_state.get(key_prefix + "_capex", 50.0)
            opex_pct = st.session_state.get(key_prefix + "_opex_pct", 5.0)
            eff = st.session_state.get(key_prefix + "_eff", 0.95)
            # approximate: capex scales with capacity (flow m3/day)
            capex_unit = capex_per_m3 * flow
            opex_annual = capex_unit * (opex_pct / 100.0) * days_per_year
            total_capex += capex_unit
            total_opex_annual += opex_annual
            units.append({"section": section, "unit": u, "capex_estimated_$": capex_unit, "opex_annual_$": opex_annual, "efficiency": eff})

    annualized_capex = total_capex / amort_years
    total_annual_cost = annualized_capex + total_opex_annual
    cost_per_m3 = total_annual_cost / (flow * days_per_year)

    st.metric("Total CAPEX (approx $)", f"{total_capex:,.0f}")
    st.metric("Total OPEX /yr (approx $)", f"{total_opex_annual:,.0f}")
    st.metric("Levelized cost /m3 ($)", f"{cost_per_m3:.2f}")

    df = pd.DataFrame(units)
    st.dataframe(df)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download unit costs CSV", csv, file_name="tea_unit_costs.csv", mime="text/csv")
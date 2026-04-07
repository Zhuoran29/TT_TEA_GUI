import streamlit as st

st.set_page_config(page_title="03_System_Design", layout="wide")

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

st.header("System design & unit assumptions")

# Check if treatment train exists
if "treatment_train" not in st.session_state:
    st.warning("Please save the Treatment Train on the previous page before proceeding.")
    st.stop()

# Get treatment train
train = st.session_state.treatment_train

# Initialize session state for all units upfront
sections = [("Pretreatment", train["pretreatment"]), ("Desalination", train["desalination"]), ("Post-treatment", train["posttreatment"]), ("Brine management", [train["brine"]])]

for section, units in sections:
    for u in units:
        key_prefix = f"unit_{section}_{u}".replace(" ", "_").replace("‑", "-")
        capex_key = key_prefix + "_capex"
        opex_key = key_prefix + "_opex_pct"
        eff_key = key_prefix + "_eff"
        if capex_key not in st.session_state:
            st.session_state[capex_key] = 50.0
        if opex_key not in st.session_state:
            st.session_state[opex_key] = 5.0
        if eff_key not in st.session_state:
            st.session_state[eff_key] = 0.95

# Display input form
st.markdown("Design parameters for each unit (CAPEX: $/m³, OPEX: %/yr, Efficiency: 0-1)")

for section, units in sections:
    st.subheader(section)
    for u in units:
        key_prefix = f"unit_{section}_{u}".replace(" ", "_").replace("‑", "-")
        capex_key = key_prefix + "_capex"
        opex_key = key_prefix + "_opex_pct"
        eff_key = key_prefix + "_eff"
        
        # Display unit name
        st.write(f"**{u}**")
        
        # Three-column input
        cols = st.columns([1.5, 1.5, 1.5])
        with cols[0]:
            st.number_input("CAPEX ($/m³)", min_value=0.0, value=st.session_state.get(capex_key, 50.0), key=capex_key)
        with cols[1]:
            st.number_input("OPEX (%/yr)", min_value=0.0, max_value=100.0, value=st.session_state.get(opex_key, 5.0), key=opex_key)
        with cols[2]:
            st.number_input("Efficiency", min_value=0.0, max_value=1.0, value=st.session_state.get(eff_key, 0.95), key=eff_key)

# Save button
if st.button("TEA Results →", type="primary"):
    st.success("✓ System design parameters saved!")
    st.switch_page("pages/04_TEA_Results.py")
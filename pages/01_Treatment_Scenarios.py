import streamlit as st

st.set_page_config(page_title="Produced Water TEA — Home", layout="wide")

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

st.title("Fit-for-Purpose Treatment Scenarios")
st.markdown(
    "Choose the water treatment scenario.  \n\n"
)

# Initialize session state keys if not present
if "influent_type" not in st.session_state:
    st.session_state.influent_type = "Produced water"
if "ffp_scenarios" not in st.session_state:
    st.session_state.ffp_scenarios = ["Surface water discharge"]
if "desal_type" not in st.session_state:
    st.session_state.desal_type = "Mechanical Vapor Compression (MVC)"

# Display selection options
st.markdown("##### Influent type")
influent = st.selectbox(
    "Influent type", 
    ["Produced water", "Brackish groundwater"], 
    index=0,
    label_visibility="collapsed"
)

st.markdown("##### Concentration level")
concentration = st.selectbox(
    "Concentration level", 
    ["High", "Medium", "Low"], 
    index=0,
    label_visibility="collapsed"
)

st.markdown("##### Fit‑for‑purpose scenario")
ffp = st.selectbox(
    "Fit‑for‑purpose scenario",
    [
        "Agricultural use",
        "Surface water discharge",
        "Powerplant cooling water",
        "Data center cooling water",
        "Feedwater to UPW production",
        "Hydraulic fracturing reuse",
        "ZLD feed conditioning",
    ],
    index=0,
    label_visibility="collapsed"
)

st.markdown("##### Primary desalination type")
desal = st.selectbox("Primary desalination type", 
                    ["Mechanical Vapor Compression (MVC)", "Membrane desalination (MD)", "Low-salt rejection reverse osmosis (LSRRO)"],
                    index=0, label_visibility="collapsed")

# Next button with automatic session state save
if st.button("Configure Treatment Train →", type="primary"):
    st.session_state.influent_type = influent
    st.session_state.ffp_scenarios = [ffp]
    st.session_state.desal_type = desal
    st.session_state.conc_level = concentration
    st.success("✓ Selections saved! Moving to Treatment Train configuration...")
    st.switch_page("pages/02_Treatment_Trains.py")
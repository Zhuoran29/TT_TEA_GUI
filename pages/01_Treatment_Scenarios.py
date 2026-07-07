import streamlit as st
from config import APP_VERSION, DATA_VERSION
from feedback import render_report_button

st.set_page_config(page_title="Produced Water TEA — Home", layout="wide")

st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

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

title_col, report_col = st.columns([0.82, 0.18])
with title_col:
    st.title("Fit-for-Purpose Treatment Scenarios")
with report_col:
    render_report_button("Treatment scenarios", use_container_width=True)
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
if "project_name" not in st.session_state:
    st.session_state.project_name = "TEA project"

# Display selection options
st.markdown("##### Project name")
project_name = st.text_input(
    "Project name",
    value=st.session_state.project_name,
    label_visibility="collapsed",
    placeholder="Enter project name",
)

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
        "Drinking water quality oriented(e.g. groundwater recharge)",
        "Surface water discharge",
        "Powerplant cooling water",
        "Data center cooling water",
        "Feedwater to UPW production",
        "On-site O&G hydraulic fracturing recirculation",
        "Brine valorization(In progress)",
    ],
    index=0,
    label_visibility="collapsed"
)

st.markdown("##### Primary desalination type")
desal = st.selectbox("Primary desalination type", 
                    ["Mechanical Vapor Compression (MVC)", "Membrane desalination (MD)", "Low-salt rejection reverse osmosis (LSRRO)", "Reverse osmosis (RO)"],
                    index=0, label_visibility="collapsed")

# Next button with automatic session state save
if st.button("Configure Treatment Train →", type="primary"):
    st.session_state.project_name = project_name.strip() or "TEA project"
    st.session_state.influent_type = influent
    st.session_state.ffp_scenarios = [ffp]
    st.session_state.desal_type = desal
    st.session_state.conc_level = concentration
    st.success("✓ Selections saved! Moving to Treatment Train configuration...")
    st.switch_page("pages/02_Treatment_Trains.py")

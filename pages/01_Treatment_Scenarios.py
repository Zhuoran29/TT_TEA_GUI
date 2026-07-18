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


def option_index(options, value, default=0):
    try:
        return options.index(value)
    except ValueError:
        return default


def clear_downstream_state():
    for key in [
        "current_scenario_signature",
        "treatment_config_version",
        "treatment_pretreatment",
        "treatment_desalination",
        "treatment_posttreatment",
        "treatment_brine",
        "treatment_brine_category",
        "treatment_train",
        "treatment_train_scenario_signature",
        "tea_results",
        "tea_results_signature",
        "tea_results_csv",
        "tea_detailed_results_csv",
        "tea_results_filename",
        "tea_context",
        "tea_unit_inputs",
    ]:
        st.session_state.pop(key, None)

# Display selection options
st.markdown("##### Project name")
project_name = st.text_input(
    "Project name",
    value=st.session_state.project_name,
    label_visibility="collapsed",
    placeholder="Enter project name",
)

st.markdown("##### Influent type")
influent_options = ["Produced water", "Brackish groundwater"]
influent = st.selectbox(
    "Influent type", 
    influent_options,
    index=option_index(influent_options, st.session_state.influent_type),
    label_visibility="collapsed"
)

st.markdown("##### Concentration level")
concentration_options = ["High", "Medium", "Low"]
concentration = st.selectbox(
    "Concentration level", 
    concentration_options,
    index=option_index(concentration_options, st.session_state.get("conc_level", "High")),
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
    index=option_index(
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
        st.session_state.ffp_scenarios[0] if st.session_state.ffp_scenarios else "Surface water discharge",
    ),
    label_visibility="collapsed"
)

st.markdown("##### Primary desalination type")
desal = st.selectbox("Primary desalination type", 
                    ["Mechanical Vapor Compression (MVC)", "Vacuum membrane distillation (VMD)", "Low-salt rejection reverse osmosis (LSRRO)", "Brackish-water reverse osmosis (BWRO)"],
                    index=option_index(
                        ["Mechanical Vapor Compression (MVC)", "Vacuum membrane distillation (VMD)", "Low-salt rejection reverse osmosis (LSRRO)", "Brackish-water reverse osmosis (BWRO)"],
                        st.session_state.desal_type,
                    ), label_visibility="collapsed")

# Next button with automatic session state save
if st.button("Configure Treatment Train →", type="primary"):
    previous_signature = (
        st.session_state.get("influent_type"),
        st.session_state.get("ffp_scenarios", [""])[0] if st.session_state.get("ffp_scenarios") else "",
        st.session_state.get("desal_type"),
        st.session_state.get("conc_level"),
    )
    next_signature = (influent, ffp, desal, concentration)
    if previous_signature != next_signature:
        clear_downstream_state()
    st.session_state.project_name = project_name.strip() or "TEA project"
    st.session_state.influent_type = influent
    st.session_state.ffp_scenarios = [ffp]
    st.session_state.desal_type = desal
    st.session_state.conc_level = concentration
    st.success("✓ Selections saved! Moving to Treatment Train configuration...")
    st.switch_page("pages/02_Treatment_Trains.py")

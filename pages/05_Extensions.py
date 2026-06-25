import streamlit as st
from config import APP_VERSION, DATA_VERSION
from feedback import render_report_button
from ui_helpers import render_card_title

from pages.extensions.interactive_map_ui import render_interactive_map
from pages.extensions.socioeconomic_ui import render_socioeconomic_analysis


st.set_page_config(page_title="05_Extensions", layout="wide")

st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

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
    .extension-card-title {
        font-size: 1.15rem;
        font-weight: 750;
        margin-bottom: 0.15rem;
    }
    .extension-card-subtitle {
        color: #5F6C7B;
        font-size: 0.92rem;
        margin-bottom: 0.85rem;
    }
    .extension-section-label {
        color: #1F2933;
        font-size: 0.78rem;
        font-weight: 750;
        letter-spacing: 0.04em;
        margin-top: 0.8rem;
        text-transform: uppercase;
    }
    .extension-pill {
        display: inline-block;
        border: 1px solid #D9E2EC;
        border-radius: 999px;
        color: #334E68;
        background: #F7FAFC;
        font-size: 0.78rem;
        font-weight: 650;
        margin-bottom: 0.8rem;
        padding: 0.22rem 0.55rem;
    }
    .extension-muted {
        color: #5F6C7B;
        font-size: 0.92rem;
        line-height: 1.45;
    }
    .extension-list {
        margin-bottom: 0.15rem;
        padding-left: 1.15rem;
    }
    .extension-list li {
        margin-bottom: 0.35rem;
    }
</style>
""", unsafe_allow_html=True)


def render_extension_card(title, subtitle, inputs, outputs, target_view=None):
    with st.container(border=True):
        render_card_title(
            title,
            f"Open or review the {title} extension module for additional analysis connected to this TEA workflow.",
            key=f"help_extension_{title.replace(' ', '_').lower()}",
            html=f"<div class='extension-card-title'>{title}</div>",
        )
        st.markdown(f"<div class='extension-card-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
        if target_view and st.button(f"Open", key=f"open_{title.replace(' ', '_').lower()}", type="primary"):
            st.session_state.extension_view = target_view
            st.rerun()

        # st.markdown("<div class='extension-section-label'>Planned inputs</div>", unsafe_allow_html=True)
        # st.markdown(
        #     "<ul class='extension-list'>"
        #     + "".join(f"<li>{item}</li>" for item in inputs)
        #     + "</ul>",
        #     unsafe_allow_html=True,
        # )

        # st.markdown("<div class='extension-section-label'>Expected outputs</div>", unsafe_allow_html=True)
        # st.markdown(
        #     "<ul class='extension-list'>"
        #     + "".join(f"<li>{item}</li>" for item in outputs)
        #     + "</ul>",
        #     unsafe_allow_html=True,
        # )



title_col, report_col = st.columns([0.82, 0.18])
with title_col:
    st.header("Extensions")
with report_col:
    render_report_button("Extensions", use_container_width=True)

project_name = st.session_state.get("project_name", "TEA project")
st.caption(f"Project: {project_name}")

st.markdown(
    "Further analysis modules can be connected here after the base treatment train, "
    "system design, and TEA results are available."
)

st.divider()

if st.session_state.get("extension_view") == "socioeconomic":
    if st.button("Back to Extensions", type="primary"):
        st.session_state.extension_view = None
        st.rerun()
    render_socioeconomic_analysis()
    st.stop()

if st.session_state.get("extension_view") == "interactive_map":
    if st.button("Back to Extensions", type="primary"):
        st.session_state.extension_view = None
        st.rerun()
    render_interactive_map()
    st.stop()

left_col, right_col = st.columns(2)

with left_col:
    render_extension_card(
        title="Interactive Map",
        subtitle="Spatial project planning for New Mexico water treatment cases.",

        inputs=[
            # "Project site locations, water source points, wastewater treatment facilities, and disposal or reuse destinations.",
            # "Transportation mode, road distance assumptions, hauled volume, and optional route constraints.",
            # "Regional layers such as county boundaries, basins, infrastructure corridors, or sensitive receiving areas.",
        ],
        outputs=[
            # "Map-based scenario overview with selected assets and candidate routing paths.",
            # "Estimated transportation distance, hauling intensity, and added cost contribution.",
            # "Location-aware comparison between centralized, distributed, and hybrid treatment options.",
        ],
        target_view="interactive_map",
    )

    render_extension_card(
        title="Process Optimization",
        subtitle="Unit-level and train-level optimization using WaterTAP-compatible models.",
   
        inputs=[
            # "Selected treatment train, unit model parameters, bounds, and design constraints.",
            # "Objective function such as minimum LCOW, minimum energy intensity, maximum recovery, or multi-objective tradeoff.",
            # "WaterTAP model selections for individual technologies that can be optimized separately or as a linked train.",
        ],
        outputs=[
            # "Recommended operating setpoints and design values for selected unit processes.",
            # "Objective value, active constraints, convergence status, and model diagnostics.",
            # "Comparison between current TEA assumptions and optimized process assumptions.",
        ],
    )

with right_col:
    render_extension_card(
        title="Socio-economic Analysis",
        subtitle="Community, workforce, and regional impact indicators tied to TEA scenarios.",

        inputs=[
            # "Reference report assumptions, regional economic multipliers, and project deployment scale.",
            # "Capital spending, annual operating cost, labor categories, and supply-chain allocation assumptions.",
            # "Community context indicators such as county, population, employment, income, and water-stress context.",
        ],
        outputs=[
            # "Estimated jobs, value added, tax or revenue impacts, and local economic activity indicators.",
            # "Distribution of impacts by project phase, region, and stakeholder category.",
            # "Side-by-side socio-economic comparison for alternative treatment and reuse scenarios.",
        ],
        target_view="socioeconomic",
    )

    render_extension_card(
        title="Sensitivity Analysis",
        subtitle="Range-based exploration of uncertain assumptions and key result drivers.",

        inputs=[
            # "Target output variable such as LCOW, total CAPEX, annual OPEX, product flow, or energy intensity.",
            # "Input variables to perturb, including price assumptions, flow rate, recovery, removal efficiency, or unit costs.",
            # "Range definition using low/base/high values, percent change, or custom sweep points.",
        ],
        outputs=[
            # "Sensitivity table ranking variables by effect on the selected target output.",
            # "One-way or multi-way plots for cost, recovery, energy, and water quality outcomes.",
            # "Exportable scenario matrix for documentation and later uncertainty analysis.",
        ],
    )

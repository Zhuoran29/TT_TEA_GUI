import csv
import json
from pathlib import Path
from treatment_config import WATER_QUALITY_REQUIREMENTS, get_treatment_train_config, UNIT_REMOVAL_RATES, ALL_WATER_QUALITY_PARAMS, SIDEBAR_DEFAULTS, BRINE_MANAGEMENT_OPTIONS, normalize_treatment_train_config
from tea_models.water_quality import collect_feedwater_quality, parse_removal_rate as parse_config_removal_rate
import streamlit as st
from config import APP_VERSION, DATA_VERSION
from feedback import render_report_button
from ui_helpers import render_card_title

st.set_page_config(page_title="02_Treatment_Train", layout="wide")

PRETREATMENT_UNIT_OPTIONS = [
    "Well pumping",
    "Raw water storage",
    "Equalization tank",
    "3-phase separator",
    "DAF",
    "Floc n Drop",
    "Walnut shell filtration",
    "Media filtration",
    "Cartridge filter",
    "Bag filter",
    "Ultrafiltration",
    "Ultra-fine filtration",
    "Softening / pH adjustment",
    "Softening / silica control",
    "Antiscalant / pH adjustment",
    "Antiscalant dosing",
    "Air stripping",
    "Dechlorination / activated carbon",
]

DESALINATION_UNIT_OPTIONS = [
    "MVC",
    "Vacuum membrane distillation (VMD)",
    "LSRRO",
    "OARO",
    "BWRO",
    "NF",
]

POSTTREATMENT_UNIT_OPTIONS = [
    "Ammonia stripping",
    "GAC",
    "Zeolite",
    "Ion exchange / EDI",
    "Ion exchange",
    "Boron-selective IX",
    "ZIX-Zak IX",
    "KNeW ion exchange",
    "Selective ED",
    "Bipolar membrane ED",
    "Lithium adsorption",
    "Mineral precipitation / recovery",
    "Chemical precipitation",
    "Acid/base recovery",
    "Fertilizer recovery",
    "Chlorination",
    "Polishing filter",
    "Fine filter",
    "Polishing",
    "Final filter",
    "pH adjustment",
    "pH adjustment for ammonia stripping",
    "pH adjustment for product water",
    "Scale inhibitor dosing",
    "Biocide dosing",
    "Blending / remineralization",
    "Blending / salinity adjustment",
    "Adjust TDS",
    "Additives blending",
    "Add additives",
    "Hardness adjustment",
    "Scale control",
]


def stage_options(options, current_unit=None):
    """Return stage-specific options while preserving existing session selections."""
    stage_specific = [unit for unit in options if unit in UNIT_REMOVAL_RATES]
    if current_unit and current_unit not in stage_specific:
        stage_specific.append(current_unit)
    return stage_specific



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
    st.header("Treatment train configuration")
with report_col:
    render_report_button("Treatment train configuration", use_container_width=True)

# defaults if not set
if "influent_type" not in st.session_state:
    st.session_state.influent_type = "Produced water"
if "ffp_scenarios" not in st.session_state:
    st.session_state.ffp_scenarios = ["Surface water discharge"]
if "desal_type" not in st.session_state:
    st.session_state.desal_type = "Mechanical Vapor Compression (MVC)"
if "conc_level" not in st.session_state:
    st.session_state.conc_level = "High"
if "project_name" not in st.session_state:
    st.session_state.project_name = "TEA project"

st.caption(f"Project: {st.session_state.project_name}")

# Display water quality requirements in a box
influent = st.session_state.influent_type
desal = st.session_state.desal_type
ffp_primary = st.session_state.ffp_scenarios[0] if st.session_state.ffp_scenarios else "Surface water discharge"

# Get water quality requirements and treatment train config
requirements = WATER_QUALITY_REQUIREMENTS.get(ffp_primary, {})
train_config = get_treatment_train_config(ffp_primary, desal, influent)

pretreatment = train_config["pretreatment"]
desalination = train_config["desalination"]
posttreatment = train_config["posttreatment"]
brine_default = train_config["brine"]
brine_category_default = train_config.get("brine_category", "Brine disposal")

# Set default brine option
brine_option = brine_default
brine_category = brine_category_default

if requirements:
    # Brine management radio button
    st.markdown("##### Brine management approach")
    brine_options = list(BRINE_MANAGEMENT_OPTIONS.keys())
    try:
        default_index = brine_options.index(brine_category_default)
    except ValueError:
        default_index = 0
    brine_category = st.radio("", brine_options, index=default_index, label_visibility="collapsed", horizontal=True)

# Helper function to parse removal rates from string
def parse_removal_rate(rate_str):
    """Parse removal rates using the same parser as the technical models."""
    return parse_config_removal_rate(rate_str)


def parse_ph_target(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def dot_string(value):
    return json.dumps(str(value))


def clear_tea_results_cache():
    for key in [
        "tea_results",
        "tea_results_signature",
        "tea_results_csv",
        "tea_detailed_results_csv",
        "tea_results_filename",
        "tea_context",
        "tea_unit_inputs",
    ]:
        st.session_state.pop(key, None)


def format_percent(value):
    return f"{value * 100.0:.1f}%"


def unit_tooltip_text(unit, removal_info, tracked_constituent=None):
    lines = [unit, f"Default recovery: {format_percent(default_recovery_for_unit(unit))}"]
    if removal_info:
        lines.append("Removal efficiencies:")
        ordered_items = list(removal_info.items())
        if tracked_constituent in removal_info:
            ordered_items = [
                (tracked_constituent, removal_info[tracked_constituent]),
                *[(name, rate) for name, rate in ordered_items if name != tracked_constituent],
            ]
        for constituent, rate in ordered_items:
            if constituent == "pH":
                ph_target = parse_ph_target(rate)
                parsed_text = f" (target pH {ph_target:g})" if ph_target is not None else ""
            else:
                parsed_rate = parse_removal_rate(rate)
                parsed_text = f" ({format_percent(parsed_rate)})" if parsed_rate > 0.0 else ""
            lines.append(f"- {constituent}: {rate}{parsed_text}")
    else:
        lines.append("No constituent removal assumed.")

    if tracked_constituent and tracked_constituent not in removal_info:
        lines.append(f"Tracked {tracked_constituent}: no removal assumed in this unit.")
    return "\\n".join(lines)


@st.cache_data
def load_default_recoveries():
    recoveries = {"DEFAULT": 0.95}
    input_path = Path(__file__).resolve().parents[1] / "data" / "input_tables" / "technical_inputs.csv"
    try:
        with input_path.open(newline="", encoding="utf-8") as input_file:
            for row in csv.DictReader(input_file):
                if row.get("parameter") != "recovery":
                    continue
                try:
                    recoveries[row.get("unit_process", "DEFAULT")] = float(row.get("value", 0.95))
                except (TypeError, ValueError):
                    continue
    except OSError:
        pass
    return recoveries


def default_recovery_for_unit(unit):
    recoveries = load_default_recoveries()
    return max(0.0, min(recoveries.get(unit, recoveries.get("DEFAULT", 0.95)), 0.999999))


def calculate_brine_concentration(tracked_constituent, inlet_conc, outlet_conc, recovery):
    if tracked_constituent == "pH":
        return 8.5
    if inlet_conc is None or outlet_conc is None:
        return None

    brine_fraction = 1.0 - recovery
    if brine_fraction <= 0.0:
        return None
    return max((inlet_conc - outlet_conc * recovery) / brine_fraction, 0.0)

# Generate flowchart dynamically based on actual units
def generate_treatment_flowchart(influent_name, scenario_name, pretreat_list, desal_list, posttreat_list, brine_name, tracked_constituent=None, feed_concentration=None):
    """Generate a graphviz flowchart that adapts to the number of units in each stage"""
    
    constituent_unit = ALL_WATER_QUALITY_PARAMS.get(tracked_constituent, {}).get("unit", "")
    if isinstance(brine_name, list):
        brine_list = brine_name
    elif brine_name:
        brine_list = [brine_name]
    else:
        brine_list = ["No brine unit selected"]

    # Helper function to create nodes and connections for a stage
    def create_stage_nodes(
        stage_prefix,
        stage_name,
        unit_list,
        color,
        current_conc=None,
        track_brine=False,
        first_node_conc=None,
    ):
        """Create nodes and connections for a treatment stage"""
        node_defs = f"\n subgraph cluster_{stage_prefix} {{\n"
        node_defs += f'  label="{stage_name}"; style=filled; color={color}; penwidth=2; pad=0.2;\n'
        
        node_ids = []
        concentrations = {}  # Track concentration after each unit
        brine_conc = None
        
        for i, unit in enumerate(unit_list):
            node_id = f"{stage_prefix}{i+1}"
            node_ids.append(node_id)
            
            removal_info = UNIT_REMOVAL_RATES.get(unit, {})
            tooltip_text = unit_tooltip_text(unit, removal_info, tracked_constituent)
            
            # Calculate outlet concentration if tracking a constituent
            outlet_label = unit
            use_html_label = False
            if tracked_constituent and first_node_conc is not None and i == 0:
                session_key = f"wq_target_{tracked_constituent}".replace(" ", "_")
                target_value = st.session_state.get(session_key, ALL_WATER_QUALITY_PARAMS.get(tracked_constituent, {}).get("limit", first_node_conc))
                color = "red" if first_node_conc > target_value else "green"
                outlet_label = f"{unit}<BR/><FONT COLOR='{color}'>Brine {tracked_constituent}: {first_node_conc:.2f} {constituent_unit}</FONT>"
                use_html_label = True
            if tracked_constituent and current_conc is not None:
                inlet_conc = current_conc
                if tracked_constituent in removal_info:
                    if tracked_constituent == "pH":
                        ph_target = parse_ph_target(removal_info[tracked_constituent])
                        outlet_conc = ph_target if ph_target is not None else current_conc
                    else:
                        removal_rate = parse_removal_rate(removal_info[tracked_constituent])
                        outlet_conc = current_conc * (1 - removal_rate)
                    concentrations[node_id] = outlet_conc
                    session_key = f"wq_target_{tracked_constituent}".replace(" ", "_")
                    # Get target value from session state, default to requirement limit
                    target_value = st.session_state.get(session_key, ALL_WATER_QUALITY_PARAMS.get(tracked_constituent, {}).get("limit", current_conc))
                    color = "red" if outlet_conc > target_value else "green"
                    outlet_label = f"{unit}<BR/><FONT COLOR='{color}'>{tracked_constituent}: {outlet_conc:.2f} {constituent_unit}</FONT>"
                    use_html_label = True
                    current_conc = outlet_conc
                else:
                    concentrations[node_id] = current_conc
                    outlet_conc = current_conc
                    session_key = f"wq_target_{tracked_constituent}".replace(" ", "_")
                    target_value = st.session_state.get(session_key, ALL_WATER_QUALITY_PARAMS.get(tracked_constituent, {}).get("limit", current_conc))
                    color = "red" if outlet_conc > target_value else "green"
                    outlet_label = f"{unit}<BR/><FONT COLOR='{color}'>{tracked_constituent}: {outlet_conc:.2f} {constituent_unit}</FONT>"
                    use_html_label = True
                if track_brine:
                    recovery = default_recovery_for_unit(unit)
                    brine_conc = calculate_brine_concentration(
                        tracked_constituent,
                        inlet_conc,
                        outlet_conc,
                        recovery,
                    )
            
            if use_html_label:
                node_defs += f'  {node_id} [label=<{outlet_label}>, tooltip={dot_string(tooltip_text)}];\n'
            else:
                node_defs += f'  {node_id} [label={dot_string(outlet_label)}, tooltip={dot_string(tooltip_text)}];\n'
        
        # Create connections between nodes in this stage
        for i in range(len(node_ids) - 1):
            node_defs += f"  {node_ids[i]} -> {node_ids[i+1]};\n"
        
        node_defs += " }\n"
        return node_defs, node_ids, current_conc, brine_conc
    
    # Build the complete DOT graph
    dot = "digraph G {\n"
    dot += " rankdir=TB;\n"
    dot += " node [shape=box, style=rounded, fillcolor=lightblue, style=filled, fontname=Arial, align=center];\n"
    
    # Add feed concentration to influent label if tracking
    influent_label = f"{influent_name}\\n({scenario_name})"
    current_conc = feed_concentration
    session_key = f"wq_target_{tracked_constituent}".replace(" ", "_") if tracked_constituent else None
    # Get target value from session state, default to requirement limit
    target_value = st.session_state.get(session_key, ALL_WATER_QUALITY_PARAMS.get(tracked_constituent, {}).get("limit", current_conc)) if tracked_constituent else 0
    color = "red" if current_conc and target_value and current_conc > target_value else "green"
    if tracked_constituent and feed_concentration is not None:
        influent_label_base = f"{influent_name}<BR/>({scenario_name})<BR/><FONT COLOR='{color}'>{tracked_constituent}: {feed_concentration:.2f} {constituent_unit}</FONT>"
        dot += f' Influent [label=<{influent_label_base}>, fillcolor=lightgreen];\n'
    else:
        dot += f' Influent [label="{influent_label}", fillcolor=lightgreen];\n'
    
    dot += " // Pretreatment units\n"
    
    # Pretreatment stage (using PT prefix to avoid collision with Post-treatment)
    pre_dot, pre_nodes, current_conc, _ = create_stage_nodes("PT", "Pretreatment", pretreat_list, "lightgrey", current_conc)
    dot += pre_dot
    
    # Desalination stage
    desal_dot, desal_nodes, current_conc, brine_conc = create_stage_nodes(
        "D",
        "Desalination",
        desal_list,
        "lightyellow",
        current_conc,
        track_brine=True,
    )
    dot += desal_dot
    
    # Post-treatment stage (using PST prefix to distinguish from Pretreatment)
    post_dot, post_nodes, current_conc, _ = create_stage_nodes("PST", "Post-treatment", posttreat_list, "lightcyan", current_conc)
    dot += post_dot
    
    # Brine management stage
    brine_dot, brine_nodes, _, _ = create_stage_nodes(
        "B",
        "Brine management",
        brine_list,
        "lightcoral",
        None,
        first_node_conc=brine_conc,
    )
    dot += brine_dot
    
    # Add Product Water label with final concentration if tracking
    if tracked_constituent and current_conc is not None:
        session_key = f"wq_target_{tracked_constituent}".replace(" ", "_")
        # Get target value from session state, default to requirement limit
        target_value = st.session_state.get(session_key, ALL_WATER_QUALITY_PARAMS.get(tracked_constituent, {}).get("limit", current_conc))
        color = "red" if current_conc > target_value else "green"
        product_label = f"Product Water<BR/><FONT COLOR='{color}'>{tracked_constituent}: {current_conc:.2f} {constituent_unit}</FONT>"
        dot += f' Product_Water [label=<{product_label}>, fillcolor=lightgreen];\n'
    else:
        dot += f' Product_Water [label="Product Water", fillcolor=lightgreen];\n'
    
    # Flow connections. Empty stages are allowed and skipped.
    dot += "\n // Flow connections\n"
    stage_nodes = [pre_nodes, desal_nodes, post_nodes]
    non_empty_stages = [nodes for nodes in stage_nodes if nodes]

    if non_empty_stages:
        dot += f" Influent -> {non_empty_stages[0][0]};\n"
        for current_stage, next_stage in zip(non_empty_stages, non_empty_stages[1:]):
            dot += f" {current_stage[-1]} -> {next_stage[0]};\n"
        dot += f" {non_empty_stages[-1][-1]} -> Product_Water;\n"
    else:
        dot += " Influent -> Product_Water;\n"

    if desal_nodes:
        dot += f" {desal_nodes[-1]} -> {brine_nodes[0]} [style=dashed];\n"
    elif non_empty_stages:
        dot += f" {non_empty_stages[-1][-1]} -> {brine_nodes[0]} [style=dashed];\n"
    else:
        dot += f" Influent -> {brine_nodes[0]} [style=dashed];\n"
    dot += "}\n"
    return dot

# Mapping from parameter names to sidebar session state keys
PARAM_TO_SIDEBAR_KEY = {
    "pH": "wq_ph",
    "Oil": "wq_oil",
    "Conductivity": "wq_conductivity",
    "TDS": "wq_tds",
    "TSS": "wq_tss",
    "Turbidity": "wq_turbidity",
    "Hardness": "wq_hardness",
    "Alkalinity": "wq_alk",
    "TOC": "wq_toc",
    "BOD": "wq_bod",
    "Ammonia nitrogen": "wq_nh4",
    "Boron": "wq_boron",
    "Sodium": "wq_sodium",
    "Chloride": "wq_chloride",
    "Silica": "wq_silica",
    "Iron": "wq_iron",
    "Magnesium": "wq_magnesium",
    "Manganese": "wq_manganese",
    "Calcium": "wq_calcium",
    "Barium": "wq_barium",
    "Lithium": "wq_lithium",
    "Strontium": "wq_strontium",
    "Sulfate": "wq_sulfate",
    "Bicarbonate": "wq_bicarbonate",
    "Fluoride": "wq_fluoride",
    "Uranium": "wq_uranium",
    "SAR": "wq_sar",
    "Selenium": "wq_selenium",
    "BTEX": "wq_btex",
    "PAHs": "wq_pahs",
    "Gross Alpha": "wq_gross_alpha",
    "Gross Beta": "wq_gross_beta",
    "Radium-226": "wq_radium_226",
    "Radium-228": "wq_radium_228",
}

REQUIREMENT_TO_INTERNAL_PARAM = {
    "Ba2+": "Barium",
    "SO4": "Sulfate",
}


def target_range(info):
    range_text = str(info.get("range", "") or "")
    if "-" not in range_text:
        return None
    try:
        low_text, high_text = range_text.split("-", 1)
        return float(low_text.strip()), float(high_text.strip())
    except (TypeError, ValueError):
        return None


def feed_concentration_for_param(parameter):
    internal_param = REQUIREMENT_TO_INTERNAL_PARAM.get(parameter, parameter)
    sidebar_key = PARAM_TO_SIDEBAR_KEY.get(internal_param)
    if sidebar_key and sidebar_key in st.session_state:
        return float(st.session_state[sidebar_key] or 0.0)

    additional_input_key = f"additional_input_{internal_param}".replace(" ", "_")
    if additional_input_key in st.session_state:
        return float(st.session_state[additional_input_key] or 0.0)

    conc_level = st.session_state.get("conc_level", "High")
    influent_type = st.session_state.get("influent_type", "Produced water")
    sidebar_defaults_for_water = SIDEBAR_DEFAULTS.get(influent_type, SIDEBAR_DEFAULTS)
    sidebar_defaults_for_level = sidebar_defaults_for_water.get(conc_level, {})
    if internal_param in sidebar_defaults_for_level:
        return float(sidebar_defaults_for_level[internal_param] or 0.0)
    if parameter in sidebar_defaults_for_level:
        return float(sidebar_defaults_for_level[parameter] or 0.0)
    return None


def target_display_value(parameter, info):
    parameter_range = target_range(info)
    if parameter_range:
        low, high = parameter_range
        return f"{low:g}-{high:g}", parameter_range

    session_key = f"wq_target_{parameter}".replace(" ", "_")
    target_value = st.session_state.get(session_key, info.get("limit"))
    try:
        target_value = float(target_value)
    except (TypeError, ValueError):
        return "N/A", None
    return f"{target_value:g}", target_value


def estimate_product_concentration(parameter, feed_concentration, pretreat_list, desal_list, posttreat_list):
    internal_param = REQUIREMENT_TO_INTERNAL_PARAM.get(parameter, parameter)
    concentration = float(feed_concentration)
    for unit in [*pretreat_list, *desal_list, *posttreat_list]:
        removal_info = UNIT_REMOVAL_RATES.get(unit, {})
        if internal_param == "pH" and internal_param in removal_info:
            ph_target = parse_ph_target(removal_info.get(internal_param))
            if ph_target is not None:
                concentration = ph_target
            continue
        removal_rate = parse_removal_rate(removal_info.get(internal_param, 0.0))
        concentration *= 1.0 - removal_rate
    return max(concentration, 0.0)


def water_quality_gap_summary(requirements, pretreat_list, desal_list, posttreat_list):
    rows = []
    for parameter, info in requirements.items():
        if parameter in {"Notes", "url"}:
            continue
        if REQUIREMENT_TO_INTERNAL_PARAM.get(parameter, parameter) == "pH":
            continue

        feed_value = feed_concentration_for_param(parameter)
        unit = info.get("unit", ALL_WATER_QUALITY_PARAMS.get(REQUIREMENT_TO_INTERNAL_PARAM.get(parameter, parameter), {}).get("unit", ""))
        target_text, target_value = target_display_value(parameter, info)
        if feed_value is None:
            continue

        product_value = estimate_product_concentration(
            parameter,
            feed_value,
            pretreat_list,
            desal_list,
            posttreat_list,
        )
        if isinstance(target_value, tuple):
            low, high = target_value
            meets_target = low <= product_value <= high
        elif target_value is not None:
            meets_target = product_value <= target_value
        else:
            meets_target = True

        if not meets_target:
            rows.append(
                {
                    "Pollutant": parameter,
                    "Feed": f"{feed_value:,.2f}",
                    "Estimated product": f"{product_value:,.2f}",
                    "Target": target_text,
                    "Unit": unit,
                    "Status": "May exceed target",
                }
            )
    return rows


def render_water_quality_gap_summary(requirements, pretreat_list, desal_list, posttreat_list):
    summary_rows = water_quality_gap_summary(
        requirements,
        pretreat_list,
        desal_list,
        posttreat_list,
    )
    st.markdown("**Potential water quality gaps**")
    if not summary_rows:
        st.success("No target exceedances estimated for the listed fit-for-purpose requirements.")
        return
    st.dataframe(
        summary_rows,
        hide_index=True,
        width="stretch",
    )


# Display flowchart and requirements side-by-side
if requirements:    
    # Add constituent tracking selector
    st.markdown("##### Track Constituents")
    track_col1, track_col2 = st.columns([2, 1])
    
    with track_col1:
        constituent_options = ["None"] + list(ALL_WATER_QUALITY_PARAMS.keys())
        tracked_const = st.selectbox(
            "Select constituent to track",
            constituent_options,
            index=0,
            key="tracked_constituent_selector",
            label_visibility="collapsed",
            width = 170,
        )
    
    # Get feed concentration from sidebar or use default
    feed_conc = None
    if tracked_const != "None":
        # Try to get from sidebar key mapping first
        sidebar_key = PARAM_TO_SIDEBAR_KEY.get(tracked_const)
        if sidebar_key and sidebar_key in st.session_state:
            feed_conc = st.session_state[sidebar_key]
        else:
            # Try to get from additional_input (sidebar additional parameters)
            additional_input_key = f"additional_input_{tracked_const}".replace(" ", "_")
            if additional_input_key in st.session_state:
                feed_conc = st.session_state[additional_input_key]
            else:
                # Try to get from wq_target (water quality requirements)
                wq_target_key = f"wq_target_{tracked_const}".replace(" ", "_")
                if wq_target_key in st.session_state:
                    feed_conc = st.session_state[wq_target_key]
                else:
                    # Use default limit from ALL_WATER_QUALITY_PARAMS
                    feed_conc = ALL_WATER_QUALITY_PARAMS.get(tracked_const, {}).get("limit", 0.0)
        
        # with track_col2:
        #     source = "sidebar" if sidebar_key and sidebar_key in st.session_state else "default"
        #     st.metric("Feed conc.", f"{feed_conc:.2f}", source)
    
    chart_col, design_col, req_col = st.columns([1.5, 1, 1])
    
    # Reset editable train state when the selected scenario or default config changes.
    # This prevents stale units from older defaults from lingering in the UI.
    TRAIN_CONFIG_VERSION = 3

    def _as_unit_list(value):
        if isinstance(value, list):
            return value.copy()
        if value:
            return [value]
        return []

    scenario_signature = (
        influent,
        ffp_primary,
        desal,
        tuple(pretreatment),
        tuple(desalination),
        tuple(posttreatment),
        brine_category,
        tuple(_as_unit_list(brine_option)),
    )

    def _load_default_treatment_train():
        st.session_state.current_scenario_signature = scenario_signature
        st.session_state.treatment_config_version = TRAIN_CONFIG_VERSION
        st.session_state.treatment_pretreatment = pretreatment.copy()
        st.session_state.treatment_desalination = desalination.copy()
        st.session_state.treatment_posttreatment = posttreatment.copy()
        st.session_state.treatment_brine = _as_unit_list(brine_option)
        st.session_state.treatment_brine_category = brine_category
        st.session_state.pop("treatment_train", None)
        st.session_state.pop("treatment_train_scenario_signature", None)
        clear_tea_results_cache()
        st.session_state.reset_counter = st.session_state.get("reset_counter", 0) + 1

    if (
        st.session_state.get("current_scenario_signature") != scenario_signature
        or st.session_state.get("treatment_config_version") != TRAIN_CONFIG_VERSION
    ):
        _load_default_treatment_train()
    
    # Initialize session state for editable treatment units BEFORE using them
    if "treatment_pretreatment" not in st.session_state:
        st.session_state.treatment_pretreatment = pretreatment.copy()
    if "treatment_desalination" not in st.session_state:
        st.session_state.treatment_desalination = desalination.copy()
    if "treatment_posttreatment" not in st.session_state:
        st.session_state.treatment_posttreatment = posttreatment.copy()
    if "treatment_brine" not in st.session_state:
        st.session_state.treatment_brine = _as_unit_list(brine_option)
    if isinstance(st.session_state.treatment_brine, str):
        st.session_state.treatment_brine = [st.session_state.treatment_brine]
    if "treatment_brine_category" not in st.session_state:
        st.session_state.treatment_brine_category = brine_category
    if "reset_counter" not in st.session_state:
        st.session_state.reset_counter = 0

    if st.session_state.treatment_brine_category != brine_category:
        st.session_state.treatment_brine_category = brine_category
        default_units = BRINE_MANAGEMENT_OPTIONS.get(brine_category, ["Brine disposal"])
        st.session_state.treatment_brine = [default_units[0]]
        st.rerun()
    
    # Use session state values for display and editing
    pretreatment = st.session_state.treatment_pretreatment
    desalination = st.session_state.treatment_desalination
    posttreatment = st.session_state.treatment_posttreatment
    brine_option = st.session_state.treatment_brine
    brine_category = st.session_state.treatment_brine_category

    def _sync_stage_widget_values(stage_key, widget_prefix):
        stage_units = st.session_state.get(stage_key, [])
        changed = False
        for index, unit in enumerate(stage_units):
            widget_key = f"{widget_prefix}_{index}_{st.session_state.reset_counter}"
            widget_value = st.session_state.get(widget_key)
            if widget_value and widget_value != unit:
                stage_units[index] = widget_value
                changed = True
        if changed:
            st.session_state[stage_key] = stage_units
        return changed

    _sync_stage_widget_values("treatment_pretreatment", "pretreat")
    _sync_stage_widget_values("treatment_desalination", "desal")
    _sync_stage_widget_values("treatment_posttreatment", "posttreat")
    _sync_stage_widget_values("treatment_brine", "brine_unit")

    pretreatment = st.session_state.treatment_pretreatment
    desalination = st.session_state.treatment_desalination
    posttreatment = st.session_state.treatment_posttreatment
    brine_option = st.session_state.treatment_brine
    
    with chart_col:
        if tracked_const != "None":
            dot = generate_treatment_flowchart(influent, ffp_primary, pretreatment, desalination, posttreatment, brine_option, tracked_const, feed_conc)
        else:
            dot = generate_treatment_flowchart(influent, ffp_primary, pretreatment, desalination, posttreatment, brine_option)
        st.graphviz_chart(dot)
        render_water_quality_gap_summary(requirements, pretreatment, desalination, posttreatment)
        if st.button("System Design →", type="primary"):
            st.session_state.treatment_train = normalize_treatment_train_config({
                "pretreatment": pretreatment,
                "desalination": desalination,
                "posttreatment": posttreatment,
                "brine_category": brine_category,
                "brine": brine_option,
            })
            st.session_state.treatment_train_scenario_signature = scenario_signature
            clear_tea_results_cache()
            st.success("✓ Treatment train configuration saved! Moving to System Design...")
            st.switch_page("pages/03_System_Design.py")
    
    with design_col:
        with st.container(border=True):
            render_card_title(
                "Treatment Chain Design",
                "Edit the unit processes included in the treatment train before moving to system design.",
                key="help_treatment_chain_design",
                html="<h5 style='margin-top: 0;'>Treatment Chain Design</h5>",
            )
            # Display and edit pretreatment
            st.markdown("**Pretreatment**")
            for i, unit in enumerate(st.session_state.treatment_pretreatment):
                pretreatment_units = stage_options(PRETREATMENT_UNIT_OPTIONS, unit)
                col_select, col_remove = st.columns([8, 1])
                with col_select:
                    new_unit = st.selectbox(
                        "Unit type",
                        pretreatment_units,
                        index=pretreatment_units.index(unit) if unit in pretreatment_units else 0,
                        key=f"pretreat_{i}_{st.session_state.reset_counter}",
                        label_visibility="collapsed"
                    )
                    if new_unit != unit:
                        st.session_state.treatment_pretreatment[i] = new_unit
                        st.rerun()
                
                with col_remove:
                    if st.button("✕", key=f"remove_pretreat_{i}", use_container_width=True):
                        st.session_state.treatment_pretreatment.pop(i)
                        st.rerun()
            
            # Add button for pretreatment
            if st.button("➕", key="add_pretreat", use_container_width=True):
                st.session_state.treatment_pretreatment.append(stage_options(PRETREATMENT_UNIT_OPTIONS)[0])
                st.rerun()
            
            # Display and edit desalination
            st.markdown("**Desalination**")
            for i, unit in enumerate(st.session_state.treatment_desalination):
                desalination_units = stage_options(DESALINATION_UNIT_OPTIONS, unit)
                col_select, col_remove = st.columns([8, 1])
                with col_select:
                    new_unit = st.selectbox(
                        "Unit type",
                        desalination_units,
                        index=desalination_units.index(unit) if unit in desalination_units else 0,
                        key=f"desal_{i}_{st.session_state.reset_counter}",
                        label_visibility="collapsed"
                    )
                    if new_unit != unit:
                        st.session_state.treatment_desalination[i] = new_unit
                        st.rerun()
                
                with col_remove:
                    if st.button("✕", key=f"remove_desal_{i}", use_container_width=True):
                        st.session_state.treatment_desalination.pop(i)
                        st.rerun()
            
            # Add button for desalination
            if st.button("➕", key="add_desal", use_container_width=True):
                st.session_state.treatment_desalination.append(stage_options(DESALINATION_UNIT_OPTIONS)[0])
                st.rerun()
            
            # Display and edit posttreatment
            st.markdown("**Posttreatment**")
            for i, unit in enumerate(st.session_state.treatment_posttreatment):
                posttreatment_units = stage_options(POSTTREATMENT_UNIT_OPTIONS, unit)
                col_select, col_remove = st.columns([8, 1])
                with col_select:
                    new_unit = st.selectbox(
                        "Unit type",
                        posttreatment_units,
                        index=posttreatment_units.index(unit) if unit in posttreatment_units else 0,
                        key=f"posttreat_{i}_{st.session_state.reset_counter}",
                        label_visibility="collapsed"
                    )
                    if new_unit != unit:
                        st.session_state.treatment_posttreatment[i] = new_unit
                        st.rerun()
                
                with col_remove:
                    if st.button("✕", key=f"remove_posttreat_{i}", use_container_width=True):
                        st.session_state.treatment_posttreatment.pop(i)
                        st.rerun()
            
            # Add button for posttreatment
            if st.button("➕", key="add_posttreat", use_container_width=True):
                st.session_state.treatment_posttreatment.append(stage_options(POSTTREATMENT_UNIT_OPTIONS)[0])
                st.rerun()
            
            # Display and edit brine
            st.markdown(f"**Brine Management: {st.session_state.treatment_brine_category}**")
            brine_units = BRINE_MANAGEMENT_OPTIONS.get(st.session_state.treatment_brine_category, ["Brine disposal"])
            for i, unit in enumerate(st.session_state.treatment_brine):
                available_brine_units = stage_options(brine_units, unit)
                col_select, col_remove = st.columns([8, 1])
                with col_select:
                    new_brine = st.selectbox(
                        "Brine type",
                        available_brine_units,
                        index=available_brine_units.index(unit) if unit in available_brine_units else 0,
                        key=f"brine_unit_{i}_{st.session_state.reset_counter}",
                        label_visibility="collapsed"
                    )
                    if new_brine != unit:
                        st.session_state.treatment_brine[i] = new_brine
                        st.rerun()

                with col_remove:
                    if st.button("✕", key=f"remove_brine_{i}", use_container_width=True):
                        st.session_state.treatment_brine.pop(i)
                        st.rerun()

            if st.button("➕", key="add_brine", use_container_width=True):
                st.session_state.treatment_brine.append(stage_options(brine_units)[0])
                st.rerun()
            
            # Reset button
            st.markdown("---")
            if st.button("🔄 Reset to Default", use_container_width=True):
                # Get default config from treatment_config
                default_config = get_treatment_train_config(ffp_primary, desal, influent)
                
                # Reset to default values from get_treatment_train_config
                st.session_state.treatment_pretreatment = default_config["pretreatment"].copy()
                st.session_state.treatment_desalination = default_config["desalination"].copy()
                st.session_state.treatment_posttreatment = default_config["posttreatment"].copy()
                st.session_state.treatment_brine = _as_unit_list(default_config["brine"])
                st.session_state.treatment_brine_category = default_config["brine_category"]
                st.session_state.current_scenario_signature = scenario_signature
                st.session_state.treatment_config_version = TRAIN_CONFIG_VERSION
                st.session_state.pop("treatment_train", None)
                st.session_state.pop("treatment_train_scenario_signature", None)
                clear_tea_results_cache()
                
                # Increment reset counter to force selectbox re-render
                st.session_state.reset_counter += 1
                
                st.rerun()


    with req_col:
        with st.container(border=True):
            render_card_title(
                f"{ffp_primary} - Water Quality Requirements",
                "Review or adjust the target water quality requirements for the selected fit-for-purpose use.",
                key="help_water_quality_requirements",
                html=f"<h5 style='margin-top: 0;'>{ffp_primary} - Water Quality Requirements</h5>",
            )
            
            # Initialize session state for additional parameters
            session_key_added = f"added_params_{ffp_primary}".replace(" ", "_")
            if session_key_added not in st.session_state:
                st.session_state[session_key_added] = []
            
            # Get parameters for this scenario
            params = WATER_QUALITY_REQUIREMENTS.get(ffp_primary, {})
            
            if params:
                # Initialize session state for each default parameter
                for param, info in params.items():
                    if param in ["Notes", "url"]:  # Skip Notes and URL fields
                        continue
                    session_key = f"wq_target_{param}".replace(" ", "_")
                    if session_key not in st.session_state:
                        # Use "limit" if available, otherwise skip initialization for range parameters
                        if "limit" in info:
                            st.session_state[session_key] = info["limit"]
                
                # Display editable default parameters 
                st.markdown("<style>input {font-size: 16px !important;} label {font-size: 16px !important;}</style>", unsafe_allow_html=True)
                for param, info in params.items():
                    if param in ["Notes", "url"]:  # Skip Notes and URL fields
                        continue
                    
                    label_col, input_col = st.columns([2.2, 1])
                    
                    # Check if parameter has a range (like pH) or limit (like other parameters)
                    if "range" in info:
                        # Display range parameters as text/info only
                        with label_col:
                            st.markdown(f"<div style='font-size: 16px; line-height: 1.2;'>{param} ({info['unit']})</div>", unsafe_allow_html=True)
                        with input_col:
                            st.markdown(f"<div style='font-size: 16px; line-height: 1.2;'>{info['range']}</div>", unsafe_allow_html=True)
                    else:
                        # Display limit parameters as editable inputs
                        with label_col:
                            st.markdown(f"<div style='font-size: 16px; line-height: 1.2;'>{param} ({info['unit']})</div>", unsafe_allow_html=True)
                        with input_col:
                            session_key = f"wq_target_{param}".replace(" ", "_")
                            st.number_input(
                                "Target",
                                min_value=0.0,
                                value=st.session_state.get(session_key, info.get("limit", 0.0)),
                                key=session_key,
                                label_visibility="collapsed",
                            )
                
                # Display additional parameters added by user
                if st.session_state[session_key_added]:
                    for added_param in st.session_state[session_key_added]:
                        info = ALL_WATER_QUALITY_PARAMS.get(added_param, {})
                        session_key = f"wq_target_{added_param}".replace(" ", "_")
                        if session_key not in st.session_state:
                            st.session_state[session_key] = info.get("limit", 100.0)
                        
                        col_label, col_input, col_remove = st.columns([2.1, 1, 0.6])
                        with col_label:
                            st.markdown(
                                f"<div style='font-size: 16px; line-height: 1.2;'>{added_param} ({info.get('unit', 'unit')})</div>",
                                unsafe_allow_html=True
                            )
                        with col_input:
                            st.number_input(
                                "Target",
                                min_value=0.0,
                                value=st.session_state.get(session_key, info.get("limit", 100.0)),
                                key=session_key,
                                label_visibility="collapsed"
                            )
                        with col_remove:
                            if st.button("✕", key=f"remove_{added_param}", use_container_width=True):
                                st.session_state[session_key_added].remove(added_param)
                                st.rerun()
                
                # Add new parameter functionality
                add_col1, add_col2 = st.columns([3, 1])
                with add_col1:
                    selected_params = (set(params.keys()) - {"Notes"}) | set(st.session_state[session_key_added])
                    available_params = [p for p in ALL_WATER_QUALITY_PARAMS.keys() if p not in selected_params]
                    
                    if available_params:
                        new_param = st.selectbox(
                            "Add param",
                            available_params,
                            key="select_new_param",
                            label_visibility="collapsed",
                            width=170,
                        )
                    else:
                        new_param = None
                
                with add_col2:
                    if available_params and st.button("➕", key="btn_add_param", use_container_width=True):
                        if new_param and new_param not in st.session_state[session_key_added]:
                            st.session_state[session_key_added].append(new_param)
                            st.rerun()
            
            # Scenario description area (from Notes field)
            
            # Display notes if available - format with better structure
            if "Notes" in requirements:
                import re
                notes_text = requirements['Notes'].strip()
                
                # Check if notes contain bullet items marked with *
                if ' * ' in notes_text:
                    # Split by * to get intro and bullet items
                    parts = notes_text.split(' * ')
                    intro = parts[0].strip()
                    
                    # Normalize whitespace in intro (remove extra spaces from line continuation)
                    intro = re.sub(r'\s+', ' ', intro)
                    
                    if intro:
                        # Replace \n with double newline for markdown rendering
                        intro = intro.replace('\\n', '\n\n')
                        st.markdown(f"💡 {intro}")
                    
                    # Display bullet items
                    st.markdown("**Key requirements:**")
                    for item in parts[1:]:
                        # Normalize whitespace and handle newlines
                        item = re.sub(r'\s+', ' ', item.strip()).rstrip(',').strip()
                        if item:
                            st.markdown(f"- {item}")
                else:
                    # Display as regular info for simple notes
                    notes_text = re.sub(r'\s+', ' ', notes_text)  # Normalize internal spaces
                    notes_text = notes_text.replace('\\n', '\n\n')  # Replace \n with double newline
                    st.markdown(f"💡 {notes_text}")
            
            # Display references url if available
            if "url" in requirements:
                for ref, url in requirements["url"].items():
                    st.link_button(f"🔗 {ref}", url=url)
else:
    # Fallback if no flowchart
    dot = generate_treatment_flowchart(influent, ffp_primary, pretreatment, desalination, posttreatment, brine_option)
    st.graphviz_chart(dot)
    if st.button("System Design →", type="primary"):
        st.session_state.treatment_train = normalize_treatment_train_config({
            "pretreatment": pretreatment,
            "desalination": desalination,
            "posttreatment": posttreatment,
            "brine_category": brine_category,
            "brine": brine_option,
        })
        st.session_state.treatment_train_scenario_signature = scenario_signature
        clear_tea_results_cache()
        st.success("✓ Treatment train configuration saved! Moving to System Design...")
        st.switch_page("pages/03_System_Design.py")


st.sidebar.header("Influent water quality")

# Hide spinner buttons on number inputs with CSS
st.markdown("""
<style>
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}
input[type=number] {
    -moz-appearance: textfield;
}
</style>
""", unsafe_allow_html=True)



# Add CSS for better alignment and responsive layout
st.sidebar.markdown("""
<style>
    /* Align label and input height in sidebar */
    [data-testid="stSidebar"] .stColumns {
        gap: 0.5rem;
    }
    
    /* Text center alignment */
    [data-testid="stSidebar"] .stMarkdown > div > div {
        display: flex;
        align-items: center;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Create sidebar inputs from ALL_WATER_QUALITY_PARAMS - Flow first
sidebar_key = "wq_flow"
col1, col2 = st.sidebar.columns([1.5, 1], gap="small")
# with col1:
#     st.markdown(f"<div style='font-size: 13px; font-weight: 500;'>Flow (bbl/day)<br/><span style='font-size: 11px; color: #888;'>(bbl/day)</span></div>", unsafe_allow_html=True)
# with col2:
#     st.number_input(
#         "Flow (bbl/day)",
#         min_value=0.0,
#         value=1000.0,
#         key=sidebar_key,
#         label_visibility="collapsed"
#     )

# Then create inputs for each parameter - create new columns for each row
conc_lvl = st.session_state.conc_level
sidebar_defaults_for_water = SIDEBAR_DEFAULTS.get(st.session_state.influent_type, SIDEBAR_DEFAULTS)
sidebar_defaults_for_level = sidebar_defaults_for_water.get(conc_lvl, {})
add_param = []
current_feedwater_params = []
for param, param_info in ALL_WATER_QUALITY_PARAMS.items():
    if param in sidebar_defaults_for_level.keys():
        sidebar_key = PARAM_TO_SIDEBAR_KEY.get(param)
        if sidebar_key:
            current_feedwater_params.append(param)
            default_value = sidebar_defaults_for_level.get(param, param_info["limit"])
            # Create new columns for each parameter row
            col1, col2 = st.sidebar.columns([1.5, 1], gap="small")
            with col1:
                st.markdown(f"<div style='font-size: 13px; font-weight: 500;'>{param}<br/><span style='font-size: 11px; color: #888;'>({param_info['unit']})</span></div>", unsafe_allow_html=True)
            with col2:
                st.number_input(
                    f"{param}",
                    min_value=0.0,
                    value=float(default_value),
                    key=sidebar_key,
                    label_visibility="collapsed"
                )
    else:
        add_param.append(param)
 
# Allow additional input parameters from the users
if 'additional_input_params_added' not in st.session_state:
    st.session_state.additional_input_params_added = []
st.sidebar.markdown("**Additional Input Parameters:**")
add_input_col1, add_input_col2 = st.sidebar.columns([2.1, 0.6])
with add_input_col1:
    selected_additional = set(st.session_state.additional_input_params_added) if 'additional_input_params_added' in st.session_state else set()
    available_additional_params = [p for p in add_param if p not in selected_additional]
    
    if available_additional_params:
        new_additional_param = st.selectbox(
            "Add additional param",
            available_additional_params,
            key="select_new_additional_param",
            label_visibility="collapsed",
        )
    else:
        new_additional_param = None

with add_input_col2:
    if available_additional_params and st.button("➕", key="btn_add_additional_param", use_container_width=True):
        if new_additional_param and new_additional_param not in st.session_state.additional_input_params_added:
            st.session_state.additional_input_params_added.append(new_additional_param)
            st.rerun()

# Display added additional input parameters
if st.session_state.additional_input_params_added:

    for added_additional_param in st.session_state.additional_input_params_added:
        current_feedwater_params.append(added_additional_param)
        info = ALL_WATER_QUALITY_PARAMS.get(added_additional_param, {})
        session_key = f"additional_input_{added_additional_param}".replace(" ", "_")
        if session_key not in st.session_state:
            st.session_state[session_key] = info.get("limit", 0.0)
        
        col_label, col_input, col_remove = st.sidebar.columns([2.1, 1, 0.6])
        with col_label:
            st.markdown(f"<div style='font-size: 13px; font-weight: 500;'>{added_additional_param}<br/><span style='font-size: 11px; color: #888;'>({info.get('unit', '')})</span></div>", unsafe_allow_html=True)
        with col_input:
            st.number_input(
                "Value",
                min_value=0.0,
                value=float(st.session_state.get(session_key, info.get("limit", 0.0))),
                key=session_key,
                label_visibility="collapsed"
            )
        with col_remove:
            if st.button("✕", key=f"remove_additional_{added_additional_param}", use_container_width=True):
                st.session_state.additional_input_params_added.remove(added_additional_param)
                st.rerun()

st.session_state.feedwater_quality_params = current_feedwater_params
st.session_state.feedwater_quality = collect_feedwater_quality(
    st.session_state,
    current_feedwater_params,
)

st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

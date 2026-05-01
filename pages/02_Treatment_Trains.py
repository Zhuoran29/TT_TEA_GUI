import streamlit as st
from treatment_config import WATER_QUALITY_REQUIREMENTS, get_treatment_train_config, UNIT_REMOVAL_RATES, ALL_WATER_QUALITY_PARAMS, SIDEBAR_DEFAULTS

st.set_page_config(page_title="02_Treatment_Train", layout="wide")

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

st.header("Treatment train configuration")

# defaults if not set
if "influent_type" not in st.session_state:
    st.session_state.influent_type = "Produced water"
if "ffp_scenarios" not in st.session_state:
    st.session_state.ffp_scenarios = ["Surface water discharge"]
if "desal_type" not in st.session_state:
    st.session_state.desal_type = "Mechanical Vapor Compression (MVC)"
if "conc_level" not in st.session_state:
    st.session_state.conc_level = "High"

# Display water quality requirements in a box
influent = st.session_state.influent_type
desal = st.session_state.desal_type
ffp_primary = st.session_state.ffp_scenarios[0] if st.session_state.ffp_scenarios else "Surface water discharge"

# Get water quality requirements and treatment train config
requirements = WATER_QUALITY_REQUIREMENTS.get(ffp_primary, {})
train_config = get_treatment_train_config(ffp_primary, desal)

pretreatment = train_config["pretreatment"]
desalination = train_config["desalination"]
posttreatment = train_config["posttreatment"]
brine_default = train_config["brine"]

# Set default brine option
brine_option = brine_default

if requirements:
    # Brine management radio button
    st.markdown("##### Brine management approach")
    brine_options = ["Brine disposal", "Brine valorization"]
    try:
        default_index = brine_options.index(brine_default)
    except ValueError:
        default_index = 0
    brine_option = st.radio("", brine_options, index=default_index, label_visibility="collapsed", horizontal=True)

# Helper function to parse removal rates from string
def parse_removal_rate(rate_str):
    """Parse removal rate from string format (e.g., '90-95%', '99%+', '0%') to float (0-1)"""
    if not rate_str or rate_str == "0%":
        return 0.0
    if isinstance(rate_str, (int, float)):
        return float(rate_str) / 100.0
    
    rate_str = str(rate_str).strip()
    
    # Handle percentage formats
    if "%" in rate_str:
        # Extract numbers
        nums = []
        parts = rate_str.replace("%", "").replace("+", "").split("-")
        for part in parts:
            try:
                nums.append(float(part.strip()))
            except ValueError:
                pass
        
        if nums:
            return min(nums) / 100.0  # Use minimum for conservative estimate
    
    return 0.0

# Generate flowchart dynamically based on actual units
def generate_treatment_flowchart(influent_name, scenario_name, pretreat_list, desal_list, posttreat_list, brine_name, tracked_constituent=None, feed_concentration=None):
    """Generate a graphviz flowchart that adapts to the number of units in each stage"""
    
    constituent_unit = ALL_WATER_QUALITY_PARAMS.get(tracked_constituent, {}).get("unit", "")

    # Helper function to create nodes and connections for a stage
    def create_stage_nodes(stage_prefix, stage_name, unit_list, color, current_conc=None):
        """Create nodes and connections for a treatment stage"""
        node_defs = f"\n subgraph cluster_{stage_prefix} {{\n"
        node_defs += f'  label="{stage_name}"; style=filled; color={color}; penwidth=2; pad=0.2;\n'
        
        node_ids = []
        concentrations = {}  # Track concentration after each unit
        
        for i, unit in enumerate(unit_list):
            node_id = f"{stage_prefix}{i+1}"
            node_ids.append(node_id)
            
            # Get removal rates for tooltip
            removal_info = UNIT_REMOVAL_RATES.get(unit, {})
            tooltip_text = f"{unit}\\n"
            if removal_info:
                for constituent, rate in list(removal_info.items())[:3]:  # Show top 3 constituents
                    tooltip_text += f"{constituent}: {rate}\\n"
            else:
                tooltip_text += "No data"
            
            # Calculate outlet concentration if tracking a constituent
            outlet_label = unit
            use_html_label = False
            if tracked_constituent and current_conc is not None:
                if tracked_constituent in removal_info:
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
            
            if use_html_label:
                node_defs += f'  {node_id} [label=<{outlet_label}>, tooltip="{tooltip_text}"];\n'
            else:
                node_defs += f'  {node_id} [label="{outlet_label}", tooltip="{tooltip_text}"];\n'
        
        # Create connections between nodes in this stage
        for i in range(len(node_ids) - 1):
            node_defs += f"  {node_ids[i]} -> {node_ids[i+1]};\n"
        
        node_defs += " }\n"
        return node_defs, node_ids, current_conc
    
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
    pre_dot, pre_nodes, current_conc = create_stage_nodes("PT", "Pretreatment", pretreat_list, "lightgrey", current_conc)
    dot += pre_dot
    
    # Desalination stage
    desal_dot, desal_nodes, current_conc = create_stage_nodes("D", "Desalination", desal_list, "lightyellow", current_conc)
    dot += desal_dot
    
    # Post-treatment stage (using PST prefix to distinguish from Pretreatment)
    post_dot, post_nodes, current_conc = create_stage_nodes("PST", "Post-treatment", posttreat_list, "lightcyan", current_conc)
    dot += post_dot
    
    # Brine management - positioned to the right of first desalination unit
    dot += f' Brine [label="{brine_name}", fillcolor=lightcoral];\n'
    
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
    
    # Flow connections
    dot += "\n // Flow connections\n"
    dot += f" Influent -> {pre_nodes[0]};\n"
    dot += f" {pre_nodes[-1]} -> {desal_nodes[0]};\n"
    dot += f" {desal_nodes[-1]} -> {post_nodes[0]};\n"
    dot += f" {desal_nodes[0]} -> Brine [style=dashed];\n"
    dot += f" {post_nodes[-1]} -> Product_Water;\n"
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
    "NH4-N": "wq_nh4",
    "Boron": "wq_boron",
    "Sodium": "wq_sodium",
    "Chloride": "wq_chloride",
    "Silica": "wq_silica",
    "Iron": "wq_iron",
    "Manganese": "wq_manganese",
    "Calcium": "wq_calcium",
    "Barium": "wq_barium",
    "Lithium": "wq_lithium",
    "Strontium": "wq_strontium",
    "Sulfate": "wq_sulfate",
    "Bicarbonate": "wq_bicarbonate",
    "Selenium": "wq_selenium",
    "BTEX": "wq_btex",
    "PAHs": "wq_pahs",
    "Gross Alpha": "wq_gross_alpha",
    "Gross Beta": "wq_gross_beta",
    "Radium-226": "wq_radium_226",
    "Radium-228": "wq_radium_228",
}

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
    
    # Check if desal_type has changed, if so reinitialize treatment units
    if "current_desal_type" not in st.session_state:
        st.session_state.current_desal_type = desal
    
    if st.session_state.current_desal_type != desal:
        # Desal type has changed, reinitialize everything
        st.session_state.current_desal_type = desal
        st.session_state.treatment_pretreatment = pretreatment.copy()
        st.session_state.treatment_desalination = desalination.copy()
        st.session_state.treatment_posttreatment = posttreatment.copy()
        st.session_state.treatment_brine = brine_option
        st.session_state.reset_counter = 0
    
    # Initialize session state for editable treatment units BEFORE using them
    if "treatment_pretreatment" not in st.session_state:
        st.session_state.treatment_pretreatment = pretreatment.copy()
    if "treatment_desalination" not in st.session_state:
        st.session_state.treatment_desalination = desalination.copy()
    if "treatment_posttreatment" not in st.session_state:
        st.session_state.treatment_posttreatment = posttreatment.copy()
    if "treatment_brine" not in st.session_state:
        st.session_state.treatment_brine = brine_option
    if "reset_counter" not in st.session_state:
        st.session_state.reset_counter = 0
    
    # Use session state values for display and editing
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
        if st.button("System Design →", type="primary"):
            st.session_state.treatment_train = {
                "pretreatment": pretreatment,
                "desalination": desalination,
                "posttreatment": posttreatment,
                "brine": brine_option,
            }
            st.success("✓ Treatment train configuration saved! Moving to System Design...")
            st.switch_page("pages/03_System_Design.py")
    
    with design_col:
        with st.container(border=True):
            st.markdown(f"<h5 style='margin-top: 0;'>Treatment Chain Design</h5>", unsafe_allow_html=True)
            
            # Get all available units from UNIT_REMOVAL_RATES
            all_units = list(UNIT_REMOVAL_RATES.keys())
            
            # Display and edit pretreatment
            st.markdown("**Pretreatment**")
            for i, unit in enumerate(st.session_state.treatment_pretreatment):
                col_select, col_remove = st.columns([8, 1])
                with col_select:
                    new_unit = st.selectbox(
                        "Unit type",
                        all_units,
                        index=all_units.index(unit) if unit in all_units else 0,
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
                st.session_state.treatment_pretreatment.append(all_units[0])
                st.rerun()
            
            # Display and edit desalination
            st.markdown("**Desalination**")
            for i, unit in enumerate(st.session_state.treatment_desalination):
                col_select, col_remove = st.columns([8, 1])
                with col_select:
                    new_unit = st.selectbox(
                        "Unit type",
                        all_units,
                        index=all_units.index(unit) if unit in all_units else 0,
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
                st.session_state.treatment_desalination.append(all_units[0])
                st.rerun()
            
            # Display and edit posttreatment
            st.markdown("**Posttreatment**")
            for i, unit in enumerate(st.session_state.treatment_posttreatment):
                col_select, col_remove = st.columns([8, 1])
                with col_select:
                    new_unit = st.selectbox(
                        "Unit type",
                        all_units,
                        index=all_units.index(unit) if unit in all_units else 0,
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
                st.session_state.treatment_posttreatment.append(all_units[0])
                st.rerun()
            
            # Display and edit brine
            st.markdown("**Brine Management**")
            col_select, col_remove = st.columns([8, 1])
            with col_select:
                new_brine = st.selectbox(
                    "Brine type",
                    all_units,
                    index=all_units.index(st.session_state.treatment_brine) if st.session_state.treatment_brine in all_units else 0,
                    key=f"brine_unit_{st.session_state.reset_counter}",
                    label_visibility="collapsed"
                )
                if new_brine != st.session_state.treatment_brine:
                    st.session_state.treatment_brine = new_brine
                    st.rerun()
            
            # Reset button
            st.markdown("---")
            if st.button("🔄 Reset to Default", use_container_width=True):
                # Get default config from treatment_config
                default_config = get_treatment_train_config(ffp_primary, desal)
                
                # Reset to default values from get_treatment_train_config
                st.session_state.treatment_pretreatment = default_config["pretreatment"].copy()
                st.session_state.treatment_desalination = default_config["desalination"].copy()
                st.session_state.treatment_posttreatment = default_config["posttreatment"].copy()
                st.session_state.treatment_brine = default_config["brine"]
                
                # Increment reset counter to force selectbox re-render
                st.session_state.reset_counter += 1
                
                st.rerun()


    with req_col:
        with st.container(border=True):
            st.markdown(f"<h5 style='margin-top: 0;'>{ffp_primary} - Water Quality Requirements</h5>", unsafe_allow_html=True)
            
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
        st.session_state.treatment_train = {
            "pretreatment": pretreatment,
            "desalination": desalination,
            "posttreatment": posttreatment,
            "brine": brine_option,
        }
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
with col1:
    st.markdown(f"<div style='font-size: 13px; font-weight: 500;'>Flow (bbl/day)<br/><span style='font-size: 11px; color: #888;'>(bbl/day)</span></div>", unsafe_allow_html=True)
with col2:
    st.number_input(
        "Flow (bbl/day)",
        min_value=0.0,
        value=1000.0,
        key=sidebar_key,
        label_visibility="collapsed"
    )

# Then create inputs for each parameter - create new columns for each row
conc_lvl = st.session_state.conc_level
add_param = []
for param, param_info in ALL_WATER_QUALITY_PARAMS.items():
    if param in SIDEBAR_DEFAULTS[conc_lvl].keys():
        sidebar_key = PARAM_TO_SIDEBAR_KEY.get(param)
        if sidebar_key:
            default_value = SIDEBAR_DEFAULTS[conc_lvl].get(param, param_info["limit"])
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
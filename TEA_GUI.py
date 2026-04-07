import streamlit as st

st.set_page_config(page_title="Produced Water TEA", layout="wide")

st.title("Techno‑Economic Analysis — Fit-for-Purpose Water Treatment")
st.markdown(
    """
    #### Welcome to the NMPWRC TEA Tool 😊.
    
    Use the sidebar to navigate between different steps:
    - **Treatment Scenario**: Select treatment scenario
    - **Treatment Train**: Configure treatment train
    - **System Design**: Set up unit parameters
    - **TEA Results**: View cost analysis
    

    """
)


# Quick start button
if st.button("Start →", type="primary"):
    st.switch_page("pages/01_Treatment_Scenarios.py")
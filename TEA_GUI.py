import streamlit as st
import hmac
from config import APP_VERSION, DATA_VERSION

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return

    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if hmac.compare_digest(password, st.secrets["APP_PASSWORD"]):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password")

    st.stop()

check_password()

st.set_page_config(page_title="Produced Water TEA", layout="wide")

st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

st.title("Techno‑Economic Analysis — Fit-for-Purpose Water Treatment")
st.markdown(
    """
    #### Welcome to the NMPWRC TEA Tool 😊.
    
    Use the sidebar to navigate between different steps:
    - **Treatment Scenario**: Select treatment scenario
    - **Treatment Train**: Configure treatment train
    - **System Design**: Set up unit parameters
    - **TEA Results**: View cost analysis
    - **Extensions**: Explore planned GIS, socio-economic, optimization, and sensitivity modules
    

    """
)


# Quick start button
if st.button("Start →", type="primary"):
    st.switch_page("pages/01_Treatment_Scenarios.py")

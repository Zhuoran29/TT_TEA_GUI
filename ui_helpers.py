"""Shared Streamlit UI helpers."""

import streamlit as st


def render_card_title(title, help_text, key=None, html=None):
    """Render a card title with Streamlit's native help tooltip on the right."""
    title_col, help_col = st.columns([0.9, 0.1], vertical_alignment="center")
    with title_col:
        if html:
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown(f"**{title}**")
    with help_col:
        st.markdown("&nbsp;", unsafe_allow_html=True, help=help_text)

"""Small feedback/report button helpers for Streamlit pages."""

import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import streamlit as st


def _config_value(name):
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.getenv(name.upper())


def _url_with_query_params(url, params):
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: value for key, value in params.items() if value})
    return urlunparse(parsed._replace(query=urlencode(query)))


def feedback_form_url(context):
    """Return the configured feedback form URL, optionally with Google Form prefill params."""
    base_url = _config_value("feedback_form_url")
    if not base_url:
        return None

    params = {}
    context_entry = _config_value("feedback_context_entry")
    project_entry = _config_value("feedback_project_entry")

    if context_entry:
        params[context_entry] = context
    if project_entry:
        params[project_entry] = st.session_state.get("project_name", "TEA project")

    if not params:
        return base_url
    return _url_with_query_params(base_url, params)


def render_report_button(context, label="Report", use_container_width=False):
    """Render a gray Report button linked to the configured feedback form."""
    url = feedback_form_url(context)
    if url:
        st.link_button(
            label,
            url=url,
            type="secondary",
            help="Report an issue or leave feedback for this part of the app.",
            use_container_width=use_container_width,
        )
        return

    st.button(
        label,
        type="secondary",
        disabled=True,
        help='Set feedback_form_url in .streamlit/secrets.toml to enable this button.',
        use_container_width=use_container_width,
    )

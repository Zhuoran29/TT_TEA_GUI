"""Streamlit dialog that hosts the Treatment Train Explorer."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from streamlit.components.v2 import component as _v2_component

from .payload import build_payload

TEMPLATE_PATH = Path(__file__).with_name("template.html")

# The explorer runs in an st.iframe, which cannot return values.
# This invisible bidirectional component listens for the iframe's
# "Apply to Treatment Train" message and hands the configuration to Python.
_BRIDGE_JS = """
export default function(component) {
  const { setTriggerValue } = component;
  const onMessage = (event) => {
    const msg = event.data;
    if (!msg || msg.type !== "tea-train-explorer-apply" || typeof msg.config !== "object") return;
    setTriggerValue("apply", msg.config);
  };
  window.addEventListener("message", onMessage);
  return () => window.removeEventListener("message", onMessage);
}
"""
_apply_bridge = _v2_component("tea_train_explorer_apply_bridge", js=_BRIDGE_JS)


def render_explorer_html(payload):
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    body = TEMPLATE_PATH.read_text(encoding="utf-8").replace("__PAYLOAD__", data)
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"></head><body>"
        f"{body}</body></html>"
    )


@st.dialog("Treatment Train Explorer", width="large")
def open_train_explorer(context, on_apply=None):
    """Open the explorer for the treatment train currently on the page.

    ``context`` holds the keyword arguments of ``payload.build_payload``.
    ``on_apply(config)`` writes an applied configuration back to session state.
    """
    bridge = _apply_bridge(key="train_explorer_apply_bridge", on_apply_change=lambda: None, height=0)
    config = getattr(bridge, "apply", None)
    if config and on_apply is not None:
        on_apply(config)
        st.rerun()

    with st.spinner("Preparing the explorer and checking scaling tendency..."):
        payload = build_payload(**context)
    st.iframe(render_explorer_html(payload), height="content")

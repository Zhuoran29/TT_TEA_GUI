"""TEA-focused intelligence for nontraditional water treatment."""

from __future__ import annotations

import json
import os

import streamlit as st

from config import APP_VERSION, DATA_VERSION
from feedback import render_report_button
from intelligence import IntelligenceSettings, refresh_intelligence
from intelligence.db import latest_run, list_items
from intelligence.summarizer import ollama_health


st.set_page_config(page_title="TEA Intelligence", layout="wide")
st.sidebar.caption(f"v{APP_VERSION} | {DATA_VERSION}")

st.markdown(
    """
    <style>
        * { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif; }
        h1, h2, h3, h4, h5, h6 { letter-spacing: -0.5px; }
        [data-testid="stContainer"] { border-radius: 12px; }
        .intel-meta { color: #5F6C7B; font-size: 0.86rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

settings = IntelligenceSettings()

TEA_CATEGORIES = (
    "Assumption Updates",
    "Technology Evidence",
    "Cost & Project Signals",
    "Policy Impact",
    "Funding Opportunities",
    "Background Industry News",
)

CATEGORY_DESCRIPTIONS = {
    "Assumption Updates": (
        "Numerical evidence that may justify reviewing a technical or economic model assumption."
    ),
    "Technology Evidence": (
        "Treatment configurations, pilot results, performance, reliability, fouling, and scale-up evidence."
    ),
    "Cost & Project Signals": (
        "Project capacity, awards, commercial deployment, CAPEX/OPEX, contracts, and market signals."
    ),
    "Policy Impact": (
        "Regulatory, permitting, monitoring, reuse, discharge, and disposal changes with possible cost impact."
    ),
    "Funding Opportunities": (
        "Grants, solicitations, prizes, deadlines, eligibility, and cost-share information."
    ),
    "Background Industry News": (
        "Relevant context that does not currently provide enough evidence to change a TEA assumption."
    ),
}


def _json_list(item, field):
    try:
        value = json.loads(item[field] or "[]")
        return value if isinstance(value, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def render_intelligence_card(item):
    with st.container(border=True):
        heading_col, link_col = st.columns([0.86, 0.14], vertical_alignment="center")
        with heading_col:
            st.markdown(f"#### {item['title']}")
        with link_col:
            if item["url"]:
                st.link_button("Open source", item["url"], use_container_width=True)

        date_text = item["published_at"] or "Date unavailable"
        score_text = (
            f" · TEA relevance: {item['model_score']}/100"
            if item["model_score"] is not None else ""
        )
        st.caption(
            f"{item['source_type']} · {item['source_name']} · {date_text} · "
            f"Evidence basis: {item['summary_basis']}{score_text}"
        )
        if item["authors"]:
            st.caption(item["authors"])

        if item["summary"]:
            st.write(item["summary"])
        elif item["abstract"]:
            with st.expander("Abstract (not yet summarized)"):
                st.write(item["abstract"])
        elif item["snippet"]:
            st.write(item["snippet"])
        else:
            st.caption("Metadata only; no abstract or public snippet was available.")

        if item["why_it_matters"]:
            st.markdown(f"**Potential TEA impact:** {item['why_it_matters']}")

        tea_parameters = _json_list(item, "tea_parameters")
        if tea_parameters:
            st.markdown(f"**Parameters to review:** {', '.join(map(str, tea_parameters))}")

        numerical_evidence = _json_list(item, "numerical_evidence")
        if numerical_evidence:
            st.markdown("**Numerical evidence from the source:**")
            for evidence in numerical_evidence:
                st.markdown(f"- {evidence}")

        if item["review_recommended"]:
            st.info("Model-assumption review recommended; verify the source before changing defaults.")

        tags = []
        for field in ("topics", "technologies", "matched_terms"):
            tags.extend(_json_list(item, field))
        tags = list(dict.fromkeys(str(tag) for tag in tags if tag))
        if tags:
            st.caption(" · ".join(tags))

        if item["doi"]:
            st.caption(f"DOI: {item['doi']}")
        if item["processing_status"] == "error":
            st.warning(
                "The source was saved, but local TEA analysis failed. "
                f"Details: {item['processing_error']}"
            )

title_col, report_col = st.columns([0.82, 0.18])
with title_col:
    st.title("TEA Intelligence for Nontraditional Water Treatment")
with report_col:
    render_report_button("Water intelligence", use_container_width=True)

st.caption(
    "Evidence-focused updates for produced water and brackish water treatment. "
    "Items are organized by their potential effect on treatment selection and TEA assumptions; "
    "publication analysis uses only the available abstract."
)

run = latest_run(settings.db_path)
if run:
    status_col, fetched_col, new_col, summary_col = st.columns(4)
    status_col.metric("Last run", run["status"].title())
    fetched_col.metric("Retrieved", run["fetched"])
    new_col.metric("New candidates", run["new_items"])
    summary_col.metric("TEA analyses", run["summarized"])
    completed = run["completed_at"] or run["started_at"]
    st.caption(f"Last updated: {completed}")
    if run["error_message"]:
        st.warning(f"Some sources could not be refreshed: {run['error_message']}")
else:
    st.info(
        "No digest has been collected yet. Run `python refresh_intelligence.py` "
        "from the project directory, or use the alpha controls below."
    )

with st.expander("Alpha controls", expanded=not bool(run)):
    st.write(
        f"Local model: `{settings.ollama_model}`  \n"
        f"Ollama endpoint: `{settings.ollama_url}`  \n"
        f"Database: `{settings.db_path}`"
    )
    test_col, refresh_col = st.columns(2)
    with test_col:
        if st.button("Test local model", use_container_width=True):
            healthy, message = ollama_health(settings)
            (st.success if healthy else st.error)(message)
    with refresh_col:
        manual_enabled = os.getenv("INTELLIGENCE_ENABLE_MANUAL_REFRESH", "1") == "1"
        if st.button(
            "Run refresh now",
            type="primary",
            disabled=not manual_enabled,
            help="This may keep the page busy for several minutes while abstracts are summarized.",
            use_container_width=True,
        ):
            with st.spinner("Retrieving and summarizing new public items..."):
                try:
                    stats = refresh_intelligence(settings)
                    st.success(
                        f"Refresh complete: {stats.new_items} new candidates, "
                        f"{stats.summarized} summarized, {stats.errors} errors."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Refresh failed: {exc}")
    st.caption(
        "For normal operation, use Windows Task Scheduler instead of this button. "
        "Set INTELLIGENCE_ENABLE_MANUAL_REFRESH=0 to hide manual execution."
    )

st.divider()

filter_col, date_col, search_col = st.columns([0.22, 0.18, 0.60])
with filter_col:
    source_type = st.selectbox(
        "Content type", ("All", "Publication", "News", "Newsletter")
    )
with date_col:
    days = st.selectbox("Date range", (7, 30, 90, 365), index=1, format_func=lambda x: f"{x} days")
with search_col:
    search = st.text_input(
        "Search", placeholder="e.g., reverse osmosis, Permian Basin, beneficial reuse"
    )

show_rejected = st.toggle("Show items rejected by the local model", value=False)
items = list_items(
    settings.db_path,
    source_type=source_type,
    search=search,
    days=days,
    include_rejected=show_rejected,
)

st.subheader(f"TEA intelligence ({len(items)})")
if not items:
    st.info("No items match the current filters.")

grouped_items = {category: [] for category in TEA_CATEGORIES}
for item in items:
    category = item["tea_category"]
    if category not in grouped_items:
        category = "Background Industry News"
    grouped_items[category].append(item)

primary_categories = TEA_CATEGORIES[:-1]
tabs = st.tabs(
    [f"{category} ({len(grouped_items[category])})" for category in primary_categories]
)
for tab, category in zip(tabs, primary_categories):
    with tab:
        st.caption(CATEGORY_DESCRIPTIONS[category])
        if not grouped_items[category]:
            st.info(f"No {category.lower()} match the current filters.")
        for item in grouped_items[category]:
            render_intelligence_card(item)

background = grouped_items["Background Industry News"]
with st.expander(f"Background Industry News ({len(background)})", expanded=False):
    st.caption(CATEGORY_DESCRIPTIONS["Background Industry News"])
    if not background:
        st.info("No background items match the current filters.")
    for item in background:
        render_intelligence_card(item)

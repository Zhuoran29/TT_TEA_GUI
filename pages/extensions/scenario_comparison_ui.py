"""Streamlit UI for saving and comparing TEA scenarios."""

import pandas as pd
import streamlit as st

from tea_models.analyses.scenario_comparison import (
    MAX_COMPARISON_SCENARIOS,
    comparison_csv,
    comparison_rows,
    create_scenario_snapshot,
    unit_cost_breakdown_rows,
)


def _unique_default_name(existing):
    base = "Current scenario"
    names = {item["name"] for item in existing}
    if base not in names:
        return base
    index = 2
    while f"{base} {index}" in names:
        index += 1
    return f"{base} {index}"


def _render_comparison(selected):
    rows = comparison_rows(selected)
    summary = pd.DataFrame(rows)
    currency_years = {row["Currency year"] for row in rows if row["Currency year"]}
    if len(currency_years) > 1:
        st.warning("Selected scenarios use different base currency years. Cost values are shown as calculated and are not escalated to a common year.")

    st.subheader("Summary")
    display = summary.copy()
    numeric_formats = {
        "Feed LCOW ($/bbl feed)": "${:,.3f}",
        "Product LCOW ($/bbl product)": "${:,.3f}",
        "Total CAPEX (USD)": "${:,.0f}",
        "Annual OPEX (USD/year)": "${:,.0f}",
        "Product flow (m3/day)": "{:,.1f}",
        "Electricity intensity (kWh/bbl feed)": "{:,.3f}",
        "Thermal intensity (kWh/bbl feed)": "{:,.3f}",
    }
    st.dataframe(display.style.format(numeric_formats), hide_index=True, use_container_width=True)

    lcow_chart = summary.set_index("Scenario")[[
        "Feed LCOW ($/bbl feed)", "Product LCOW ($/bbl product)"
    ]]
    st.subheader("LCOW comparison")
    st.bar_chart(lcow_chart, use_container_width=True)

    cost_col, energy_col = st.columns(2)
    with cost_col:
        st.markdown("**Project costs**")
        st.bar_chart(
            summary.set_index("Scenario")[["Total CAPEX (USD)", "Annual OPEX (USD/year)"]],
            use_container_width=True,
        )
    with energy_col:
        st.markdown("**Energy intensity**")
        st.bar_chart(
            summary.set_index("Scenario")[[
                "Electricity intensity (kWh/bbl feed)",
                "Thermal intensity (kWh/bbl feed)",
            ]],
            use_container_width=True,
        )

    breakdown = pd.DataFrame(unit_cost_breakdown_rows(selected))
    if not breakdown.empty:
        st.subheader("Unit-process LCOW contribution")
        totals = breakdown.groupby(["Scenario", "Unit process"], as_index=False)[
            "LCOW contribution ($/bbl feed)"
        ].sum()
        pivoted = totals.pivot(index="Scenario", columns="Unit process", values="LCOW contribution ($/bbl feed)").fillna(0.0)
        st.bar_chart(pivoted, use_container_width=True, stack=True)
        with st.expander("View unit-process comparison table"):
            st.dataframe(breakdown, hide_index=True, use_container_width=True)

    st.download_button(
        "Download comparison CSV",
        comparison_csv(selected),
        file_name="tea_scenario_comparison.csv",
        mime="text/csv",
    )


def render_scenario_comparison():
    """Render scenario capture, management, and comparison controls."""
    st.header("Scenario comparison")
    st.caption("Save completed TEA cases and compare normalized project and unit-process results.")
    saved = st.session_state.setdefault("saved_tea_scenarios", [])
    if st.session_state.pop("reset_scenario_snapshot_name", False):
        st.session_state.pop("scenario_snapshot_name", None)

    with st.container(border=True):
        st.markdown("**Save current TEA result**")
        if "tea_results" not in st.session_state:
            st.info("Run a TEA calculation on the System Design page before saving a scenario.")
            if st.button("Go to System Design", type="primary"):
                st.switch_page("pages/03_System_Design.py")
        else:
            name_col, save_col = st.columns([0.75, 0.25], vertical_alignment="bottom")
            with name_col:
                scenario_name = st.text_input(
                    "Scenario name",
                    value=_unique_default_name(saved),
                    key="scenario_snapshot_name",
                )
            with save_col:
                if st.button("Save current scenario", type="primary", use_container_width=True):
                    if any(item["name"].casefold() == scenario_name.strip().casefold() for item in saved):
                        st.error("Scenario names must be unique.")
                    else:
                        try:
                            saved.append(create_scenario_snapshot(scenario_name, st.session_state))
                        except ValueError as exc:
                            st.error(str(exc))
                        else:
                            st.success(f"Saved {scenario_name.strip()}.")
                            st.session_state.reset_scenario_snapshot_name = True
                            st.rerun()

    if not saved:
        st.info("No scenarios have been saved yet. Save the current result, then configure and run another case.")
        return

    st.subheader("Saved scenarios")
    inventory = pd.DataFrame([
        {
            "Scenario": item["name"],
            "Project": item.get("project_name", ""),
            "Desalination": item.get("configuration", {}).get("desalination_type", ""),
            "Saved (UTC)": item.get("created_at", "").replace("T", " "),
        }
        for item in saved
    ])
    st.dataframe(inventory, hide_index=True, use_container_width=True)

    names = [item["name"] for item in saved]
    default_selection = names[:MAX_COMPARISON_SCENARIOS]
    selected_names = st.multiselect(
        f"Scenarios to compare (up to {MAX_COMPARISON_SCENARIOS})",
        names,
        default=default_selection,
        max_selections=MAX_COMPARISON_SCENARIOS,
    )
    selected = [item for item in saved if item["name"] in selected_names]
    if selected:
        _render_comparison(selected)

    with st.expander("Manage saved scenarios"):
        delete_names = st.multiselect("Select scenarios to remove", names, key="scenario_delete_names")
        if st.button("Remove selected scenarios", disabled=not delete_names):
            st.session_state.saved_tea_scenarios = [
                item for item in saved if item["name"] not in delete_names
            ]
            st.rerun()

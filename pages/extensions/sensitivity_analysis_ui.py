"""Streamlit UI for one-way TEA sensitivity analysis."""

import pandas as pd
import streamlit as st

from tea_models.analyses.sensitivity import (
    OUTPUT_METRICS,
    SYSTEM_PARAMETERS,
    run_one_way_sensitivity,
    tornado_rows,
)


def _render_results(rows, metric_key):
    output = OUTPUT_METRICS[metric_key]
    detailed = pd.DataFrame(rows)
    tornado = pd.DataFrame(tornado_rows(rows)).set_index("Parameter")

    st.subheader(f"Effect on {output['label']}")
    st.caption(f"Bars show percent change from the current baseline ({output['unit']}).")
    st.bar_chart(tornado, horizontal=True, use_container_width=True)

    st.subheader("Low / base / high results")
    result_pivot = detailed.pivot(
        index="Parameter", columns="Case", values="Output value"
    ).reset_index()
    ordered_columns = [column for column in ["Parameter", "Low", "Base", "High"] if column in result_pivot]
    st.dataframe(
        result_pivot[ordered_columns].style.format(
            {column: "{:,.4g}" for column in ["Low", "Base", "High"] if column in result_pivot}
        ),
        hide_index=True,
        use_container_width=True,
    )

    with st.expander("View detailed sensitivity matrix"):
        st.dataframe(detailed, hide_index=True, use_container_width=True)
    st.download_button(
        "Download sensitivity CSV",
        detailed.to_csv(index=False).encode("utf-8"),
        file_name="tea_sensitivity_analysis.csv",
        mime="text/csv",
    )


def render_sensitivity_analysis():
    """Render baseline controls and run a one-way sensitivity analysis."""
    st.header("Sensitivity analysis")
    st.caption("Vary selected system assumptions independently around the current completed TEA case.")
    required = ["tea_results", "tea_context", "tea_unit_inputs", "treatment_train", "feedwater_quality"]
    missing = [key for key in required if key not in st.session_state]
    if missing:
        st.info("Run a TEA calculation on the System Design page before starting sensitivity analysis.")
        if st.button("Go to System Design", type="primary"):
            st.switch_page("pages/03_System_Design.py")
        return

    context = st.session_state.tea_context
    parameter_labels = {key: value["label"] for key, value in SYSTEM_PARAMETERS.items()}
    output_labels = {key: value["label"] for key, value in OUTPUT_METRICS.items()}

    with st.container(border=True):
        st.markdown("**One-way analysis setup**")
        selected_parameters = st.multiselect(
            "Inputs to vary",
            list(SYSTEM_PARAMETERS),
            default=["electricity_price", "thermal_energy_price", "discount_rate", "investment_factor"],
            format_func=parameter_labels.get,
        )
        control_cols = st.columns(2)
        with control_cols[0]:
            metric_key = st.selectbox(
                "Target output",
                list(OUTPUT_METRICS),
                format_func=output_labels.get,
            )
        with control_cols[1]:
            variation_percent = st.number_input(
                "Variation from baseline (%)",
                min_value=0.1,
                max_value=100.0,
                value=20.0,
                step=5.0,
            )

        baseline_rows = []
        for key in selected_parameters:
            definition = SYSTEM_PARAMETERS[key]
            baseline_rows.append({
                "Input": definition["label"],
                "Baseline": float(context.get(definition["context_key"], 0.0) or 0.0),
                "Unit": definition["unit"],
            })
        if baseline_rows:
            st.dataframe(pd.DataFrame(baseline_rows), hide_index=True, use_container_width=True)

        run_clicked = st.button(
            "Run sensitivity analysis",
            type="primary",
            disabled=not selected_parameters,
        )

    if run_clicked:
        with st.spinner("Running low and high cases for each selected input..."):
            try:
                rows = run_one_way_sensitivity(
                    st.session_state.treatment_train,
                    st.session_state.tea_context,
                    st.session_state.feedwater_quality,
                    st.session_state.tea_unit_inputs,
                    st.session_state.tea_results,
                    selected_parameters,
                    metric_key,
                    variation_percent,
                )
            except (KeyError, ValueError) as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Sensitivity calculation could not be completed: {exc}")
            else:
                st.session_state.sensitivity_analysis_result = {
                    "rows": rows,
                    "metric_key": metric_key,
                    "variation_percent": variation_percent,
                    "baseline_signature": st.session_state.get("tea_results_signature", ""),
                }

    saved = st.session_state.get("sensitivity_analysis_result")
    if saved:
        if saved.get("baseline_signature") != st.session_state.get("tea_results_signature", ""):
            st.warning("The TEA baseline has changed since this sensitivity analysis was run. Run it again to refresh the results.")
        _render_results(saved["rows"], saved["metric_key"])

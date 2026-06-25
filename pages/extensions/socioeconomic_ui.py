"""Socio-economic extension UI."""

import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt
from ui_helpers import render_card_title

from tea_models.socioeconomic import (
    COUNTY_BASELINES,
    DEFAULT_SECTOR_WATER_USE_AF_YR,
    SECTOR_OUTPUTS,
    daily_flow_to_af_per_year,
    run_socioeconomic_model,
)


def currency(value):
    return f"${value:,.0f}"


def percent(value):
    return f"{100.0 * value:,.2f}%"


def tea_default_water_af_yr():
    results = st.session_state.get("tea_results")
    if not results:
        return 1200.0
    flow = results.get("final_product_flow", 0.0)
    unit = results.get("final_product_flow_unit", "m3/day")
    context = st.session_state.get("tea_context", {})
    operating_days = context.get("operating_days_per_year", 365.0)
    return daily_flow_to_af_per_year(flow, unit, operating_days)


def tea_default_annual_cost():
    results = st.session_state.get("tea_results")
    if not results:
        return 1_000_000.0
    return float(results.get("total_annual_cost", 0.0))


def render_socioeconomic_analysis():
    st.subheader("Socio-economic analysis")
    st.markdown(
        "This is a screening-level translation of the economic logic described "
        "in the Sandia PW-ESESim technical report. It does not reproduce the full IMPLAN "
        "database or map interface; it shows the main input-output pathway so the workflow "
        "can be connected to the TEA tool."
    )

    with st.expander("Extracted core formulas from the report", expanded=True):
        formula_cols = st.columns(3)
        with formula_cols[0]:
            st.markdown("**Water-to-production link**")
            st.caption(
                "Added treated water creates a percent change in sector water use, "
                "mapped to a percent change in sector production."
            )
            st.latex(r"\Delta Pct_{prod} = \frac{Q_{treated}}{Q_{sector,baseline}} \cdot E")
        with formula_cols[1]:
            st.markdown("**Economic impact approximation**")
            st.caption(
                "The full model links to IMPLAN outputs. Here, a multiplier approximates "
                "county-wide direct, indirect, and induced effects."
            )
            st.latex(r"\Delta Output = Output_{sector,baseline} \cdot \Delta Pct_{prod} \cdot M")
        with formula_cols[2]:
            st.markdown("**Net benefit and present worth**")
            st.caption(
                "Annual value-added benefit is compared with treatment and delivery cost "
                "over the project life."
            )
            st.latex(r"PW_{net} = \sum_{t=1}^{n}\frac{Benefit_t - Cost_t}{(1+r)^t}")

    input_col, assumption_col = st.columns([1.1, 1])

    with input_col:
        with st.container(border=True):
            render_card_title(
                "Scenario inputs",
                "Define the county, sector, treated water volume, and annual project cost for the screening calculation.",
                key="help_socioeconomic_scenario_inputs",
            )
            county = st.selectbox("County", list(COUNTY_BASELINES.keys()), index=0)
            sector = st.selectbox("Target economic sector", list(SECTOR_OUTPUTS[county].keys()), index=1)

            treated_water_af_yr = st.number_input(
                "Treated produced water added to sector",
                min_value=0.0,
                value=float(tea_default_water_af_yr()),
                step=100.0,
                help="acre-ft/year; auto-filled from TEA product flow when results are available",
            )
            annual_project_cost = st.number_input(
                "Annual treatment and delivery cost",
                min_value=0.0,
                value=float(tea_default_annual_cost()),
                step=100000.0,
                help="USD/year; auto-filled from TEA total annual cost when results are available",
            )
            sector_water_use_af_yr = st.number_input(
                "Baseline sector water use",
                min_value=1.0,
                value=float(DEFAULT_SECTOR_WATER_USE_AF_YR[sector]),
                step=100.0,
                help="Placeholder value until the original county-sector water-use database is connected",
            )

    with assumption_col:
        with st.container(border=True):
            render_card_title(
                "Model assumptions",
                "Tune the simplified economic response assumptions used by the socio-economic screening model.",
                key="help_socioeconomic_model_assumptions",
            )
            water_to_output_elasticity = st.slider(
                "Water-to-output elasticity",
                min_value=0.0,
                max_value=2.0,
                value=1.0,
                step=0.05,
            )
            output_multiplier = st.slider(
                "Economic output multiplier",
                min_value=1.0,
                max_value=3.0,
                value=1.6,
                step=0.05,
            )
            ramp_years = st.number_input("Infrastructure ramp period", min_value=1, value=5, step=1)
            project_life_years = st.number_input("Project life", min_value=1, value=15, step=1)
            discount_rate_percent = st.number_input("Discount rate", min_value=0.0, value=5.0, step=0.5)
            unemployment_rate_percent = st.number_input(
                "Baseline unemployment rate",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.25,
            )

    results = run_socioeconomic_model(
        county=county,
        sector=sector,
        treated_water_af_yr=treated_water_af_yr,
        annual_project_cost=annual_project_cost,
        sector_water_use_af_yr=sector_water_use_af_yr,
        water_to_output_elasticity=water_to_output_elasticity,
        output_multiplier=output_multiplier,
        ramp_years=ramp_years,
        project_life_years=project_life_years,
        discount_rate_percent=discount_rate_percent,
        unemployment_rate_percent=unemployment_rate_percent,
    )

    st.divider()

    summary_values = {
        "Water change": percent(results["water_change_fraction"]),
        "Output change": currency(results["total_output_change"]),
        "Value added": currency(results["value_added_change"]),
        "Jobs": f"{results['jobs_created']:,.1f}",
        "Annual net benefit": currency(results["annual_net_benefit"]),
    }
    st.markdown("""
    <style>
        div[data-testid="stVerticalBlock"] > div:has(.socio-summary-cell) {
            gap: 0;
        }
        .socio-summary-cell {
            border: 1px solid #D9E2EC;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        .socio-summary-label {
            align-items: center;
            background: #F7FAFC;
            border-bottom: 1px solid #D9E2EC;
            color: #334E68;
            display: flex;
            font-size: 0.96rem;
            font-weight: 750;
            height: 42px;
            justify-content: center;
            position: relative;
            text-align: center;
        }
        .socio-summary-help {
            align-items: center;
            border: 1px solid #CBD5E1;
            border-radius: 999px;
            color: #64748B;
            display: inline-flex;
            font-size: 0.72rem;
            height: 18px;
            justify-content: center;
            position: absolute;
            right: 8px;
            width: 18px;
        }
        .socio-summary-value {
            align-items: center;
            background: #FFFFFF;
            color: #102A43;
            display: flex;
            font-size: 1.16rem;
            font-weight: 800;
            height: 48px;
            justify-content: center;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    summary_cols = st.columns(len(summary_values), gap="small")
    for column, (name, value) in zip(summary_cols, summary_values.items()):
        with column:
            st.markdown(
                f"""
                <div class="socio-summary-cell">
                    <div class="socio-summary-label">
                        {name}
                        <span class="socio-summary-help" title="Screening-level socio-economic result based on the current input assumptions.">?</span>
                    </div>
                    <div class="socio-summary-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    chart_col, table_col = st.columns([1.25, 1])
    annual_df = pd.DataFrame(results["annual_rows"])

    with chart_col:
        st.subheader("Projected annual impacts")
        fig, ax = plt.subplots(figsize=(8, 4.2))
        ax.plot(
            annual_df["Year"],
            annual_df["Net benefit"],
            color="#1F6FEB",
            linewidth=2.4,
            marker="o",
            markersize=4,
        )
        ax.set_xlabel("Year")
        ax.set_ylabel("Net benefit ($)")
        ax.grid(axis="y", alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with table_col:
        st.subheader("Output summary")
        summary = pd.DataFrame([
            {"Metric": "Direct sector output change", "Value": currency(results["direct_output_change"])},
            {"Metric": "Total county output change", "Value": currency(results["total_output_change"])},
            {"Metric": "Labor income change", "Value": currency(results["labor_income_change"])},
            {"Metric": "Tax change", "Value": currency(results["tax_change"])},
            {
                "Metric": "Unemployment reduction",
                "Value": f"{results['unemployment_reduction_points']:,.2f} percentage points",
            },
            {"Metric": "Present worth benefit", "Value": currency(results["present_worth_benefit"])},
            {"Metric": "Present worth cost", "Value": currency(results["present_worth_cost"])},
            {"Metric": "Present worth net", "Value": currency(results["present_worth_net"])},
        ])
        st.dataframe(summary, hide_index=True, use_container_width=True)

    st.info(
        "Current limitation: this view approximates the IMPLAN-linked PW-ESESim workflow. "
        "When the original IMPLAN result database or Powersim variable export is available, "
        "the multiplier step can be replaced with the original county-sector lookup tables."
    )

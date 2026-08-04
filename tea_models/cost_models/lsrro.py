"""LSRRO cost model using literature/NMPWRC assumptions and app-level LCOW logic."""

from __future__ import annotations

from tea_models.cost_models.cost_utils import (
    cost_index_factor_to_base,
    cost_year,
    escalate_cost,
    input_value,
    investment_factor,
    value,
)
from tea_models.lsrro_core import BBL_TO_M3, REFERENCE_FLOW_BBL_DAY


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = value(technical_result, "inlet_flow")
    outlet_flow = value(technical_result, "outlet_flow")
    if inlet_flow <= 0.0:
        raise ValueError("LSRRO inlet flow must be positive.")

    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_feed = inlet_flow * operating_days
    annual_product = outlet_flow * operating_days
    inlet_bbl_day = inlet_flow / BBL_TO_M3

    reference_direct_capex = input_value(
        cost_inputs,
        "reference_direct_membrane_capex",
        20.5e6,
    )
    reference_flow_bbl_day = _input(
        cost_inputs,
        "reference_flow_bbl_day",
        REFERENCE_FLOW_BBL_DAY,
    )
    scaling_exponent = _input(cost_inputs, "capex_scaling_exponent", 0.81)
    direct_cost_factor = cost_index_factor_to_base(
        context,
        cost_year(cost_inputs, "reference_direct_membrane_capex"),
    )
    if reference_direct_capex < 0.0 or reference_flow_bbl_day <= 0.0:
        raise ValueError("LSRRO reference CAPEX must be nonnegative and reference flow positive.")
    if scaling_exponent < 0.0:
        raise ValueError("LSRRO CAPEX scaling exponent cannot be negative.")

    direct_membrane_capex = (
        reference_direct_capex
        * direct_cost_factor
        * (inlet_bbl_day / reference_flow_bbl_day) ** scaling_exponent
    )
    installed_capex = direct_membrane_capex * investment_factor(context)

    electricity_cost = (
        annual_feed
        * value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    membrane_replacement_factor = _input(
        cost_inputs,
        "membrane_replacement_factor",
        0.20,
    )
    antiscalant_dose = _input(cost_inputs, "antiscalant_dose_mg_l", 3.0)
    antiscalant_price = escalate_cost(
        input_value(cost_inputs, "antiscalant_unit_price", 61.40),
        cost_inputs,
        "antiscalant_unit_price",
        context,
    )
    antiscalant_density = _input(cost_inputs, "antiscalant_density_kg_l", 1.10)
    cip_rate = escalate_cost(
        input_value(cost_inputs, "cip_cost_per_m3_product", 0.07),
        cost_inputs,
        "cip_cost_per_m3_product",
        context,
    )
    labor_fte = _input(cost_inputs, "labor_fte", 1.0)
    labor_cost = escalate_cost(
        input_value(cost_inputs, "labor_cost_per_fte_year", 80000.0),
        cost_inputs,
        "labor_cost_per_fte_year",
        context,
    )
    om_contingency_factor = _input(cost_inputs, "om_contingency_factor", 0.20)

    if any(
        item < 0.0
        for item in [
            membrane_replacement_factor,
            antiscalant_dose,
            antiscalant_price,
            antiscalant_density,
            cip_rate,
            labor_fte,
            labor_cost,
            om_contingency_factor,
        ]
    ):
        raise ValueError("LSRRO cost inputs cannot be negative.")

    membrane_replacement = direct_membrane_capex * membrane_replacement_factor

    antiscalant_kg_year = antiscalant_dose * annual_feed * 1000.0 / 1e6
    kg_per_gal = max(antiscalant_density * 3.785411784, 1e-12)
    antiscalant_cost = antiscalant_kg_year / kg_per_gal * antiscalant_price
    cip_cost = annual_product * cip_rate
    labor = labor_fte * labor_cost

    opex_before_contingency = (
        electricity_cost
        + membrane_replacement
        + antiscalant_cost
        + cip_cost
        + labor
    )
    om_contingency = opex_before_contingency * om_contingency_factor
    total_opex = opex_before_contingency + om_contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_membrane_capex, "USD"),
        "reference_direct_membrane_capex": _result(reference_direct_capex, "USD"),
        "cost_index_factor": _result(direct_cost_factor, "factor"),
        "capex_scaling_exponent": _result(scaling_exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "electricity_operating_cost": _result(electricity_cost, "USD/year"),
        "membrane_replacement_cost": _result(membrane_replacement, "USD/year"),
        "antiscalant_cost": _result(antiscalant_cost, "USD/year"),
        "cip_cost": _result(cip_cost, "USD/year"),
        "labor_cost": _result(labor, "USD/year"),
        "om_contingency": _result(om_contingency, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "annual_feed_volume": _result(annual_feed, "m3/year"),
        "annual_product_volume": _result(annual_product, "m3/year"),
    }

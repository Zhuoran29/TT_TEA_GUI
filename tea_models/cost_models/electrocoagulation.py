"""Electrocoagulation cost model adapted from the EC-Al TEA script."""

from __future__ import annotations

from tea_models.cost_models.cost_utils import (
    cost_index_factor_to_base,
    cost_year,
    escalate_cost,
    input_value,
    investment_factor,
    value,
)


DEFAULTS = {
    "reference_ec_capex": 1595666.0,
    "reference_capacity": 11356.0,
    "capex_scaling_exponent": 0.87,
    "aluminum_price": 2.23,
    "solid_disposal_cost": 0.11,
    "labor_fte": 1.0,
    "labor_cost_per_fte_year": 80000.0,
    "om_contingency_factor": 0.20,
}


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_feed = inlet_flow * operating_days
    reference_capex = input_value(cost_inputs, "reference_ec_capex", DEFAULTS["reference_ec_capex"])
    reference_capacity = _input(cost_inputs, "reference_capacity", DEFAULTS["reference_capacity"])
    exponent = _input(cost_inputs, "capex_scaling_exponent", DEFAULTS["capex_scaling_exponent"])
    if reference_capex < 0.0 or reference_capacity <= 0.0 or exponent < 0.0:
        raise ValueError("EC CAPEX reference values must be nonnegative with positive reference capacity.")
    index_factor = cost_index_factor_to_base(context, cost_year(cost_inputs, "reference_ec_capex", 2025))
    equipment_capex = reference_capex * index_factor * (inlet_flow / reference_capacity) ** exponent
    installed_capex = equipment_capex * investment_factor(context)

    aluminum_price = escalate_cost(input_value(cost_inputs, "aluminum_price", DEFAULTS["aluminum_price"]), cost_inputs, "aluminum_price", context, 2022)
    disposal_price = escalate_cost(input_value(cost_inputs, "solid_disposal_cost", DEFAULTS["solid_disposal_cost"]), cost_inputs, "solid_disposal_cost", context)
    labor_cost_per_fte = escalate_cost(input_value(cost_inputs, "labor_cost_per_fte_year", DEFAULTS["labor_cost_per_fte_year"]), cost_inputs, "labor_cost_per_fte_year", context)
    labor_fte = _input(cost_inputs, "labor_fte", DEFAULTS["labor_fte"])
    contingency_factor = _input(cost_inputs, "om_contingency_factor", DEFAULTS["om_contingency_factor"])
    if any(v < 0.0 for v in [aluminum_price, disposal_price, labor_cost_per_fte, labor_fte, contingency_factor]):
        raise ValueError("EC cost inputs cannot be negative.")

    aluminum = value(technical_result, "aluminum_consumption") * operating_days * aluminum_price
    energy = annual_feed * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    solid_disposal = value(technical_result, "solid_waste_generation") * annual_feed * disposal_price
    labor = labor_fte * labor_cost_per_fte
    opex_before_contingency = aluminum + energy + solid_disposal + labor
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "cost_index_factor": _result(index_factor, "factor"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "aluminum_operating_cost": _result(aluminum, "USD/year"),
        "energy_operating_cost": _result(energy, "USD/year"),
        "solid_disposal_operating_cost": _result(solid_disposal, "USD/year"),
        "labor_cost": _result(labor, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
    }

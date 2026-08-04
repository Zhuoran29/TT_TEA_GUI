"""Walnut shell filtration cost model using DOE DGF+WSF basis."""

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
    "reference_capex_cost_per_bbl": 0.02,
    "reference_opex_cost_per_bbl": 0.03,
    "reference_flow_bbl_day": 20000.0,
    "capex_scaling_exponent": 0.87,
    "labor_fte": 1.0,
    "labor_cost_per_fte_year": 80000.0,
    "om_contingency_factor": 0.20,
}
M3_TO_BBL = 6.2898107704


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
    crf = max(float(context.get("capital_recovery_factor", 0.0) or 0.0), 1e-12)
    annual_bbl = inlet_flow * operating_days * M3_TO_BBL
    inlet_bbl_day = inlet_flow * M3_TO_BBL
    reference_bbl_day = _input(cost_inputs, "reference_flow_bbl_day", DEFAULTS["reference_flow_bbl_day"])
    exponent = _input(cost_inputs, "capex_scaling_exponent", DEFAULTS["capex_scaling_exponent"])
    capex_rate = escalate_cost(input_value(cost_inputs, "reference_capex_cost_per_bbl", DEFAULTS["reference_capex_cost_per_bbl"]), cost_inputs, "reference_capex_cost_per_bbl", context, 2022)
    reference_annualized_capex = capex_rate * reference_bbl_day * operating_days
    reference_installed_capex = reference_annualized_capex / crf
    equipment_capex = reference_installed_capex * (inlet_bbl_day / max(reference_bbl_day, 1e-12)) ** exponent
    installed_capex = equipment_capex * investment_factor(context)

    opex_rate = escalate_cost(input_value(cost_inputs, "reference_opex_cost_per_bbl", DEFAULTS["reference_opex_cost_per_bbl"]), cost_inputs, "reference_opex_cost_per_bbl", context, 2022)
    baseline_variable_opex = annual_bbl * opex_rate
    energy_cost = inlet_flow * operating_days * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    labor = _input(cost_inputs, "labor_fte", DEFAULTS["labor_fte"]) * escalate_cost(
        input_value(cost_inputs, "labor_cost_per_fte_year", DEFAULTS["labor_cost_per_fte_year"]),
        cost_inputs,
        "labor_cost_per_fte_year",
        context,
    )
    contingency = (baseline_variable_opex + energy_cost + labor) * _input(cost_inputs, "om_contingency_factor", DEFAULTS["om_contingency_factor"])
    total_opex = baseline_variable_opex + energy_cost + labor + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "reference_installed_capital_cost": _result(reference_installed_capex, "USD"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "baseline_variable_operating_cost": _result(baseline_variable_opex, "USD/year"),
        "energy_operating_cost": _result(energy_cost, "USD/year"),
        "labor_cost": _result(labor, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
    }

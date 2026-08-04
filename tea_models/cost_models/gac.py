"""GAC cost model using BV-based replacement/regeneration."""

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
    "reference_gac_capex": 1345660.0,
    "reference_capacity": 3760.0,
    "capex_scaling_exponent": 0.87,
    "gac_replacement_cost": 4.58,
    "gac_regeneration_cost": 4.28,
    "gac_replacement_regeneration_energy": 23.0,
    "regeneration_fraction": 0.80,
    "replacement_fraction": 0.20,
    "om_contingency_factor": 0.20,
}


def _result(value, unit):
    return {"value": value, "unit": unit}


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        return float(entry.get("value", default) if isinstance(entry, dict) else entry)
    except (TypeError, ValueError):
        return float(default)


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    investment_factor_value = investment_factor(context)

    reference_capex = input_value(cost_inputs, "reference_gac_capex", DEFAULTS["reference_gac_capex"])
    reference_capacity = _input(cost_inputs, "reference_capacity", DEFAULTS["reference_capacity"])
    exponent = _input(cost_inputs, "capex_scaling_exponent", DEFAULTS["capex_scaling_exponent"])
    if reference_capex < 0.0 or reference_capacity <= 0.0 or exponent < 0.0:
        raise ValueError("GAC CAPEX reference values must be nonnegative with positive reference capacity.")
    index_factor = cost_index_factor_to_base(context, cost_year(cost_inputs, "reference_gac_capex", 2025))
    equipment_capex = reference_capex * index_factor * (inlet_flow / reference_capacity) ** exponent
    installed_capex = equipment_capex * investment_factor_value

    replacement_cost = escalate_cost(
        input_value(cost_inputs, "gac_replacement_cost", DEFAULTS["gac_replacement_cost"]),
        cost_inputs,
        "gac_replacement_cost",
        context,
        2025,
    )
    regeneration_cost = escalate_cost(
        input_value(cost_inputs, "gac_regeneration_cost", DEFAULTS["gac_regeneration_cost"]),
        cost_inputs,
        "gac_regeneration_cost",
        context,
        2025,
    )
    media_energy = _input(cost_inputs, "gac_replacement_regeneration_energy", DEFAULTS["gac_replacement_regeneration_energy"])
    regeneration_fraction = _input(cost_inputs, "regeneration_fraction", DEFAULTS["regeneration_fraction"])
    replacement_fraction = _input(cost_inputs, "replacement_fraction", DEFAULTS["replacement_fraction"])
    contingency_factor = _input(cost_inputs, "om_contingency_factor", DEFAULTS["om_contingency_factor"])
    annual_usage = value(technical_result, "annual_gac_usage")
    operating_fraction = operating_days / 365.0
    annual_usage *= operating_fraction
    replacement_kg = annual_usage * replacement_fraction
    regeneration_kg = annual_usage * regeneration_fraction
    replacement_opex = replacement_kg * replacement_cost
    regeneration_opex = regeneration_kg * regeneration_cost
    material_energy_opex = annual_usage * media_energy * float(context.get("electricity_price", 0.0))
    opex_before_contingency = replacement_opex + regeneration_opex + material_energy_opex
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "cost_index_factor": _result(index_factor, "factor"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor_value, "-"),
        "gac_replacement_operating_cost": _result(replacement_opex, "USD/year"),
        "gac_regeneration_operating_cost": _result(regeneration_opex, "USD/year"),
        "gac_replacement_regeneration_energy_cost": _result(material_energy_opex, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "variable_operating_cost": _result(total_opex, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "annual_gac_usage": _result(annual_usage, "kg/year"),
    }

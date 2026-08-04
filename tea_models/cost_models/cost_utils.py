"""Shared cost-model helpers for currency-year escalation and CAPEX scaling."""

from __future__ import annotations

from tea_models.technical_models.helper_function import CostIndexFactor


DEFAULT_COST_YEAR = 2024
DEFAULT_REFERENCE_CAPACITY_M3_DAY = 1000.0
DEFAULT_SCALING_EXPONENT = 1.0


def value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        if isinstance(entry, dict):
            return float(entry.get("value", default) or default)
        return float(entry or default)
    except (TypeError, ValueError):
        return float(default)


def input_value(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def result(value_, unit):
    return {"value": value_, "unit": unit}


def investment_factor(context):
    try:
        return max(float(context.get("investment_factor", 2.5)), 0.0)
    except (TypeError, ValueError):
        return 2.5


def cost_year(cost_inputs, parameter, default=DEFAULT_COST_YEAR):
    years = cost_inputs.get("_cost_years", {}) if isinstance(cost_inputs, dict) else {}
    try:
        return int(years.get(parameter, default))
    except (TypeError, ValueError):
        return int(default)


def cost_index_factor_to_base(context, from_year):
    to_year = int(context.get("base_currency_year", DEFAULT_COST_YEAR))
    return CostIndexFactor(int(from_year), to_year)


def escalate_cost(value_, cost_inputs, parameter, context, default_year=DEFAULT_COST_YEAR):
    return float(value_) * cost_index_factor_to_base(
        context,
        cost_year(cost_inputs, parameter, default_year),
    )


def scaled_capex_from_unit_cost(
    unit_cost,
    capacity,
    cost_inputs,
    context,
    cost_parameter="capex_per_flow",
    reference_capacity_parameter="reference_capacity",
    exponent_parameter="capex_scaling_exponent",
):
    """Scale equipment CAPEX from a reference unit cost and capacity."""
    capacity = max(float(capacity or 0.0), 0.0)
    if capacity <= 0.0:
        return 0.0

    reference_capacity = input_value(
        cost_inputs,
        reference_capacity_parameter,
        DEFAULT_REFERENCE_CAPACITY_M3_DAY,
    )
    if reference_capacity <= 0.0:
        raise ValueError("CAPEX reference capacity must be positive.")

    exponent = input_value(
        cost_inputs,
        exponent_parameter,
        DEFAULT_SCALING_EXPONENT,
    )
    if exponent < 0.0:
        raise ValueError("CAPEX scaling exponent cannot be negative.")

    escalated_unit_cost = escalate_cost(unit_cost, cost_inputs, cost_parameter, context)
    reference_capex = escalated_unit_cost * reference_capacity
    return reference_capex * (capacity / reference_capacity) ** exponent

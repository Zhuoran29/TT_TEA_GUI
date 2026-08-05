from tea_models.cost_models.cost_utils import (
    escalate_cost,
    input_value,
    investment_factor,
    scaled_capex_from_unit_cost,
)


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    if isinstance(entry, dict):
        return float(entry.get("value", default) or default)
    return float(entry or default)


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _result(value, unit):
    return {"value": value, "unit": unit}


def run(unit_process, technical_result, cost_inputs, context):
    """MVC cost model using MVC-specific editable cost inputs."""
    inlet_flow = _value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330))
    annual_volume = inlet_flow * operating_days
    investment_factor_value = investment_factor(context)

    capex_per_flow = input_value(cost_inputs, "capex_per_flow", 1104.0)
    column_capex_multiplier = _input(cost_inputs, "column_capex_multiplier", 1.0)
    if column_capex_multiplier < 0.0:
        raise ValueError("MVC column CAPEX multiplier cannot be negative.")
    fixed_opex_fraction = _input(cost_inputs, "fixed_opex_fraction", 0.05)
    variable_opex_per_m3 = escalate_cost(
        input_value(cost_inputs, "variable_opex_per_m3", 0.0),
        cost_inputs,
        "variable_opex_per_m3",
        context,
    )
    electricity_price = float(context.get("electricity_price", 0.0))
    energy_opex = annual_volume * _value(technical_result, "energy_intensity") * electricity_price

    bare_equipment_capex = scaled_capex_from_unit_cost(
        capex_per_flow,
        inlet_flow,
        cost_inputs,
        context,
    )
    equipment_capex = bare_equipment_capex * column_capex_multiplier
    capex = equipment_capex * investment_factor_value
    fixed_opex = capex * fixed_opex_fraction
    variable_opex = annual_volume * variable_opex_per_m3
    annual_opex = fixed_opex + variable_opex + energy_opex

    return {
        "installed_capital_cost": _result(capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "column_capex_multiplier": _result(column_capex_multiplier, "-"),
        "investment_factor": _result(investment_factor_value, "-"),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "variable_operating_cost": _result(variable_opex, "USD/year"),
        "energy_operating_cost": _result(energy_opex, "USD/year"),
        "total_annual_operating_cost": _result(annual_opex, "USD/year"),
    }

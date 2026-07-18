"""Saltwater disposal well cost template model."""


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


def _investment_factor(context):
    try:
        return max(float(context.get("investment_factor", 2.5)), 0.0)
    except (TypeError, ValueError):
        return 2.5


def run(unit_process, technical_result, cost_inputs, context):
    disposed_flow = _value(technical_result, "disposed_flow", _value(technical_result, "inlet_flow"))
    operating_days = float(context.get("operating_days_per_year", 330))
    annual_disposed_volume = disposed_flow * operating_days
    investment_factor = _investment_factor(context)

    capex_per_flow = _input(cost_inputs, "capex_per_flow", 0.0)
    capex_per_well = _input(cost_inputs, "capex_per_well", 0.0)
    fixed_opex_fraction = _input(cost_inputs, "fixed_opex_fraction", 0.0)
    variable_opex_per_m3 = _input(cost_inputs, "variable_opex_per_m3", 6.29)
    electricity_price = float(context.get("electricity_price", 0.0))

    well_count = _value(technical_result, "injection_well_count")
    flow_capex = capex_per_flow * disposed_flow
    well_capex = capex_per_well * well_count
    equipment_capex = flow_capex + well_capex
    capex = equipment_capex * investment_factor

    fixed_opex = capex * fixed_opex_fraction
    variable_opex = annual_disposed_volume * variable_opex_per_m3
    energy_opex = annual_disposed_volume * _value(technical_result, "energy_intensity") * electricity_price
    annual_opex = fixed_opex + variable_opex + energy_opex

    return {
        "installed_capital_cost": _result(capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "investment_factor": _result(investment_factor, "-"),
        "flow_capacity_capital_cost": _result(flow_capex, "USD"),
        "well_capital_cost": _result(well_capex, "USD"),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "variable_operating_cost": _result(variable_opex, "USD/year"),
        "energy_operating_cost": _result(energy_opex, "USD/year"),
        "total_annual_operating_cost": _result(annual_opex, "USD/year"),
    }

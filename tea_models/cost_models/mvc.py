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
    """MVC cost model using MVC-specific editable cost inputs."""
    inlet_flow = _value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330))
    annual_volume = inlet_flow * operating_days
    investment_factor = _investment_factor(context)

    capex_per_flow = _input(cost_inputs, "capex_per_flow", 1104.0)
    fixed_opex_fraction = _input(cost_inputs, "fixed_opex_fraction", 0.05)
    variable_opex_per_m3 = _input(cost_inputs, "variable_opex_per_m3", 0.0)
    evaporator_capex = _value(technical_result, "evaporator_capex")
    compressor_capex = _value(technical_result, "compressor_capex")
    surrogate_capex = evaporator_capex + compressor_capex

    electricity_price = float(context.get("electricity_price", 0.0))
    electricity_cost = annual_volume * _value(technical_result, "energy_intensity") * electricity_price

    equipment_capex = capex_per_flow * inlet_flow
    capex = equipment_capex * investment_factor
    fixed_opex = capex * fixed_opex_fraction
    variable_opex = annual_volume * variable_opex_per_m3
    annual_opex = fixed_opex + variable_opex + electricity_cost

    return {
        "installed_capital_cost": _result(capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "investment_factor": _result(investment_factor, "-"),
        "mvc_surrogate_capital_cost": _result(surrogate_capex, "USD"),
        "evaporator_capital_cost": _result(evaporator_capex, "USD"),
        "compressor_capital_cost": _result(compressor_capex, "USD"),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "variable_operating_cost": _result(variable_opex, "USD/year"),
        "energy_operating_cost": _result(electricity_cost, "USD/year"),
        "total_annual_operating_cost": _result(annual_opex, "USD/year"),
    }

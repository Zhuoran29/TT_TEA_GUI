def _value(result, name, default=0.0):
    entry = result.get(name, {})
    if isinstance(entry, dict):
        return float(entry.get("value", default) or default)
    return float(entry or default)


def run(unit_process, technical_result, cost_inputs, context):
    """Use MVC surrogate capital and annual electricity-cost outputs."""
    evaporator_capex = _value(technical_result, "evaporator_capex")
    compressor_capex = _value(technical_result, "compressor_capex")
    electricity_price = context.get("electricity_price")
    if electricity_price is None:
        electricity_cost = _value(technical_result, "electricity_cost")
    else:
        electricity_cost = (
            _value(technical_result, "inlet_flow")
            * float(context.get("operating_days_per_year", 330))
            * _value(technical_result, "energy_intensity")
            * float(electricity_price)
        )

    capex = evaporator_capex + compressor_capex
    fixed_opex = capex * float(cost_inputs.get("fixed_opex_fraction", 0.0))
    variable_opex = (
        _value(technical_result, "inlet_flow")
        * float(context.get("operating_days_per_year", 330))
        * float(cost_inputs.get("variable_opex_per_m3", 0.0))
    )
    annual_opex = fixed_opex + variable_opex + electricity_cost

    return {
        "installed_capital_cost": {"value": capex, "unit": "USD"},
        "fixed_operating_cost": {"value": fixed_opex, "unit": "USD/year"},
        "variable_operating_cost": {"value": variable_opex, "unit": "USD/year"},
        "energy_operating_cost": {"value": electricity_cost, "unit": "USD/year"},
        "total_annual_operating_cost": {"value": annual_opex, "unit": "USD/year"},
    }

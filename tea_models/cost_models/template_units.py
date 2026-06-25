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


def run_template(technical_result, cost_inputs, context, defaults):
    inlet_flow = _value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330))
    annual_volume = inlet_flow * operating_days

    capex_per_flow = _input(cost_inputs, "capex_per_flow", defaults.get("capex_per_flow", 0.0))
    fixed_opex_fraction = _input(
        cost_inputs,
        "fixed_opex_fraction",
        defaults.get("fixed_opex_fraction", 0.04),
    )
    variable_opex_per_m3 = _input(
        cost_inputs,
        "variable_opex_per_m3",
        defaults.get("variable_opex_per_m3", 0.0),
    )
    electricity_price = float(context.get("electricity_price", 0.0))
    chemical_price = _input(cost_inputs, "chemical_price", defaults.get("chemical_price", 0.0))
    media_replacement_price = _input(
        cost_inputs,
        "media_replacement_price",
        defaults.get("media_replacement_price", 0.0),
    )
    media_replacement_fraction = _input(
        cost_inputs,
        "media_replacement_fraction",
        defaults.get("media_replacement_fraction", 0.0),
    )
    land_cost_per_m2 = _input(cost_inputs, "land_cost_per_m2", defaults.get("land_cost_per_m2", 0.0))
    liner_cost_per_m2 = _input(cost_inputs, "liner_cost_per_m2", defaults.get("liner_cost_per_m2", 0.0))

    equipment_capex = capex_per_flow * inlet_flow
    land_capex = _value(technical_result, "pond_area") * land_cost_per_m2
    liner_capex = _value(technical_result, "pond_area") * liner_cost_per_m2
    capex = equipment_capex + land_capex + liner_capex

    fixed_opex = capex * fixed_opex_fraction
    variable_opex = annual_volume * variable_opex_per_m3
    energy_opex = annual_volume * _value(technical_result, "energy_intensity") * electricity_price
    chemical_opex = (
        _value(technical_result, "chemical_consumption")
        * operating_days
        * chemical_price
    )
    replacement_basis = (
        _value(technical_result, "media_inventory")
        or _value(technical_result, "membrane_area")
    )
    media_replacement_cost = (
        replacement_basis
        * media_replacement_fraction
        * media_replacement_price
    )
    annual_opex = (
        fixed_opex
        + variable_opex
        + energy_opex
        + chemical_opex
        + media_replacement_cost
    )

    return {
        "installed_capital_cost": _result(capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "land_capital_cost": _result(land_capex, "USD"),
        "liner_capital_cost": _result(liner_capex, "USD"),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "variable_operating_cost": _result(variable_opex, "USD/year"),
        "energy_operating_cost": _result(energy_opex, "USD/year"),
        "chemical_operating_cost": _result(chemical_opex, "USD/year"),
        "media_replacement_cost": _result(media_replacement_cost, "USD/year"),
        "total_annual_operating_cost": _result(annual_opex, "USD/year"),
    }

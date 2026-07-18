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


def run_template(technical_result, cost_inputs, context, defaults):
    inlet_flow = _value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330))
    annual_volume = inlet_flow * operating_days
    investment_factor = _investment_factor(context)

    capex_per_flow = _input(cost_inputs, "capex_per_flow", defaults.get("capex_per_flow", 0.0))
    column_capex_multiplier = _input(
        cost_inputs,
        "column_capex_multiplier",
        defaults.get("column_capex_multiplier", 1.0),
    )
    if column_capex_multiplier < 0.0:
        raise ValueError("Column CAPEX multiplier cannot be negative.")
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
    capex_per_kw = _input(cost_inputs, "capex_per_kw", defaults.get("capex_per_kw", 0.0))
    land_cost_per_m2 = _input(cost_inputs, "land_cost_per_m2", defaults.get("land_cost_per_m2", 0.0))
    liner_cost_per_m2 = _input(cost_inputs, "liner_cost_per_m2", defaults.get("liner_cost_per_m2", 0.0))
    thermal_energy_price = float(context.get("thermal_energy_price", 0.0))

    bare_flow_capex = capex_per_flow * inlet_flow
    equipment_capex = bare_flow_capex * column_capex_multiplier
    power_capex = _value(technical_result, "power_capacity") * capex_per_kw
    land_capex = _value(technical_result, "pond_area") * land_cost_per_m2
    liner_capex = _value(technical_result, "pond_area") * liner_cost_per_m2
    total_equipment_capex = equipment_capex + power_capex + land_capex + liner_capex
    capex = total_equipment_capex * investment_factor

    fixed_opex = capex * fixed_opex_fraction
    variable_opex = annual_volume * variable_opex_per_m3
    energy_opex = annual_volume * _value(technical_result, "energy_intensity") * electricity_price
    thermal_energy_opex = (
        annual_volume
        * _value(technical_result, "thermal_energy_intensity")
        * thermal_energy_price
    )
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
        + thermal_energy_opex
        + chemical_opex
        + media_replacement_cost
    )

    return {
        "installed_capital_cost": _result(capex, "USD"),
        "equipment_capital_cost": _result(total_equipment_capex, "USD"),
        "bare_flow_capital_cost": _result(bare_flow_capex, "USD"),
        "column_capex_multiplier": _result(column_capex_multiplier, "-"),
        "investment_factor": _result(investment_factor, "-"),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "variable_operating_cost": _result(variable_opex, "USD/year"),
        "energy_operating_cost": _result(energy_opex, "USD/year"),
        "thermal_energy_operating_cost": _result(thermal_energy_opex, "USD/year"),
        "chemical_operating_cost": _result(chemical_opex, "USD/year"),
        "media_replacement_cost": _result(media_replacement_cost, "USD/year"),
        "total_annual_operating_cost": _result(annual_opex, "USD/year"),
    }

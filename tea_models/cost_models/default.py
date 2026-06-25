def run(unit_process, technical_result, cost_inputs, context):
    """Default cost model for a unit process.

    Unit-specific cost model files can replace this function while keeping the
    same signature.
    """
    inlet_flow = float(technical_result.get("inlet_flow", {}).get("value", 0.0))
    annual_volume = inlet_flow * float(context.get("operating_days_per_year", 330))
    capex = float(cost_inputs.get("capex_per_flow", 0.0)) * inlet_flow

    fixed_opex = capex * float(cost_inputs.get("fixed_opex_fraction", 0.0))
    variable_opex = annual_volume * float(cost_inputs.get("variable_opex_per_m3", 0.0))
    electricity_price = float(context.get("electricity_price", 0.0))
    energy_opex = (
        annual_volume
        * float(technical_result.get("energy_intensity", {}).get("value", 0.0))
        * electricity_price
    )
    thermal_energy_price = float(context.get("thermal_energy_price", 0.0))
    thermal_energy_opex = (
        annual_volume
        * float(technical_result.get("thermal_energy_intensity", {}).get("value", 0.0))
        * thermal_energy_price
    )

    annual_opex = fixed_opex + variable_opex + energy_opex + thermal_energy_opex

    return {
        "installed_capital_cost": {"value": capex, "unit": "USD"},
        "fixed_operating_cost": {"value": fixed_opex, "unit": "USD/year"},
        "variable_operating_cost": {"value": variable_opex, "unit": "USD/year"},
        "energy_operating_cost": {"value": energy_opex, "unit": "USD/year"},
        "thermal_energy_operating_cost": {"value": thermal_energy_opex, "unit": "USD/year"},
        "total_annual_operating_cost": {"value": annual_opex, "unit": "USD/year"},
    }

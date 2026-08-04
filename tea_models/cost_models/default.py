from tea_models.cost_models.cost_utils import (
    escalate_cost,
    input_value,
    investment_factor,
    result,
    scaled_capex_from_unit_cost,
    value,
)


def run(unit_process, technical_result, cost_inputs, context):
    """Default cost model for a unit process.

    Unit-specific cost model files can replace this function while keeping the
    same signature.
    """
    inlet_flow = value(technical_result, "inlet_flow")
    annual_volume = inlet_flow * float(context.get("operating_days_per_year", 330))
    equipment_capex = scaled_capex_from_unit_cost(
        input_value(cost_inputs, "capex_per_flow", 0.0),
        inlet_flow,
        cost_inputs,
        context,
    )
    investment_factor_value = investment_factor(context)
    capex = equipment_capex * investment_factor_value

    fixed_opex = capex * input_value(cost_inputs, "fixed_opex_fraction", 0.0)
    variable_opex = annual_volume * escalate_cost(
        input_value(cost_inputs, "variable_opex_per_m3", 0.0),
        cost_inputs,
        "variable_opex_per_m3",
        context,
    )
    electricity_price = float(context.get("electricity_price", 0.0))
    energy_opex = (
        annual_volume
        * value(technical_result, "energy_intensity")
        * electricity_price
    )
    thermal_energy_price = float(context.get("thermal_energy_price", 0.0))
    thermal_energy_opex = (
        annual_volume
        * value(technical_result, "thermal_energy_intensity")
        * thermal_energy_price
    )

    annual_opex = fixed_opex + variable_opex + energy_opex + thermal_energy_opex

    return {
        "installed_capital_cost": result(capex, "USD"),
        "equipment_capital_cost": result(equipment_capex, "USD"),
        "investment_factor": result(investment_factor_value, "-"),
        "fixed_operating_cost": result(fixed_opex, "USD/year"),
        "variable_operating_cost": result(variable_opex, "USD/year"),
        "energy_operating_cost": result(energy_opex, "USD/year"),
        "thermal_energy_operating_cost": result(thermal_energy_opex, "USD/year"),
        "total_annual_operating_cost": result(annual_opex, "USD/year"),
    }

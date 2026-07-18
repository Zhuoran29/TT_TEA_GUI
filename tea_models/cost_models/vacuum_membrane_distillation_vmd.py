"""VMD equipment and operating cost breakdown from the workbook model."""

from __future__ import annotations

from tea_models.technical_models.helper_function import CostIndexFactor


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
    inlet_flow = _value(technical_result, "inlet_flow")
    inlet_flow_m3_s = inlet_flow / 86_400.0
    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_feed = inlet_flow * operating_days
    investment_factor = max(float(context.get("investment_factor", 2.0)), 0.0)
    base_year = int(context.get("base_currency_year", 2018))
    index_2018 = CostIndexFactor(2018, base_year)
    index_2020 = CostIndexFactor(2020, base_year)

    low_pressure_pump_cost = _input(cost_inputs, "low_pressure_pump_cost", 889.0)
    hx_material_factor = _input(cost_inputs, "heat_exchanger_material_factor", 1.0)
    hx_unit_cost = _input(cost_inputs, "heat_exchanger_unit_cost", 300.0)
    mixer_unit_cost = _input(cost_inputs, "mixer_unit_cost", 361.0)
    heater_unit_cost = _input(cost_inputs, "heater_unit_cost", 0.066)
    chiller_unit_cost = _input(cost_inputs, "chiller_unit_cost", 0.20)
    chiller_cop = _input(cost_inputs, "chiller_cop", 7.0)
    membrane_cost = _input(cost_inputs, "membrane_cost", 56.0)
    membrane_replacement = _input(cost_inputs, "membrane_replacement_fraction", 0.20)
    fixed_opex_fraction = _input(cost_inputs, "fixed_opex_fraction", 0.03)
    if chiller_cop <= 0.0:
        raise ValueError("VMD chiller COP must be positive.")
    if any(value < 0.0 for value in (
        low_pressure_pump_cost,
        hx_material_factor,
        hx_unit_cost,
        mixer_unit_cost,
        heater_unit_cost,
        chiller_unit_cost,
        membrane_cost,
        membrane_replacement,
        fixed_opex_fraction,
    )):
        raise ValueError("VMD cost inputs cannot be negative.")

    recycle_ratio = _value(technical_result, "recycle_ratio", 6.169)
    membrane_area = _value(technical_result, "membrane_area")
    hx_area = _value(technical_result, "heat_exchanger_area")
    heater_duty = _value(technical_result, "heater_thermal_duty")
    chiller_duty = _value(technical_result, "chiller_thermal_duty")
    auxiliary_electric_power = _value(technical_result, "auxiliary_electric_power")

    membrane_capex = investment_factor * membrane_cost * membrane_area * index_2018
    heater_capex = (
        investment_factor * heater_unit_cost * heater_duty * 1000.0 * index_2018
    )
    chiller_capex = (
        investment_factor * chiller_unit_cost * chiller_duty * 1000.0
        / chiller_cop * index_2018
    )
    feed_pump_capex = (
        investment_factor * 1000.0 * low_pressure_pump_cost * inlet_flow_m3_s * index_2018
    )
    permeate_pump_capex = feed_pump_capex * recycle_ratio
    brine_pump_capex = feed_pump_capex * (1.0 + recycle_ratio)
    heat_exchanger_capex = (
        investment_factor * hx_unit_cost * hx_material_factor * hx_area * index_2020
    )
    mixer_capex = (
        investment_factor * 1000.0 * mixer_unit_cost * inlet_flow_m3_s
        * (1.0 + recycle_ratio) * index_2018
    )
    installed_capex = sum((
        membrane_capex,
        heater_capex,
        chiller_capex,
        feed_pump_capex,
        permeate_pump_capex,
        brine_pump_capex,
        heat_exchanger_capex,
        mixer_capex,
    ))

    fixed_opex = installed_capex * fixed_opex_fraction
    replacement_opex = membrane_replacement * membrane_cost * membrane_area * index_2018
    electricity_opex = (
        annual_feed
        * _value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    thermal_energy_opex = (
        annual_feed
        * _value(technical_result, "thermal_energy_intensity")
        * float(context.get("thermal_energy_price", 0.0))
    )
    annual_opex = fixed_opex + replacement_opex + electricity_opex + thermal_energy_opex

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(installed_capex, "USD"),
        "investment_factor": _result(investment_factor, "-"),
        "membrane_capital_cost": _result(membrane_capex, "USD"),
        "heater_capital_cost": _result(heater_capex, "USD"),
        "chiller_capital_cost": _result(chiller_capex, "USD"),
        "feed_pump_capital_cost": _result(feed_pump_capex, "USD"),
        "permeate_pump_capital_cost": _result(permeate_pump_capex, "USD"),
        "brine_pump_capital_cost": _result(brine_pump_capex, "USD"),
        "heat_exchanger_capital_cost": _result(heat_exchanger_capex, "USD"),
        "mixer_capital_cost": _result(mixer_capex, "USD"),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "membrane_replacement_cost": _result(replacement_opex, "USD/year"),
        "energy_operating_cost": _result(electricity_opex, "USD/year"),
        "electricity_operating_cost": _result(electricity_opex, "USD/year"),
        "thermal_energy_operating_cost": _result(thermal_energy_opex, "USD/year"),
        "auxiliary_electric_power": _result(auxiliary_electric_power, "kW"),
        "total_annual_operating_cost": _result(annual_opex, "USD/year"),
    }

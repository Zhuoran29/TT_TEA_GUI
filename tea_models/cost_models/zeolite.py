"""Zeolite cost model with NH4Cl recovery credit."""

from __future__ import annotations

from tea_models.cost_models.cost_utils import (
    cost_index_factor_to_base,
    cost_year,
    escalate_cost,
    input_value,
    investment_factor,
    value,
)


DEFAULTS = {
    "equipment_capex_per_gpm": 150.0,
    "capex_scaling_exponent": 1.0,
    "zeolite_price": 4.41,
    "media_replacement_fraction_per_cycle": 0.0,
    "nh4cl_price": 57.5,
    "om_contingency_factor": 0.20,
}

M3_DAY_TO_GPM = 264.172052 / 1440.0
N_TO_NH4CL_MASS_RATIO = 53.491 / 14.0067


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    flow_gpm = inlet_flow * M3_DAY_TO_GPM
    capex_per_gpm = input_value(cost_inputs, "equipment_capex_per_gpm", DEFAULTS["equipment_capex_per_gpm"])
    exponent = _input(cost_inputs, "capex_scaling_exponent", DEFAULTS["capex_scaling_exponent"])
    capex_factor = cost_index_factor_to_base(context, cost_year(cost_inputs, "equipment_capex_per_gpm"))
    if capex_per_gpm < 0.0 or exponent < 0.0:
        raise ValueError("Zeolite CAPEX inputs cannot be negative.")
    equipment_capex = capex_per_gpm * capex_factor * flow_gpm**exponent
    installed_capex = equipment_capex * investment_factor(context)

    zeolite_price = escalate_cost(input_value(cost_inputs, "zeolite_price", DEFAULTS["zeolite_price"]), cost_inputs, "zeolite_price", context, 2014)
    media_replacement_fraction = _input(
        cost_inputs,
        "media_replacement_fraction_per_cycle",
        DEFAULTS["media_replacement_fraction_per_cycle"],
    )
    nh4cl_price = escalate_cost(input_value(cost_inputs, "nh4cl_price", DEFAULTS["nh4cl_price"]), cost_inputs, "nh4cl_price", context, 2024)
    contingency_factor = _input(cost_inputs, "om_contingency_factor", DEFAULTS["om_contingency_factor"])
    if any(v < 0.0 for v in [zeolite_price, media_replacement_fraction, nh4cl_price, contingency_factor]):
        raise ValueError("Zeolite OPEX inputs cannot be negative.")

    cycles_per_year = value(technical_result, "cycles_per_year")
    zeolite_mass = value(technical_result, "zeolite_mass_from_aec")
    annual_media_replacement = (
        zeolite_mass
        * zeolite_price
        * cycles_per_year
        * operating_days
        / 365.0
        * media_replacement_fraction
    )
    annual_removed_n = value(technical_result, "ammonia_removed") * operating_days
    nh4cl_tonne_year = annual_removed_n * N_TO_NH4CL_MASS_RATIO / 1000.0
    nh4cl_credit = nh4cl_tonne_year * nh4cl_price
    energy = inlet_flow * operating_days * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    opex_before_contingency = energy + annual_media_replacement
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency - nh4cl_credit

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "cost_index_factor": _result(capex_factor, "factor"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "energy_operating_cost": _result(energy, "USD/year"),
        "zeolite_media_replacement_cost": _result(annual_media_replacement, "USD/year"),
        "media_replacement_fraction_per_cycle": _result(media_replacement_fraction, "fraction/cycle"),
        "om_contingency": _result(contingency, "USD/year"),
        "nh4cl_revenue_credit": _result(-nh4cl_credit, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "annual_nh4cl_product": _result(nh4cl_tonne_year, "metric tonne/year"),
    }

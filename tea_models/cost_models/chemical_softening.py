"""Chemical softening cost model adapted from the KBH/NMPWRC TEA basis."""

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
    "reference_direct_cs_capex": 25829456.94,
    "reference_capacity": 3785.41,
    "capex_scaling_exponent": 0.87,
    "lime_price": 0.05,
    "soda_ash_price": 0.45,
    "h2so4_price": 0.043,
    "solid_disposal_cost": 0.11,
    "lime_purity_fraction": 1.0,
    "soda_ash_purity_fraction": 1.0,
    "h2so4_purity_fraction": 0.98,
    "labor_fte": 1.0,
    "labor_cost_per_fte_year": 80000.0,
    "om_contingency_factor": 0.20,
}

LB_PER_KG = 2.2046226218


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _scaled_reference_capex(cost_inputs, context, capacity):
    reference_capex = input_value(
        cost_inputs,
        "reference_direct_cs_capex",
        DEFAULTS["reference_direct_cs_capex"],
    )
    reference_capacity = _input(cost_inputs, "reference_capacity", DEFAULTS["reference_capacity"])
    exponent = _input(cost_inputs, "capex_scaling_exponent", DEFAULTS["capex_scaling_exponent"])
    if reference_capex < 0.0 or reference_capacity <= 0.0 or exponent < 0.0:
        raise ValueError("Chemical softening CAPEX reference values must be nonnegative with positive reference capacity.")
    factor = cost_index_factor_to_base(context, cost_year(cost_inputs, "reference_direct_cs_capex"))
    return reference_capex * factor * (capacity / reference_capacity) ** exponent, factor, exponent


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_feed = inlet_flow * operating_days
    equipment_capex, index_factor, exponent = _scaled_reference_capex(cost_inputs, context, inlet_flow)
    installed_capex = equipment_capex * investment_factor(context)

    lime_price = escalate_cost(input_value(cost_inputs, "lime_price", DEFAULTS["lime_price"]), cost_inputs, "lime_price", context)
    soda_price = escalate_cost(input_value(cost_inputs, "soda_ash_price", DEFAULTS["soda_ash_price"]), cost_inputs, "soda_ash_price", context)
    acid_price = escalate_cost(input_value(cost_inputs, "h2so4_price", DEFAULTS["h2so4_price"]), cost_inputs, "h2so4_price", context)
    disposal_price = escalate_cost(input_value(cost_inputs, "solid_disposal_cost", DEFAULTS["solid_disposal_cost"]), cost_inputs, "solid_disposal_cost", context)
    labor_cost_per_fte = escalate_cost(input_value(cost_inputs, "labor_cost_per_fte_year", DEFAULTS["labor_cost_per_fte_year"]), cost_inputs, "labor_cost_per_fte_year", context)
    labor_fte = _input(cost_inputs, "labor_fte", DEFAULTS["labor_fte"])
    om_contingency_factor = _input(cost_inputs, "om_contingency_factor", DEFAULTS["om_contingency_factor"])

    if any(v < 0.0 for v in [lime_price, soda_price, acid_price, disposal_price, labor_fte, labor_cost_per_fte, om_contingency_factor]):
        raise ValueError("Chemical softening cost inputs cannot be negative.")

    lime_kg_year = value(technical_result, "lime_dose") * annual_feed / 1000.0
    soda_kg_year = value(technical_result, "soda_ash_dose") * annual_feed / 1000.0
    acid_kg_year = value(technical_result, "h2so4_dose") * annual_feed / 1000.0
    chemical_cost = (
        lime_kg_year * LB_PER_KG * lime_price
        + soda_kg_year * LB_PER_KG * soda_price
        + acid_kg_year * LB_PER_KG * acid_price
    )
    energy_cost = annual_feed * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    solid_disposal = value(technical_result, "solid_waste_generation") * annual_feed * disposal_price
    labor = labor_fte * labor_cost_per_fte
    opex_before_contingency = chemical_cost + energy_cost + solid_disposal + labor
    contingency = opex_before_contingency * om_contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "cost_index_factor": _result(index_factor, "factor"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "lime_operating_cost": _result(lime_kg_year * LB_PER_KG * lime_price, "USD/year"),
        "soda_ash_operating_cost": _result(soda_kg_year * LB_PER_KG * soda_price, "USD/year"),
        "h2so4_operating_cost": _result(acid_kg_year * LB_PER_KG * acid_price, "USD/year"),
        "chemical_operating_cost": _result(chemical_cost, "USD/year"),
        "energy_operating_cost": _result(energy_cost, "USD/year"),
        "solid_disposal_operating_cost": _result(solid_disposal, "USD/year"),
        "labor_cost": _result(labor, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
    }

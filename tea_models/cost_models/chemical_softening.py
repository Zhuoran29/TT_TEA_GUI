"""Chemical softening cost model (NMSU CS model; KBH ROC TEA workbook basis).

Capital (KBH TEA Appendix, Capital_Summary, ENR May 2024, location factor 0.815):
  C_bare    = 25,829,457 x (Q / 3,785.41 m3/day)^0.87       2024 $; lime softening 6.8 $/gpd x 1 MGD
                                                           + lime dewatering 11.53 M + chemical area 7.5 M
  C_direct  = TIC x C_bare                                 TIC = 1.43 (KBH site 10% and E&IC 30%)
  CAPEX     = IF x C_direct                                system-level investment factor
Operating:
  chemicals   = (lime + soda ash + H2SO4) x days x unit prices
  electricity = energy_intensity x Q x days x electricity price
  maintenance = f_maint x C_direct                          KBH "other maintenance" 2% of system direct; includes labor
  total       = (1 + f_contingency) x (chemicals + electricity + maintenance)
Precipitated solids are reported for the system-level waste stream; their disposal cost is not
included in this unit.
"""

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
    "installation_factor": 1.43,
    "maintenance_fraction": 0.02,
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
    bare_capex, index_factor, exponent = _scaled_reference_capex(cost_inputs, context, inlet_flow)
    tic = _input(cost_inputs, "installation_factor", DEFAULTS["installation_factor"])
    maintenance_fraction = _input(cost_inputs, "maintenance_fraction", DEFAULTS["maintenance_fraction"])
    om_contingency_factor = _input(cost_inputs, "om_contingency_factor", DEFAULTS["om_contingency_factor"])
    direct_capex = tic * bare_capex
    installed_capex = direct_capex * investment_factor(context)

    lime_price = escalate_cost(input_value(cost_inputs, "lime_price", DEFAULTS["lime_price"]), cost_inputs, "lime_price", context)
    soda_price = escalate_cost(input_value(cost_inputs, "soda_ash_price", DEFAULTS["soda_ash_price"]), cost_inputs, "soda_ash_price", context)
    acid_price = escalate_cost(input_value(cost_inputs, "h2so4_price", DEFAULTS["h2so4_price"]), cost_inputs, "h2so4_price", context)
    if any(v < 0.0 for v in [lime_price, soda_price, acid_price, tic, maintenance_fraction, om_contingency_factor]):
        raise ValueError("Chemical softening cost inputs cannot be negative.")

    lime_kg_year = value(technical_result, "lime_dose") * annual_feed / 1000.0
    soda_kg_year = value(technical_result, "soda_ash_dose") * annual_feed / 1000.0
    acid_kg_year = value(technical_result, "h2so4_dose") * annual_feed / 1000.0
    lime_cost = lime_kg_year * LB_PER_KG * lime_price
    soda_cost = soda_kg_year * LB_PER_KG * soda_price
    acid_cost = acid_kg_year * LB_PER_KG * acid_price
    chemical_cost = lime_cost + soda_cost + acid_cost
    energy_cost = annual_feed * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    maintenance = maintenance_fraction * direct_capex
    opex_before_contingency = chemical_cost + energy_cost + maintenance
    contingency = opex_before_contingency * om_contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "installation_factor": _result(tic, "-"),
        "cost_index_factor": _result(index_factor, "factor"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "lime_operating_cost": _result(lime_cost, "USD/year"),
        "soda_ash_operating_cost": _result(soda_cost, "USD/year"),
        "h2so4_operating_cost": _result(acid_cost, "USD/year"),
        "chemical_operating_cost": _result(chemical_cost, "USD/year"),
        "energy_operating_cost": _result(energy_cost, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "fixed_operating_cost": _result(maintenance * (1.0 + om_contingency_factor), "USD/year"),
        "variable_operating_cost": _result((chemical_cost + energy_cost) * (1.0 + om_contingency_factor), "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "solid_waste": _result(value(technical_result, "solid_waste") * operating_days, "kg dry/year"),
    }

"""Electrocoagulation cost model (NMSU EC-Al model, harmonized cost structure).

Capital (NMSU EC model: Lugo et al. 2025 reference EC-Al cost at 11,356 m3/day):
  C_bare    = C_ref x (Q / Q_ref)^n          2024 dollars, escalated with CEPCI; n = 0.87
  C_direct  = TIC x C_bare                   TIC = 1 (reference is a plant-level cost)
  CAPEX     = IF x C_direct                  system-level investment factor
Operating:
  aluminum    = Al consumption x Al price    anode (electrode) replacement
  electricity = energy_intensity x Q x days x electricity price
  maintenance = f_maint x C_direct           includes labor
  total       = (1 + f_contingency) x (aluminum + electricity + maintenance)
Sludge (Al(OH)3 + removed TSS) is reported for the system-level waste stream; its
disposal cost is not included in this unit.
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


REFERENCE_COST_YEAR = 2024  # Lugo et al. 2025 report costs in 2024 dollars
ALUMINUM_PRICE_YEAR = 2022

DEFAULTS = {
    "reference_ec_capex": 1595666.0,
    "reference_capacity": 11356.0,
    "capex_scaling_exponent": 0.87,
    "installation_factor": 1.0,
    "aluminum_price": 2.23,
    "maintenance_fraction": 0.03,
    "om_contingency_factor": 0.20,
}


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def run(unit_process, technical_result, cost_inputs, context):
    def get(name):
        return input_value(cost_inputs, name, DEFAULTS[name])

    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    reference_capex = get("reference_ec_capex")
    reference_capacity = get("reference_capacity")
    exponent = get("capex_scaling_exponent")
    tic = get("installation_factor")
    maintenance_fraction = get("maintenance_fraction")
    contingency_factor = get("om_contingency_factor")
    if reference_capex < 0.0 or reference_capacity <= 0.0:
        raise ValueError("EC reference CAPEX must be nonnegative and the reference capacity positive.")
    if any(v < 0.0 for v in [exponent, tic, maintenance_fraction, contingency_factor]):
        raise ValueError("EC cost inputs cannot be negative.")

    index_factor = cost_index_factor_to_base(
        context, cost_year(cost_inputs, "reference_ec_capex", REFERENCE_COST_YEAR)
    )
    bare_capex = (
        reference_capex * (inlet_flow / reference_capacity) ** exponent * index_factor
        if inlet_flow > 0.0
        else 0.0
    )
    direct_capex = tic * bare_capex
    installed_capex = investment_factor(context) * direct_capex

    aluminum_price = escalate_cost(get("aluminum_price"), cost_inputs, "aluminum_price", context, ALUMINUM_PRICE_YEAR)
    if aluminum_price < 0.0:
        raise ValueError("Aluminum price cannot be negative.")
    aluminum_kg = value(technical_result, "aluminum_consumption") * operating_days
    aluminum = aluminum_kg * aluminum_price
    electricity = (
        inlet_flow
        * operating_days
        * value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    maintenance = maintenance_fraction * direct_capex
    opex_before_contingency = aluminum + electricity + maintenance
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "installation_factor": _result(tic, "-"),
        "investment_factor": _result(investment_factor(context), "-"),
        "cost_index_factor": _result(index_factor, "factor"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "aluminum_operating_cost": _result(aluminum, "USD/year"),
        "energy_operating_cost": _result(electricity, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "fixed_operating_cost": _result(maintenance * (1.0 + contingency_factor), "USD/year"),
        "variable_operating_cost": _result((aluminum + electricity) * (1.0 + contingency_factor), "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "annual_aluminum_consumption": _result(aluminum_kg, "kg/year"),
        "solid_waste": _result(value(technical_result, "solid_waste") * operating_days, "kg dry/year"),
    }

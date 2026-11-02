"""DAF cost model (NMSU assumptions).

Capital:
  C_bare    = 313,992 x (Q / Q_ref)^n        Q_ref = 3 MGD; 2018 dollars; n = 0.87
  C_direct  = TIC x C_bare                   TIC = 1 (the reference cost is an installed cost)
  CAPEX     = IF x C_direct                  system-level investment factor
Operating:
  electricity = energy_intensity x Q x days x electricity price
  chemicals   = (ACH x c_ACH + polymer x c_polymer + H2O2 x c_H2O2) x days
  maintenance = f_maint x C_direct           includes labor
  total       = (1 + f_contingency) x (electricity + chemicals + maintenance)

The float is reported as a waste output; its disposal cost is not included.
"""

from __future__ import annotations

from tea_models.cost_models.cost_utils import (
    cost_index_factor_to_base,
    escalate_cost,
    input_value,
    investment_factor,
    value,
)


REFERENCE_CAPEX = 313992.0  # USD_2018 at 3 MGD (WaterTAP zero-order DAF cost at 3 MGD)
REFERENCE_FLOW_M3_DAY = 3.0e6 * 3.785411784 / 1000.0  # 3 MGD
REFERENCE_COST_YEAR = 2018
CHEMICAL_COST_YEAR = 2021

DEFAULTS = {
    "capex_scaling_exponent": 0.87,
    "installation_factor": 1.0,
    "maintenance_fraction": 0.03,
    "om_contingency_factor": 0.20,
    "ach_price": 0.4506,  # $/kg product (EPA WBS polyaluminum chloride, large quantity, 2021 $)
    "polymer_price": 1.6344,  # $/kg (EPA WBS polymers, 2021 $)
    "h2o2_price": 1.3986,  # $/kg as 100% H2O2 (EPA WBS 50% H2O2, large quantity, 2021 $)
}


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def run(unit_process, technical_result, cost_inputs, context):
    def get(name):
        return input_value(cost_inputs, name, DEFAULTS[name])

    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    exponent = get("capex_scaling_exponent")
    tic = get("installation_factor")
    maintenance_fraction = get("maintenance_fraction")
    contingency_factor = get("om_contingency_factor")
    if any(v < 0.0 for v in [exponent, tic, maintenance_fraction, contingency_factor]):
        raise ValueError("DAF cost inputs cannot be negative.")

    index_factor = cost_index_factor_to_base(context, REFERENCE_COST_YEAR)
    bare_capex = (
        REFERENCE_CAPEX * (inlet_flow / REFERENCE_FLOW_M3_DAY) ** exponent * index_factor
        if inlet_flow > 0.0
        else 0.0
    )
    direct_capex = tic * bare_capex
    installed_capex = investment_factor(context) * direct_capex

    electricity = (
        inlet_flow
        * operating_days
        * value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    prices = {
        name: escalate_cost(get(name), cost_inputs, name, context, CHEMICAL_COST_YEAR)
        for name in ("ach_price", "polymer_price", "h2o2_price")
    }
    if any(p < 0.0 for p in prices.values()):
        raise ValueError("DAF chemical prices cannot be negative.")
    ach_kg = value(technical_result, "ach_consumption") * operating_days
    polymer_kg = value(technical_result, "polymer_consumption") * operating_days
    h2o2_kg = value(technical_result, "h2o2_consumption") * operating_days
    ach_cost = ach_kg * prices["ach_price"]
    polymer_cost = polymer_kg * prices["polymer_price"]
    h2o2_cost = h2o2_kg * prices["h2o2_price"]
    chemical_cost = ach_cost + polymer_cost + h2o2_cost

    maintenance = maintenance_fraction * direct_capex
    opex_before_contingency = electricity + chemical_cost + maintenance
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "installation_factor": _result(tic, "-"),
        "investment_factor": _result(investment_factor(context), "-"),
        "cost_index_factor": _result(index_factor, "factor"),
        "energy_operating_cost": _result(electricity, "USD/year"),
        "ach_operating_cost": _result(ach_cost, "USD/year"),
        "polymer_operating_cost": _result(polymer_cost, "USD/year"),
        "h2o2_operating_cost": _result(h2o2_cost, "USD/year"),
        "chemical_operating_cost": _result(chemical_cost, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "fixed_operating_cost": _result(maintenance * (1.0 + contingency_factor), "USD/year"),
        "variable_operating_cost": _result((electricity + chemical_cost) * (1.0 + contingency_factor), "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "annual_ach_consumption": _result(ach_kg, "kg/year"),
        "annual_polymer_consumption": _result(polymer_kg, "kg/year"),
        "annual_h2o2_consumption": _result(h2o2_kg, "kg/year"),
        "float_solid_waste": _result(value(technical_result, "float_dry_mass") * operating_days, "kg dry/year"),
        "float_waste_volume": _result(value(technical_result, "float_volume") * operating_days, "m3/year"),
    }

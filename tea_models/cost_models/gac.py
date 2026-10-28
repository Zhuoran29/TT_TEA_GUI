"""GAC cost model following the WaterTAP 1.4 GAC costing method.

Capital (steel pressure contactors; correlations regressed by WaterTAP from the
US EPA WBS GAC model, USD_2020):
  contactors  = N_total * (c0 + c1*v + c2*v^2 + c3*v^3)      v = bed volume per vessel
  adsorbent   = a * exp(b * min(M, M_cap)) * M                M = fresh GAC mass
  other       = A * V_total^n                                 V_total incl. redundant vessels
  direct      = TIC * (contactors + adsorbent + other)        unit-level installation factor
  installed   = IF * direct                                   system-level investment factor

The EPA WBS unit costs behind these correlations already include equipment
transportation and installation, so the default TIC is low (1.15).

Operating (spent-GAC quantities scale with operating days):
  regeneration = f_regen * usage * c_regen
  makeup       = (1 - f_regen) * usage * c_makeup
  electricity  = pump energy * electricity price
  maintenance  = f_maint * direct capital
  total        = (1 + f_contingency) * sum of the above

Spent GAC that is not regenerated, (1 - f_regen) * usage, is reported as a
solid-waste quantity; its disposal cost is left to the system level.
"""

from __future__ import annotations

import math

from tea_models.cost_models.cost_utils import (
    cost_index_factor_to_base,
    escalate_cost,
    input_value,
    investment_factor,
    value,
)


CORRELATION_COST_YEAR = 2020

# Fixed capital correlations for steel pressure contactors (USD_2020).
CONTACTOR_COST_COEFFS = (10010.9, 2204.95, -15.9378, 0.110592)  # USD per vessel, v in m3
ADSORBENT_UNIT_COST_COEFFS = (4.58342, -1.25311e-5)  # USD/kg, exponent per kg
ADSORBENT_REFERENCE_MASS_MAX = 18143.7  # kg; unit price stops falling above this mass
OTHER_PROCESS_COST_COEFFS = (16660.7, 0.552207)  # USD, exponent on total contactor volume (m3)

DEFAULTS = {
    "installation_factor": 1.15,
    "gac_regeneration_cost": 4.28352,
    "gac_replacement_cost": 4.58223,
    "regeneration_fraction": 0.80,
    "maintenance_fraction": 0.03,
    "om_contingency_factor": 0.20,
}


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def capital_costs(n_total, vessel_volume, total_volume, gac_mass):
    """Bare capital items in USD_2020: contactors, initial GAC charge, other process."""
    if n_total > 0 and vessel_volume > 0.0:
        c0, c1, c2, c3 = CONTACTOR_COST_COEFFS
        contactors = n_total * (c0 + c1 * vessel_volume + c2 * vessel_volume**2 + c3 * vessel_volume**3)
    else:
        contactors = 0.0
    a, b = ADSORBENT_UNIT_COST_COEFFS
    unit_cost = a * math.exp(b * min(gac_mass, ADSORBENT_REFERENCE_MASS_MAX))
    adsorbent = unit_cost * gac_mass
    coeff, exponent = OTHER_PROCESS_COST_COEFFS
    other = coeff * total_volume**exponent if total_volume > 0.0 else 0.0
    return contactors, adsorbent, unit_cost, other


def run(unit_process, technical_result, cost_inputs, context):
    def get(name):
        return input_value(cost_inputs, name, DEFAULTS[name])

    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    operating_fraction = operating_days / 365.0
    investment_factor_value = investment_factor(context)

    tic = get("installation_factor")
    regeneration_fraction = get("regeneration_fraction")
    maintenance_fraction = get("maintenance_fraction")
    contingency_factor = get("om_contingency_factor")
    if tic < 0.0 or maintenance_fraction < 0.0 or contingency_factor < 0.0:
        raise ValueError("GAC installation, maintenance and contingency factors must be nonnegative.")
    if not 0.0 <= regeneration_fraction <= 1.0:
        raise ValueError("GAC regeneration fraction must be between 0 and 1.")

    # --- Capital ---
    index_factor = cost_index_factor_to_base(context, CORRELATION_COST_YEAR)
    contactors, adsorbent, adsorbent_unit_cost, other = capital_costs(
        value(technical_result, "operating_vessels") + value(technical_result, "redundant_vessels"),
        value(technical_result, "bed_volume_per_vessel"),
        value(technical_result, "total_contactor_volume"),
        value(technical_result, "fresh_gac_mass"),
    )
    contactor_cost = contactors * index_factor
    adsorbent_cost = adsorbent * index_factor
    other_process_cost = other * index_factor
    bare_capex = contactor_cost + adsorbent_cost + other_process_cost
    direct_capex = tic * bare_capex
    installed_capex = investment_factor_value * direct_capex

    # --- Operating ---
    regeneration_cost = escalate_cost(
        get("gac_regeneration_cost"), cost_inputs, "gac_regeneration_cost", context, CORRELATION_COST_YEAR
    )
    makeup_cost = escalate_cost(
        get("gac_replacement_cost"), cost_inputs, "gac_replacement_cost", context, CORRELATION_COST_YEAR
    )

    annual_usage = value(technical_result, "annual_gac_usage") * operating_fraction
    regenerated_kg = annual_usage * regeneration_fraction
    makeup_kg = annual_usage * (1.0 - regeneration_fraction)

    regeneration_opex = regenerated_kg * regeneration_cost
    makeup_opex = makeup_kg * makeup_cost
    electricity_opex = (
        value(technical_result, "energy_intensity")
        * inlet_flow
        * operating_days
        * float(context.get("electricity_price", 0.0))
    )
    maintenance_opex = maintenance_fraction * direct_capex

    variable_before_contingency = regeneration_opex + makeup_opex + electricity_opex
    opex_before_contingency = variable_before_contingency + maintenance_opex
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "contactor_capital_cost": _result(contactor_cost, "USD"),
        "adsorbent_initial_charge_cost": _result(adsorbent_cost, "USD"),
        "adsorbent_unit_cost": _result(adsorbent_unit_cost * index_factor, "USD/kg"),
        "other_process_capital_cost": _result(other_process_cost, "USD"),
        "installation_factor": _result(tic, "-"),
        "investment_factor": _result(investment_factor_value, "-"),
        "cost_index_factor": _result(index_factor, "factor"),
        "gac_regeneration_operating_cost": _result(regeneration_opex, "USD/year"),
        "gac_replacement_operating_cost": _result(makeup_opex, "USD/year"),
        "electricity_operating_cost": _result(electricity_opex, "USD/year"),
        "maintenance_operating_cost": _result(maintenance_opex, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "fixed_operating_cost": _result(maintenance_opex * (1.0 + contingency_factor), "USD/year"),
        "variable_operating_cost": _result(variable_before_contingency * (1.0 + contingency_factor), "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "annual_gac_usage": _result(annual_usage, "kg/year"),
        "regenerated_gac": _result(regenerated_kg, "kg/year"),
        "makeup_gac": _result(makeup_kg, "kg/year"),
        "spent_gac_solid_waste": _result(makeup_kg, "kg/year"),
    }

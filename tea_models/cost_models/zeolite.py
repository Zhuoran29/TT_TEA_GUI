"""Zeolite cost model (NMSU assumptions).

Capital (US EPA WBS cation-exchange model run with zeolite settings, USD_2021):
  bare      = a * Q^b                            Q = inlet flow (m3/day); excludes the media charge
  direct    = TIC * bare                         unit-level installation factor
  installed = IF * direct                        system-level investment factor
Operating:
  electricity = energy_intensity * Q * days * electricity price
  regenerant  = (NaCl + NaOH consumption) * days/365 * unit prices
  media       = M_AEC * f_replace * n_cycles * days/365 * zeolite price
  maintenance = f_maint * direct capital
  total       = (1 + f_contingency) * (electricity + regenerant + media + maintenance)

The default media replacement fraction is 0 (media regenerated in place).
Spent brine disposal and the NH4Cl recovery credit are not included.
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
    "capex_coefficient": 3305.1,  # $(2021), Q in m3/day
    "capex_exponent": 0.6961,
    "installation_factor": 1.15,
    "maintenance_fraction": 0.02,
    "om_contingency_factor": 0.20,
    "nacl_price": 40.0,  # $/metric tonne, Deng et al. 2014
    "naoh_price": 300.0,  # $/metric tonne, Deng et al. 2014
    "zeolite_price": 4.41,  # $/kg
    "media_replacement_fraction_per_cycle": 0.0,
}
EQUIPMENT_COST_YEAR = 2021
CHEMICAL_COST_YEAR = 2014



def _result(value_, unit):
    return {"value": value_, "unit": unit}


def run(unit_process, technical_result, cost_inputs, context):
    def get(name):
        return input_value(cost_inputs, name, DEFAULTS[name])

    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    capex_coefficient = get("capex_coefficient")
    capex_exponent = get("capex_exponent")
    tic = get("installation_factor")
    maintenance_fraction = get("maintenance_fraction")
    contingency_factor = get("om_contingency_factor")
    if any(v < 0.0 for v in [capex_coefficient, capex_exponent, tic, maintenance_fraction, contingency_factor]):
        raise ValueError("Zeolite cost inputs cannot be negative.")

    index_factor = cost_index_factor_to_base(
        context, cost_year(cost_inputs, "capex_coefficient", EQUIPMENT_COST_YEAR)
    )
    bare_capex = capex_coefficient * max(inlet_flow, 0.0) ** capex_exponent * index_factor if inlet_flow > 0.0 else 0.0
    direct_capex = tic * bare_capex
    installed_capex = investment_factor(context) * direct_capex

    electricity = (
        inlet_flow
        * operating_days
        * value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    nacl_price = escalate_cost(get("nacl_price"), cost_inputs, "nacl_price", context, CHEMICAL_COST_YEAR)
    naoh_price = escalate_cost(get("naoh_price"), cost_inputs, "naoh_price", context, CHEMICAL_COST_YEAR)
    if nacl_price < 0.0 or naoh_price < 0.0:
        raise ValueError("Zeolite chemical prices cannot be negative.")
    operating_fraction = operating_days / 365.0
    nacl_kg = value(technical_result, "annual_nacl_consumption") * operating_fraction
    naoh_kg = value(technical_result, "annual_naoh_consumption") * operating_fraction
    nacl_cost = nacl_kg / 1000.0 * nacl_price
    naoh_cost = naoh_kg / 1000.0 * naoh_price
    chemical_cost = nacl_cost + naoh_cost

    zeolite_price = escalate_cost(get("zeolite_price"), cost_inputs, "zeolite_price", context, CHEMICAL_COST_YEAR)
    replacement_fraction = get("media_replacement_fraction_per_cycle")
    if zeolite_price < 0.0 or not 0.0 <= replacement_fraction <= 1.0:
        raise ValueError("Zeolite price must be nonnegative and the replacement fraction between 0 and 1.")
    replaced_media_kg = (
        value(technical_result, "zeolite_mass_from_aec")
        * replacement_fraction
        * value(technical_result, "cycles_per_year")
        * operating_fraction
    )
    media_cost = replaced_media_kg * zeolite_price

    maintenance = maintenance_fraction * direct_capex
    opex_before_contingency = electricity + chemical_cost + media_cost + maintenance
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
        "nacl_operating_cost": _result(nacl_cost, "USD/year"),
        "naoh_operating_cost": _result(naoh_cost, "USD/year"),
        "chemical_operating_cost": _result(chemical_cost, "USD/year"),
        "zeolite_media_replacement_cost": _result(media_cost, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "fixed_operating_cost": _result(maintenance * (1.0 + contingency_factor), "USD/year"),
        "variable_operating_cost": _result((electricity + chemical_cost + media_cost) * (1.0 + contingency_factor), "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "annual_nacl_consumption": _result(nacl_kg, "kg/year"),
        "annual_naoh_consumption": _result(naoh_kg, "kg/year"),
        "spent_zeolite_solid_waste": _result(replaced_media_kg, "kg/year"),
        "spent_brine_generation": _result(value(technical_result, "spent_brine_generation") * operating_fraction, "m3/year"),
        "annual_ammonia_removed": _result(value(technical_result, "ammonia_removed") * operating_days, "kg N/year"),
    }

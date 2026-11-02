"""Walnut shell filtration cost model (NMSU assumptions).

Capital (NMSU WSF model, US DOE vendor data for the WSF alone at 20,000 bbl/day):
  C_ref     = c_bbl x V_ref / CRF_ref           annualized CAPEX back to an installed cost
              c_bbl = 0.008993 $/bbl, V_ref = 7,200,000 bbl/yr, CRF_ref = CRF(5%, 10 yr)
  C_bare    = C_ref x (Q / Q_ref)^n              Q_ref = 3,180 m3/day; 2020 dollars; n = 0.87
  C_direct  = TIC x C_bare                       TIC = 1 (the reference cost includes installation)
  CAPEX     = IF x C_direct                      system-level investment factor
Operating:
  electricity = energy_intensity x Q x days x electricity price
  cleaning    = media cleaning cost per m3 x Q x days
  maintenance = f_maint x C_direct               includes labor
  total       = (1 + f_contingency) x (electricity + cleaning + maintenance)
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


REFERENCE_FLOW_M3_DAY = 20000.0 * 0.158987294928  # 20,000 bbl/day
REFERENCE_ANNUAL_BBL = 7.2e6  # DOE vendor basis, bbl/yr
REFERENCE_INTEREST_RATE = 0.05  # DOE amortization
REFERENCE_AMORTIZATION_YEARS = 10.0
REFERENCE_COST_YEAR = 2020


def reference_crf():
    i, n = REFERENCE_INTEREST_RATE, REFERENCE_AMORTIZATION_YEARS
    return i * (1.0 + i) ** n / ((1.0 + i) ** n - 1.0)


def reference_installed_capex(capex_cost_per_bbl):
    """Installed WSF cost at the reference flow from the annualized DOE CAPEX ($/bbl)."""
    return capex_cost_per_bbl * REFERENCE_ANNUAL_BBL / reference_crf()

DEFAULTS = {
    "reference_capex_cost_per_bbl": 0.008993,  # $(2020)/bbl: WSF amortization 64,752 $/yr / 7,200,000 bbl/yr
    "capex_scaling_exponent": 0.87,
    "installation_factor": 1.0,
    "media_cleaning_cost_per_m3": 0.0546,  # $(2020)/m3: 62,500 $/yr at 7,200,000 bbl/yr
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
    exponent = get("capex_scaling_exponent")
    tic = get("installation_factor")
    maintenance_fraction = get("maintenance_fraction")
    contingency_factor = get("om_contingency_factor")
    if any(v < 0.0 for v in [exponent, tic, maintenance_fraction, contingency_factor]):
        raise ValueError("Walnut shell filtration cost inputs cannot be negative.")

    capex_per_bbl = get("reference_capex_cost_per_bbl")
    if capex_per_bbl < 0.0:
        raise ValueError("Reference CAPEX cost cannot be negative.")
    reference_capex = reference_installed_capex(capex_per_bbl)
    index_factor = cost_index_factor_to_base(context, cost_year(cost_inputs, "reference_capex_cost_per_bbl", REFERENCE_COST_YEAR))
    bare_capex = (
        reference_capex * (inlet_flow / REFERENCE_FLOW_M3_DAY) ** exponent * index_factor
        if inlet_flow > 0.0
        else 0.0
    )
    direct_capex = tic * bare_capex
    installed_capex = investment_factor(context) * direct_capex

    annual_volume = inlet_flow * operating_days
    electricity = annual_volume * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    cleaning_price = escalate_cost(
        get("media_cleaning_cost_per_m3"), cost_inputs, "media_cleaning_cost_per_m3", context, REFERENCE_COST_YEAR
    )
    if cleaning_price < 0.0:
        raise ValueError("Media cleaning cost cannot be negative.")
    cleaning = annual_volume * cleaning_price
    maintenance = maintenance_fraction * direct_capex
    opex_before_contingency = electricity + cleaning + maintenance
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "reference_installed_capital_cost": _result(reference_capex, "USD"),
        "installation_factor": _result(tic, "-"),
        "investment_factor": _result(investment_factor(context), "-"),
        "cost_index_factor": _result(index_factor, "factor"),
        "energy_operating_cost": _result(electricity, "USD/year"),
        "media_cleaning_cost": _result(cleaning, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "fixed_operating_cost": _result(maintenance * (1.0 + contingency_factor), "USD/year"),
        "variable_operating_cost": _result((electricity + cleaning) * (1.0 + contingency_factor), "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
    }

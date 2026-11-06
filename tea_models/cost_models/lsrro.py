"""LSRRO cost model (WaterTAP LSRRO unit costs; NMSU O&M structure).

Capital (WaterTAP 2018 $ escalated with CEPCI):
  c_eq      = membrane + pumps + ERD equipment cost per m3/day feed       WaterTAP design table, TIC removed
  C_bare    = c_eq x Q_ref x (Q / Q_ref)^n                                Q_ref = 50,000 bbl/day, n = 0.81
  C_direct  = TIC x C_bare                                                TIC = 2 (WaterTAP)
  CAPEX     = IF x C_direct                                               system-level investment factor
Operating:
  electricity = energy x Q x days x price
  membranes   = WaterTAP membrane replacement (0.15/yr of membrane cost) per m3/day feed x Q
  maintenance = f_maint x C_direct                                        includes labor
  antiscalant = dose x Q x price;  CIP = rate x product
  OPEX        = (1 + f_contingency) x (electricity + membranes + maintenance + antiscalant + CIP)
"""

from __future__ import annotations

from tea_models.cost_models.cost_utils import (
    cost_index_factor_to_base,
    escalate_cost,
    input_value,
    investment_factor,
    value,
)
from tea_models.lsrro_core import DESIGN_TABLE_YEAR, REFERENCE_FLOW_M3_DAY


DEFAULTS = {
    "reference_flow_m3_day": REFERENCE_FLOW_M3_DAY,
    "capex_scaling_exponent": 0.81,
    "installation_factor": 2.0,
    "maintenance_fraction": 0.02,
    "antiscalant_dose_mg_l": 3.0,
    "antiscalant_unit_price": 61.40,
    "antiscalant_density_kg_l": 1.10,
    "cip_cost_per_m3_product": 0.07,
    "om_contingency_factor": 0.20,
}


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def _input(values, name, default=None):
    default = DEFAULTS[name] if default is None else default
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = value(technical_result, "inlet_flow")
    outlet_flow = value(technical_result, "outlet_flow")
    if inlet_flow <= 0.0:
        raise ValueError("LSRRO inlet flow must be positive.")

    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_feed = inlet_flow * operating_days
    annual_product = outlet_flow * operating_days

    reference_flow = _input(cost_inputs, "reference_flow_m3_day")
    exponent = _input(cost_inputs, "capex_scaling_exponent")
    tic = _input(cost_inputs, "installation_factor")
    maintenance_fraction = _input(cost_inputs, "maintenance_fraction")
    om_contingency_factor = _input(cost_inputs, "om_contingency_factor")
    if reference_flow <= 0.0 or exponent < 0.0 or tic <= 0.0:
        raise ValueError("LSRRO reference flow and TIC must be positive and the scaling exponent nonnegative.")
    index = cost_index_factor_to_base(context, DESIGN_TABLE_YEAR)
    scale = reference_flow * (inlet_flow / reference_flow) ** exponent

    membrane_bare = value(technical_result, "membrane_equipment_cost_per_feed") * index * scale
    pump_bare = value(technical_result, "pump_equipment_cost_per_feed") * index * scale
    erd_bare = value(technical_result, "erd_equipment_cost_per_feed") * index * scale
    bare_capex = membrane_bare + pump_bare + erd_bare
    direct_capex = tic * bare_capex
    installed_capex = investment_factor(context) * direct_capex

    electricity = annual_feed * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    membrane_replacement = value(technical_result, "membrane_replacement_per_feed") * index * inlet_flow
    maintenance = maintenance_fraction * direct_capex
    antiscalant_price = escalate_cost(
        input_value(cost_inputs, "antiscalant_unit_price", DEFAULTS["antiscalant_unit_price"]),
        cost_inputs, "antiscalant_unit_price", context,
    )
    kg_per_gal = max(_input(cost_inputs, "antiscalant_density_kg_l") * 3.785411784, 1e-12)
    antiscalant = _input(cost_inputs, "antiscalant_dose_mg_l") * annual_feed / 1000.0 / kg_per_gal * antiscalant_price
    cip_rate = escalate_cost(
        input_value(cost_inputs, "cip_cost_per_m3_product", DEFAULTS["cip_cost_per_m3_product"]),
        cost_inputs, "cip_cost_per_m3_product", context,
    )
    cip = annual_product * cip_rate
    subtotal = electricity + membrane_replacement + maintenance + antiscalant + cip
    contingency = om_contingency_factor * subtotal

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "membrane_equipment_cost": _result(membrane_bare, "USD"),
        "pump_equipment_cost": _result(pump_bare, "USD"),
        "erd_equipment_cost": _result(erd_bare, "USD"),
        "installation_factor": _result(tic, "-"),
        "cost_index_factor": _result(index, "factor"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "electricity_operating_cost": _result(electricity, "USD/year"),
        "membrane_replacement_cost": _result(membrane_replacement, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "antiscalant_cost": _result(antiscalant, "USD/year"),
        "cip_cost": _result(cip, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "total_annual_operating_cost": _result(subtotal + contingency, "USD/year"),
    }

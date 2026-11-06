"""Ultrafiltration cost model (NMSU UF model; KBH TEA workbook basis).

Capital (KBH TEA Appendix, Capital_Summary, 2024 $):
  C_ref     = 970,000 gpd x 2 $/gpd + 2,000 ft2 x 300 $/ft2 = 2.54 M$     equipment + building
  C_bare    = C_ref x (Q / 970,000 gpd)^0.87
  C_direct  = TIC x C_bare                                 TIC = 1.43 (KBH site 10% and E&IC 30%)
  CAPEX     = IF x C_direct                                system-level investment factor
Operating:
  electricity = energy_intensity x Q x days x electricity price
  bisulfite   = NaHSO3 x days x price
  maintenance = f_maint x C_direct                          KBH "other maintenance" 2% of system direct;
                                                           includes labor and membrane replacement
  total       = (1 + f_contingency) x (electricity + bisulfite + maintenance)
"""

from tea_models.cost_models.cost_utils import (
    escalate_cost,
    input_value,
    investment_factor,
    value,
)


DEFAULTS = {
    "reference_uf_flow_gpd": 970000.0,
    "uf_equipment_unit_cost": 2.0,
    "uf_building_unit_cost": 300.0,
    "reference_building_area_ft2": 2000.0,
    "capex_scaling_exponent": 0.87,
    "installation_factor": 1.43,
    "sodium_bisulfite_price": 0.25,
    "maintenance_fraction": 0.02,
    "om_contingency_factor": 0.20,
}
GALLON_PER_M3 = 264.172052
LB_PER_KG = 2.2046226218


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
    target_flow_gpd = inlet_flow * GALLON_PER_M3
    reference_flow = _input(cost_inputs, "reference_uf_flow_gpd", DEFAULTS["reference_uf_flow_gpd"])
    equipment_unit_cost = escalate_cost(input_value(cost_inputs, "uf_equipment_unit_cost", DEFAULTS["uf_equipment_unit_cost"]), cost_inputs, "uf_equipment_unit_cost", context)
    building_unit_cost = escalate_cost(input_value(cost_inputs, "uf_building_unit_cost", DEFAULTS["uf_building_unit_cost"]), cost_inputs, "uf_building_unit_cost", context)
    building_area = _input(cost_inputs, "reference_building_area_ft2", DEFAULTS["reference_building_area_ft2"])
    exponent = _input(cost_inputs, "capex_scaling_exponent", DEFAULTS["capex_scaling_exponent"])
    if reference_flow <= 0.0 or exponent < 0.0:
        raise ValueError("UF reference flow must be positive and scaling exponent nonnegative.")
    tic = _input(cost_inputs, "installation_factor", DEFAULTS["installation_factor"])
    maintenance_fraction = _input(cost_inputs, "maintenance_fraction", DEFAULTS["maintenance_fraction"])
    om_contingency_factor = _input(cost_inputs, "om_contingency_factor", DEFAULTS["om_contingency_factor"])

    reference_bare_capex = reference_flow * equipment_unit_cost + building_area * building_unit_cost
    bare_capex = reference_bare_capex * (target_flow_gpd / reference_flow) ** exponent
    direct_capex = tic * bare_capex
    installed_capex = direct_capex * investment_factor(context)

    annual_feed = inlet_flow * operating_days
    energy = annual_feed * value(technical_result, "energy_intensity") * float(context.get("electricity_price", 0.0))
    bisulfite_price = escalate_cost(input_value(cost_inputs, "sodium_bisulfite_price", DEFAULTS["sodium_bisulfite_price"]), cost_inputs, "sodium_bisulfite_price", context)
    chemical = value(technical_result, "sodium_bisulfite_consumption") * operating_days * LB_PER_KG * bisulfite_price
    maintenance = maintenance_fraction * direct_capex
    subtotal = energy + chemical + maintenance
    contingency = om_contingency_factor * subtotal
    total_opex = subtotal + contingency

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "reference_direct_capital_cost": _result(reference_bare_capex, "USD"),
        "installation_factor": _result(tic, "-"),
        "capex_scaling_exponent": _result(exponent, "exponent"),
        "investment_factor": _result(investment_factor(context), "-"),
        "energy_operating_cost": _result(energy, "USD/year"),
        "sodium_bisulfite_operating_cost": _result(chemical, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
    }

"""Ion exchange cost model (selective IX and demineralization).

Capital (US EPA WBS cation and anion exchange models, standard designs 2-7, 2021 $):
  bare_b    = a_b x Q_b^n_b                      Q_b = flow through bed b (m3/day); excludes resin
  resin_b   = V_b x resin price_b                initial resin charge
  direct    = TIC x sum_b (bare_b + resin_b)     unit-level installation factor
  installed = IF x direct                        system-level investment factor
Operating:
  regenerant  = regenerant use x days/365 x price        NaCl (selective) or HCl + NaOH
  resin       = sum_b V_b x resin price_b x (1/life + annual loss)
  electricity = energy_intensity x Q x days x electricity price
  maintenance = f_maint x direct
  total       = (1 + f_contingency) x (regenerant + resin + electricity + maintenance)
Spent regenerant is reported for the system-level waste stream; its disposal cost is not
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


EQUIPMENT_COST_YEAR = 2021

SELECTIVE_DEFAULTS = {
    "cation_capex_coefficient": 698.35,
    "cation_capex_exponent": 0.7478,
    "anion_capex_coefficient": 673.45,
    "anion_capex_exponent": 0.7282,
    "installation_factor": 1.15,
    "cation_resin_price": 8175.0,
    "anion_resin_price": 8198.0,
    "resin_life": 7.0,
    "annual_resin_loss": 0.045,
    "salt_price": 230.3,
    "maintenance_fraction": 0.02,
    "om_contingency_factor": 0.20,
}

DEMIN_DEFAULTS = {
    key: val for key, val in SELECTIVE_DEFAULTS.items() if key != "salt_price"
}
DEMIN_DEFAULTS.update({"hcl_price": 1085.9, "caustic_price": 940.3})
DEFAULTS = SELECTIVE_DEFAULTS


def _result(value_, unit):
    return {"value": value_, "unit": unit}


def run_cost(unit_process, technical_result, cost_inputs, context, defaults):
    def get(name):
        return input_value(cost_inputs, name, defaults[name])

    demineralization = "hcl_price" in defaults
    inlet_flow = value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    operating_fraction = operating_days / 365.0
    tic = get("installation_factor")
    maintenance_fraction = get("maintenance_fraction")
    contingency_factor = get("om_contingency_factor")
    resin_life = get("resin_life")
    resin_loss = get("annual_resin_loss")
    if any(v < 0.0 for v in [tic, maintenance_fraction, contingency_factor, resin_loss]) or resin_life <= 0.0:
        raise ValueError("Ion exchange cost inputs cannot be negative and the resin life must be positive.")

    bare = {}
    resin = {}
    resin_annual = {}
    for bed in ("cation", "anion"):
        coefficient = get(f"{bed}_capex_coefficient")
        exponent = get(f"{bed}_capex_exponent")
        if coefficient < 0.0 or exponent < 0.0:
            raise ValueError("Ion exchange cost-curve inputs cannot be negative.")
        index = cost_index_factor_to_base(context, cost_year(cost_inputs, f"{bed}_capex_coefficient", EQUIPMENT_COST_YEAR))
        flow = value(technical_result, f"{bed}_treated_flow")
        bare[bed] = coefficient * flow ** exponent * index if flow > 0.0 else 0.0
        price = escalate_cost(get(f"{bed}_resin_price"), cost_inputs, f"{bed}_resin_price", context, EQUIPMENT_COST_YEAR)
        volume = value(technical_result, f"{bed}_resin_volume")
        resin[bed] = volume * price
        resin_annual[bed] = volume * price * (1.0 / resin_life + resin_loss) * operating_fraction

    bare_capex = bare["cation"] + bare["anion"]
    resin_capex = resin["cation"] + resin["anion"]
    direct_capex = tic * (bare_capex + resin_capex)
    installed_capex = investment_factor(context) * direct_capex

    if demineralization:
        hcl_price = escalate_cost(get("hcl_price"), cost_inputs, "hcl_price", context, EQUIPMENT_COST_YEAR)
        caustic_price = escalate_cost(get("caustic_price"), cost_inputs, "caustic_price", context, EQUIPMENT_COST_YEAR)
        hcl_kg = value(technical_result, "annual_hcl_consumption") * operating_fraction
        naoh_kg = value(technical_result, "annual_naoh_consumption") * operating_fraction
        chemicals = {"hcl": hcl_kg / 1000.0 * hcl_price, "naoh": naoh_kg / 1000.0 * caustic_price}
    else:
        salt_price = escalate_cost(get("salt_price"), cost_inputs, "salt_price", context, EQUIPMENT_COST_YEAR)
        nacl_kg = value(technical_result, "annual_nacl_consumption") * operating_fraction
        chemicals = {"nacl": nacl_kg / 1000.0 * salt_price}
    chemical_cost = sum(chemicals.values())
    resin_cost = resin_annual["cation"] + resin_annual["anion"]
    electricity = (
        inlet_flow
        * operating_days
        * value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    maintenance = maintenance_fraction * direct_capex
    opex_before_contingency = chemical_cost + resin_cost + electricity + maintenance
    contingency = opex_before_contingency * contingency_factor
    total_opex = opex_before_contingency + contingency

    outputs = {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(direct_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_capex, "USD"),
        "cation_bed_capital_cost": _result(bare["cation"], "USD"),
        "anion_bed_capital_cost": _result(bare["anion"], "USD"),
        "initial_resin_cost": _result(resin_capex, "USD"),
        "installation_factor": _result(tic, "-"),
        "investment_factor": _result(investment_factor(context), "-"),
        "chemical_operating_cost": _result(chemical_cost, "USD/year"),
        "resin_replacement_cost": _result(resin_cost, "USD/year"),
        "energy_operating_cost": _result(electricity, "USD/year"),
        "maintenance_operating_cost": _result(maintenance, "USD/year"),
        "om_contingency": _result(contingency, "USD/year"),
        "fixed_operating_cost": _result(maintenance * (1.0 + contingency_factor), "USD/year"),
        "variable_operating_cost": _result((chemical_cost + resin_cost + electricity) * (1.0 + contingency_factor), "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "spent_regenerant_generation": _result(value(technical_result, "spent_regenerant_flow") * operating_days, "m3/year"),
    }
    if demineralization:
        outputs.update({
            "hcl_operating_cost": _result(chemicals["hcl"], "USD/year"),
            "naoh_operating_cost": _result(chemicals["naoh"], "USD/year"),
            "annual_hcl_consumption": _result(hcl_kg, "kg/year"),
            "annual_naoh_consumption": _result(naoh_kg, "kg/year"),
        })
    else:
        outputs.update({
            "nacl_operating_cost": _result(chemicals["nacl"], "USD/year"),
            "annual_nacl_consumption": _result(nacl_kg, "kg/year"),
        })
    return outputs


def run(unit_process, technical_result, cost_inputs, context):
    return run_cost(unit_process, technical_result, cost_inputs, context, SELECTIVE_DEFAULTS)

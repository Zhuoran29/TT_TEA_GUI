"""GAC capital/fixed cost plus TOC-dependent operating-cost breakdown."""

from __future__ import annotations


DEFAULTS = {
    "capex_per_flow": 481.6,
    "column_capex_multiplier": 1.0,
    "fixed_opex_fraction": 0.04,
    "cost_method": 0.0,
    "gac_media_cost": 0.321 * 8000.0 / 450.0,
    "solid_disposal_cost": 0.11,
    "reference_media_cost_coefficient": 0.321,
    "reference_toc_removal": 0.67,
}


def _result(value, unit):
    return {"value": value, "unit": unit}


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        return float(entry.get("value", default) if isinstance(entry, dict) else entry)
    except (TypeError, ValueError):
        return float(default)


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_result, cost_inputs, context):
    inlet_flow = _value(technical_result, "inlet_flow")
    operating_days = float(context.get("operating_days_per_year", 330.0))
    annual_volume = inlet_flow * operating_days
    investment_factor = max(float(context.get("investment_factor", 2.5)), 0.0)

    bare_equipment_capex = _input(
        cost_inputs, "capex_per_flow", DEFAULTS["capex_per_flow"]
    ) * inlet_flow
    column_capex_multiplier = _input(
        cost_inputs,
        "column_capex_multiplier",
        DEFAULTS["column_capex_multiplier"],
    )
    if column_capex_multiplier < 0.0:
        raise ValueError("GAC column CAPEX multiplier cannot be negative.")
    equipment_capex = bare_equipment_capex * column_capex_multiplier
    installed_capex = equipment_capex * investment_factor
    fixed_opex = installed_capex * _input(
        cost_inputs, "fixed_opex_fraction", DEFAULTS["fixed_opex_fraction"]
    )

    media_cost = _input(cost_inputs, "gac_media_cost", DEFAULTS["gac_media_cost"])
    disposal_cost = _input(
        cost_inputs, "solid_disposal_cost", DEFAULTS["solid_disposal_cost"]
    )
    density = _value(technical_result, "media_bulk_density", 450.0)
    breakthrough_bv = _value(technical_result, "breakthrough_bed_volumes")
    toc_removal = _value(technical_result, "toc_removal")
    cost_method = int(round(_input(cost_inputs, "cost_method", 0.0)))
    if cost_method not in (0, 1):
        raise ValueError("GAC cost_method must be 0 (feed TOC) or 1 (TOC removal).")
    if min(media_cost, disposal_cost, density) < 0.0:
        raise ValueError("GAC media cost, disposal cost, and density cannot be negative.")

    if cost_method == 1:
        reference_coefficient = _input(
            cost_inputs,
            "reference_media_cost_coefficient",
            DEFAULTS["reference_media_cost_coefficient"],
        )
        reference_removal = _input(
            cost_inputs, "reference_toc_removal", DEFAULTS["reference_toc_removal"]
        )
        media_rate = reference_coefficient * toc_removal / max(reference_removal, 1e-12)
        disposal_rate = (
            reference_coefficient
            * disposal_cost
            / max(media_cost, 1e-12)
            * toc_removal
            / max(reference_removal, 1e-12)
        )
        method_name = "TOC-removal correlation"
    else:
        media_rate = density * media_cost / max(breakthrough_bv, 1e-12)
        disposal_rate = density * disposal_cost / max(breakthrough_bv, 1e-12)
        if breakthrough_bv <= 0.0:
            media_rate = 0.0
            disposal_rate = 0.0
        method_name = "feed-TOC breakthrough correlation"

    media_opex = annual_volume * media_rate
    disposal_opex = annual_volume * disposal_rate
    energy_opex = (
        annual_volume
        * _value(technical_result, "energy_intensity")
        * float(context.get("electricity_price", 0.0))
    )
    variable_opex = media_opex + disposal_opex + energy_opex
    total_opex = fixed_opex + variable_opex

    return {
        "installed_capital_cost": _result(installed_capex, "USD"),
        "equipment_capital_cost": _result(equipment_capex, "USD"),
        "bare_equipment_capital_cost": _result(bare_equipment_capex, "USD"),
        "column_capex_multiplier": _result(column_capex_multiplier, "-"),
        "investment_factor": _result(investment_factor, "-"),
        "opex_calculation_method": _result(method_name, ""),
        "fixed_operating_cost": _result(fixed_opex, "USD/year"),
        "gac_media_operating_cost": _result(media_opex, "USD/year"),
        "solid_disposal_operating_cost": _result(disposal_opex, "USD/year"),
        "energy_operating_cost": _result(energy_opex, "USD/year"),
        "variable_operating_cost": _result(variable_opex, "USD/year"),
        "total_annual_operating_cost": _result(total_opex, "USD/year"),
        "gac_media_cost_rate": _result(media_rate, "USD/m3 feed"),
        "solid_disposal_cost_rate": _result(disposal_rate, "USD/m3 feed"),
    }

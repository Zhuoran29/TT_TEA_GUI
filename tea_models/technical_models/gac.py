"""Granular activated carbon model with TOC-based BV saturation."""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "gac",
    "recovery": 0.995,
    "energy_intensity": 0.0,
    "chemical_dose": 0.0,
    "empty_bed_contact_time": 10.0,
    "media_bulk_density": 450.0,
    "adsorber_bed_volume_m3": 78.783,
    "fresh_gac_mass_kg": 31513.0,
}

TOC_REMOVAL_FRACTION = 1.0 - (0.28773 / 1.15)
BV_POWER_A = 1.5e5
BV_POWER_B = -1.85
MAX_BV_TO_SATURATION = 150000.0
MIN_BV_TO_SATURATION = 1.0


def _result(value, unit):
    return {"value": value, "unit": unit}


def _quality_value(quality, parameter, default=0.0):
    try:
        return float((quality.get(parameter, {}) or {}).get("value", default) or default)
    except (TypeError, ValueError):
        return float(default)


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_inputs, stream):
    model_removals = {
        "TOC": TOC_REMOVAL_FRACTION,
        "Oil": TOC_REMOVAL_FRACTION,
        "BTEX": TOC_REMOVAL_FRACTION,
        "PAHs": TOC_REMOVAL_FRACTION,
    }
    removals = {**model_removals, **(technical_inputs.get("removal_efficiencies") or {})}
    template_inputs = {**technical_inputs, "removal_efficiencies": removals}
    outputs = run_template(unit_process, template_inputs, stream, DEFAULTS)
    outputs["energy_intensity"]["unit"] = "kWh/m3 feed"
    inlet_toc = _quality_value(outputs["water_quality_in"], "TOC")
    outlet_toc = _quality_value(outputs["water_quality_out"], "TOC", inlet_toc)
    toc_removal = (
        max(min(1.0 - outlet_toc / inlet_toc, 1.0), 0.0)
        if inlet_toc > 0.0
        else 0.0
    )
    breakthrough_bv = (
        BV_POWER_A * inlet_toc**BV_POWER_B if inlet_toc > 0.0 else 0.0
    )
    if inlet_toc > 0.0:
        breakthrough_bv = min(max(breakthrough_bv, MIN_BV_TO_SATURATION), MAX_BV_TO_SATURATION)
    media_inventory = float(outputs["media_inventory"]["value"] or 0.0)
    inlet_flow = float(outputs["inlet_flow"]["value"] or 0.0)
    bed_volume = _input(technical_inputs, "adsorber_bed_volume_m3", DEFAULTS["adsorber_bed_volume_m3"])
    fresh_gac_mass = _input(technical_inputs, "fresh_gac_mass_kg", DEFAULTS["fresh_gac_mass_kg"])
    changeout_days = (
        breakthrough_bv * bed_volume
        / inlet_flow
        if breakthrough_bv > 0.0 and inlet_flow > 0.0
        else 0.0
    )
    changeouts_per_year = 365.0 / changeout_days if changeout_days > 0.0 else 0.0
    annual_gac_usage = fresh_gac_mass * changeouts_per_year
    outputs.update({
        "feed_toc": _result(inlet_toc, "mg/L"),
        "outlet_toc": _result(outlet_toc, "mg/L"),
        "toc_removal": _result(toc_removal, "fraction"),
        "model_toc_removal": _result(TOC_REMOVAL_FRACTION, "fraction"),
        "breakthrough_bed_volumes": _result(breakthrough_bv, "bed volumes"),
        "adsorber_bed_volume": _result(bed_volume, "m3"),
        "fresh_gac_mass": _result(fresh_gac_mass, "kg"),
        "estimated_changeout_interval": _result(changeout_days, "day"),
        "changeouts_per_year": _result(changeouts_per_year, "1/year"),
        "annual_gac_usage": _result(annual_gac_usage, "kg/year"),
        "model_warnings": _result(
            ["Feed TOC is unavailable; TOC-dependent media and disposal OPEX will be zero."]
            if inlet_toc <= 0.0
            else (
                []
                if 0.4 <= inlet_toc <= 250.0
                else ["Feed TOC is outside the source correlation range used to fit the BV power law."]
            ),
            "",
        ),
    })
    return outputs

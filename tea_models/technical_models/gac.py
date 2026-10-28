"""Granular activated carbon (GAC) technical model.

Bed life uses the NMSU empirical bed-volume (BV) power law in feed TOC.
Bed sizing follows WaterTAP (V = Q * EBCT); the bed is split into parallel
pressure vessels when it exceeds a maximum bed volume per vessel. Pump energy
is hydraulic (P = rho * g * H * Q / eta), as in the US EPA WBS GAC model.
"""

from __future__ import annotations

import math

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "gac",
    "recovery": 0.995,
    "energy_intensity": 0.0,
    "chemical_dose": 0.0,
    # Design
    "empty_bed_contact_time": 10.0,  # min (600 s)
    "max_bed_volume_per_vessel": 40.0,  # m3; EPA WBS vertical vessel, 14 ft x 14 ft, 50% expansion
    "redundant_vessels": 1.0,
    # Media
    "media_bulk_density": 400.0,  # kg/m3
    # NMSU empirical bed-life model: BV = A * TOC^b
    "bv_coefficient_a": 1.5e5,
    "bv_exponent_b": -1.85,
    # Pumping through pressure contactors (head loss of bed, underdrain and piping)
    "pump_head": 10.0,  # m
    "pump_efficiency": 0.70,
}

TOC_REMOVAL_FRACTION = 1.0 - (0.28773 / 1.15)
MAX_BV_TO_SATURATION = 150000.0
MIN_BV_TO_SATURATION = 1.0
TOC_FIT_RANGE_MG_L = (0.4, 250.0)


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


def breakthrough_bed_volumes(inlet_toc, coefficient_a, exponent_b):
    """NMSU empirical BV to changeout as a function of feed TOC (mg/L)."""
    if inlet_toc <= 0.0:
        return 0.0
    bv = coefficient_a * inlet_toc**exponent_b
    return min(max(bv, MIN_BV_TO_SATURATION), MAX_BV_TO_SATURATION)


def size_contactors(inlet_flow_m3_day, ebct_min, max_bed_volume, redundant_vessels):
    """Return bed volume, operating/redundant vessel counts and per-vessel volume."""
    bed_volume = max(inlet_flow_m3_day, 0.0) / 1440.0 * max(ebct_min, 0.0)
    if bed_volume <= 0.0:
        return bed_volume, 0, 0, 0.0
    if max_bed_volume > 0.0:
        operating = max(int(math.ceil(bed_volume / max_bed_volume - 1e-9)), 1)
    else:
        operating = 1
    redundant = max(int(round(redundant_vessels)), 0)
    return bed_volume, operating, redundant, bed_volume / operating


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

    def get(name):
        return _input(technical_inputs, name, DEFAULTS[name])

    inlet_flow = float(outputs["inlet_flow"]["value"] or 0.0)
    inlet_toc = _quality_value(outputs["water_quality_in"], "TOC")
    outlet_toc = _quality_value(outputs["water_quality_out"], "TOC", inlet_toc)
    toc_removal = (
        max(min(1.0 - outlet_toc / inlet_toc, 1.0), 0.0) if inlet_toc > 0.0 else 0.0
    )

    # Bed sizing (WaterTAP: V = Q * EBCT) and parallel vessels
    ebct = get("empty_bed_contact_time")
    density = get("media_bulk_density")
    bed_volume, n_operating, n_redundant, vessel_volume = size_contactors(
        inlet_flow, ebct, get("max_bed_volume_per_vessel"), get("redundant_vessels")
    )
    n_total = n_operating + n_redundant
    total_contactor_volume = n_total * vessel_volume
    fresh_gac_mass = density * bed_volume  # carbon in operating beds (WaterTAP bed_mass_gac)

    # Bed life (NMSU empirical model)
    breakthrough_bv = breakthrough_bed_volumes(
        inlet_toc, get("bv_coefficient_a"), get("bv_exponent_b")
    )
    changeout_days = breakthrough_bv * ebct / 1440.0 if breakthrough_bv > 0.0 else 0.0
    changeouts_per_year = 365.0 / changeout_days if changeout_days > 0.0 else 0.0
    annual_gac_usage = fresh_gac_mass * changeouts_per_year  # calendar-year basis
    carbon_usage_rate = (
        fresh_gac_mass / (breakthrough_bv * bed_volume)
        if breakthrough_bv > 0.0 and bed_volume > 0.0
        else 0.0
    )
    adsorbed_toc = max(inlet_toc - outlet_toc, 0.0) * inlet_flow / 1000.0 * 365.0

    # Pump energy: P = rho * g * H * Q / eta
    pump_head = max(get("pump_head"), 0.0)
    pump_efficiency = max(get("pump_efficiency"), 1e-9)
    energy_intensity = 1000.0 * 9.80665 * pump_head / pump_efficiency / 3.6e6  # kWh/m3
    pump_power_kw = energy_intensity * inlet_flow / 24.0

    warnings = []
    if inlet_toc <= 0.0:
        warnings.append("Feed TOC is unavailable; bed life and media OPEX are zero.")
    elif not TOC_FIT_RANGE_MG_L[0] <= inlet_toc <= TOC_FIT_RANGE_MG_L[1]:
        warnings.append("Feed TOC is outside the range used to fit the BV power law.")

    outputs.update({
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "pump_power": _result(pump_power_kw, "kW"),
        "pump_head": _result(pump_head, "m"),
        "pump_efficiency": _result(pump_efficiency, "fraction"),
        "feed_toc": _result(inlet_toc, "mg/L"),
        "outlet_toc": _result(outlet_toc, "mg/L"),
        "toc_removal": _result(toc_removal, "fraction"),
        "model_toc_removal": _result(TOC_REMOVAL_FRACTION, "fraction"),
        "empty_bed_contact_time": _result(ebct, "min"),
        "media_bulk_density": _result(density, "kg/m3"),
        "media_bed_volume": _result(bed_volume, "m3"),
        "media_inventory": _result(fresh_gac_mass, "kg"),
        "operating_vessels": _result(n_operating, "count"),
        "redundant_vessels": _result(n_redundant, "count"),
        "bed_volume_per_vessel": _result(vessel_volume, "m3"),
        "total_contactor_volume": _result(total_contactor_volume, "m3"),
        "adsorber_bed_volume": _result(bed_volume, "m3"),
        "fresh_gac_mass": _result(fresh_gac_mass, "kg"),
        "breakthrough_bed_volumes": _result(breakthrough_bv, "bed volumes"),
        "estimated_changeout_interval": _result(changeout_days, "day"),
        "changeouts_per_year": _result(changeouts_per_year, "1/year"),
        "carbon_usage_rate": _result(carbon_usage_rate, "kg/m3 treated"),
        "annual_gac_usage": _result(annual_gac_usage, "kg/year"),
        "spent_gac_generation": _result(annual_gac_usage, "kg/year"),
        "adsorbed_toc_load": _result(adsorbed_toc, "kg/year"),
        "model_warnings": _result(warnings, ""),
    })
    return outputs

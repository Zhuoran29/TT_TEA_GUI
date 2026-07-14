"""Zeolite ammonia-removal, breakthrough, and regeneration-cycle model."""

from __future__ import annotations

from math import exp

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "zeolite",
    "recovery": 0.995,
    "energy_intensity": 0.04,
    "chemical_dose": 0.0,
    "empty_bed_contact_time": 20.0,
    "media_bulk_density": 824.0,
    "reference_feed_ammonia": 25.0,
    "reference_ammonia_removal": 0.90,
    "reference_breakthrough_bv": 645.0,
    "capacity_removal_coefficient": 0.55,
    "capacity_feed_coefficient": 0.0035,
    "capacity_factor_min": 0.45,
    "capacity_factor_max": 2.15,
}


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _quality_value(quality, parameter, default=0.0):
    try:
        return float((quality.get(parameter, {}) or {}).get("value", default) or default)
    except (TypeError, ValueError):
        return float(default)


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        return float(entry.get("value", default) if isinstance(entry, dict) else entry)
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_inputs, stream):
    outputs = run_template(unit_process, technical_inputs, stream, DEFAULTS)
    inlet_ammonia = _quality_value(outputs["water_quality_in"], "Ammonia nitrogen")
    outlet_ammonia = _quality_value(
        outputs["water_quality_out"], "Ammonia nitrogen", inlet_ammonia
    )
    removal = (
        max(min(1.0 - outlet_ammonia / inlet_ammonia, 1.0), 0.0)
        if inlet_ammonia > 0.0
        else 0.0
    )

    density = _value(outputs, "media_bulk_density", DEFAULTS["media_bulk_density"])
    ref_feed = _input(
        technical_inputs, "reference_feed_ammonia", DEFAULTS["reference_feed_ammonia"]
    )
    ref_removal = _input(
        technical_inputs,
        "reference_ammonia_removal",
        DEFAULTS["reference_ammonia_removal"],
    )
    ref_bv = _input(
        technical_inputs, "reference_breakthrough_bv", DEFAULTS["reference_breakthrough_bv"]
    )
    reference_capacity = ref_bv * ref_feed * ref_removal / max(density, 1e-12)
    removal_coefficient = _input(
        technical_inputs,
        "capacity_removal_coefficient",
        DEFAULTS["capacity_removal_coefficient"],
    )
    feed_coefficient = _input(
        technical_inputs,
        "capacity_feed_coefficient",
        DEFAULTS["capacity_feed_coefficient"],
    )
    factor_min = _input(
        technical_inputs, "capacity_factor_min", DEFAULTS["capacity_factor_min"]
    )
    factor_max = _input(
        technical_inputs, "capacity_factor_max", DEFAULTS["capacity_factor_max"]
    )
    removal_factor = 1.0 - removal_coefficient * max(0.0, removal - ref_removal)
    feed_factor = exp(-feed_coefficient * max(0.0, inlet_ammonia - ref_feed))
    capacity_factor = max(min(removal_factor * feed_factor, factor_max), factor_min)
    working_capacity = reference_capacity * capacity_factor
    breakthrough_bv = (
        density * working_capacity / (inlet_ammonia * removal)
        if inlet_ammonia > 0.0 and removal > 0.0
        else 0.0
    )
    inlet_flow = _value(outputs, "inlet_flow")
    bed_volume = _value(outputs, "media_bed_volume")
    cycle_days = (
        breakthrough_bv * bed_volume / inlet_flow
        if breakthrough_bv > 0.0 and inlet_flow > 0.0
        else 0.0
    )
    removed_ammonia = inlet_flow * inlet_ammonia * removal / 1000.0

    outputs.update({
        "feed_ammonia": _result(inlet_ammonia, "mg/L"),
        "outlet_ammonia": _result(outlet_ammonia, "mg/L"),
        "ammonia_removal": _result(removal, "fraction"),
        "working_capacity": _result(working_capacity, "g N/kg zeolite"),
        "breakthrough_bed_volumes": _result(breakthrough_bv, "bed volumes"),
        "cycle_duration": _result(cycle_days, "day"),
        "ammonia_removed": _result(removed_ammonia, "kg N/day"),
        "model_warnings": _result(
            ["Feed ammonia is unavailable; regeneration costs and NH4Cl credit will be zero."]
            if inlet_ammonia <= 0.0
            else (
                ["Ammonia removal is zero; regeneration costs and NH4Cl credit will be zero."]
                if removal <= 0.0
                else []
            ),
            "",
        ),
    })
    return outputs

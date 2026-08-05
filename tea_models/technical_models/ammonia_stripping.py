"""Ammonia stripping model adapted from the NMPWRC TEA workbook."""

from __future__ import annotations

import math

from tea_models.water_quality import apply_unit_water_quality


DEFAULTS = {
    "unit_kind": "ammonia_stripping",
    "recovery": 0.995,
    "energy_intensity": 0.12,
    "feed_temperature": 68.0,
    "target_ammonia_mg_l": 1.0,
    "henry_cp_25c": 0.59,
    "henry_conversion_factor": 2479.0,
    "stripping_design_factor": 20.0,
    "kla_s": 6.3611111111111114e-5,
    "tower_diameter_in": 10.0,
}

SQIN_TO_M2 = 0.00064516
GPM_PER_M3_DAY = 0.183452812


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


def _tower_height_m(liquid_flow_m3_s, tower_area_m2, kla_s, stripping_factor, c0, ce):
    if liquid_flow_m3_s <= 0.0 or tower_area_m2 <= 0.0 or kla_s <= 0.0:
        return 0.0
    if c0 <= 0.0 or ce <= 0.0 or c0 <= ce:
        return 0.0
    if stripping_factor <= 1.0:
        return 0.0

    log_term = math.log(1.0 + (c0 / ce) * (stripping_factor - 1.0) / stripping_factor)
    return (
        liquid_flow_m3_s
        / tower_area_m2
        / kla_s
        * (stripping_factor / (stripping_factor - 1.0))
        * log_term
    )


def run(unit_process, technical_inputs, stream):
    recovery = max(0.0, min(_input(technical_inputs, "recovery", DEFAULTS["recovery"]), 1.0))
    inlet_quality = stream.get("water_quality", {}) or {}
    inlet_ammonia = _quality_value(inlet_quality, "Ammonia nitrogen")
    target_ammonia = max(_input(technical_inputs, "target_ammonia_mg_l", DEFAULTS["target_ammonia_mg_l"]), 0.0)
    outlet_ammonia = min(inlet_ammonia, target_ammonia) if inlet_ammonia > 0.0 else 0.0
    removal = max((inlet_ammonia - outlet_ammonia) / inlet_ammonia, 0.0) if inlet_ammonia > 0.0 else 0.0

    (
        inlet_flow,
        outlet_flow,
        brine_flow,
        water_quality_in,
        water_quality_out,
        outlet_stream,
    ) = apply_unit_water_quality(
        stream,
        recovery,
        {"Ammonia nitrogen": removal},
        {"Ammonia nitrogen": outlet_ammonia},
    )

    henry_cp = max(_input(technical_inputs, "henry_cp_25c", DEFAULTS["henry_cp_25c"]), 1e-12)
    henry_factor = max(_input(technical_inputs, "henry_conversion_factor", DEFAULTS["henry_conversion_factor"]), 1e-12)
    henry_yc = 1.0 / (henry_cp * henry_factor)
    design_factor = max(_input(technical_inputs, "stripping_design_factor", DEFAULTS["stripping_design_factor"]), 0.0)
    if inlet_ammonia > 0.0 and outlet_ammonia < inlet_ammonia:
        air_water_ratio = (inlet_ammonia - max(outlet_ammonia, 1e-12)) / (henry_yc * inlet_ammonia) * design_factor
    else:
        air_water_ratio = 0.0
    stripping_factor = air_water_ratio * henry_yc

    tower_diameter_in = max(_input(technical_inputs, "tower_diameter_in", DEFAULTS["tower_diameter_in"]), 0.0)
    tower_area_m2 = math.pi * (tower_diameter_in / 2.0) ** 2 * SQIN_TO_M2
    kla_s = max(_input(technical_inputs, "kla_s", DEFAULTS["kla_s"]), 0.0)
    liquid_flow_m3_s = inlet_flow / 86400.0
    tower_height_m = _tower_height_m(
        liquid_flow_m3_s,
        tower_area_m2,
        kla_s,
        stripping_factor,
        inlet_ammonia,
        max(outlet_ammonia, 1e-12),
    )
    energy_intensity = max(_input(technical_inputs, "energy_intensity", DEFAULTS["energy_intensity"]), 0.0)
    warnings = []
    if inlet_ammonia <= 0.0:
        warnings.append("Feed ammonia is unavailable or zero; ammonia stripping removal is zero.")
    if stripping_factor and stripping_factor <= 1.0:
        warnings.append("Stripping factor is <= 1; tower height is not calculated.")

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "feed_temperature": _result(_input(technical_inputs, "feed_temperature", DEFAULTS["feed_temperature"]), "deg C"),
        "feed_ammonia": _result(inlet_ammonia, "mg/L"),
        "target_ammonia": _result(target_ammonia, "mg/L"),
        "outlet_ammonia": _result(outlet_ammonia, "mg/L"),
        "ammonia_removal": _result(removal, "fraction"),
        "henry_cp_25c": _result(henry_cp, "mol/m3/Pa"),
        "henry_yc": _result(henry_yc, "(mg/L gas)/(mg/L aq)"),
        "kla": _result(kla_s, "1/s"),
        "stripping_design_factor": _result(design_factor, "-"),
        "air_water_ratio": _result(air_water_ratio, "m3 air/m3 water"),
        "stripping_factor": _result(stripping_factor, "-"),
        "liquid_flow": _result(inlet_flow * GPM_PER_M3_DAY, "gpm"),
        "air_flow": _result(inlet_flow * air_water_ratio / 24.0, "m3/h"),
        "tower_diameter": _result(tower_diameter_in, "in"),
        "tower_area": _result(tower_area_m2, "m2"),
        "tower_height": _result(tower_height_m, "m"),
        "tower_height_ft": _result(tower_height_m * 3.280839895, "ft"),
        "removal_efficiencies": {"Ammonia nitrogen": removal},
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "outlet_stream": outlet_stream,
        "model_warnings": _result(warnings, ""),
    }

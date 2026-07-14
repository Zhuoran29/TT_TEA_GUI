"""Vacuum membrane distillation model adapted from the VMD workbook sheet.

The ``MD Design Model (Surrogate)`` worksheet contains a verified calibration
point for SEEC, membrane/HX area, and heater/chiller duty.  Those cells are
constants rather than input-dependent formulas, so this adapter scales them
transparently by feed or product capacity instead of using unrelated formulas
that remain in the optional-output section of the workbook.
"""

from __future__ import annotations

from tea_models.technical_models.helper_function import sw_dens_mass
from tea_models.water_quality import apply_unit_water_quality, get_default_removal_efficiencies


SECONDS_PER_DAY = 86_400.0


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _stream_tds_mg_l(stream):
    entry = (stream.get("water_quality", {}) or {}).get("TDS", {}) or {}
    try:
        value = float(entry.get("value", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
    unit = str(entry.get("unit", "mg/L") or "mg/L").lower().replace(" ", "")
    if unit in {"g/l", "kg/m3"}:
        return value * 1000.0
    return value


def _tds_mass_fraction(stream, temperature_c, fallback):
    concentration = _stream_tds_mg_l(stream)
    if concentration <= 0.0:
        return fallback
    fraction = min(max(concentration / 1_000_000.0, 0.0), 0.5)
    for _ in range(10):
        density = sw_dens_mass(temperature_c, fraction)
        fraction = concentration / max(density * 1000.0, 1e-12)
    return fraction


def run(unit_process, technical_inputs, stream):
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    if inlet_flow <= 0.0:
        raise ValueError("VMD inlet flow must be positive.")

    recovery = min(max(_input(technical_inputs, "recovery", 0.50), 0.0), 0.999999)
    temperature = _input(technical_inputs, "feed_temperature", 25.0)
    tds_fraction = _tds_mass_fraction(
        stream,
        temperature,
        _input(technical_inputs, "feed_tds_mass_fraction", 0.035),
    )
    recycle_ratio = _input(technical_inputs, "recycle_ratio", 6.169)
    seec = _input(technical_inputs, "specific_electric_energy", 91.43)
    reference_feed = _input(
        technical_inputs, "reference_feed_flow", 0.0223 * 3785.41
    )
    reference_recovery = _input(technical_inputs, "reference_recovery", 0.50)
    reference_membrane_area = _input(
        technical_inputs, "reference_membrane_area", 103.1817
    )
    reference_hx_area = _input(
        technical_inputs, "reference_heat_exchanger_area", 291.08
    )
    reference_heater_power = _input(
        technical_inputs, "reference_heater_power", 268.454
    )
    reference_chiller_power = _input(
        technical_inputs, "reference_chiller_power", 274.402
    )
    if reference_feed <= 0.0 or reference_recovery <= 0.0:
        raise ValueError("VMD reference feed flow and recovery must be positive.")
    if min(recycle_ratio, seec, reference_membrane_area, reference_hx_area) < 0.0:
        raise ValueError("VMD design and energy inputs cannot be negative.")

    inlet_quality = stream.get("water_quality", {})
    removals = technical_inputs.get("removal_efficiencies")
    if removals is None:
        removals = get_default_removal_efficiencies(unit_process, inlet_quality)
    (
        inlet_flow,
        outlet_flow,
        brine_flow,
        water_quality_in,
        water_quality_out,
        outlet_stream,
    ) = apply_unit_water_quality(stream, recovery, removals)

    feed_scale = inlet_flow / reference_feed
    product_scale = outlet_flow / max(reference_feed * reference_recovery, 1e-12)
    membrane_area = reference_membrane_area * product_scale
    heat_exchanger_area = reference_hx_area * feed_scale
    heater_power = reference_heater_power * feed_scale
    chiller_power = reference_chiller_power * feed_scale
    total_power = seec * inlet_flow / 24.0
    feed_density = sw_dens_mass(temperature, tds_fraction)
    feed_h2o_mass_flow = (
        inlet_flow / SECONDS_PER_DAY * feed_density * (1.0 - tds_fraction)
    )
    feed_tds_g_l = tds_fraction * feed_density
    brine_salinity = feed_tds_g_l / max(1.0 - recovery, 1e-12)

    warnings = []
    if abs(tds_fraction - 0.035) > 0.01:
        warnings.append("Feed TDS differs materially from the 3.5 wt% workbook calibration point.")
    if abs(recovery - 0.50) > 0.10:
        warnings.append("Recovery differs materially from the 50% workbook calibration point.")
    if abs(temperature - 25.0) > 5.0:
        warnings.append("Feed temperature differs materially from the 25 C workbook calibration point.")
    if tds_fraction / max(1.0 - recovery, 1e-12) > 0.28:
        warnings.append("Calculated brine TDS may exceed the workbook's 28 wt% physical limit.")
    warnings.append(
        "SEEC and equipment sizes use workbook calibration-point scaling because the corresponding worksheet cells are constants."
    )

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "energy_intensity": _result(seec, "kWh/m3 feed"),
        "thermal_energy_intensity": _result(0.0, "kWh/m3 feed"),
        "removal_efficiencies": removals,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "outlet_stream": outlet_stream,
        "feed_tds_mass_fraction": _result(tds_fraction, "fraction"),
        "feed_temperature": _result(temperature, "deg C"),
        "feed_h2o_mass_flow": _result(feed_h2o_mass_flow, "kg/s"),
        "recycle_ratio": _result(recycle_ratio, "recycle/feed"),
        "brine_salinity": _result(brine_salinity, "g/L"),
        "membrane_area": _result(membrane_area, "m2"),
        "heat_exchanger_area": _result(heat_exchanger_area, "m2"),
        "heater_thermal_duty": _result(heater_power, "kW"),
        "chiller_thermal_duty": _result(chiller_power, "kW"),
        "total_electric_power": _result(total_power, "kW"),
        "model_warnings": _result(warnings, ""),
    }

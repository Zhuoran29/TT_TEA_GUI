"""LSRRO technical model adapted from the NMSU PW membrane model files."""

from __future__ import annotations

from tea_models.lsrro_core import (
    BBL_TO_M3,
    DEFAULT_ERD_FRACTION,
    PSI_TO_BAR,
    REFERENCE_FLOW_BBL_DAY,
    REFERENCE_GROSS_PUMP_POWER_KW,
    calculate_recovery_fraction,
    lookup_stage_pressure,
    predict_water_quality,
    tds_mg_l,
)
from tea_models.water_quality import calculate_brine_quality


def _result(value, unit):
    return {"value": value, "unit": unit}


def _number(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_inputs, stream):
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    if inlet_flow <= 0.0:
        raise ValueError("LSRRO inlet flow must be positive.")

    water_quality_in = stream.get("water_quality", {}) or {}
    auto_recovery, warnings = calculate_recovery_fraction(water_quality_in)
    recovery = min(max(_number(technical_inputs, "recovery", 0.50), 0.01), 0.90)
    recovery_basis = "manual input"

    outlet_flow = inlet_flow * recovery
    brine_flow = max(inlet_flow - outlet_flow, 0.0)

    clip_negative = _number(technical_inputs, "clip_negative_permeate", 1.0) >= 0.5
    water_quality_out, removal_efficiencies, prediction_methods = predict_water_quality(
        water_quality_in,
        clip_negative,
    )
    outlet_stream = {
        "flow_m3_day": outlet_flow,
        "water_quality": water_quality_out,
    }
    brine_quality = calculate_brine_quality(
        water_quality_in,
        water_quality_out,
        inlet_flow,
        outlet_flow,
        brine_flow,
    )

    feed_tds_g_l = tds_mg_l(water_quality_in) / 1000.0
    stages, pressure_psi = lookup_stage_pressure(feed_tds_g_l)
    stage_override = int(round(_number(technical_inputs, "stage_override", 0.0)))
    pressure_override_psi = _number(technical_inputs, "pressure_override_psi", 0.0)
    if stage_override > 0:
        stages = stage_override
    if pressure_override_psi > 0.0:
        pressure_psi = pressure_override_psi

    reference_flow_bbl_day = _number(
        technical_inputs,
        "reference_flow_bbl_day",
        REFERENCE_FLOW_BBL_DAY,
    )
    reference_gross_power = _number(
        technical_inputs,
        "gross_pump_power_kw",
        REFERENCE_GROSS_PUMP_POWER_KW,
    )
    erd_fraction = min(max(_number(
        technical_inputs,
        "energy_recovery_fraction",
        DEFAULT_ERD_FRACTION,
    ), 0.0), 1.0)
    inlet_bbl_day = inlet_flow / BBL_TO_M3
    gross_pump_power = (
        reference_gross_power * inlet_bbl_day / max(reference_flow_bbl_day, 1e-12)
    )
    net_pump_power = gross_pump_power * (1.0 - erd_fraction)
    energy_intensity = net_pump_power * 24.0 / inlet_flow

    membrane_flux = _number(technical_inputs, "membrane_flux", 18.0)
    membrane_area = outlet_flow * 1000.0 / max(membrane_flux * 24.0, 1e-12)

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "recovery_percent": _result(recovery * 100.0, "%"),
        "recovery_basis": _result(recovery_basis, ""),
        "calculated_recovery": _result(auto_recovery, "fraction"),
        "calculated_recovery_percent": _result(auto_recovery * 100.0, "%"),
        "feed_tds": _result(feed_tds_g_l, "g/L"),
        "hardness": _result(
            float(water_quality_in.get("Hardness", {}).get("value", 0.0) or 0.0),
            water_quality_in.get("Hardness", {}).get("unit", "mg/L as CaCO3"),
        ),
        "silica": _result(
            float(water_quality_in.get("Silica", {}).get("value", 0.0) or 0.0),
            water_quality_in.get("Silica", {}).get("unit", "mg/L"),
        ),
        "number_of_stages": _result(stages, "count"),
        "operating_pressure": _result(pressure_psi * PSI_TO_BAR, "bar"),
        "operating_pressure_psi": _result(pressure_psi, "psi"),
        "gross_pump_power": _result(gross_pump_power, "kW"),
        "net_pump_power": _result(net_pump_power, "kW"),
        "energy_recovery_fraction": _result(erd_fraction, "fraction"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "thermal_energy_intensity": _result(0.0, "kWh/m3 feed"),
        "membrane_flux": _result(membrane_flux, "L/m2-h"),
        "membrane_area": _result(membrane_area, "m2"),
        "reference_flow": _result(reference_flow_bbl_day, "bbl/day"),
        "removal_efficiencies": removal_efficiencies,
        "prediction_methods": prediction_methods,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "brine_water_quality": brine_quality,
        "outlet_stream": outlet_stream,
        "design_warnings": _result(warnings, ""),
    }

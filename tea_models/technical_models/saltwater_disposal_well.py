"""Saltwater disposal well technical template model."""

from __future__ import annotations

import math


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _result(value, unit):
    return {"value": value, "unit": unit}


def run(unit_process, technical_inputs, stream):
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    water_quality = stream.get("water_quality", {})

    disposal_fraction = _input(technical_inputs, "disposal_fraction", 1.0)
    disposal_fraction = max(0.0, min(disposal_fraction, 1.0))
    disposed_flow = inlet_flow * disposal_fraction
    outlet_flow = inlet_flow - disposed_flow

    well_capacity = _input(technical_inputs, "injection_well_capacity", 2000.0)
    injection_pressure = _input(technical_inputs, "injection_pressure", 50.0)
    pump_efficiency = max(_input(technical_inputs, "pump_efficiency", 0.75), 1e-9)
    energy_intensity = _input(technical_inputs, "energy_intensity", 0.0)
    if energy_intensity <= 0.0:
        energy_intensity = injection_pressure * 100000.0 / pump_efficiency / 3600000.0

    well_count = math.ceil(disposed_flow / max(well_capacity, 1e-9)) if disposed_flow > 0.0 else 0
    outlet_stream = {
        "flow_m3_day": outlet_flow,
        "water_quality": water_quality.copy(),
    }

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(disposed_flow, "m3/day"),
        "disposed_flow": _result(disposed_flow, "m3/day"),
        "water_recovery": _result(1.0 - disposal_fraction, "fraction"),
        "disposal_fraction": _result(disposal_fraction, "fraction"),
        "injection_well_capacity": _result(well_capacity, "m3/day/well"),
        "injection_well_count": _result(well_count, "well"),
        "injection_pressure": _result(injection_pressure, "bar"),
        "pump_efficiency": _result(pump_efficiency, "fraction"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 disposed"),
        "chemical_dose": _result(0.0, "kg/m3"),
        "chemical_consumption": _result(0.0, "kg/day"),
        "removal_efficiencies": {},
        "water_quality_in": water_quality.copy(),
        "water_quality_out": water_quality.copy(),
        "outlet_stream": outlet_stream,
    }

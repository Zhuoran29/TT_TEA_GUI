"""Electrocoagulation model adapted from the NMPWRC EC-Al script."""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "chemical_clarification",
    "recovery": 0.98,
    "current_density_mA_cm2": 20.0,
    "electrode_gap_m": 0.02,
    "hydraulic_retention_time": 30.0,
    "energy_intensity": 0.0,
}

REFERENCE_ELECTRODE_AREA_M2 = 567.0
REFERENCE_FLOW_M3_DAY = 11356.0
REFERENCE_HRT_MIN = 15.0
REFERENCE_REACTOR_VOLUME_M3 = 12.5
MW_ALOH3_G_MOL = 78.00
MW_AL_G_MOL = 26.98
Z_AL = 3.0
M_AL_KG_MOL = 26.98 / 1000.0
F_C_MOL = 96485.3329


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        return float(entry.get("value", default) if isinstance(entry, dict) else entry)
    except (TypeError, ValueError):
        return float(default)


def _quality_value(quality, parameter, default=0.0):
    try:
        return float((quality.get(parameter, {}) or {}).get("value", default) or default)
    except (TypeError, ValueError):
        return float(default)


def _nacl_from_rho(rho_mS_cm):
    return (
        -1.74e-9 * rho_mS_cm**5
        + 9.54e-7 * rho_mS_cm**4
        - 1.652e-4 * rho_mS_cm**3
        + 0.01 * rho_mS_cm**2
        + 0.338 * rho_mS_cm
        + 0.09
    )


def _rho_from_nacl(nacl_g_l):
    lo = 0.0
    hi = 260.0
    f_lo = _nacl_from_rho(lo) - nacl_g_l
    f_hi = _nacl_from_rho(hi) - nacl_g_l
    if f_lo == 0.0:
        return lo
    if f_hi == 0.0:
        return hi
    if f_lo * f_hi > 0.0:
        return max(0.0, min(nacl_g_l / 0.338, hi))
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = _nacl_from_rho(mid) - nacl_g_l
        if abs(f_mid) < 1e-9:
            return mid
        if f_lo * f_mid <= 0.0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid
    return 0.5 * (lo + hi)


def run(unit_process, technical_inputs, stream):
    outputs = run_template(unit_process, technical_inputs, stream, DEFAULTS)
    inlet_flow = _value(outputs, "inlet_flow")
    hrt = _input(technical_inputs, "hydraulic_retention_time", DEFAULTS["hydraulic_retention_time"])
    gap_m = _input(technical_inputs, "electrode_gap_m", DEFAULTS["electrode_gap_m"])
    current_density = _input(technical_inputs, "current_density_mA_cm2", DEFAULTS["current_density_mA_cm2"])

    reference_flow_volume = REFERENCE_FLOW_M3_DAY * (REFERENCE_HRT_MIN / 1440.0)
    reactor_scaling = reference_flow_volume / REFERENCE_REACTOR_VOLUME_M3
    aspect_ratio = REFERENCE_REACTOR_VOLUME_M3 / REFERENCE_ELECTRODE_AREA_M2
    reactor_volume = inlet_flow * (hrt / 1440.0) / max(reactor_scaling, 1e-12)
    electrode_area = reactor_volume / max(aspect_ratio, 1e-12)

    tds_mg_l = _quality_value(outputs.get("water_quality_in", {}), "TDS")
    nacl_g_l = max(tds_mg_l / 1000.0, 1e-9)
    try:
        rho = _rho_from_nacl(nacl_g_l)
        conductivity_s_m = rho / 10.0
        resistance = gap_m / max(conductivity_s_m * electrode_area, 1e-12)
    except Exception:
        rho = 0.0
        resistance = 0.0

    current_a = current_density * 10.0 * electrode_area
    voltage_v = current_a * resistance + 1.50
    power_kw = current_a * voltage_v / 1000.0
    energy_intensity = power_kw * 24.0 / max(inlet_flow, 1e-12)

    flow_l_s = inlet_flow * 1000.0 / 86400.0
    al_dose_mg_l = current_a * M_AL_KG_MOL * 1e6 / max(Z_AL * F_C_MOL * flow_l_s, 1e-12)
    aloh3_solids_mg_l = al_dose_mg_l * MW_ALOH3_G_MOL / MW_AL_G_MOL
    feed_tss = _quality_value(outputs.get("water_quality_in", {}), "TSS")
    outlet_tss = _quality_value(outputs.get("water_quality_out", {}), "TSS", feed_tss)
    removed_tss = max(feed_tss - outlet_tss, 0.0)
    solid_waste_kg_m3 = (aloh3_solids_mg_l + removed_tss) / 1000.0

    outputs.update({
        "hydraulic_retention_time": _result(hrt, "min"),
        "reactor_volume": _result(reactor_volume, "m3"),
        "electrode_area": _result(electrode_area, "m2"),
        "conductivity_from_tds": _result(rho, "mS/cm"),
        "solution_resistance": _result(resistance, "ohm"),
        "system_current": _result(current_a, "A"),
        "system_voltage": _result(voltage_v, "V"),
        "system_power": _result(power_kw, "kW"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "aluminum_dose": _result(al_dose_mg_l, "mg/L"),
        "aluminum_consumption": _result(al_dose_mg_l * inlet_flow / 1000.0, "kg/day"),
        "solid_waste_generation": _result(solid_waste_kg_m3, "kg/m3 feed"),
        "solid_waste": _result(solid_waste_kg_m3 * inlet_flow, "kg/day"),
    })
    return outputs

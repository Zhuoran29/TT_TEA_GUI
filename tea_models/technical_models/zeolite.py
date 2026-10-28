"""Zeolite (clinoptilolite) ammonia-removal model using bench breakthrough data.

Bed life comes from cycle 1 of the NMSU bench column test (KMI zeolite 14x30,
EBCT 20 min, ~25 mg/L NH3-N): the curve is interpolated at the NH3-N removal
from the unit's removal-efficiency table
and scaled to the inlet NH3-N by mass loading (BV x C held constant). Zeolite
is used as a post-treatment after desalination, where competing cations are
low, so no correction for Na/K/Ca competition is applied.

Regeneration follows the bench procedure: a 10% NaCl brine at pH 11 (NaOH),
0.9 L per 10 mL bed (90 bed volumes) reused for 5 regenerations. Pump energy
is hydraulic (P = rho * g * H * Q / eta), as for GAC.
"""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "zeolite",
    "recovery": 0.995,
    "energy_intensity": 0.0,
    "chemical_dose": 0.0,
    "empty_bed_contact_time": 20.0,
    # Pumping
    "pump_head": 10.0,  # m
    "pump_efficiency": 0.70,
    # Regeneration (bench procedure)
    "regenerant_bed_volumes": 90.0,  # brine volume per regeneration, in bed volumes
    "brine_reuse_cycles": 5.0,
    "nacl_mass_fraction": 0.10,
    "naoh_to_nitrogen_molar_ratio": 1.0,  # OH- per NH4+ eluted, holds pH 11
    # Ammonium exchange capacity used to size the zeolite mass per cycle (Deng et al. 2014)
    "aec_mg_n_g": 4.0,
    # Bench column: 8.24 g zeolite in a 10 mL bed (0.5 mL/min x 20 min); used to report bed inventory.
    "media_bulk_density": 824.0,
}

# Bench cycle 1: (BV, feed NH3-N mg/L, effluent NH3-N mg/L, removal %)
BENCH_DATA = [
    (0.0, 24.9, 0.001, 100.0),
    (103.7, 24.9, 0.001, 100.0),
    (202.2, 23.9, 0.003, 100.0),
    (297.9, 24.5, 0.0, 100.0),
    (390.7, 24.8, 0.002, 100.0),
    (482.3, 25.3, 0.063, 99.8),
    (558.7, 25.3, 2.68, 89.4),
    (723.9, 25.0, 15.7, 37.2),
    (825.3, 24.8, 20.0, 19.4),
    (893.8, 24.8, 20.9, 15.7),
    (1014.3, 25.3, 21.3, 15.8),
    (1112.2, 24.5, 21.1, 13.9),
    (1169.0, 24.5, 20.0, 18.4),
    (1243.5, 21.6, 23.9, 0.0),
    (1319.9, 21.6, 24.1, 0.0),
]
BENCH_FEED_AVG_MG_L = sum(row[1] for row in BENCH_DATA) / len(BENCH_DATA)
DEFAULT_AMMONIA_REMOVAL = 0.95  # used only when the removal table has no NH3-N entry
MW_N = 14.0067
MW_NAOH = 39.997


def brine_density_kg_m3(nacl_mass_fraction):
    """Approximate NaCl brine density at about 20 C (within ~0.5% up to saturation)."""
    return 997.0 + 735.0 * max(nacl_mass_fraction, 0.0)


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


def interpolate_bv_at_removal(target_removal_percent):
    """Bench BV at which cycle-1 removal first falls to the target (linear interpolation)."""
    rows = sorted(BENCH_DATA, key=lambda row: row[0])
    target = min(max(target_removal_percent, 0.0), 100.0)
    if target >= rows[0][3]:
        # Removal stays at 100% over the first rows: use the last BV still at 100%.
        last_full = rows[0][0]
        for bv, _feed, _eff, removal in rows:
            if removal >= target:
                last_full = bv
            else:
                break
        return last_full
    for idx in range(len(rows) - 1):
        bv1, _feed1, _eff1, r1 = rows[idx]
        bv2, _feed2, _eff2, r2 = rows[idx + 1]
        if r1 >= target >= r2 and r1 != r2:
            return bv1 + (target - r1) * (bv2 - bv1) / (r2 - r1)
    return rows[-1][0]


def run(unit_process, technical_inputs, stream):
    # NH3-N removal comes from the removal-efficiency table (default 95% in UNIT_REMOVAL_RATES).
    removals = dict(technical_inputs.get("removal_efficiencies") or {})
    try:
        removal = float(removals.get("Ammonia nitrogen", DEFAULT_AMMONIA_REMOVAL))
    except (TypeError, ValueError):
        removal = DEFAULT_AMMONIA_REMOVAL
    removal = min(max(removal, 0.0), 1.0)
    removals["Ammonia nitrogen"] = removal
    template_inputs = {**technical_inputs, "removal_efficiencies": removals}
    outputs = run_template(unit_process, template_inputs, stream, DEFAULTS)

    def get(name):
        return _input(technical_inputs, name, DEFAULTS[name])

    inlet_flow = _value(outputs, "inlet_flow")
    inlet_ammonia = _quality_value(outputs["water_quality_in"], "Ammonia nitrogen")
    outlet_ammonia = _quality_value(outputs["water_quality_out"], "Ammonia nitrogen", inlet_ammonia)

    bench_bv = interpolate_bv_at_removal(removal * 100.0)
    adjusted_bv = bench_bv * BENCH_FEED_AVG_MG_L / inlet_ammonia if inlet_ammonia > 0.0 else 0.0
    ebct_min = _input(technical_inputs, "empty_bed_contact_time", DEFAULTS["empty_bed_contact_time"])
    service_time_days = adjusted_bv * ebct_min / 1440.0 if adjusted_bv > 0.0 else 0.0
    cycles_per_year = 365.0 / service_time_days if service_time_days > 0.0 else 0.0
    ammonia_removed_kg_day = inlet_flow * max(inlet_ammonia - outlet_ammonia, 0.0) / 1000.0
    bed_volume = inlet_flow / 1440.0 * ebct_min

    # Regeneration chemicals (calendar-year basis; the cost model scales by operating days)
    nacl_fraction = min(max(get("nacl_mass_fraction"), 0.0), 0.26)
    reuse = max(get("brine_reuse_cycles"), 1.0)
    fresh_brine_per_regen = max(get("regenerant_bed_volumes"), 0.0) * bed_volume / reuse  # m3
    nacl_per_regen = fresh_brine_per_regen * brine_density_kg_m3(nacl_fraction) * nacl_fraction  # kg
    annual_nacl = nacl_per_regen * cycles_per_year
    annual_spent_brine = fresh_brine_per_regen * cycles_per_year
    annual_n_removed = ammonia_removed_kg_day * 365.0
    annual_naoh = annual_n_removed / MW_N * max(get("naoh_to_nitrogen_molar_ratio"), 0.0) * MW_NAOH

    # Zeolite mass loaded with the N removed in one cycle at the given exchange capacity
    aec = max(get("aec_mg_n_g"), 1e-12)
    zeolite_mass_from_aec = ammonia_removed_kg_day * service_time_days * 1000.0 / aec  # kg

    # Pump energy: P = rho * g * H * Q / eta
    pump_head = max(get("pump_head"), 0.0)
    pump_efficiency = max(get("pump_efficiency"), 1e-9)
    energy_intensity = 1000.0 * 9.80665 * pump_head / pump_efficiency / 3.6e6  # kWh/m3
    pump_power_kw = energy_intensity * inlet_flow / 24.0

    warnings = []
    if inlet_ammonia <= 0.0:
        warnings.append("Feed ammonia is unavailable; bed life is not calculated.")
    elif inlet_ammonia > 30.0:
        warnings.append("Feed NH3-N is above the bench test range (~25 mg/L); bed life is extrapolated.")

    outputs.update({
        "feed_ammonia": _result(inlet_ammonia, "mg/L"),
        "outlet_ammonia": _result(outlet_ammonia, "mg/L"),
        "ammonia_removal": _result(removal, "fraction"),
        "bench_breakthrough_bv": _result(bench_bv, "bed volumes"),
        "bench_feed_ammonia": _result(BENCH_FEED_AVG_MG_L, "mg/L"),
        "breakthrough_bed_volumes": _result(adjusted_bv, "bed volumes"),
        "service_time": _result(service_time_days, "day"),
        "cycle_duration": _result(service_time_days, "day"),
        "cycles_per_year": _result(cycles_per_year, "1/year"),
        "ammonia_removed": _result(ammonia_removed_kg_day, "kg N/day"),
        "aec": _result(aec, "mg N/g zeolite"),
        "zeolite_mass_from_aec": _result(zeolite_mass_from_aec, "kg"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "pump_power": _result(pump_power_kw, "kW"),
        "media_bed_volume": _result(bed_volume, "m3"),
        "fresh_brine_per_regeneration": _result(fresh_brine_per_regen, "m3"),
        "nacl_per_regeneration": _result(nacl_per_regen, "kg"),
        "annual_nacl_consumption": _result(annual_nacl, "kg/year"),
        "annual_naoh_consumption": _result(annual_naoh, "kg/year"),
        "spent_brine_generation": _result(annual_spent_brine, "m3/year"),
        "model_warnings": _result(warnings, ""),
    })
    return outputs

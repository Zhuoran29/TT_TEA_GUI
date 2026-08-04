"""Zeolite ammonia-removal model using bench breakthrough data."""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "zeolite",
    "recovery": 0.995,
    "energy_intensity": 0.02,
    "chemical_dose": 0.0,
    "empty_bed_contact_time": 20.0,
    "media_bulk_density": 824.0,
    "ammonia_removal": 0.95,
    "aec_mg_n_g": 4.0,
}

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


def _interpolate_bv_at_removal(target_removal_percent):
    rows = sorted(BENCH_DATA, key=lambda row: row[0])
    for idx in range(len(rows) - 1):
        bv1, _feed1, _eff1, r1 = rows[idx]
        bv2, _feed2, _eff2, r2 = rows[idx + 1]
        if r1 >= target_removal_percent and r2 <= target_removal_percent:
            return bv1 + (target_removal_percent - r1) * (bv2 - bv1) / (r2 - r1)
    return rows[-1][0]


def run(unit_process, technical_inputs, stream):
    removal = min(max(_input(technical_inputs, "ammonia_removal", DEFAULTS["ammonia_removal"]), 0.0), 1.0)
    removals = {"Ammonia nitrogen": removal, **(technical_inputs.get("removal_efficiencies") or {})}
    removals["Ammonia nitrogen"] = removal
    template_inputs = {**technical_inputs, "removal_efficiencies": removals}
    outputs = run_template(unit_process, template_inputs, stream, DEFAULTS)
    outputs["energy_intensity"]["unit"] = "kWh/m3 feed"

    inlet_flow = _value(outputs, "inlet_flow")
    inlet_ammonia = _quality_value(outputs["water_quality_in"], "Ammonia nitrogen")
    outlet_ammonia = _quality_value(outputs["water_quality_out"], "Ammonia nitrogen", inlet_ammonia)
    bench_feed_avg = sum(row[1] for row in BENCH_DATA) / len(BENCH_DATA)
    target_removal_percent = removal * 100.0
    bench_bv = _interpolate_bv_at_removal(target_removal_percent)
    adjusted_bv = bench_bv * bench_feed_avg / max(inlet_ammonia, 1e-12) if inlet_ammonia > 0.0 else 0.0
    ebct_min = _input(technical_inputs, "empty_bed_contact_time", DEFAULTS["empty_bed_contact_time"])
    service_time_days = adjusted_bv * ebct_min / 1440.0 if adjusted_bv > 0.0 else 0.0
    cycles_per_year = 365.0 / service_time_days if service_time_days > 0.0 else 0.0
    ammonia_removed_kg_day = inlet_flow * max(inlet_ammonia - outlet_ammonia, 0.0) / 1000.0
    aec = max(_input(technical_inputs, "aec_mg_n_g", DEFAULTS["aec_mg_n_g"]), 1e-12)
    zeolite_mass_from_aec = ammonia_removed_kg_day * service_time_days * 1000.0 / aec

    outputs.update({
        "feed_ammonia": _result(inlet_ammonia, "mg/L"),
        "outlet_ammonia": _result(outlet_ammonia, "mg/L"),
        "ammonia_removal": _result(removal, "fraction"),
        "bench_breakthrough_bv": _result(bench_bv, "bed volumes"),
        "breakthrough_bed_volumes": _result(adjusted_bv, "bed volumes"),
        "bench_feed_ammonia": _result(bench_feed_avg, "mg/L"),
        "service_time": _result(service_time_days, "day"),
        "cycle_duration": _result(service_time_days, "day"),
        "cycles_per_year": _result(cycles_per_year, "1/year"),
        "ammonia_removed": _result(ammonia_removed_kg_day, "kg N/day"),
        "aec": _result(aec, "mg N/g zeolite"),
        "zeolite_mass_from_aec": _result(zeolite_mass_from_aec, "kg"),
        "model_warnings": _result(
            ["Feed ammonia is unavailable; regeneration costs and NH4Cl credit will be zero."]
            if inlet_ammonia <= 0.0
            else [],
            "",
        ),
    })
    return outputs

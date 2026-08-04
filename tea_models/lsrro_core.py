"""Shared LSRRO recovery and water-quality equations."""

from __future__ import annotations

from copy import deepcopy


BBL_TO_M3 = 0.158987294928
PSI_TO_BAR = 0.0689475729

REFERENCE_FLOW_BBL_DAY = 50000.0
REFERENCE_FLOW_M3_DAY = REFERENCE_FLOW_BBL_DAY * BBL_TO_M3
REFERENCE_GROSS_PUMP_POWER_KW = 3534.0
DEFAULT_ERD_FRACTION = 0.30

RECOVERY_TABLE = [
    (20.0, 1, 943.0, 77.0),
    (35.0, 2, 1150.0, 70.0),
    (50.0, 2, 1150.0, 64.0),
    (75.0, 3, 1150.0, 55.0),
    (100.0, 5, 1150.0, 44.0),
    (120.0, 4, 1150.0, 35.0),
    (130.0, 6, 1150.0, 31.0),
]

REGRESSION_MODELS = {
    "Alkalinity": (48.49, -0.4797, 1.36e-3),
    "Ammonia nitrogen": (-6.97, 0.0875, -1.05e-4),
    "BTEX": (0.00278, -0.00215, 4.85e-4),
    "Calcium": (11.85, -0.023595, 6.33e-6),
    "Chloride": (71.76, -0.00206, 6.47e-8),
}

AVERAGE_REMOVALS = {
    "TDS": 0.9940,
    "TOC": 0.9155,
    "TSS": 0.9312,
    "Conductivity": 0.9921,
    "Hardness": 0.9941,
    "Ammonia nitrogen": 0.9838,
    "Barium": 0.9985,
    "Boron": 0.9811,
    "Magnesium": 0.9947,
    "Silica": 0.9855,
    "Sodium": 0.9924,
    "Strontium": 0.9963,
    "Iron": 0.9841,
    "Sulfate": 0.8797,
    "Gross Alpha": 0.9936,
    "Gross Beta": 0.9932,
    "Radium-226": 0.9758,
    "Radium-228": 0.9982,
    "Oil": 0.7275,
    "TPH": 0.9408,
    "PAHs": 0.9155,
}

DIRECT_ASSIGNMENT = {"pH", "Temperature"}


def numeric_entry(quality, parameter, default=0.0):
    entry = (quality or {}).get(parameter, {})
    try:
        return float(entry.get("value", default) or default)
    except (TypeError, ValueError):
        return float(default)


def concentration_unit(quality, parameter, default="mg/L"):
    return (quality or {}).get(parameter, {}).get("unit", default) or default


def tds_mg_l(quality, default=0.0):
    value = numeric_entry(quality, "TDS", default)
    unit = concentration_unit(quality, "TDS", "mg/L").lower().replace(" ", "")
    if unit in {"g/l", "kg/m3"}:
        return value * 1000.0
    return value


def calculate_recovery_fraction(quality):
    """Return LSRRO water recovery and warnings from the empirical regression."""
    feed_tds_mg_l = tds_mg_l(quality)
    hardness = numeric_entry(quality, "Hardness")
    silica = numeric_entry(quality, "Silica")
    tds_g_l = feed_tds_mg_l / 1000.0
    warnings = []

    if tds_g_l < 20.0:
        warnings.append("Feed TDS is below the LSRRO recovery regression range of 20-150 g/L.")
    if tds_g_l > 150.0:
        warnings.append("Feed TDS is above the LSRRO recovery regression range of 20-150 g/L.")

    recovery_base = -0.0002 * tds_g_l**2 - 0.3816 * tds_g_l + 84.01
    recovery_percent = recovery_base - 0.000369 * hardness - 0.0001 * silica
    clipped = min(max(recovery_percent, 1.0), 90.0)
    if clipped != recovery_percent:
        warnings.append("Calculated LSRRO recovery was clipped to the 1-90% range.")
    return clipped / 100.0, warnings


def lookup_stage_pressure(tds_g_l):
    """Lookup the next-larger TDS design point for stages and pressure."""
    for threshold, stages, pressure_psi, _recovery in RECOVERY_TABLE:
        if tds_g_l <= threshold:
            return stages, pressure_psi
    return RECOVERY_TABLE[-1][1], RECOVERY_TABLE[-1][2]


def predict_permeate(parameter, feed_value, clip_negative=True):
    if parameter in DIRECT_ASSIGNMENT:
        return feed_value, "direct_assignment"
    if parameter in REGRESSION_MODELS:
        a, b, c = REGRESSION_MODELS[parameter]
        value = a + b * feed_value + c * feed_value**2
        if clip_negative and value < 0.0 and parameter in AVERAGE_REMOVALS:
            return (
                feed_value * (1.0 - AVERAGE_REMOVALS[parameter]),
                "average_removal_fallback",
            )
        if clip_negative:
            value = max(value, 0.0)
        return value, "regression"
    if parameter in AVERAGE_REMOVALS:
        return feed_value * (1.0 - AVERAGE_REMOVALS[parameter]), "average_removal"
    return feed_value, "not_modeled"


def predict_water_quality(quality, clip_negative=True):
    """Predict LSRRO permeate quality for the app's tracked constituents."""
    inlet_quality = deepcopy(quality or {})
    outlet_quality = deepcopy(inlet_quality)
    removal_efficiencies = {}
    methods = {}

    for parameter, entry in inlet_quality.items():
        try:
            feed_value = float(entry.get("value", 0.0) or 0.0)
        except (TypeError, ValueError):
            continue

        permeate_value, method = predict_permeate(parameter, feed_value, clip_negative)
        unit = entry.get("unit", "")
        outlet_quality[parameter] = {"value": permeate_value, "unit": unit}
        if feed_value:
            removal = (1.0 - permeate_value / feed_value)
        else:
            removal = 0.0
        removal_efficiencies[parameter] = min(max(removal, 0.0), 1.0)
        methods[parameter] = method

    return outlet_quality, removal_efficiencies, methods


def removal_preview_rows(quality, clip_negative=True):
    outlet_quality, removal_efficiencies, methods = predict_water_quality(
        quality,
        clip_negative,
    )
    rows = []
    for parameter, entry in (quality or {}).items():
        if parameter not in removal_efficiencies:
            continue
        rows.append({
            "parameter": parameter,
            "feed_concentration": entry.get("value", 0.0),
            "predicted_permeate": outlet_quality.get(parameter, {}).get("value", 0.0),
            "removal_efficiency": removal_efficiencies.get(parameter, 0.0),
            "method": methods.get(parameter, ""),
        })
    return rows

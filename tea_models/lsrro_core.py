"""Shared LSRRO recovery, WaterTAP design-table and water-quality equations."""

from __future__ import annotations

import csv
from copy import deepcopy
from functools import lru_cache
from pathlib import Path


BBL_TO_M3 = 0.158987294928
PSI_TO_BAR = 0.0689475729

REFERENCE_FLOW_BBL_DAY = 50000.0
REFERENCE_FLOW_M3_DAY = REFERENCE_FLOW_BBL_DAY * BBL_TO_M3

DESIGN_TABLE_PATH = Path(__file__).resolve().parents[1] / "data" / "model_tables" / "lsrro_watertap_table.csv"
DESIGN_TABLE_YEAR = 2018
INTERPOLATED_COLUMNS = (
    "sec_kwh_m3_product",
    "membrane_area_m2_per_m3d_product",
    "first_stage_area_m2_per_m3d_product",
    "membrane_capex_usd_per_m3d_feed",
    "pump_capex_usd_per_m3d_feed",
    "erd_capex_usd_per_m3d_feed",
    "equipment_capex_usd_per_m3d_feed",
    "membrane_replacement_usd_yr_per_m3d_feed",
    "watertap_lcow_usd_m3_product",
    "stages",
)

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
    "Naphthalene": 0.9155,
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
        warnings.append("Feed TDS is below the LSRRO recovery regression range of 20-130 g/L.")
    if tds_g_l > 130.0:
        warnings.append("Feed TDS is above the LSRRO recovery regression range of 20-130 g/L.")

    recovery_base = -0.0002 * tds_g_l**2 - 0.3816 * tds_g_l + 84.01
    recovery_percent = recovery_base - 0.000369 * hardness - 0.0001 * silica
    clipped = min(max(recovery_percent, 1.0), 90.0)
    if clipped != recovery_percent:
        warnings.append("Calculated LSRRO recovery was clipped to the 1-90% range.")
    return clipped / 100.0, warnings


@lru_cache(maxsize=4)
def load_design_table(path=str(DESIGN_TABLE_PATH)):
    """Return {feed TDS (g/L): {recovery: {stages: row}}} from the WaterTAP design table."""
    table = {}
    with open(path, newline="") as handle:
        for row in csv.DictReader(handle):
            values = {key: float(value) for key, value in row.items()}
            line = table.setdefault(values["feed_tds_g_l"], {})
            line.setdefault(values["recovery"], {})[int(values["stages"])] = values
    return {tds: dict(sorted(line.items())) for tds, line in sorted(table.items())}


def _weight(x, x0, x1):
    """Linear weights of x0 and x1 for x between them."""
    if x1 == x0:
        return 1.0, 0.0
    w1 = (x - x0) / (x1 - x0)
    return 1.0 - w1, w1


def _line_corners(line, recovery):
    """Neighboring table recoveries on one TDS line; the recovery is clamped to the line's feasible range."""
    recoveries = list(line)
    clamped = min(max(recovery, recoveries[0]), recoveries[-1])
    r0 = max(r for r in recoveries if r <= clamped + 1e-12)
    r1 = min(r for r in recoveries if r >= clamped - 1e-12)
    w0, w1 = _weight(clamped, r0, r1)
    return clamped, [(w0, line[r0]), (w1, line[r1])]


def lookup_design(feed_tds_g_l, recovery, table=None):
    """Interpolate the WaterTAP LSRRO design (per unit flow) at a feed TDS and recovery.

    The design is interpolated between neighboring table points that have the same stage count. Of
    the stage counts feasible at all neighboring points, the one with the lowest interpolated WaterTAP
    LCOW is used. Outside the table the nearest feasible point is used. Returns (design, warnings).
    """
    table = table or load_design_table()
    warnings = []
    tds_values = list(table)
    tds = min(max(feed_tds_g_l, tds_values[0]), tds_values[-1])
    if tds != feed_tds_g_l:
        warnings.append(
            f"Feed TDS {feed_tds_g_l:.0f} g/L is outside the WaterTAP LSRRO table "
            f"({tds_values[0]:.0f}-{tds_values[-1]:.0f} g/L); the nearest table TDS is used."
        )
    lower = max(t for t in tds_values if t <= tds)
    upper = min(t for t in tds_values if t >= tds)
    w_low, w_high = _weight(tds, lower, upper)

    corners = []
    for line_tds, w_tds in ((lower, w_low), (upper, w_high)):
        line = table[line_tds]
        used, line_corners = _line_corners(line, recovery)
        if abs(used - recovery) > 1e-9 and not any("feasible range" in w for w in warnings):
            recoveries = list(line)
            warnings.append(
                f"Recovery {recovery:.0%} is outside the WaterTAP feasible range at {line_tds:.0f} g/L "
                f"({recoveries[0]:.0%}-{recoveries[-1]:.0%}); the nearest feasible design is used."
            )
        corners += [(w_tds * w, designs) for w, designs in line_corners]
    corners = [(w, designs) for w, designs in corners if w > 1e-12]

    def blend(rows):
        return {key: sum(w * row[key] for (w, _), row in zip(corners, rows)) for key in INTERPOLATED_COLUMNS}

    common = set.intersection(*(set(designs) for _, designs in corners))
    if common:
        lcow = {
            n: sum(w * designs[n]["watertap_lcow_usd_m3_product"] for w, designs in corners) for n in common
        }
        stages = min(lcow, key=lcow.get)
        return blend([designs[stages] for _, designs in corners]), warnings

    best = [min(designs.values(), key=lambda row: row["watertap_lcow_usd_m3_product"]) for _, designs in corners]
    design = blend(best)
    design["stages"] = max(row["stages"] for row in best)
    warnings.append("No stage count is feasible at all neighboring WaterTAP table points; designs with different stage counts are blended.")
    return design, warnings


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

"""Scenario snapshot and comparison utilities."""

from copy import deepcopy
from datetime import datetime, timezone
import uuid

import pandas as pd


BBL_PER_M3 = 6.289810770432
MAX_COMPARISON_SCENARIOS = 4


def create_scenario_snapshot(name, state):
    """Create an immutable-by-convention copy of the current TEA case."""
    results = state.get("tea_results")
    if not results:
        raise ValueError("A completed TEA calculation is required before saving a scenario.")
    cleaned_name = str(name or "").strip()
    if not cleaned_name:
        raise ValueError("Scenario name is required.")

    ffp = state.get("ffp_scenarios", [])
    return {
        "id": uuid.uuid4().hex,
        "name": cleaned_name,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project_name": state.get("project_name", "TEA project"),
        "configuration": {
            "influent_type": state.get("influent_type", ""),
            "concentration_level": state.get("conc_level", ""),
            "fit_for_purpose": ffp[0] if ffp else "",
            "desalination_type": state.get("desal_type", ""),
        },
        "treatment_train": deepcopy(state.get("treatment_train", {})),
        "context": deepcopy(state.get("tea_context", {})),
        "feedwater_quality": deepcopy(state.get("feedwater_quality", {})),
        "unit_inputs": deepcopy(state.get("tea_unit_inputs", {})),
        "results": deepcopy(results),
        "run_signature": state.get("tea_results_signature", ""),
    }


def product_flow_m3_day(snapshot):
    results = snapshot["results"]
    value = float(results.get("final_product_flow", 0.0) or 0.0)
    if str(results.get("final_product_flow_unit", "m3/day")).lower() == "bbl/day":
        return value / BBL_PER_M3
    return value


def feed_lcow_per_bbl(snapshot):
    results = snapshot["results"]
    value = float(results.get("levelized_cost_of_water", 0.0) or 0.0)
    unit = str(results.get("levelized_cost_unit", "$/m3 feed")).lower()
    if "/m3" in unit:
        return value / BBL_PER_M3
    return value


def product_lcow_per_bbl(snapshot):
    results = snapshot["results"]
    operating_days = float(snapshot.get("context", {}).get("operating_days_per_year", 365.0) or 365.0)
    annual_product_bbl = product_flow_m3_day(snapshot) * BBL_PER_M3 * operating_days
    if annual_product_bbl <= 0.0:
        return 0.0
    return float(results.get("total_annual_cost", 0.0) or 0.0) / annual_product_bbl


def comparison_rows(snapshots):
    """Return normalized project-level comparison rows."""
    rows = []
    for snapshot in snapshots:
        results = snapshot["results"]
        context = snapshot.get("context", {})
        config = snapshot.get("configuration", {})
        rows.append({
            "Scenario": snapshot["name"],
            "Influent": config.get("influent_type", ""),
            "Concentration": config.get("concentration_level", ""),
            "Fit-for-purpose": config.get("fit_for_purpose", ""),
            "Desalination": config.get("desalination_type", ""),
            "Currency year": int(context.get("base_currency_year", 0) or 0),
            "Feed LCOW ($/bbl feed)": feed_lcow_per_bbl(snapshot),
            "Product LCOW ($/bbl product)": product_lcow_per_bbl(snapshot),
            "Total CAPEX (USD)": float(results.get("total_capital_cost", 0.0) or 0.0),
            "Annual OPEX (USD/year)": float(results.get("total_annual_operating_cost", 0.0) or 0.0),
            "Product flow (m3/day)": product_flow_m3_day(snapshot),
            "Electricity intensity (kWh/bbl feed)": float(results.get("electricity_intensity_kwh_per_bbl_feed", 0.0) or 0.0),
            "Thermal intensity (kWh/bbl feed)": float(results.get("thermal_energy_intensity_kwh_per_bbl_feed", 0.0) or 0.0),
        })
    return rows


def unit_cost_breakdown_rows(snapshots):
    """Return normalized unit-level LCOW contributions for charting/export."""
    rows = []
    for snapshot in snapshots:
        for unit in snapshot["results"].get("unit_results", []):
            capital = float(unit.get("capital_lcow_contribution", 0.0) or 0.0)
            operating = float(unit.get("opex_lcow_contribution", 0.0) or 0.0)
            contribution_unit = str(unit.get("capital_lcow_contribution_unit", "$/m3 feed")).lower()
            if "/m3" in contribution_unit:
                capital /= BBL_PER_M3
                operating /= BBL_PER_M3
            rows.extend([
                {
                    "Scenario": snapshot["name"],
                    "Unit process": unit.get("unit_process", ""),
                    "Cost type": "Annualized CAPEX",
                    "LCOW contribution ($/bbl feed)": capital,
                },
                {
                    "Scenario": snapshot["name"],
                    "Unit process": unit.get("unit_process", ""),
                    "Cost type": "OPEX",
                    "LCOW contribution ($/bbl feed)": operating,
                },
            ])
    return rows


def _quality_entry(entry):
    """Return a display-safe water-quality value and its reported unit."""
    if isinstance(entry, dict):
        value = entry.get("value")
        unit = str(entry.get("unit", "") or "").strip()
    else:
        value = entry
        unit = ""
    try:
        missing = value is None or bool(pd.isna(value))
    except (TypeError, ValueError):
        missing = value is None
    return ("" if missing else value), unit


def water_quality_for_snapshot(snapshot, stage):
    """Return influent or final product-water quality from a scenario snapshot."""
    results = snapshot.get("results", {})
    trace = results.get("water_quality_trace", []) or []

    if stage == "influent":
        feedwater = snapshot.get("feedwater_quality", {}) or {}
        if isinstance(feedwater, dict):
            quality = feedwater.get("water_quality")
            if isinstance(quality, dict) and quality:
                return quality
        if trace:
            quality = trace[0].get("water_quality", {}) or {}
            if isinstance(quality, dict):
                return quality
        return {}

    if stage != "effluent":
        raise ValueError("Water-quality stage must be 'influent' or 'effluent'.")

    # The TEA engine's trace contains feed and non-brine treatment outlets only,
    # so its final entry represents the final product-water node.
    if len(trace) > 1:
        quality = trace[-1].get("water_quality", {}) or {}
        if isinstance(quality, dict):
            return quality

    # Compatibility fallback for older saved results that predate the trace.
    units = sorted(
        results.get("unit_results", []) or [],
        key=lambda row: row.get("sequence", 0),
        reverse=True,
    )
    for unit in units:
        section = str(unit.get("section", ""))
        if section.startswith("Brine management") or section == "Extension":
            continue
        technical = unit.get("technical_results", {}) or {}
        quality = technical.get("water_quality_out")
        if isinstance(quality, dict):
            return quality
    return {}


def water_quality_comparison_rows(snapshots, stage):
    """Build a union-based wide table, leaving unreported scenario values blank."""
    scenario_qualities = [
        (snapshot["name"], water_quality_for_snapshot(snapshot, stage))
        for snapshot in snapshots
    ]
    parameters = []
    for _, quality in scenario_qualities:
        for parameter in quality:
            if parameter not in parameters:
                parameters.append(parameter)

    rows = []
    for parameter in parameters:
        entries = {}
        reported_units = []
        has_unspecified_unit = False
        for scenario_name, quality in scenario_qualities:
            if parameter not in quality:
                continue
            value, unit = _quality_entry(quality[parameter])
            entries[scenario_name] = (value, unit)
            if unit:
                if unit not in reported_units:
                    reported_units.append(unit)
            else:
                has_unspecified_unit = True

        # A missing unit can safely share the only reported unit. If scenarios
        # report conflicting units, keep separate rows instead of comparing raw
        # values with incompatible bases.
        if len(reported_units) <= 1:
            row_units = reported_units or [""]
        else:
            row_units = reported_units + (["Unspecified"] if has_unspecified_unit else [])

        for row_unit in row_units:
            row = {"Parameter": parameter, "Unit": row_unit}
            for scenario_name, _ in scenario_qualities:
                value_and_unit = entries.get(scenario_name)
                if value_and_unit is None:
                    row[scenario_name] = ""
                    continue
                value, actual_unit = value_and_unit
                if len(reported_units) <= 1:
                    row[scenario_name] = value
                elif actual_unit == row_unit or (not actual_unit and row_unit == "Unspecified"):
                    row[scenario_name] = value
                else:
                    row[scenario_name] = ""
            rows.append(row)
    return rows


def comparison_csv(snapshots):
    """Build a sectioned CSV for project, cost, and water-quality comparisons."""
    summary = pd.DataFrame(comparison_rows(snapshots))
    breakdown = pd.DataFrame(unit_cost_breakdown_rows(snapshots))
    influent_quality = pd.DataFrame(water_quality_comparison_rows(snapshots, "influent"))
    effluent_quality = pd.DataFrame(water_quality_comparison_rows(snapshots, "effluent"))
    output = "Scenario summary\n" + summary.to_csv(index=False)
    output += "\nUnit LCOW breakdown\n" + breakdown.to_csv(index=False)
    output += "\nInfluent water quality\n" + influent_quality.to_csv(index=False)
    output += "\nEffluent water quality\n" + effluent_quality.to_csv(index=False)
    return output.encode("utf-8")

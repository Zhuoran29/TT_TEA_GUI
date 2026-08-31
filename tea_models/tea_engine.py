"""Reusable treatment-train TEA calculation engine.

This module intentionally contains no Streamlit calls so the same calculation
can be used by the System Design page and by extension analyses.
"""

from importlib import import_module
import re

import pandas as pd

from tea_models.registry import model_key as unit_model_key
from tea_models.registry import run_cost_model, run_technical_model
from tea_models.water_quality import calculate_brine_quality, combine_streams, make_stream
from treatment_config import normalize_treatment_train_config


BBL_TO_M3 = 0.158987294928
M3_TO_BBL = 1 / BBL_TO_M3
HIDDEN_COST_OUTPUTS = {
    "bare_equipment_capital_cost",
    "bare_flow_capital_cost",
    "flow_capacity_equipment_capital_cost",
    "power_capacity_capital_cost",
    "land_capital_cost",
    "liner_capital_cost",
    "mvc_surrogate_capital_cost",
    "evaporator_capital_cost",
    "compressor_capital_cost",
}
HIDDEN_TECHNICAL_COST_OUTPUTS = {
    "evaporator_capex",
    "compressor_capex",
    "electricity_cost",
    "capex_opex_ratio",
    "surrogate_lcow_feed",
    "surrogate_lcow_permeate",
}
HIDDEN_UNIT_MODEL_TECHNICAL_OUTPUTS = {
    "chemical_dose",
    "regenerant_dose",
    "chemical_consumption",
    "constituent_removal_efficiency",
}


def ordered_units_from_train(train):
    """Flatten a treatment-train configuration into calculation order."""
    train = normalize_treatment_train_config(train)
    brine_units = train.get("brine", [])
    if isinstance(brine_units, str):
        brine_units = [brine_units]
    sections = [
        ("Pretreatment", train.get("pretreatment", [])),
        ("Desalination", train.get("desalination", [])),
        ("Post-treatment", train.get("posttreatment", [])),
        (f"Brine management - {train.get('brine_category', 'Brine management')}", brine_units),
    ]
    ordered_units = []
    sequence = 1
    for section, units in sections:
        for unit_process in units:
            if unit_process == "RO":
                unit_process = "BWRO"
            elif unit_process in {"MD", "VMD"}:
                unit_process = "Vacuum membrane distillation (VMD)"
            ordered_units.append({
                "sequence": sequence,
                "section": section,
                "unit_process": unit_process,
            })
            sequence += 1
    return ordered_units


def calculate_crf(discount_rate_percent, project_life_years):
    """Return the capital recovery factor matching Excel PMT rate logic."""
    project_life_years = max(float(project_life_years or 0.0), 1.0)
    rate = float(discount_rate_percent or 0.0) / 100.0
    if abs(rate) < 1e-12:
        return 1.0 / project_life_years
    factor = (1.0 + rate) ** project_life_years
    return rate * factor / (factor - 1.0)


def display_flow_value(flow_m3_day, display_unit):
    """Return flow in the same daily unit selected by the user."""
    if display_unit == "bbl/day":
        return float(flow_m3_day) * M3_TO_BBL
    return float(flow_m3_day)


def feed_lcow_unit(display_unit):
    """Return the LCOW unit for feed-volume normalization."""
    if display_unit == "bbl/day":
        return "$/bbl feed"
    return "$/m3 feed"


def empty_stream():
    """Return an empty stream for brine management when no waste has accumulated."""
    return {"flow_m3_day": 0.0, "water_quality": {}}


def table_to_input_dict(table):
    """Convert edited table rows into the dictionary expected by unit models."""
    values = {}
    cost_years = {}
    for _, row in table.iterrows():
        parameter = row.get("parameter")
        if not parameter:
            continue
        values[str(parameter)] = float(row.get("value", 0.0) or 0.0)
        unit = str(row.get("unit", "") or "")
        year_match = re.search(r"(?:USD_|\$\()(\d{4})", unit)
        if year_match:
            cost_years[str(parameter)] = int(year_match.group(1))
    if cost_years:
        values["_cost_years"] = cost_years
    return values


def result_value(result, name, default=0.0):
    """Read a numeric value from a model result entry with value/unit fields."""
    entry = result.get(name, {})
    if isinstance(entry, dict):
        return float(entry.get("value", default) or default)
    return float(entry or default)


def result_unit(result, name):
    """Read a unit string from a model result entry with value/unit fields."""
    entry = result.get(name, {})
    if isinstance(entry, dict):
        return entry.get("unit", "")
    return ""


def energy_basis_flow_m3_day(technical_result, intensity_unit):
    """Select the flow basis that matches an energy-intensity unit."""
    unit_text = str(intensity_unit or "").lower()
    if "product" in unit_text or "permeate" in unit_text:
        return result_value(technical_result, "outlet_flow")
    if "disposed" in unit_text:
        return result_value(
            technical_result,
            "disposed_flow",
            result_value(technical_result, "inlet_flow"),
        )
    return result_value(technical_result, "inlet_flow")


def unit_energy_summary(technical_result, intensity_name, train_feed_bbl_day):
    """Summarize unit energy use as daily energy, power, and train-feed intensity."""
    intensity = result_value(technical_result, intensity_name)
    intensity_unit = result_unit(technical_result, intensity_name)
    if intensity <= 0.0 or train_feed_bbl_day <= 0.0:
        return {
            "intensity": 0.0,
            "intensity_unit": intensity_unit,
            "energy_kwh_day": 0.0,
            "power_kw": 0.0,
            "kwh_per_bbl_feed": 0.0,
        }

    basis_flow_m3_day = energy_basis_flow_m3_day(technical_result, intensity_unit)
    energy_kwh_day = intensity * basis_flow_m3_day
    return {
        "intensity": intensity,
        "intensity_unit": intensity_unit,
        "energy_kwh_day": energy_kwh_day,
        "power_kw": energy_kwh_day / 24.0,
        "kwh_per_bbl_feed": energy_kwh_day / train_feed_bbl_day,
    }


def uses_default_technical_model(unit_process):
    """Return True when the registry would fall back to the default model."""
    module_name = f"tea_models.technical_models.{unit_model_key(unit_process)}"
    try:
        import_module(module_name)
        return False
    except ModuleNotFoundError as exc:
        if exc.name != module_name:
            return False

    try:
        generic_model = import_module("tea_models.technical_models.generic_unit_library")
    except ModuleNotFoundError:
        generic_model = None
    return not (generic_model is not None and generic_model.supports(unit_process))


def should_hide_model_result(unit_process, model_type, result_name):
    if model_type == "cost":
        return result_name in HIDDEN_COST_OUTPUTS
    if model_type != "technical":
        return False
    if result_name in HIDDEN_TECHNICAL_COST_OUTPUTS:
        return True
    if result_name in HIDDEN_UNIT_MODEL_TECHNICAL_OUTPUTS:
        return not uses_default_technical_model(unit_process)
    return False


def flatten_model_results(sequence, section, unit_process, model_type, model_results):
    """Convert nested model outputs into rows for results export."""
    rows = []
    for result_name, result in model_results.items():
        if should_hide_model_result(unit_process, model_type, result_name):
            continue
        if not isinstance(result, dict) or "value" not in result:
            continue
        rows.append({
            "sequence": sequence,
            "section": section,
            "unit_process": unit_process,
            "model_type": model_type,
            "result_name": result_name,
            "value": result.get("value"),
            "unit": result.get("unit", ""),
        })
    return rows


def build_results_csv_rows(results):
    """Create a long-form results table with units for download and export."""
    rows = []
    for unit_result in results["unit_results"]:
        rows.extend(flatten_model_results(
            unit_result["sequence"], unit_result["section"], unit_result["unit_process"],
            "technical", unit_result["technical_results"],
        ))
        rows.extend(flatten_model_results(
            unit_result["sequence"], unit_result["section"], unit_result["unit_process"],
            "cost", unit_result["cost_results"],
        ))

    project_rows = [
        ("total_capital_cost", results["total_capital_cost"], "USD"),
        ("annualized_capital_cost", results["annualized_capital_cost"], "USD/year"),
        ("total_annual_operating_cost", results["total_annual_operating_cost"], "USD/year"),
        ("total_annual_cost", results["total_annual_cost"], "USD/year"),
        ("final_product_flow", results["final_product_flow"], results["final_product_flow_unit"]),
        ("electricity_intensity", results.get("electricity_intensity_kwh_per_bbl_feed", 0.0), "kWh/bbl feed"),
        ("electricity_power_requirement", results.get("electricity_power_requirement_kw", 0.0), "kW"),
        ("thermal_energy_intensity", results.get("thermal_energy_intensity_kwh_per_bbl_feed", 0.0), "kWh/bbl feed"),
        ("thermal_power_requirement", results.get("thermal_power_requirement_kw", 0.0), "kW"),
        ("levelized_cost_of_water", results["levelized_cost_of_water"], results["levelized_cost_unit"]),
    ]
    for result_name, value, unit in project_rows:
        rows.append({
            "sequence": "", "section": "Project", "unit_process": "Overall system",
            "model_type": "project_summary", "result_name": result_name,
            "value": value, "unit": unit,
        })
    return rows


def transportation_extension_payload(context):
    payload = context.get("transportation_cost", {}) or {}
    try:
        annual_cost = float(payload.get("annual_transportation_cost", 0.0) or 0.0)
    except (TypeError, ValueError):
        annual_cost = 0.0
    payload["annual_transportation_cost"] = max(annual_cost, 0.0)
    return payload


def calculate_lcow(ordered_units, technical_tables, cost_tables, removal_tables, context, feedwater_quality):
    """Run the modular TEA calculation across all unit processes."""
    stream = make_stream(feedwater_quality, context["feed_flow_m3_day"])
    brine_stream = None
    water_quality_trace = [{
        "sequence": 0, "section": "Feedwater", "unit_process": "Feedwater",
        "flow_m3_day": stream["flow_m3_day"],
        "water_quality": stream.get("water_quality", {}),
    }]
    unit_results = []
    total_capital_cost = 0.0
    total_annual_operating_cost = 0.0
    total_electricity_kwh_day = 0.0
    total_thermal_kwh_day = 0.0
    crf = float(context["capital_recovery_factor"])
    train_feed_bbl_day = max(float(context.get("feed_flow_bbl_day", 0.0) or 0.0), 1e-9)

    for unit in ordered_units:
        unit_process = unit["unit_process"]
        is_brine_management = unit["section"].startswith("Brine management")
        technical_inputs = table_to_input_dict(technical_tables[unit["sequence"]])
        technical_inputs["removal_efficiencies"] = removal_tables.get(unit["sequence"], {})
        cost_inputs = table_to_input_dict(cost_tables[unit["sequence"]])
        model_stream = (
            brine_stream if is_brine_management and brine_stream is not None
            else empty_stream() if is_brine_management else stream
        )
        technical_result = run_technical_model(unit_process, technical_inputs, model_stream)
        cost_result = run_cost_model(unit_process, technical_result, cost_inputs, context)

        capital_cost = result_value(cost_result, "installed_capital_cost")
        annualized_capital_cost = capital_cost * crf
        annual_operating_cost = result_value(cost_result, "total_annual_operating_cost")
        outlet_flow = result_value(technical_result, "outlet_flow")
        electricity_summary = unit_energy_summary(technical_result, "energy_intensity", train_feed_bbl_day)
        thermal_summary = unit_energy_summary(technical_result, "thermal_energy_intensity", train_feed_bbl_day)
        total_electricity_kwh_day += electricity_summary["energy_kwh_day"]
        total_thermal_kwh_day += thermal_summary["energy_kwh_day"]
        total_capital_cost += capital_cost
        total_annual_operating_cost += annual_operating_cost

        brine_flow = result_value(technical_result, "brine_flow")
        if brine_flow > 0.0 and not is_brine_management:
            brine_quality = technical_result.get("brine_water_quality")
            if not brine_quality:
                brine_quality = calculate_brine_quality(
                    technical_result.get("water_quality_in", {}),
                    technical_result.get("water_quality_out", {}),
                    result_value(technical_result, "inlet_flow"), outlet_flow, brine_flow,
                )
            brine_stream = combine_streams(brine_stream, {
                "flow_m3_day": brine_flow, "water_quality": brine_quality,
            })
            technical_result["brine_water_quality"] = brine_quality
        if is_brine_management:
            brine_stream = technical_result.get("outlet_stream", {
                "flow_m3_day": outlet_flow, "water_quality": {},
            })
        else:
            stream = technical_result.get("outlet_stream", {
                "flow_m3_day": outlet_flow, "water_quality": stream.get("water_quality", {}),
            })
            water_quality_trace.append({
                "sequence": unit["sequence"], "section": unit["section"],
                "unit_process": unit_process, "flow_m3_day": outlet_flow,
                "water_quality": technical_result.get("water_quality_out", {}),
            })

        unit_results.append({
            "sequence": unit["sequence"], "section": unit["section"], "unit_process": unit_process,
            "inlet_flow": result_value(technical_result, "inlet_flow"),
            "inlet_flow_unit": result_unit(technical_result, "inlet_flow"),
            "outlet_flow": outlet_flow, "outlet_flow_unit": result_unit(technical_result, "outlet_flow"),
            "water_recovery": result_value(technical_result, "water_recovery"),
            "water_recovery_unit": result_unit(technical_result, "water_recovery"),
            "energy_intensity": result_value(technical_result, "energy_intensity"),
            "energy_intensity_unit": result_unit(technical_result, "energy_intensity"),
            "electricity_consumption_kwh_day": electricity_summary["energy_kwh_day"],
            "electricity_intensity_kwh_per_bbl_feed": electricity_summary["kwh_per_bbl_feed"],
            "electricity_power_requirement_kw": electricity_summary["power_kw"],
            "thermal_energy_consumption_kwh_day": thermal_summary["energy_kwh_day"],
            "thermal_energy_intensity_kwh_per_bbl_feed": thermal_summary["kwh_per_bbl_feed"],
            "thermal_power_requirement_kw": thermal_summary["power_kw"],
            "installed_capital_cost": capital_cost,
            "installed_capital_cost_unit": result_unit(cost_result, "installed_capital_cost"),
            "annualized_capital_cost": annualized_capital_cost, "annualized_capital_cost_unit": "USD/year",
            "total_annual_operating_cost": annual_operating_cost,
            "total_annual_operating_cost_unit": result_unit(cost_result, "total_annual_operating_cost"),
            "technical_results": technical_result, "cost_results": cost_result,
        })

    operating_days = float(context["operating_days_per_year"])
    flow_display_unit = context.get("feed_flow_display_unit", "m3/day")
    annual_feed_volume = (
        float(context["feed_flow_bbl_day"]) * operating_days
        if flow_display_unit == "bbl/day"
        else float(context["feed_flow_m3_day"]) * operating_days
    )
    transportation_cost = transportation_extension_payload(context)
    annual_transportation_cost = transportation_cost["annual_transportation_cost"]
    if annual_transportation_cost > 0.0:
        total_annual_operating_cost += annual_transportation_cost
        unit_results.append({
            "sequence": len(unit_results) + 1, "section": "Extension", "unit_process": "Transportation",
            "inlet_flow": 0.0, "inlet_flow_unit": "", "outlet_flow": 0.0, "outlet_flow_unit": "",
            "water_recovery": 0.0, "water_recovery_unit": "", "energy_intensity": 0.0,
            "energy_intensity_unit": "", "electricity_consumption_kwh_day": 0.0,
            "electricity_intensity_kwh_per_bbl_feed": 0.0, "electricity_power_requirement_kw": 0.0,
            "thermal_energy_consumption_kwh_day": 0.0, "thermal_energy_intensity_kwh_per_bbl_feed": 0.0,
            "thermal_power_requirement_kw": 0.0, "installed_capital_cost": 0.0,
            "installed_capital_cost_unit": "USD", "annualized_capital_cost": 0.0,
            "annualized_capital_cost_unit": "USD/year",
            "total_annual_operating_cost": annual_transportation_cost,
            "total_annual_operating_cost_unit": "USD/year",
            "technical_results": {
                "distance_miles": {"value": float(transportation_cost.get("distance_miles", 0.0) or 0.0), "unit": "mile"},
                "transported_volume": {
                    "value": float(transportation_cost.get("annual_transported_volume_bbl", transportation_cost.get("transported_volume_bbl_day", 0.0)) or 0.0),
                    "unit": "bbl/year" if "annual_transported_volume_bbl" in transportation_cost else "bbl/day",
                },
            },
            "cost_results": {
                "cost_per_bbl_mile": {"value": float(transportation_cost.get("cost_per_bbl_mile", 0.0) or 0.0), "unit": "$/bbl-mile"},
                "total_annual_operating_cost": {"value": annual_transportation_cost, "unit": "USD/year"},
            },
        })

    annualized_capital_cost = total_capital_cost * crf
    total_annual_cost = annualized_capital_cost + total_annual_operating_cost
    annual_feed_volume = max(annual_feed_volume, 1e-9)
    lcow = total_annual_cost / annual_feed_volume
    for unit_result in unit_results:
        unit_result["capital_lcow_contribution"] = unit_result["annualized_capital_cost"] / annual_feed_volume
        unit_result["capital_lcow_contribution_unit"] = feed_lcow_unit(flow_display_unit)
        unit_result["opex_lcow_contribution"] = unit_result["total_annual_operating_cost"] / annual_feed_volume
        unit_result["opex_lcow_contribution_unit"] = feed_lcow_unit(flow_display_unit)

    results = {
        "total_capital_cost": total_capital_cost,
        "annualized_capital_cost": annualized_capital_cost,
        "total_annual_operating_cost": total_annual_operating_cost,
        "total_annual_cost": total_annual_cost,
        "final_product_flow": display_flow_value(stream["flow_m3_day"], flow_display_unit),
        "final_product_flow_unit": flow_display_unit,
        "electricity_intensity_kwh_per_bbl_feed": total_electricity_kwh_day / train_feed_bbl_day,
        "electricity_power_requirement_kw": total_electricity_kwh_day / 24.0,
        "thermal_energy_intensity_kwh_per_bbl_feed": total_thermal_kwh_day / train_feed_bbl_day,
        "thermal_power_requirement_kw": total_thermal_kwh_day / 24.0,
        "levelized_cost_of_water": lcow,
        "levelized_cost_unit": feed_lcow_unit(flow_display_unit),
        "unit_results": unit_results,
        "water_quality_trace": water_quality_trace,
        "transportation_cost": transportation_cost,
    }
    results["results_csv_rows"] = build_results_csv_rows(results)
    return results


def input_records_to_tables(input_records):
    """Rebuild calculation tables stored in a session-safe records payload."""
    return {
        int(sequence): pd.DataFrame(rows)
        for sequence, rows in (input_records or {}).items()
    }

"""LSRRO technical model (NMSU LSRRO model with a WaterTAP design table).

Recovery (NMSU assumptions, SI Eq. B5-1, fit to WaterTAP PBSE design points):
  R(%) = -0.0002 TDS^2 - 0.3816 TDS + 84.01 - 3.69e-4 Hardness - 1e-4 Silica      TDS in g/L
  used when the recovery input is 0; a positive input overrides it.
Energy and design (WaterTAP LSRRO flowsheet, Atia et al. 2023, lowest-LCOW design per point):
  SEC (kWh/m3 product, net of energy recovery), membrane area and equipment costs are interpolated in
  feed TDS and recovery from data/model_tables/lsrro_watertap_table.csv, between designs with the same
  stage count (lsrro_core.lookup_design).
  energy = SEC x recovery                                                         kWh/m3 feed
Permeate quality: NMSU regression and average-removal model (lsrro_core.predict_water_quality).
"""

from __future__ import annotations

from tea_models.lsrro_core import (
    calculate_recovery_fraction,
    lookup_design,
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
    calculated_recovery, warnings = calculate_recovery_fraction(water_quality_in)
    recovery_input = _number(technical_inputs, "recovery", 0.0)
    if recovery_input > 0.0:
        recovery = min(max(recovery_input, 0.01), 0.90)
        recovery_basis = "manual input"
    else:
        recovery = calculated_recovery
        recovery_basis = "recovery correlation"

    outlet_flow = inlet_flow * recovery
    brine_flow = max(inlet_flow - outlet_flow, 0.0)

    clip_negative = _number(technical_inputs, "clip_negative_permeate", 1.0) >= 0.5
    water_quality_out, removal_efficiencies, prediction_methods = predict_water_quality(
        water_quality_in,
        clip_negative,
    )
    brine_quality = calculate_brine_quality(
        water_quality_in,
        water_quality_out,
        inlet_flow,
        outlet_flow,
        brine_flow,
    )

    feed_tds_g_l = tds_mg_l(water_quality_in) / 1000.0
    design, design_warnings = lookup_design(feed_tds_g_l, recovery)
    warnings = list(warnings) + design_warnings
    sec_product = design["sec_kwh_m3_product"]
    energy_intensity = sec_product * recovery

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "recovery_basis": _result(recovery_basis, ""),
        "calculated_recovery": _result(calculated_recovery, "fraction"),
        "feed_tds": _result(feed_tds_g_l, "g/L"),
        "number_of_stages": _result(int(round(design["stages"])), "count"),
        "specific_energy_consumption": _result(sec_product, "kWh/m3 product"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "thermal_energy_intensity": _result(0.0, "kWh/m3 feed"),
        "membrane_area": _result(design["membrane_area_m2_per_m3d_product"] * outlet_flow, "m2"),
        "membrane_equipment_cost_per_feed": _result(design["membrane_capex_usd_per_m3d_feed"], "$(2018)/(m3/day feed)"),
        "pump_equipment_cost_per_feed": _result(design["pump_capex_usd_per_m3d_feed"], "$(2018)/(m3/day feed)"),
        "erd_equipment_cost_per_feed": _result(design["erd_capex_usd_per_m3d_feed"], "$(2018)/(m3/day feed)"),
        "membrane_replacement_per_feed": _result(design["membrane_replacement_usd_yr_per_m3d_feed"], "$(2018)/yr per (m3/day feed)"),
        "removal_efficiencies": removal_efficiencies,
        "prediction_methods": prediction_methods,
        "water_quality_in": water_quality_in,
        "water_quality_out": water_quality_out,
        "brine_water_quality": brine_quality,
        "outlet_stream": {"flow_m3_day": outlet_flow, "water_quality": water_quality_out},
        "model_warnings": _result(warnings, ""),
    }

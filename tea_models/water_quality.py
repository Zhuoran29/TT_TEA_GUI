from __future__ import annotations

import copy

import pandas as pd

from treatment_config import ALL_WATER_QUALITY_PARAMS, UNIT_REMOVAL_RATES


BBL_TO_M3 = 0.158987294928
EXCLUDED_AUTO_QUALITY_PARAMETERS = {"SAR"}

PARAM_TO_SIDEBAR_KEY = {
    "pH": "wq_ph",
    "Oil": "wq_oil",
    "Conductivity": "wq_conductivity",
    "TDS": "wq_tds",
    "TSS": "wq_tss",
    "Turbidity": "wq_turbidity",
    "Hardness": "wq_hardness",
    "Alkalinity": "wq_alk",
    "TOC": "wq_toc",
    "BOD": "wq_bod",
    "Ammonia nitrogen": "wq_nh4",
    "Boron": "wq_boron",
    "Sodium": "wq_sodium",
    "Chloride": "wq_chloride",
    "Silica": "wq_silica",
    "Iron": "wq_iron",
    "Magnesium": "wq_magnesium",
    "Manganese": "wq_manganese",
    "Calcium": "wq_calcium",
    "Barium": "wq_barium",
    "Lithium": "wq_lithium",
    "Strontium": "wq_strontium",
    "Sulfate": "wq_sulfate",
    "Bicarbonate": "wq_bicarbonate",
    "Fluoride": "wq_fluoride",
    "Uranium": "wq_uranium",
    "SAR": "wq_sar",
    "Selenium": "wq_selenium",
    "BTEX": "wq_btex",
    "PAHs": "wq_pahs",
    "Gross Alpha": "wq_gross_alpha",
    "Gross Beta": "wq_gross_beta",
    "Radium-226": "wq_radium_226",
    "Radium-228": "wq_radium_228",
}


def parse_removal_rate(rate):
    """Parse config removal rates and use the midpoint for ranges."""
    if rate in (None, ""):
        return 0.0
    if isinstance(rate, (int, float)):
        value = float(rate)
        return max(0.0, min(value if value <= 1.0 else value / 100.0, 1.0))

    text = str(rate).strip().replace("+", "")
    if not text or text == "0%":
        return 0.0

    if "%" in text:
        numbers = []
        for part in text.replace("%", "").split("-"):
            try:
                numbers.append(float(part.strip()))
            except ValueError:
                continue
        if numbers:
            return max(0.0, min((sum(numbers) / len(numbers)) / 100.0, 1.0))

    try:
        value = float(text)
    except ValueError:
        return 0.0
    return max(0.0, min(value if value <= 1.0 else value / 100.0, 1.0))


def parse_ph_target(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def collect_feedwater_quality(session_state, current_parameters=None):
    """Build the feedwater quality object from page 02 sidebar inputs."""
    if current_parameters is None:
        current_parameters = session_state.get("feedwater_quality_params", [])

    quality = {}
    for parameter in current_parameters:
        if parameter in EXCLUDED_AUTO_QUALITY_PARAMETERS:
            continue
        sidebar_key = PARAM_TO_SIDEBAR_KEY.get(parameter)
        additional_key = f"additional_input_{parameter}".replace(" ", "_")
        value = None
        if sidebar_key and sidebar_key in session_state:
            value = session_state.get(sidebar_key)
        elif additional_key in session_state:
            value = session_state.get(additional_key)

        if value is None:
            continue

        info = ALL_WATER_QUALITY_PARAMS.get(parameter, {})
        quality[parameter] = {
            "value": float(value or 0.0),
            "unit": info.get("unit", ""),
        }

    return {
        "flow": {
            "value": float(session_state.get("wq_flow", 1000.0) or 0.0),
            "unit": "bbl/day",
        },
        "water_quality": quality,
    }


def make_stream(feedwater_quality, feed_flow_m3_day=None):
    """Create the technical-model stream object from feedwater quality."""
    flow_bbl_day = float(feedwater_quality.get("flow", {}).get("value", 0.0) or 0.0)
    if feed_flow_m3_day is None:
        feed_flow_m3_day = flow_bbl_day * BBL_TO_M3
    return {
        "flow_m3_day": float(feed_flow_m3_day or 0.0),
        "water_quality": copy.deepcopy(feedwater_quality.get("water_quality", {})),
    }


def get_default_removal_efficiencies(unit_process, quality):
    """Return defaults for the currently tracked water-quality parameters."""
    unit_rates = UNIT_REMOVAL_RATES.get(unit_process, {})
    defaults = {}
    for parameter in quality:
        if parameter in EXCLUDED_AUTO_QUALITY_PARAMETERS:
            continue
        if parameter == "pH" and parameter in unit_rates:
            ph_target = parse_ph_target(unit_rates.get(parameter))
            defaults[parameter] = ph_target if ph_target is not None else None
        else:
            defaults[parameter] = parse_removal_rate(unit_rates.get(parameter, 0.0))
    return defaults


def apply_removal_overrides(defaults, overrides):
    merged = defaults.copy()
    for parameter, value in (overrides or {}).items():
        try:
            merged[parameter] = max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            continue
    return merged


def apply_unit_water_quality(stream, recovery, removal_efficiencies, target_values=None):
    """Propagate flow and water quality through a unit process."""
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    recovery = max(0.0, min(float(recovery or 0.0), 1.0))
    outlet_flow = inlet_flow * recovery
    brine_flow = max(inlet_flow - outlet_flow, 0.0)

    inlet_quality = copy.deepcopy(stream.get("water_quality", {}))
    outlet_quality = copy.deepcopy(inlet_quality)
    target_values = target_values or {}

    for parameter, entry in inlet_quality.items():
        value = float(entry.get("value", 0.0) or 0.0)
        unit = entry.get("unit", ALL_WATER_QUALITY_PARAMS.get(parameter, {}).get("unit", ""))
        if parameter in target_values and target_values[parameter] not in (None, ""):
            outlet_value = float(target_values[parameter])
        elif parameter == "pH" and parameter in removal_efficiencies:
            ph_target = parse_ph_target(removal_efficiencies.get(parameter))
            outlet_value = ph_target if ph_target is not None else value
        else:
            removal = max(0.0, min(float(removal_efficiencies.get(parameter, 0.0) or 0.0), 1.0))
            outlet_value = value * (1.0 - removal)
        outlet_quality[parameter] = {"value": outlet_value, "unit": unit}

    outlet_stream = {
        "flow_m3_day": outlet_flow,
        "water_quality": outlet_quality,
    }
    return inlet_flow, outlet_flow, brine_flow, inlet_quality, outlet_quality, outlet_stream


def calculate_brine_quality(inlet_quality, outlet_quality, inlet_flow, outlet_flow, brine_flow):
    """Estimate brine-side water quality by constituent mass balance."""
    brine_quality = {}
    if brine_flow <= 0.0:
        return brine_quality

    for parameter, inlet_entry in (inlet_quality or {}).items():
        unit = inlet_entry.get("unit", ALL_WATER_QUALITY_PARAMS.get(parameter, {}).get("unit", ""))
        if parameter == "pH":
            brine_quality[parameter] = {"value": 8.5, "unit": unit}
            continue

        try:
            inlet_value = float(inlet_entry.get("value", 0.0) or 0.0)
            outlet_value = float(
                (outlet_quality or {}).get(parameter, {}).get("value", inlet_value) or 0.0
            )
        except (TypeError, ValueError):
            continue

        brine_value = (inlet_value * inlet_flow - outlet_value * outlet_flow) / brine_flow
        brine_quality[parameter] = {"value": max(brine_value, 0.0), "unit": unit}

    return brine_quality


def combine_streams(*streams):
    """Combine streams with flow-weighted water quality."""
    combined_flow = 0.0
    weighted_quality = {}
    quality_units = {}

    for stream in streams:
        if not stream:
            continue
        try:
            flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
        except (TypeError, ValueError):
            flow = 0.0
        if flow <= 0.0:
            continue

        combined_flow += flow
        for parameter, entry in (stream.get("water_quality", {}) or {}).items():
            try:
                value = float(entry.get("value", 0.0) or 0.0)
            except (TypeError, ValueError):
                continue
            weighted_quality[parameter] = weighted_quality.get(parameter, 0.0) + value * flow
            quality_units.setdefault(
                parameter,
                entry.get("unit", ALL_WATER_QUALITY_PARAMS.get(parameter, {}).get("unit", "")),
            )

    combined_quality = {}
    if combined_flow > 0.0:
        combined_quality = {
            parameter: {
                "value": value_sum / combined_flow,
                "unit": quality_units.get(parameter, ""),
            }
            for parameter, value_sum in weighted_quality.items()
        }

    return {
        "flow_m3_day": combined_flow,
        "water_quality": combined_quality,
    }


def water_quality_comparison_table(inlet_quality, outlet_quality, removal_efficiencies):
    rows = []
    parameters = list(outlet_quality.keys())
    for parameter in parameters:
        inlet = inlet_quality.get(parameter, {})
        outlet = outlet_quality.get(parameter, {})
        rows.append({
            "parameter": parameter,
            "inlet_value": inlet.get("value"),
            "outlet_value": outlet.get("value"),
            "unit": outlet.get("unit", inlet.get("unit", "")),
            "removal_efficiency": removal_efficiencies.get(parameter, 0.0),
        })
    return pd.DataFrame(rows)

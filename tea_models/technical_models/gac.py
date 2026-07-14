"""Granular activated carbon model based on feed TOC and breakthrough BV."""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "gac",
    "recovery": 0.995,
    "energy_intensity": 0.14,
    "chemical_dose": 0.0,
    "empty_bed_contact_time": 10.0,
    "media_bulk_density": 450.0,
}

BV_COEFFICIENT = 7490.624141766438
BV_EXPONENT = -0.18445203043163802


def _result(value, unit):
    return {"value": value, "unit": unit}


def _quality_value(quality, parameter, default=0.0):
    try:
        return float((quality.get(parameter, {}) or {}).get("value", default) or default)
    except (TypeError, ValueError):
        return float(default)


def run(unit_process, technical_inputs, stream):
    outputs = run_template(unit_process, technical_inputs, stream, DEFAULTS)
    outputs["energy_intensity"]["unit"] = "kWh/m3 feed"
    inlet_toc = _quality_value(outputs["water_quality_in"], "TOC")
    outlet_toc = _quality_value(outputs["water_quality_out"], "TOC", inlet_toc)
    toc_removal = (
        max(min(1.0 - outlet_toc / inlet_toc, 1.0), 0.0)
        if inlet_toc > 0.0
        else 0.0
    )
    breakthrough_bv = (
        BV_COEFFICIENT * inlet_toc**BV_EXPONENT if inlet_toc > 0.0 else 0.0
    )
    media_inventory = float(outputs["media_inventory"]["value"] or 0.0)
    inlet_flow = float(outputs["inlet_flow"]["value"] or 0.0)
    changeout_days = (
        breakthrough_bv * media_inventory
        / max(float(outputs["media_bulk_density"]["value"]), 1e-12)
        / inlet_flow
        if breakthrough_bv > 0.0 and inlet_flow > 0.0
        else 0.0
    )
    outputs.update({
        "feed_toc": _result(inlet_toc, "mg/L"),
        "outlet_toc": _result(outlet_toc, "mg/L"),
        "toc_removal": _result(toc_removal, "fraction"),
        "breakthrough_bed_volumes": _result(breakthrough_bv, "bed volumes"),
        "estimated_changeout_interval": _result(changeout_days, "day"),
        "model_warnings": _result(
            ["Feed TOC is unavailable; TOC-dependent media and disposal OPEX will be zero."]
            if inlet_toc <= 0.0
            else (
                []
                if 1.0 <= inlet_toc <= 250.0
                else ["Feed TOC is outside the source correlation range of 1--250 mg/L."]
            ),
            "",
        ),
    })
    return outputs

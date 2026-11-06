"""Data payload for the Treatment Train Explorer dialog.

Everything the explorer shows is read from the app's own configuration and
models; nothing here runs the TEA engine.  Removal efficiencies follow
``tea_models.water_quality.get_default_removal_efficiencies`` (table midpoints,
LSRRO regression, DAF TOC from the feed-iron H2O2 dose).
"""

from __future__ import annotations

import csv
import importlib
from functools import lru_cache
from pathlib import Path

from treatment_config import UNIT_REMOVAL_RATES
from tea_models.lsrro_core import AVERAGE_REMOVALS, REGRESSION_MODELS, predict_permeate
from tea_models.registry import model_key
from tea_models.water_quality import parse_removal_rate

from . import rules as _rules
from .rules import CROSS_STAGE_UNITS, OPERATIONAL_RULES, UNIT_DISPLAY

ROOT = Path(__file__).resolve().parents[1]
TECHNICAL_MODEL_DIR = ROOT / "tea_models" / "technical_models"
NON_UNIT_MODULES = {"default", "generic_unit_library", "template_units", "helper_function", "__init__"}
MAIN_STAGES = ("pretreatment", "desalination", "posttreatment")


def has_technical_model(unit):
    """True when the unit has its own file in tea_models/technical_models."""
    key = model_key(unit)
    return key not in NON_UNIT_MODULES and (TECHNICAL_MODEL_DIR / f"{key}.py").exists()


def display_unit_name(unit):
    if unit == "Vacuum membrane distillation (VMD)":
        return "VMD"
    return unit


def _parse_rate(raw):
    """Return (kind, default, low, high) for one UNIT_REMOVAL_RATES entry."""
    text = str(raw).strip()
    if text.lower().startswith("regression"):
        return "regression", None, None, None
    if "%" not in text:
        try:
            return "ph", float(text), None, None
        except ValueError:
            return "unknown", 0.0, None, None
    default = parse_removal_rate(text)
    numbers = []
    for part in text.replace("%", "").replace("+", "").split("-"):
        try:
            numbers.append(float(part.strip()) / 100.0)
        except ValueError:
            pass
    if "+" in text and numbers:
        return "plus", default, numbers[0], 1.0
    if len(numbers) >= 2:
        return "range", default, numbers[0], numbers[1]
    return "fixed", default, default, default


@lru_cache(maxsize=1)
def _default_recoveries():
    recoveries = {"DEFAULT": 0.95}
    path = ROOT / "data" / "input_tables" / "technical_inputs.csv"
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("parameter") != "recovery":
                    continue
                try:
                    recoveries[row.get("unit_process", "DEFAULT")] = float(row.get("value", 0.95))
                except (TypeError, ValueError):
                    continue
    except OSError:
        pass
    return recoveries


def default_recovery(unit):
    recoveries = _default_recoveries()
    return max(0.0, min(recoveries.get(unit, recoveries.get("DEFAULT", 0.95)), 0.999999))


def _unit_record(unit):
    display = UNIT_DISPLAY.get(unit, {})
    removals = {}
    ph_target = None
    for parameter, raw in UNIT_REMOVAL_RATES.get(unit, {}).items():
        kind, default, low, high = _parse_rate(raw)
        if kind == "ph":
            ph_target = default
            continue
        removals[parameter] = {"raw": str(raw), "kind": kind, "default": default, "low": low, "high": high}
    return {
        "name": unit,
        "label": display_unit_name(unit),
        "mech": display.get("mech", "dose"),
        "path": display.get("path", "brine"),
        "residual": display.get("residual", ""),
        "note": display.get("note", ""),
        "recovery": default_recovery(unit),
        "ph_target": ph_target,
        "has_model": has_technical_model(unit),
        "has_data": unit in UNIT_REMOVAL_RATES,
        "removals": removals,
    }


def _daf_toc_table():
    """DAF TOC removal vs. DAF feed iron, from the DAF model (H2O2 dose set by iron)."""
    try:
        from tea_models.technical_models.daf import calculated_toc_removal
    except Exception:
        return None
    grid = [0.0] + [10 ** (k / 8.0) for k in range(-16, 25)]   # 0.01 .. 1000 mg/L
    return [[fe, float(calculated_toc_removal({"Iron": {"value": fe, "unit": "mg/L"}}))] for fe in grid]


def unit_removal(unit, parameter, concentration, quality):
    """Python mirror of the explorer's removal rule (used for the scaling check)."""
    if unit == "LSRRO":
        outlet, _method = predict_permeate(parameter, float(concentration))
        return 1.0 - max(outlet, 0.0) / concentration if concentration else 0.0
    if unit == "DAF" and parameter == "TOC":
        try:
            from tea_models.technical_models.daf import calculated_toc_removal
            return float(calculated_toc_removal({"Iron": {"value": quality.get("Iron", 0.0)}}))
        except Exception:
            pass
    return parse_removal_rate(UNIT_REMOVAL_RATES.get(unit, {}).get(parameter, 0.0))


def _propagate(units, feed, feed_ph):
    """Concentration and pH entering each unit, plus final product."""
    states = [(dict(feed), feed_ph)]
    quality, ph = dict(feed), feed_ph
    for unit in units:
        outlet = {}
        for parameter, value in quality.items():
            outlet[parameter] = value * (1.0 - unit_removal(unit, parameter, value, quality))
        target = _unit_record(unit)["ph_target"]
        quality, ph = outlet, (target if target is not None else ph)
        states.append((dict(quality), ph))
    return states


@lru_cache(maxsize=64)
def _scaling_cached(items, ph):
    from tea_models.scaling_tendency import calculate_scaling_tendency

    quality = {name: {"value": value, "unit": "mg/L"} for name, value in items}
    if ph is not None:
        quality["pH"] = {"value": ph, "unit": "-"}
    result = calculate_scaling_tendency(quality)
    likely, near = [], []
    for mineral in result.get("minerals", []):
        row = {"mineral": mineral.get("mineral"), "omega": mineral.get("scaling_tendency"), "si": mineral.get("saturation_index")}
        if mineral.get("tendency") == "Scaling likely":
            likely.append(row)
        elif mineral.get("tendency") == "Near saturation":
            near.append(row)
    return likely, near


def scaling_check(train, feed, feed_ph):
    """Reaktoro scaling tendency of each desalination unit's concentrate/brine.

    Uses tea_models.scaling_tendency.calculate_scaling_tendency (Pitzer, 25 C,
    1 atm), the same function System Design applies to unit outlets.  The
    concentrate composition comes from a mass balance with the unit's default
    recovery: C_brine = (C_in - R * C_out) / (1 - R).
    """
    units = [u for stage in MAIN_STAGES for u in train.get(stage, [])]
    desal_positions = {len(train.get("pretreatment", [])) + i for i in range(len(train.get("desalination", [])))}
    states = _propagate(units, feed, feed_ph)
    rows = []
    for index, unit in enumerate(units):
        if index not in desal_positions or UNIT_DISPLAY.get(unit, {}).get("mech") not in {"membrane", "thermal"}:
            continue
        recovery = default_recovery(unit)
        (c_in, ph_in), (c_out, _ph_out) = states[index], states[index + 1]
        brine = {}
        for parameter, value in c_in.items():
            if recovery >= 1.0:
                continue
            brine[parameter] = max((value - recovery * c_out.get(parameter, 0.0)) / (1.0 - recovery), 0.0)
        row = {"position": index + 1, "unit": unit, "recovery": recovery}
        try:
            likely, near = _scaling_cached(tuple(sorted((k, round(v, 6)) for k, v in brine.items())), ph_in)
            row.update({"likely": likely, "near": near})
        except Exception as exc:  # Reaktoro missing or solver failure
            row["error"] = f"{type(exc).__name__}: {exc}"[:240]
        rows.append(row)
    return {"train": units, "rows": rows}


def build_payload(
    *,
    current_train,
    stage_options,
    brine_options,
    feed,
    feed_ph,
    targets,
    scenario,
    param_units,
    removal_overrides=None,
):
    """Assemble the JSON payload injected into template.html.

    current_train: {"pretreatment": [...], "desalination": [...], "posttreatment": [...],
                    "brine": [...], "brine_category": "..."} from st.session_state.
    stage_options: {"pretreatment": [...], "desalination": [...], "posttreatment": [...]} (page 02 lists).
    brine_options: BRINE_MANAGEMENT_OPTIONS.
    feed: {parameter: value} feed water quality (pH excluded); feed_ph: float or None.
    targets: {parameter: {"limit": x} | {"range": [lo, hi]}, "unit": ...} with page 02 overrides applied.
    removal_overrides: st.session_state.unit_removal_overrides from System Design,
                       {"<sequence>": {parameter: fraction}}; sequence counts from 1 across all stages.
    """
    # Re-read rules.py on every open so edits to it apply without restarting Streamlit.
    global CROSS_STAGE_UNITS, OPERATIONAL_RULES, UNIT_DISPLAY
    importlib.reload(_rules)
    CROSS_STAGE_UNITS, OPERATIONAL_RULES, UNIT_DISPLAY = _rules.CROSS_STAGE_UNITS, _rules.OPERATIONAL_RULES, _rules.UNIT_DISPLAY
    library = {
        stage: [u for u in stage_options.get(stage, []) if has_technical_model(u)]
        for stage in MAIN_STAGES
    }
    library["brine"] = [
        u for units in brine_options.values() for u in units if has_technical_model(u)
    ]
    library["brine"] = list(dict.fromkeys(library["brine"]))
    for stage, units in getattr(_rules, "EXTRA_LIBRARY_UNITS", {}).items():
        for unit in units:
            if unit not in library.get(stage, []):
                library.setdefault(stage, []).append(unit)
    for unit, stages in CROSS_STAGE_UNITS.items():
        if has_technical_model(unit):
            for stage in stages:
                if unit not in library[stage]:
                    library[stage].append(unit)

    allowed = {}
    for stage, units in library.items():
        for unit in units:
            allowed.setdefault(unit, []).append(stage)

    train = {stage: list(current_train.get(stage, []) or []) for stage in (*MAIN_STAGES, "brine")}
    for stage, units in train.items():          # units already in the train stay movable in their stage
        for unit in units:
            allowed.setdefault(unit, [])
            if stage not in allowed[unit]:
                allowed[unit].append(stage)

    all_units = sorted(allowed)
    return {
        "scenario": scenario,
        "params": param_units,
        "library": library,
        "allowed": allowed,
        "units": {u: _unit_record(u) for u in all_units},
        "train": train,
        "brine_category": current_train.get("brine_category", ""),
        "feed": feed,
        "feed_ph": feed_ph,
        "targets": targets,
        "lsrro": {"regression": REGRESSION_MODELS, "average": AVERAGE_REMOVALS},
        "daf_toc": _daf_toc_table(),
        "rules": OPERATIONAL_RULES,
        "literature": getattr(_rules, "LITERATURE_REMOVALS", []),
        "scaling": scaling_check(train, feed, feed_ph),
        "removal_overrides": {
            str(k): {p: float(v) for p, v in (vals or {}).items()}
            for k, vals in (removal_overrides or {}).items()
        },
    }

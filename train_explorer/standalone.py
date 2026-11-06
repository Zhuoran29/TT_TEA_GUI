"""Build a self-contained Treatment Train Explorer HTML file.

The standalone page carries a snapshot of the app configuration (removal-efficiency
table, default treatment trains, feed water quality defaults, Fit-for-Purpose
targets) and has its own scenario selectors. It needs no Streamlit, models or
database, so it can be opened from a file or a link (e.g. in a presentation).

Run from the GUI root:

    python -m train_explorer.standalone                      # writes treatment_train_explorer.html
    python -m train_explorer.standalone path/to/output.html

Re-run after changing treatment_config.py to refresh the snapshot.
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

from treatment_config import (
    ALL_WATER_QUALITY_PARAMS,
    BRINE_MANAGEMENT_OPTIONS,
    SIDEBAR_DEFAULTS,
    WATER_QUALITY_REQUIREMENTS,
    get_treatment_train_config,
)

from .payload import build_payload

TEMPLATE_PATH = Path(__file__).with_name("template.html")

# Same lists as pages/02_Treatment_Trains.py and pages/01_Treatment_Scenarios.py.
STAGE_OPTIONS = {
    "pretreatment": [
        "3-phase separator", "DAF", "Chemical softening", "Electrocoagulation",
        "Walnut shell filtration", "Cartridge filter", "Bag filter", "Ultrafiltration",
        "Ultra-fine filtration", "Antiscalant / pH adjustment", "Ammonia stripping",
    ],
    "desalination": ["MVC", "Vacuum membrane distillation (VMD)", "LSRRO", "BWRO"],
    "posttreatment": ["Ammonia stripping", "GAC", "Zeolite", "Ion exchange", "Ion exchange (demineralization)", "pH adjustment"],
}
DESAL_TYPES = [
    "Mechanical Vapor Compression (MVC)",
    "Vacuum membrane distillation (VMD)",
    "Low-salt rejection reverse osmosis (LSRRO)",
    "Brackish-water reverse osmosis (BWRO)",
]
WATER_TYPES = {"Produced water": SIDEBAR_DEFAULTS, "Brackish groundwater": SIDEBAR_DEFAULTS["Brackish groundwater"]}
REQUIREMENT_TO_INTERNAL_PARAM = {"Ba2+": "Barium", "SO4": "Sulfate"}
START = {"water": "Produced water", "level": "Medium", "ffp": "Surface water discharge",
         "desal": "Mechanical Vapor Compression (MVC)"}

# Constituents left out of the standalone page (feed, targets, removal table, chart list).
EXCLUDED_PARAMS = {"Alkalinity"}

# Trains shown by the standalone page that differ from get_treatment_train_config.
# Keys are "water|Fit-for-Purpose|desalination type"; values replace the listed stages.
TRAIN_OVERRIDES = {
    "Produced water|Surface water discharge|Mechanical Vapor Compression (MVC)": {
        "pretreatment": ["3-phase separator", "DAF", "Walnut shell filtration"],
    },
}


def _targets(requirements):
    out = {}
    for parameter, info in requirements.items():
        if parameter in {"Notes", "url"} or not isinstance(info, dict):
            continue
        internal = REQUIREMENT_TO_INTERNAL_PARAM.get(parameter, parameter)
        if internal in EXCLUDED_PARAMS:
            continue
        unit = info.get("unit", "")
        if "range" in info:
            try:
                low, high = (float(x) for x in str(info["range"]).split("-", 1))
                out[internal] = {"range": [low, high], "unit": unit}
            except ValueError:
                pass
        elif info.get("limit") is not None:
            out[internal] = {"limit": float(info["limit"]), "unit": unit}
    return out


def _train(water, ffp, desal):
    cfg = get_treatment_train_config(ffp, desal, water)
    brine = cfg.get("brine", [])
    return {
        "pretreatment": list(cfg.get("pretreatment", [])),
        "desalination": list(cfg.get("desalination", [])),
        "posttreatment": list(cfg.get("posttreatment", [])),
        "brine": list(brine) if isinstance(brine, list) else [brine],
        "brine_category": cfg.get("brine_category", ""),
    }


def build_standalone_payload():
    feeds = {}
    for water, by_level in WATER_TYPES.items():
        feeds[water] = {}
        for level in ("Low", "Medium", "High"):
            values = by_level.get(level, {})
            feeds[water][level] = {
                "feed": {k: float(v) for k, v in values.items()
                         if k != "pH" and k not in EXCLUDED_PARAMS and isinstance(v, (int, float)) and v > 0},
                "ph": float(values["pH"]) if "pH" in values else None,
            }

    ffps = list(WATER_QUALITY_REQUIREMENTS)
    trains = {f"{w}|{f}|{d}": _train(w, f, d) for w in WATER_TYPES for f in ffps for d in DESAL_TYPES}
    for key, stages in TRAIN_OVERRIDES.items():
        if key in trains:
            trains[key].update({stage: list(units) for stage, units in stages.items()})

    # One payload whose unit set covers every default train.
    union = {stage: [] for stage in ("pretreatment", "desalination", "posttreatment", "brine")}
    for train in trains.values():
        for stage in union:
            for unit in train[stage]:
                if unit and unit not in union[stage]:
                    union[stage].append(unit)

    start_feed = feeds[START["water"]][START["level"]]
    payload = build_payload(
        current_train=union,
        stage_options=STAGE_OPTIONS,
        brine_options=BRINE_MANAGEMENT_OPTIONS,
        feed=start_feed["feed"],
        feed_ph=start_feed["ph"],
        targets=_targets(WATER_QUALITY_REQUIREMENTS[START["ffp"]]),
        scenario={},
        param_units={k: v.get("unit", "") for k, v in ALL_WATER_QUALITY_PARAMS.items() if k not in EXCLUDED_PARAMS},
    )
    for unit in payload["units"].values():
        for parameter in EXCLUDED_PARAMS:
            unit["removals"].pop(parameter, None)
    for table in payload["lsrro"].values():
        for parameter in EXCLUDED_PARAMS:
            table.pop(parameter, None)
    payload["scaling"] = {"train": [], "rows": []}
    payload["train"] = trains[f"{START['water']}|{START['ffp']}|{START['desal']}"]
    payload["standalone"] = {
        "start": START,
        "feeds": feeds,
        "ffps": ffps,
        "desal_types": DESAL_TYPES,
        "targets": {f: _targets(WATER_QUALITY_REQUIREMENTS[f]) for f in ffps},
        "default_trains": trains,
        "note": (
            f"Snapshot of the TEA app configuration from {_dt.date.today():%B %d, %Y}. "
            "Removal efficiencies are the removal-table defaults; scaling tendency (Reaktoro) is not calculated here."
        ),
    }
    return payload


def render_standalone_html(payload):
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    body = TEMPLATE_PATH.read_text(encoding="utf-8").replace("__PAYLOAD__", data)
    # Move the template's <title>, font links and <style> into <head>.
    split = body.find("</style>") + len("</style>")
    head, rest = body[:split], body[split:]
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"{head}</head><body>{rest}</body></html>"
    )


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = Path(argv[0]) if argv else Path("treatment_train_explorer.html")
    out.write_text(render_standalone_html(build_standalone_payload()), encoding="utf-8")
    print(f"Wrote {out.resolve()}")


if __name__ == "__main__":
    main()

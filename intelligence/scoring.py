"""Transparent first-pass relevance scoring before local-model review."""

from __future__ import annotations

import re


TERM_WEIGHTS = {
    "produced water": 5,
    "oilfield wastewater": 5,
    "oil and gas wastewater": 5,
    "brackish water": 5,
    "brackish groundwater": 5,
    "desalination": 3,
    "beneficial reuse": 3,
    "concentrate management": 3,
    "brine management": 3,
    "reverse osmosis": 2,
    "electrodialysis": 2,
    "membrane distillation": 2,
    "mechanical vapor compression": 2,
    "electrocoagulation": 2,
    "ultrafiltration": 1,
    "membrane fouling": 2,
    "scaling control": 2,
    "silica removal": 2,
    "mineral recovery": 2,
    "zero liquid discharge": 2,
    "permian basin": 2,
}


def relevance_score(text: str) -> tuple[int, list[str]]:
    normalized = re.sub(r"\s+", " ", (text or "").lower())
    matches = [term for term in TERM_WEIGHTS if term in normalized]
    return sum(TERM_WEIGHTS[term] for term in matches), matches


"""Walnut shell filtration (WSF) technical model (NMSU assumptions).

Constituent removal comes from the removal-efficiency table (NMSU defaults:
oil and grease 80%, TSS 80%, TOC 60%, Fe 50%). Water recovery and electricity
use are inputs; backwash water leaves with the reject stream.
"""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template


DEFAULTS = {
    "unit_kind": "wsf",
    "recovery": 0.99,
    "energy_intensity": 0.17,  # kWh/m3 feed
    "chemical_dose": 0.0,
}


def run(unit_process, technical_inputs, stream):
    return run_template(unit_process, technical_inputs, stream, DEFAULTS)

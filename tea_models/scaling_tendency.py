from __future__ import annotations

import math

from reaktoro import *


MINERALS = [
    "Calcite",
    "Magnesite",
    "Barite",
    "Celestite",
    "Anhydrite",
    "Brucite",
    "Epsomite",
]

WATER_QUALITY_TO_REAKTORO_ION = {
    "Sodium": "Na+",
    "Chloride": "Cl-",
    "Sulfate": "SO4-2",
    "Magnesium": "Mg+2",
    "Calcium": "Ca+2",
    "Barium": "Ba+2",
    "Strontium": "Sr+2",
    "Iron": "Fe+2",
    "Bicarbonate": "HCO3-",
    "Silica": "SiO2",
}


def _quality_value(water_quality, parameter, default=0.0):
    entry = water_quality.get(parameter, {})
    if isinstance(entry, dict):
        value = entry.get("value", default)
    else:
        value = entry
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def extract_ion_concentrations(water_quality):
    """Return Reaktoro ion concentrations in mg/L from outlet water quality."""
    ions = {}
    for parameter, ion in WATER_QUALITY_TO_REAKTORO_ION.items():
        value = _quality_value(water_quality, parameter, 0.0)
        if value > 0.0:
            ions[ion] = value
    return ions


def scaling_category(scaling_tendency):
    if scaling_tendency > 1.0:
        return "Scaling likely"
    if math.isclose(scaling_tendency, 1.0, rel_tol=0.05, abs_tol=0.05):
        return "Near saturation"
    return "No scaling expected"


def calculate_scaling_tendency(
    water_quality,
    pressure_bar=1.01325,
    temperature_c=25.0,
):
    """Calculate mineral SI and scaling tendency from outlet water quality.

    Scaling tendency is returned as Omega = 10 ** SI.
    """
    ion_concentrations = extract_ion_concentrations(water_quality)
    pH = _quality_value(water_quality, "pH", 7.0)

    db = PhreeqcDatabase("pitzer.dat")
    solution = AqueousPhase(speciate("H O C Na Cl Ca Mg K S Sr Ba Si Fe"))
    solution.set(ActivityModelPitzer())

    system = ChemicalSystem(db, solution)

    specs = EquilibriumSpecs(system)
    specs.temperature()
    specs.pressure()
    specs.pH()
    specs.charge()
    specs.openTo("Cl-")
    specs.volume()
    specs.openTo("H2O")

    solver = SmartEquilibriumSolver(specs)

    state = ChemicalState(system)
    state.temperature(temperature_c, "celsius")
    state.add("H2O", 1.0, "kg")
    for ion, concentration_mg_l in ion_concentrations.items():
        try:
            state.add(ion, concentration_mg_l, "mg")
        except Exception:
            continue

    conditions = EquilibriumConditions(specs)
    conditions.temperature(temperature_c, "celsius")
    conditions.pressure(pressure_bar, "bar")
    conditions.setLowerBoundTemperature(25, "celsius")
    conditions.setUpperBoundTemperature(200, "celsius")
    conditions.pH(pH)
    conditions.charge(0.0)
    conditions.volume(0.001, "m3")

    solver.solve(state, conditions)

    props = ChemicalProps(system)
    props.update(state)
    aprops = AqueousProps.compute(props)

    rows = []
    for mineral in MINERALS:
        try:
            si = float(aprops.saturationIndex(mineral))
            tendency = 10.0 ** si
            category = scaling_category(tendency)
        except Exception:
            si = None
            tendency = None
            category = "Unavailable in database"
        rows.append({
            "mineral": mineral,
            "saturation_index": si,
            "scaling_tendency": tendency,
            "tendency": category,
        })

    return {
        "pH": float(aprops.pH()),
        "temperature_c": float(aprops.temperature()) - 273.15,
        "pressure_pa": float(aprops.pressure()),
        "ion_concentrations_mg_l": ion_concentrations,
        "minerals": rows,
    }

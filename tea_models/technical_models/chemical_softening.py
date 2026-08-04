"""Chemical softening model using Reaktoro precipitation chemistry."""

from __future__ import annotations

import math

from tea_models.water_quality import apply_unit_water_quality, calculate_brine_quality


DEFAULTS = {
    "recovery": 0.97,
    "lime_dose_mg_l": 10.0,
    "soda_ash_dose_mg_l": 4301.0,
    "target_neutral_pH": 8.0,
    "acid_dose_override_mg_l": 0.0,
    "energy_intensity": 0.223,
}

WATER_KG = 1.0
PRESSURE_ATM = 1.0
PH_TOL = 0.1
H2SO4_MAX_SEARCH_MG_L = 20000.0
H2SO4_BISECTION_MAX_ITER = 40

MW_CaOH2 = 74.093
MW_Na2CO3 = 105.989
MW_H2SO4 = 98.079
MW_CaCO3_EQ = 50.04345
MW_HCO3 = 61.0168
MW_SiO2 = 60.0843
MW_H4SiO4 = 96.1163

MOLAR_MASS_G_MOL = {
    "Calcite": 100.0869,
    "Aragonite": 100.0869,
    "Dolomite": 184.4008,
    "Magnesite": 84.3139,
    "Brucite": 58.3197,
    "Gypsum": 172.171,
    "Anhydrite": 136.1406,
    "Barite": 233.390,
    "Celestite": 183.68,
    "Quartz": 60.0843,
    "Chalcedony": 60.0843,
    "SiO2(a)": 60.0843,
}

ELEM_MM = {
    "Ca": 40.078,
    "Mg": 24.305,
    "Ba": 137.327,
    "Sr": 87.62,
    "SO4": 96.06,
    "SiO2": 60.0843,
}

AQUEOUS_SPECIES = {
    "Ca+2": ("Calcium", 40.078),
    "Mg+2": ("Magnesium", 24.305),
    "Ba+2": ("Barium", 137.327),
    "Sr+2": ("Strontium", 87.62),
    "Na+": ("Sodium", 22.9898),
    "Cl-": ("Chloride", 35.453),
    "SO4-2": ("Sulfate", 96.06),
    "HCO3-": ("Bicarbonate", 61.0168),
    "H4SiO4": ("Silica", 60.0843),
}

MINERALS = [
    "Calcite",
    "Aragonite",
    "Dolomite",
    "Magnesite",
    "Brucite",
    "Gypsum",
    "Anhydrite",
    "Barite",
    "Celestite",
    "Quartz",
    "Chalcedony",
    "SiO2(a)",
]

MINERAL_ION_STOICH = {
    "Calcite": {"Ca": 1},
    "Aragonite": {"Ca": 1},
    "Dolomite": {"Ca": 1, "Mg": 1},
    "Magnesite": {"Mg": 1},
    "Brucite": {"Mg": 1},
    "Gypsum": {"Ca": 1, "SO4": 1},
    "Anhydrite": {"Ca": 1, "SO4": 1},
    "Barite": {"Ba": 1, "SO4": 1},
    "Celestite": {"Sr": 1, "SO4": 1},
    "Quartz": {"SiO2": 1},
    "Chalcedony": {"SiO2": 1},
    "SiO2(a)": {"SiO2": 1},
}


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _quality_value(quality, parameter, default=0.0):
    entry = quality.get(parameter, {})
    value = entry.get("value", default) if isinstance(entry, dict) else entry
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _build_feed_species(quality):
    species = {}
    direct_map = {
        "Calcium": "Ca+2",
        "Magnesium": "Mg+2",
        "Barium": "Ba+2",
        "Strontium": "Sr+2",
        "Sodium": "Na+",
        "Chloride": "Cl-",
        "Sulfate": "SO4-2",
    }
    for parameter, ion in direct_map.items():
        value = _quality_value(quality, parameter)
        if value > 0.0:
            species[ion] = value

    alkalinity = _quality_value(quality, "Alkalinity")
    if alkalinity > 0.0:
        species["HCO3-"] = alkalinity * MW_HCO3 / MW_CaCO3_EQ

    silica = _quality_value(quality, "Silica")
    if silica > 0.0:
        species["H4SiO4"] = silica * MW_H4SiO4 / MW_SiO2

    initial_ions = {
        "Ca": species.get("Ca+2", 0.0),
        "Mg": species.get("Mg+2", 0.0),
        "Ba": species.get("Ba+2", 0.0),
        "Sr": species.get("Sr+2", 0.0),
        "SO4": species.get("SO4-2", 0.0),
        "SiO2": silica,
    }
    return species, initial_ions


def _build_system():
    from reaktoro import (
        ActivityModelPitzer,
        AqueousPhase,
        ChemicalSystem,
        MineralPhase,
        PhreeqcDatabase,
        speciate,
    )

    db = PhreeqcDatabase("pitzer.dat")
    aqueous = AqueousPhase(speciate("H O C Ca Mg Ba Sr Na Cl S Si"))
    aqueous.set(ActivityModelPitzer())

    mineral_phases = []
    active_minerals = []
    for mineral in MINERALS:
        try:
            phase = MineralPhase(mineral)
            ChemicalSystem(db, aqueous, phase)
            mineral_phases.append(MineralPhase(mineral))
            active_minerals.append(mineral)
        except Exception:
            continue
    return ChemicalSystem(db, aqueous, *mineral_phases), active_minerals


def _add_feed_and_chemicals(state, feed_species_mg, lime_mg_l, soda_mg_l, acid_mg_l):
    state.set("H2O", WATER_KG, "kg")
    for species, mg in feed_species_mg.items():
        try:
            state.set(species, float(mg), "mg")
        except Exception:
            continue

    lime_mol = lime_mg_l / 1000.0 / MW_CaOH2
    soda_mol = soda_mg_l / 1000.0 / MW_Na2CO3
    acid_mol = acid_mg_l / 1000.0 / MW_H2SO4
    if lime_mol > 0.0:
        state.add("Ca+2", lime_mol, "mol")
        state.add("OH-", 2.0 * lime_mol, "mol")
    if soda_mol > 0.0:
        state.add("Na+", 2.0 * soda_mol, "mol")
        state.add("CO3-2", soda_mol, "mol")
    if acid_mol > 0.0:
        state.add("H+", 2.0 * acid_mol, "mol")
        state.add("SO4-2", acid_mol, "mol")


def _equilibrium_state(system, minerals, feed_species_mg, temperature_c, lime_mg_l, soda_mg_l, acid_mg_l):
    from reaktoro import ChemicalState, EquilibriumConditions, EquilibriumSolver, EquilibriumSpecs

    state = ChemicalState(system)
    _add_feed_and_chemicals(state, feed_species_mg, lime_mg_l, soda_mg_l, acid_mg_l)
    for mineral in minerals:
        try:
            state.set(mineral, 0.0, "mol")
        except Exception:
            pass

    specs = EquilibriumSpecs(system)
    specs.temperature()
    specs.pressure()
    solver = EquilibriumSolver(specs)
    conditions = EquilibriumConditions(specs)
    conditions.temperature(temperature_c, "celsius")
    conditions.pressure(PRESSURE_ATM, "atm")
    result = solver.solve(state, conditions)
    if not result.succeeded():
        raise RuntimeError("Chemical softening equilibrium calculation failed.")
    return state


def _ph(state):
    from reaktoro import AqueousProps

    try:
        return float(AqueousProps(state).pH())
    except Exception:
        return float("nan")


def _acid_to_target(system, minerals, feed_species_mg, temperature_c, lime_mg_l, soda_mg_l, target_ph):
    state0 = _equilibrium_state(system, minerals, feed_species_mg, temperature_c, lime_mg_l, soda_mg_l, 0.0)
    pH0 = _ph(state0)
    if math.isnan(pH0) or pH0 <= target_ph + PH_TOL:
        return 0.0, state0, pH0, "no_acid_needed"

    lo = 0.0
    hi = H2SO4_MAX_SEARCH_MG_L
    state_hi = _equilibrium_state(system, minerals, feed_species_mg, temperature_c, lime_mg_l, soda_mg_l, hi)
    pH_hi = _ph(state_hi)
    if math.isnan(pH_hi) or pH_hi > target_ph:
        return hi, state_hi, pH_hi, "max_acid_bound_reached"

    best_acid = hi
    best_state = state_hi
    best_ph = pH_hi
    for _ in range(H2SO4_BISECTION_MAX_ITER):
        mid = 0.5 * (lo + hi)
        state_mid = _equilibrium_state(system, minerals, feed_species_mg, temperature_c, lime_mg_l, soda_mg_l, mid)
        pH_mid = _ph(state_mid)
        if math.isnan(pH_mid):
            hi = mid
            continue
        best_acid = mid
        best_state = state_mid
        best_ph = pH_mid
        if abs(pH_mid - target_ph) <= PH_TOL:
            return mid, state_mid, pH_mid, "target_reached"
        if pH_mid > target_ph:
            lo = mid
        else:
            hi = mid
    return best_acid, best_state, best_ph, "bisection_max_iter"


def _solids_from_state(state, minerals):
    solids = {}
    for mineral in minerals:
        try:
            mol = float(state.speciesAmount(mineral))
            mg_l = mol * MOLAR_MASS_G_MOL[mineral] * 1000.0 / WATER_KG
        except Exception:
            mol = 0.0
            mg_l = 0.0
        solids[mineral] = {"mol_L": mol / WATER_KG, "mg_L": mg_l, "kg_m3": mg_l / 1000.0}
    return solids


def _removed_from_solids(solids):
    removed = {"Ca": 0.0, "Mg": 0.0, "Ba": 0.0, "Sr": 0.0, "SO4": 0.0, "SiO2": 0.0}
    for mineral, vals in solids.items():
        mol = vals.get("mol_L", 0.0)
        for ion, coeff in MINERAL_ION_STOICH.get(mineral, {}).items():
            removed[ion] += mol * coeff * ELEM_MM[ion] * 1000.0
    return removed


def _effluent_from_state(state, water_quality_in):
    outlet = {name: entry.copy() for name, entry in water_quality_in.items()}
    for species, (parameter, mw) in AQUEOUS_SPECIES.items():
        if parameter not in outlet:
            continue
        try:
            mol = float(state.speciesAmount(species))
            mg_l = max(mol * mw * 1000.0 / WATER_KG, 0.0)
        except Exception:
            continue
        outlet[parameter] = {"value": mg_l, "unit": outlet[parameter].get("unit", "mg/L")}
    try:
        outlet["pH"] = {"value": _ph(state), "unit": outlet.get("pH", {}).get("unit", "-")}
    except Exception:
        pass
    return outlet


def _model_quality(water_quality_in, lime_mg_l, soda_mg_l, target_ph, acid_override_mg_l):
    feed_species, initial_ions = _build_feed_species(water_quality_in)
    system, minerals = _build_system()
    temperature_c = _quality_value(water_quality_in, "Temperature", 25.0)

    softened_state = _equilibrium_state(system, minerals, feed_species, temperature_c, lime_mg_l, soda_mg_l, 0.0)
    softened_ph = _ph(softened_state)
    if acid_override_mg_l > 0.0:
        acid_mg_l = acid_override_mg_l
        final_state = _equilibrium_state(system, minerals, feed_species, temperature_c, lime_mg_l, soda_mg_l, acid_mg_l)
        acid_status = "manual_acid_dose"
    else:
        acid_mg_l, final_state, _final_ph, acid_status = _acid_to_target(
            system, minerals, feed_species, temperature_c, lime_mg_l, soda_mg_l, target_ph
        )

    solids = _solids_from_state(final_state, minerals)
    removed = _removed_from_solids(solids)
    outlet_quality = _effluent_from_state(final_state, water_quality_in)
    removal_efficiencies = {}
    mapping = {
        "Ca": "Calcium",
        "Mg": "Magnesium",
        "Ba": "Barium",
        "Sr": "Strontium",
        "SO4": "Sulfate",
        "SiO2": "Silica",
    }
    for ion, parameter in mapping.items():
        inlet = initial_ions.get(ion, 0.0)
        if inlet > 0.0:
            removal_efficiencies[parameter] = min(max(removed.get(ion, 0.0) / inlet, 0.0), 1.0)
    for parameter, entry in water_quality_in.items():
        if parameter not in removal_efficiencies and parameter != "pH":
            inlet = _quality_value(water_quality_in, parameter)
            outlet = _quality_value(outlet_quality, parameter, inlet)
            removal_efficiencies[parameter] = min(max(1.0 - outlet / inlet, 0.0), 1.0) if inlet > 0.0 else 0.0
    removal_efficiencies["pH"] = _ph(final_state)
    total_solids_mg_l = sum(value.get("mg_L", 0.0) for value in solids.values())
    return outlet_quality, removal_efficiencies, {
        "softening_pH": softened_ph,
        "neutralized_pH": _ph(final_state),
        "acid_status": acid_status,
        "h2so4_dose_mg_l": acid_mg_l,
        "solid_waste_kg_m3": total_solids_mg_l / 1000.0,
        "active_minerals": minerals,
    }


def run(unit_process, technical_inputs, stream):
    inlet_flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    water_quality_in = stream.get("water_quality", {}) or {}
    recovery = min(max(_input(technical_inputs, "recovery", DEFAULTS["recovery"]), 0.0), 1.0)
    lime_mg_l = max(_input(technical_inputs, "lime_dose_mg_l", DEFAULTS["lime_dose_mg_l"]), 0.0)
    soda_mg_l = max(_input(technical_inputs, "soda_ash_dose_mg_l", DEFAULTS["soda_ash_dose_mg_l"]), 0.0)
    target_ph = max(_input(technical_inputs, "target_neutral_pH", DEFAULTS["target_neutral_pH"]), 0.0)
    acid_override = max(_input(technical_inputs, "acid_dose_override_mg_l", DEFAULTS["acid_dose_override_mg_l"]), 0.0)
    energy_intensity = max(_input(technical_inputs, "energy_intensity", DEFAULTS["energy_intensity"]), 0.0)

    warnings = []
    try:
        outlet_quality, removal_efficiencies, model = _model_quality(
            water_quality_in,
            lime_mg_l,
            soda_mg_l,
            target_ph,
            acid_override,
        )
    except Exception as exc:
        fallback_removals = technical_inputs.get("removal_efficiencies") or {}
        _, _, _, _, outlet_quality, _ = apply_unit_water_quality(
            stream,
            recovery,
            fallback_removals,
            {"pH": target_ph} if target_ph else {},
        )
        removal_efficiencies = fallback_removals
        model = {
            "softening_pH": None,
            "neutralized_pH": _quality_value(outlet_quality, "pH", target_ph),
            "acid_status": "reaktoro_failed",
            "h2so4_dose_mg_l": 0.0,
            "solid_waste_kg_m3": 0.0,
            "active_minerals": [],
        }
        warnings.append(f"Reaktoro chemical softening failed; used removal table fallback. {exc}")

    outlet_flow = inlet_flow * recovery
    brine_flow = max(inlet_flow - outlet_flow, 0.0)
    outlet_stream = {"flow_m3_day": outlet_flow, "water_quality": outlet_quality}
    brine_quality = calculate_brine_quality(water_quality_in, outlet_quality, inlet_flow, outlet_flow, brine_flow)

    return {
        "inlet_flow": _result(inlet_flow, "m3/day"),
        "outlet_flow": _result(outlet_flow, "m3/day"),
        "brine_flow": _result(brine_flow, "m3/day"),
        "water_recovery": _result(recovery, "fraction"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "thermal_energy_intensity": _result(0.0, "kWh/m3 feed"),
        "lime_dose": _result(lime_mg_l, "mg/L as Ca(OH)2"),
        "soda_ash_dose": _result(soda_mg_l, "mg/L as Na2CO3"),
        "h2so4_dose": _result(model["h2so4_dose_mg_l"], "mg/L as H2SO4"),
        "softening_pH": _result(model["softening_pH"], "-"),
        "neutralized_pH": _result(model["neutralized_pH"], "-"),
        "solid_waste_generation": _result(model["solid_waste_kg_m3"], "kg/m3 feed"),
        "solid_waste": _result(model["solid_waste_kg_m3"] * inlet_flow, "kg/day"),
        "acid_status": _result(model["acid_status"], ""),
        "active_minerals": _result(", ".join(model["active_minerals"]), ""),
        "removal_efficiencies": removal_efficiencies,
        "water_quality_in": water_quality_in,
        "water_quality_out": outlet_quality,
        "brine_water_quality": brine_quality,
        "outlet_stream": outlet_stream,
        "model_warnings": _result(warnings, ""),
    }

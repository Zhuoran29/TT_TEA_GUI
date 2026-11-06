"""Electrocoagulation (aluminum electrodes) following the NMSU EC model (EC_V1)."""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template
from tea_models.water_quality import get_default_removal_efficiencies


DEFAULTS = {
    "unit_kind": "electrocoagulation",
    "current_density_mA_cm2": 20.0,
    "electrode_gap_m": 0.02,
    "hydraulic_retention_time": 30.0,
    "energy_intensity": 0.0,
    "sludge_solids_content": 0.025,  # dry solids mass fraction of the EC sludge (Al-Ajmi et al. 2025: 2.41-2.62%)
}

REFERENCE_ELECTRODE_AREA_M2 = 567.0
REFERENCE_FLOW_M3_DAY = 11356.0
REFERENCE_HRT_MIN = 15.0
REFERENCE_REACTOR_VOLUME_M3 = 12.5
MW_ALOH3_G_MOL = 78.00
MW_AL_G_MOL = 26.98
Z_AL = 3.0
M_AL_KG_MOL = 26.98 / 1000.0
F_C_MOL = 96485.3329


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _value(result, name, default=0.0):
    entry = result.get(name, {})
    try:
        return float(entry.get("value", default) if isinstance(entry, dict) else entry)
    except (TypeError, ValueError):
        return float(default)


def _quality_value(quality, parameter, default=0.0):
    try:
        return float((quality.get(parameter, {}) or {}).get("value", default) or default)
    except (TypeError, ValueError):
        return float(default)


def _nacl_from_rho(rho_mS_cm):
    return (
        -1.74e-9 * rho_mS_cm**5
        + 9.54e-7 * rho_mS_cm**4
        - 1.652e-4 * rho_mS_cm**3
        + 0.01 * rho_mS_cm**2
        + 0.338 * rho_mS_cm
        + 0.09
    )


def _rho_from_nacl(nacl_g_l):
    lo = 0.0
    hi = 260.0
    f_lo = _nacl_from_rho(lo) - nacl_g_l
    f_hi = _nacl_from_rho(hi) - nacl_g_l
    if f_lo == 0.0:
        return lo
    if f_hi == 0.0:
        return hi
    if f_lo * f_hi > 0.0:
        return max(0.0, min(nacl_g_l / 0.338, hi))
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = _nacl_from_rho(mid) - nacl_g_l
        if abs(f_mid) < 1e-9:
            return mid
        if f_lo * f_mid <= 0.0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid
    return 0.5 * (lo + hi)



_PH_SYSTEM = None


def _ph_system():
    """Aqueous (Pitzer) + gas phase used for the effluent pH; built once."""
    global _PH_SYSTEM
    if _PH_SYSTEM is None:
        import reaktoro as rkt

        db = rkt.PhreeqcDatabase("pitzer.dat")
        aqueous = rkt.AqueousPhase(rkt.speciate("H O C Ca Mg Ba Sr Na Cl S Si"))
        aqueous.set(rkt.ActivityModelPitzer())
        _PH_SYSTEM = (
            rkt.ChemicalSystem(db, aqueous),
            rkt.ChemicalSystem(db, aqueous, rkt.GaseousPhase("CO2(g) H2O(g) Hdg(g)")),
        )
    return _PH_SYSTEM


def effluent_ph(feed_quality, charge_c_per_l, temperature_c=25.0):
    """Effluent pH after EC with aluminum anodes (Reaktoro, Pitzer activity model).

    Each Al3+ released at the anode is matched by 3 OH- from the cathode, so Al(OH)3
    formation leaves no excess base. The pH rises because the hydrogen produced at the
    cathode (charge / 2F) strips CO2 from the water; the hydrogen is equilibrated with
    the water in one stage (upper bound of the stripping). Mineral precipitation is not
    included. Returns (pH, CO2 stripped in mmol/L) or None when pH or alkalinity is
    missing or the calculation fails.
    """
    ph0 = _quality_value(feed_quality, "pH", 0.0)
    if ph0 <= 0.0 or _quality_value(feed_quality, "Alkalinity", 0.0) <= 0.0:
        return None
    try:
        import reaktoro as rkt

        from tea_models.technical_models.chemical_softening import _build_feed_species

        aqueous_system, gas_system = _ph_system()
        species_mg, _ = _build_feed_species(feed_quality)
        feed = None
        for balance_ion in ("Cl-", "Na+"):
            state = rkt.ChemicalState(aqueous_system)
            state.set("H2O", 1.0, "kg")
            for name, mg in species_mg.items():
                state.set(name, float(mg), "mg")
            specs = rkt.EquilibriumSpecs(aqueous_system)
            specs.temperature()
            specs.pressure()
            specs.pH()
            specs.charge()
            specs.openTo(balance_ion)
            conditions = rkt.EquilibriumConditions(specs)
            conditions.temperature(temperature_c, "celsius")
            conditions.pressure(1.0, "atm")
            conditions.pH(ph0)
            conditions.charge(0.0)
            if rkt.EquilibriumSolver(specs).solve(state, conditions).succeeded():
                feed = state
                break
        if feed is None:
            return None

        state = rkt.ChemicalState(gas_system)
        for species in aqueous_system.species():
            amount = float(feed.speciesAmount(species.name()))
            if amount > 0.0:
                state.set(species.name(), amount, "mol")
        state.set("Hdg(g)", max(charge_c_per_l, 0.0) / (2.0 * F_C_MOL), "mol")
        state.set("CO2(g)", 1e-14, "mol")
        state.set("H2O(g)", 1e-14, "mol")
        specs = rkt.EquilibriumSpecs(gas_system)
        specs.temperature()
        specs.pressure()
        conditions = rkt.EquilibriumConditions(specs)
        conditions.temperature(temperature_c, "celsius")
        conditions.pressure(1.0, "atm")
        if not rkt.EquilibriumSolver(specs).solve(state, conditions).succeeded():
            return None
        return float(rkt.AqueousProps(state).pH()), 1000.0 * float(state.speciesAmount("CO2(g)"))
    except Exception:
        return None


# Removed dissolved constituents counted as precipitate mass in the solid waste:
# (water-quality parameter, mass of precipitate per mass removed)
PRECIPITATE_FACTORS = (
    ("Calcium", 100.087 / 40.078),    # as CaCO3
    ("Magnesium", 58.320 / 24.305),   # as Mg(OH)2
    ("Barium", 233.39 / 137.327),     # as BaSO4
    ("Strontium", 147.63 / 87.62),    # as SrCO3
    ("Silica", 1.0),                  # as SiO2
)


def _fraction(removals, parameter):
    try:
        return min(max(float(removals.get(parameter, 0.0)), 0.0), 1.0)
    except (TypeError, ValueError):
        return 0.0


def run(unit_process, technical_inputs, stream):
    feed_quality = stream.get("water_quality", {}) or {}
    inlet_flow = max(float(stream.get("flow_m3_day", 0.0) or 0.0), 0.0)  # m3/day
    hrt = _input(technical_inputs, "hydraulic_retention_time", DEFAULTS["hydraulic_retention_time"])
    gap_m = _input(technical_inputs, "electrode_gap_m", DEFAULTS["electrode_gap_m"])
    current_density = _input(technical_inputs, "current_density_mA_cm2", DEFAULTS["current_density_mA_cm2"])
    solids_content = min(max(_input(technical_inputs, "sludge_solids_content", DEFAULTS["sludge_solids_content"]), 1e-6), 1.0)

    table = technical_inputs.get("removal_efficiencies")
    if table is None:
        table = get_default_removal_efficiencies(unit_process, feed_quality)
    removals = dict(table)

    # Reactor and electrodes (NMSU EC model): electrode area per flow from the reference
    # design (567 m2 at 11,356 m3/day), scaled by the treatment time relative to 15 min.
    reference_flow_volume = REFERENCE_FLOW_M3_DAY * (REFERENCE_HRT_MIN / 1440.0)
    reactor_scaling = reference_flow_volume / REFERENCE_REACTOR_VOLUME_M3
    aspect_ratio = REFERENCE_REACTOR_VOLUME_M3 / REFERENCE_ELECTRODE_AREA_M2
    reactor_volume = inlet_flow * (hrt / 1440.0) / max(reactor_scaling, 1e-12)
    electrode_area = reactor_volume / max(aspect_ratio, 1e-12)

    tds_mg_l = _quality_value(feed_quality, "TDS")
    nacl_g_l = max(tds_mg_l / 1000.0, 1e-9)
    try:
        rho = _rho_from_nacl(nacl_g_l)
        conductivity_s_m = rho / 10.0
        resistance = gap_m / max(conductivity_s_m * electrode_area, 1e-12)
    except Exception:
        rho = 0.0
        resistance = 0.0

    current_a = current_density * 10.0 * electrode_area
    voltage_v = current_a * resistance + 1.50
    power_kw = current_a * voltage_v / 1000.0
    energy_intensity = power_kw * 24.0 / max(inlet_flow, 1e-12)

    # Aluminum dose (Faraday's law, 100% current efficiency) and sludge
    flow_l_s = inlet_flow * 1000.0 / 86400.0
    al_dose_mg_l = current_a * M_AL_KG_MOL * 1e6 / max(Z_AL * F_C_MOL * flow_l_s, 1e-12) if inlet_flow > 0.0 else 0.0
    aloh3_solids_mg_l = al_dose_mg_l * MW_ALOH3_G_MOL / MW_AL_G_MOL
    feed_tss = max(_quality_value(feed_quality, "TSS"), 0.0)
    removed_tss = feed_tss * _fraction(removals, "TSS")
    floc_solids_kg_m3 = (aloh3_solids_mg_l + removed_tss) / 1000.0

    # Removed hardness and other precipitating constituents (mass balance for the waste line)
    precipitate_mg_l = 0.0
    if _quality_value(feed_quality, "Calcium") > 0.0 or _quality_value(feed_quality, "Magnesium") > 0.0:
        factors = PRECIPITATE_FACTORS
    else:  # only total hardness given (mg/L as CaCO3)
        factors = (("Hardness", 1.0),) + PRECIPITATE_FACTORS[2:]
    for parameter, factor in factors:
        feed_value = max(_quality_value(feed_quality, parameter), 0.0)
        precipitate_mg_l += feed_value * _fraction(removals, parameter) * factor
    precipitate_kg_m3 = precipitate_mg_l / 1000.0
    solid_waste_kg_m3 = floc_solids_kg_m3 + precipitate_kg_m3

    # Water leaves with the floc sludge (Al(OH)3 + TSS): recovery = 1 - wet sludge volume / feed.
    # Precipitated minerals are counted in the waste mass but not in the water loss.
    sludge_m3_per_m3 = floc_solids_kg_m3 / solids_content / 1000.0
    recovery = max(1.0 - sludge_m3_per_m3, 0.0)

    # Effluent pH: CO2 stripped by the cathode hydrogen (charge per liter = I / Q)
    charge_c_per_l = current_a / flow_l_s if inlet_flow > 0.0 else 0.0
    temperature = _quality_value(feed_quality, "Temperature", 25.0) or 25.0
    ph_result = effluent_ph(feed_quality, charge_c_per_l, temperature) if inlet_flow > 0.0 else None
    targets = dict(technical_inputs.get("target_values", {}) or {})
    if ph_result is not None and "pH" not in targets:
        targets["pH"] = ph_result[0]

    template_inputs = {
        **technical_inputs,
        "removal_efficiencies": removals,
        "recovery": recovery,
        "target_values": targets,
    }
    outputs = run_template(unit_process, template_inputs, stream, DEFAULTS)

    outputs.update({
        "hydraulic_retention_time": _result(hrt, "min"),
        "reactor_volume": _result(reactor_volume, "m3"),
        "electrode_area": _result(electrode_area, "m2"),
        "conductivity_from_tds": _result(rho, "mS/cm"),
        "solution_resistance": _result(resistance, "ohm"),
        "system_current": _result(current_a, "A"),
        "system_voltage": _result(voltage_v, "V"),
        "system_power": _result(power_kw, "kW"),
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "aluminum_dose": _result(al_dose_mg_l, "mg/L"),
        "aluminum_consumption": _result(al_dose_mg_l * inlet_flow / 1000.0, "kg/day"),
        "solid_waste_generation": _result(solid_waste_kg_m3, "kg/m3 feed"),
        "floc_solids_generation": _result(floc_solids_kg_m3, "kg/m3 feed"),
        "precipitated_solids_generation": _result(precipitate_kg_m3, "kg/m3 feed"),
        "solid_waste": _result(solid_waste_kg_m3 * inlet_flow, "kg/day"),
        "sludge_solids_content": _result(solids_content, "fraction"),
        "sludge_volume": _result(sludge_m3_per_m3 * inlet_flow, "m3/day"),
        "charge_loading": _result(charge_c_per_l, "C/L"),
    })
    feed_ph = _quality_value(feed_quality, "pH", 0.0)
    if ph_result is not None:
        outputs["effluent_pH"] = _result(ph_result[0], "-")
        outputs["co2_stripped"] = _result(ph_result[1], "mmol/L")
    elif feed_ph > 0.0:
        outputs["model_warnings"] = _result(
            ["Effluent pH not calculated (needs feed pH, alkalinity and Reaktoro); pH is passed through unchanged."], ""
        )
    return outputs

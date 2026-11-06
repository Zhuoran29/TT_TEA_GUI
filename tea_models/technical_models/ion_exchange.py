"""Ion exchange models: selective IX (NaCl-regenerated) and demineralization (H/OH).

Selective IX ("Ion exchange"). The targets entered in the removal table pick the beds:
  cation bed  Na-form strong acid cation (SAC) resin: hardness, Ca, Mg, Ba, Sr, Mn,
              Ra-226/228, gross alpha. All divalent cations are removed together.
              Each equivalent removed is replaced by one equivalent of Na+.
  anion bed   Cl-form strong base anion (SBA) resin: sulfate, alkalinity/bicarbonate,
              As, Se, U. Sulfate is always taken up (the resin prefers it); alkalinity
              only when it is a target. Each equivalent removed is replaced by Cl-.
  Na, Cl, TDS, conductivity, boron, ammonia, fluoride, silica and lithium are not removed.

Demineralization ("Ion exchange (demineralization)"): H-form SAC followed by OH-form SBA,
regenerated with HCl and NaOH. All ions are removed at the same fraction.

Both: the treated fraction is f = removal / bed removal; the rest bypasses the beds and is
blended back. Run length (bed volumes) = usable capacity / ionic load removed per litre,
capped at the maximum bed volumes per cycle. Regenerant use and waste volume (regenerant,
rinse and backwash bed volumes) follow from the run length. Pump energy is hydraulic.
Defaults follow the US EPA WBS cation exchange and anion exchange models.
"""

from __future__ import annotations

from tea_models.technical_models.template_units import run_template

# Equivalent weights (mg per meq)
EQ_WEIGHT = {
    "Calcium": 20.039,
    "Magnesium": 12.153,
    "Barium": 68.664,
    "Strontium": 43.81,
    "Manganese": 27.469,
    "Sodium": 22.990,
    "Lithium": 6.941,
    "Ammonia nitrogen": 14.007,
    "Chloride": 35.453,
    "Sulfate": 48.03,
    "Bicarbonate": 61.017,
    "Fluoride": 18.998,
    "Silica": 60.084,  # as H3SiO4- on OH-form resin
    "Boron": 10.81,  # as borate on OH-form resin
}
CACO3_EQ = 50.04  # mg CaCO3 per meq (hardness, alkalinity)
NA_EQ = EQ_WEIGHT["Sodium"]
CL_EQ = EQ_WEIGHT["Chloride"]
NACL_EQ = 58.443  # mg NaCl per meq (TDS fallback)
HCL_EQ = 36.461
NAOH_EQ = 39.997

CATION_TARGETS = [
    "Hardness", "Calcium", "Magnesium", "Barium", "Strontium", "Manganese",
    "Radium-226", "Radium-228", "Gross Alpha",
]
ANION_ALWAYS = ["Sulfate"]
ANION_TARGETS = ["Sulfate", "Bicarbonate", "Alkalinity", "Arsenic", "Selenium", "Uranium"]
NOT_REMOVED_SELECTIVE = [
    "Sodium", "Chloride", "TDS", "Conductivity", "Boron", "Ammonia nitrogen",
    "Fluoride", "Silica", "Lithium", "Gross Beta",
]
DEMIN_REMOVED = [
    "TDS", "Conductivity", "Hardness", "Alkalinity", "Calcium", "Magnesium", "Barium",
    "Strontium", "Manganese", "Sodium", "Lithium", "Ammonia nitrogen", "Chloride", "Sulfate",
    "Bicarbonate", "Fluoride", "Silica", "Boron", "Arsenic", "Selenium", "Uranium",
    "Radium-226", "Radium-228", "Gross Alpha", "Gross Beta",
]

SELECTIVE_DEFAULTS = {
    "unit_kind": "ion_exchange",
    "bed_removal": 0.99,
    "cation_empty_bed_contact_time": 2.5,
    "cation_capacity": 1.24,
    "cation_regenerant_dose": 240.0,
    "cation_regenerant_concentration": 107.8,
    "cation_rinse_bed_volumes": 12.0,
    "cation_backwash_bed_volumes": 3.0,
    "cation_max_bed_volumes": 1000.0,
    "anion_empty_bed_contact_time": 2.0,
    "anion_capacity": 0.8,
    "anion_regenerant_dose": 128.0,
    "anion_regenerant_concentration": 59.9,
    "anion_rinse_bed_volumes": 7.0,
    "anion_backwash_bed_volumes": 1.2,
    "anion_max_bed_volumes": 3000.0,
    "pump_head": 10.0,
    "pump_efficiency": 0.70,
}

DEMIN_DEFAULTS = {
    **SELECTIVE_DEFAULTS,
    "unit_kind": "ion_exchange_demineralization",
    "cation_capacity": 1.0,
    "cation_regenerant_dose": 100.0,
    "cation_regenerant_concentration": 51.0,
    "cation_rinse_bed_volumes": 7.0,
    "cation_backwash_bed_volumes": 1.2,
    "anion_capacity": 0.5,
    "anion_regenerant_dose": 100.0,
    "anion_regenerant_concentration": 42.0,
    "anion_max_bed_volumes": 1000.0,
}
DEFAULTS = SELECTIVE_DEFAULTS


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _q(quality, parameter):
    entry = quality.get(parameter)
    if entry is None:
        return 0.0
    value = entry.get("value", 0.0) if isinstance(entry, dict) else entry
    try:
        return max(float(value or 0.0), 0.0)
    except (TypeError, ValueError):
        return 0.0


def _removal(removals, parameter):
    try:
        value = float(removals.get(parameter, 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return min(max(value if value <= 1.0 else value / 100.0, 0.0), 1.0)


def _meq(quality, parameter):
    return _q(quality, parameter) / EQ_WEIGHT[parameter]


def divalent_cation_load(quality):
    """Hardness ions (Ca + Mg or hardness, whichever is larger) plus Ba, Sr, Mn, in meq/L."""
    ca_mg = _meq(quality, "Calcium") + _meq(quality, "Magnesium")
    hardness = _q(quality, "Hardness") / CACO3_EQ
    return max(ca_mg, hardness) + sum(_meq(quality, p) for p in ("Barium", "Strontium", "Manganese"))


def alkalinity_load(quality):
    return max(_meq(quality, "Bicarbonate"), _q(quality, "Alkalinity") / CACO3_EQ)


def total_ionic_load(quality):
    """Ionic load for demineralization (meq/L): the largest of the cation sum, the anion sum
    and TDS as NaCl (TDS can include ions that are not tracked)."""
    cations = (
        divalent_cation_load(quality)
        + sum(_meq(quality, p) for p in ("Sodium", "Lithium", "Ammonia nitrogen"))
    )
    anions = (
        sum(_meq(quality, p) for p in ("Chloride", "Sulfate", "Fluoride", "Silica", "Boron"))
        + alkalinity_load(quality)
    )
    return max(cations, anions, _q(quality, "TDS") / NACL_EQ)


def _bed(prefix, values, defaults, flow, removal, bed_removal, load_meq, regen_eq_weight):
    """Size one bed and its regeneration. flow in m3/day, load in meq/L of treated water."""
    def get(name):
        return _input(values, f"{prefix}_{name}", defaults[f"{prefix}_{name}"])

    fraction = min(removal / bed_removal, 1.0) if bed_removal > 0.0 else 1.0
    eff_removal = removal / fraction if fraction > 0.0 else 0.0
    treated = flow * fraction
    ebct = max(get("empty_bed_contact_time"), 1e-9)
    capacity = max(get("capacity"), 0.0)  # eq/L resin
    dose = max(get("regenerant_dose"), 0.0)  # g/L resin
    concentration = max(get("regenerant_concentration"), 1e-9)  # g/L
    max_bv = max(get("max_bed_volumes"), 1.0)
    loaded = eff_removal * load_meq  # meq per L treated
    capacity_bv = 1000.0 * capacity / loaded if loaded > 0.0 else max_bv
    bed_volumes = min(capacity_bv, max_bv)
    bed_volume = treated * ebct / 1440.0  # m3 resin
    cycle_days = bed_volumes * ebct / 1440.0
    cycles_per_day = 1.0 / cycle_days if cycle_days > 0.0 else 0.0
    regenerant_kg_day = dose * bed_volume * cycles_per_day  # g/L = kg/m3
    regen_bv = dose / concentration
    waste_bv = regen_bv + max(get("rinse_bed_volumes"), 0.0) + max(get("backwash_bed_volumes"), 0.0)
    waste_m3_day = waste_bv * bed_volume * cycles_per_day
    removed_eq_day = loaded * treated  # meq/L x m3/day = eq/day
    regen_eq_day = regenerant_kg_day * 1000.0 / regen_eq_weight
    return {
        "fraction": fraction,
        "treated_flow": treated,
        "bed_volume": bed_volume,
        "capacity_bed_volumes": capacity_bv,
        "bed_volumes": bed_volumes,
        "cycle_days": cycle_days,
        "cycles_per_day": cycles_per_day,
        "regenerant_kg_day": regenerant_kg_day,
        "regenerant_eq_day": regen_eq_day,
        "removed_eq_day": removed_eq_day,
        "regeneration_ratio": regen_eq_day / removed_eq_day if removed_eq_day > 0.0 else 0.0,
        "waste_bed_volumes": waste_bv,
        "waste_m3_day": waste_m3_day,
        "capped": capacity_bv > max_bv,
        "ebct": ebct,
    }


def _empty_bed():
    return {
        "fraction": 0.0, "treated_flow": 0.0, "bed_volume": 0.0, "capacity_bed_volumes": 0.0,
        "bed_volumes": 0.0, "cycle_days": 0.0, "cycles_per_day": 0.0, "regenerant_kg_day": 0.0,
        "regenerant_eq_day": 0.0, "removed_eq_day": 0.0, "regeneration_ratio": 0.0,
        "waste_bed_volumes": 0.0, "waste_m3_day": 0.0, "capped": False, "ebct": 0.0,
    }


def _set(quality, parameter, value):
    if parameter in quality:
        entry = dict(quality[parameter]) if isinstance(quality[parameter], dict) else {"value": quality[parameter]}
        entry["value"] = max(value, 0.0)
        quality[parameter] = entry


def run_ix(unit_process, technical_inputs, stream, demineralization=False):
    defaults = DEMIN_DEFAULTS if demineralization else SELECTIVE_DEFAULTS
    removals_in = dict(technical_inputs.get("removal_efficiencies") or {})
    quality_in = stream.get("water_quality", {}) or {}
    flow = float(stream.get("flow_m3_day", 0.0) or 0.0)
    bed_removal = min(max(_input(technical_inputs, "bed_removal", defaults["bed_removal"]), 1e-6), 1.0)
    warnings = []
    removals = {}
    added_mg_l = {"Sodium": 0.0, "Chloride": 0.0}

    if demineralization:
        explicit = _removal(removals_in, "TDS")
        removal = explicit if explicit > 0.0 else max((_removal(removals_in, p) for p in DEMIN_REMOVED), default=0.0)
        load = total_ionic_load(quality_in) if removal > 0.0 else 0.0
        cation = _bed("cation", technical_inputs, defaults, flow, removal, bed_removal, load, HCL_EQ) if removal > 0.0 else _empty_bed()
        anion = _bed("anion", technical_inputs, defaults, flow, removal, bed_removal, load, NAOH_EQ) if removal > 0.0 else _empty_bed()
        differing = [
            p for p in DEMIN_REMOVED
            if p != "TDS" and p in removals_in and abs(_removal(removals_in, p) - removal) > 1e-9
        ]
        if differing and removal > 0.0:
            warnings.append(
                f"Demineralization removes all ions at the TDS removal ({removal:.0%}); "
                "the other entries in the removal table are not used."
            )
        for parameter in DEMIN_REMOVED:
            removals[parameter] = removal
        cation_removal = anion_removal = removal
        removed_mass = 0.0  # TDS handled by the common removal
        regen_add = {
            "Chloride": cation["regenerant_eq_day"] * CL_EQ / 1000.0,  # kg/day
            "Sodium": anion["regenerant_eq_day"] * NA_EQ / 1000.0,
        }
        if load > 0.0 and _q(quality_in, "TDS") > 0.0 and divalent_cation_load(quality_in) + _meq(quality_in, "Sodium") <= 0.0:
            warnings.append("No ion data in the feed; the ionic load is estimated from TDS as NaCl.")
    else:
        cation_removal = max((_removal(removals_in, p) for p in CATION_TARGETS), default=0.0)
        anion_targets = [p for p in ANION_TARGETS if _removal(removals_in, p) > 0.0]
        anion_removal = max((_removal(removals_in, p) for p in anion_targets), default=0.0)
        ignored = [p for p in NOT_REMOVED_SELECTIVE if _removal(removals_in, p) > 0.0]
        if ignored:
            warnings.append(
                "Selective IX does not remove " + ", ".join(ignored)
                + "; these entries are ignored. Use Ion exchange (demineralization), BWRO, or zeolite for ammonia."
            )
        cation_load = divalent_cation_load(quality_in) if cation_removal > 0.0 else 0.0
        alk_targeted = any(p in anion_targets for p in ("Bicarbonate", "Alkalinity"))
        anion_load = (_meq(quality_in, "Sulfate") + (alkalinity_load(quality_in) if alk_targeted else 0.0)) if anion_removal > 0.0 else 0.0
        cation = _bed("cation", technical_inputs, defaults, flow, cation_removal, bed_removal, cation_load, NACL_EQ) if cation_removal > 0.0 else _empty_bed()
        anion = _bed("anion", technical_inputs, defaults, flow, anion_removal, bed_removal, anion_load, NACL_EQ) if anion_removal > 0.0 else _empty_bed()
        if cation_removal > 0.0:
            for parameter in CATION_TARGETS:
                removals[parameter] = cation_removal
        if anion_removal > 0.0:
            for parameter in ANION_ALWAYS + anion_targets:
                removals[parameter] = anion_removal
            if alk_targeted:
                removals["Bicarbonate"] = removals["Alkalinity"] = anion_removal
        # Counter-ions released into the product water
        cation_meq = cation_removal * cation_load
        anion_meq = anion_removal * anion_load
        added_mg_l["Sodium"] = cation_meq * NA_EQ
        added_mg_l["Chloride"] = anion_meq * CL_EQ
        removed_mass = (
            sum(removals.get(p, 0.0) * _q(quality_in, p) for p in ("Calcium", "Magnesium", "Barium", "Strontium", "Manganese"))
            + (0.0 if _q(quality_in, "Calcium") + _q(quality_in, "Magnesium") > 0.0
               else removals.get("Hardness", 0.0) * _q(quality_in, "Hardness") / CACO3_EQ * EQ_WEIGHT["Calcium"])
            + removals.get("Sulfate", 0.0) * _q(quality_in, "Sulfate")
            + (anion_removal * alkalinity_load(quality_in) * EQ_WEIGHT["Bicarbonate"] if alk_targeted else 0.0)
        )
        regen_eq = cation["regenerant_eq_day"] + anion["regenerant_eq_day"]
        regen_add = {"Sodium": regen_eq * NA_EQ / 1000.0, "Chloride": regen_eq * CL_EQ / 1000.0}  # kg/day
        for prefix, bed in (("cation", cation), ("anion", anion)):
            if bed["bed_volume"] > 0.0 and bed["capacity_bed_volumes"] < 50.0:
                warnings.append(
                    f"The {prefix} bed is exhausted in {bed['capacity_bed_volumes']:.0f} bed volumes; "
                    "the ionic load is too high for ion exchange."
                )

    waste_m3_day = cation["waste_m3_day"] + anion["waste_m3_day"]
    recovery = max(1.0 - waste_m3_day / flow, 0.0) if flow > 0.0 else 1.0
    template_inputs = {**technical_inputs, "removal_efficiencies": removals, "recovery": recovery, "energy_intensity": 0.0}
    outputs = run_template(unit_process, template_inputs, stream, {"unit_kind": "none", "recovery": recovery})

    quality_out = outputs["water_quality_out"]
    if not demineralization:
        _set(quality_out, "Sodium", _q(quality_in, "Sodium") + added_mg_l["Sodium"])
        _set(quality_out, "Chloride", _q(quality_in, "Chloride") + added_mg_l["Chloride"])
        tds_in = _q(quality_in, "TDS")
        if tds_in > 0.0:
            tds_out = tds_in - removed_mass + added_mg_l["Sodium"] + added_mg_l["Chloride"]
            _set(quality_out, "TDS", tds_out)
            if "Conductivity" in quality_out:
                _set(quality_out, "Conductivity", _q(quality_in, "Conductivity") * tds_out / tds_in)
    outputs["water_quality_out"] = quality_out
    outputs["outlet_stream"]["water_quality"] = quality_out

    # Spent regenerant quality: mass balance plus the regenerant ions
    outlet_flow = outputs["outlet_flow"]["value"]
    brine_flow = outputs["brine_flow"]["value"]
    brine_quality = {}
    if brine_flow > 0.0:
        for parameter, entry in quality_in.items():
            if parameter == "pH":
                continue
            unit = entry.get("unit", "") if isinstance(entry, dict) else ""
            mass = _q(quality_in, parameter) * flow - _q(quality_out, parameter) * outlet_flow  # g/day
            mass += regen_add.get(parameter, 0.0) * 1000.0
            if parameter == "TDS":
                mass += sum(regen_add.values()) * 1000.0
            brine_quality[parameter] = {"value": max(mass / brine_flow, 0.0), "unit": unit}
    outputs["brine_water_quality"] = brine_quality

    # Pump energy through the beds: P = rho g H Q / eta
    pump_head = max(_input(technical_inputs, "pump_head", defaults["pump_head"]), 0.0)
    pump_efficiency = max(_input(technical_inputs, "pump_efficiency", defaults["pump_efficiency"]), 1e-9)
    treated_fraction = max(cation["fraction"], anion["fraction"])
    energy_intensity = 1000.0 * 9.80665 * pump_head / pump_efficiency / 3.6e6 * treated_fraction

    for prefix, bed in (("cation", cation), ("anion", anion)):
        if bed["capped"] and bed["bed_volume"] > 0.0:
            warnings.append(
                f"The {prefix} bed is regenerated at the maximum run length ({bed['bed_volumes']:.0f} bed volumes) "
                f"before its capacity is used ({bed['capacity_bed_volumes']:.0f} bed volumes)."
            )

    if demineralization:
        cation_label, anion_label = "HCl", "NaOH"
    else:
        cation_label = anion_label = "NaCl"
    outputs.update({
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "pump_power": _result(energy_intensity * flow / 24.0, "kW"),
        "bed_removal": _result(bed_removal, "fraction"),
        "cation_bed_removal_target": _result(cation_removal, "fraction"),
        "anion_bed_removal_target": _result(anion_removal, "fraction"),
        "cation_treated_fraction": _result(cation["fraction"], "fraction"),
        "anion_treated_fraction": _result(anion["fraction"], "fraction"),
        "cation_treated_flow": _result(cation["treated_flow"], "m3/day"),
        "anion_treated_flow": _result(anion["treated_flow"], "m3/day"),
        "cation_resin_volume": _result(cation["bed_volume"], "m3"),
        "anion_resin_volume": _result(anion["bed_volume"], "m3"),
        "cation_ionic_load": _result(cation["removed_eq_day"] / cation["treated_flow"] if cation["treated_flow"] > 0.0 else 0.0, "meq/L treated"),
        "anion_ionic_load": _result(anion["removed_eq_day"] / anion["treated_flow"] if anion["treated_flow"] > 0.0 else 0.0, "meq/L treated"),
        "cation_bed_volumes_per_cycle": _result(cation["bed_volumes"], "bed volumes"),
        "anion_bed_volumes_per_cycle": _result(anion["bed_volumes"], "bed volumes"),
        "cation_cycle_duration": _result(cation["cycle_days"], "day"),
        "anion_cycle_duration": _result(anion["cycle_days"], "day"),
        "cation_regeneration_ratio": _result(cation["regeneration_ratio"], "eq regenerant/eq removed"),
        "anion_regeneration_ratio": _result(anion["regeneration_ratio"], "eq regenerant/eq removed"),
        "sodium_added": _result(added_mg_l["Sodium"], "mg/L"),
        "chloride_added": _result(added_mg_l["Chloride"], "mg/L"),
        "spent_regenerant_flow": _result(waste_m3_day, "m3/day"),
        "spent_regenerant_generation": _result(waste_m3_day * 365.0, "m3/year"),
        # Regenerant use on a calendar-year basis; the cost model scales by operating days
        "annual_cation_regenerant_consumption": _result(cation["regenerant_kg_day"] * 365.0, f"kg {cation_label}/year"),
        "annual_anion_regenerant_consumption": _result(anion["regenerant_kg_day"] * 365.0, f"kg {anion_label}/year"),
        "model_warnings": _result(warnings, ""),
    })
    if not demineralization:
        outputs["annual_nacl_consumption"] = _result((cation["regenerant_kg_day"] + anion["regenerant_kg_day"]) * 365.0, "kg/year")
    else:
        outputs["annual_hcl_consumption"] = _result(cation["regenerant_kg_day"] * 365.0, "kg/year")
        outputs["annual_naoh_consumption"] = _result(anion["regenerant_kg_day"] * 365.0, "kg/year")
    return outputs


def run(unit_process, technical_inputs, stream):
    return run_ix(unit_process, technical_inputs, stream, demineralization=False)

"""Dissolved air flotation (DAF) with coagulation and H2O2 oxidation (NMSU assumptions).

Chemical dosing follows the NMSU DAF model:
- ACH (mg Al/L) and polymer (mg/L) doses are the combination at which the
  predicted TSS and Fe removals equal their targets in the removal-efficiency
  table. The dose-removal fits use the jar-test data of Abada et al. 2022
  (hypersaline produced water, DAF at pH 7.5, 12% recycle).
- H2O2 is dosed in proportion to the feed iron (1.75 mg H2O2 per mg Fe). COD
  removal is a function of the H2O2:Fe molar ratio and the H2O2 concentration,
  fitted to the Fenton oxidation data of Afzal et al. 2018. TOC removal is set
  equal to the COD removal. The removal table shows this calculated value;
  editing it there overrides the calculation.
- H2S is oxidized to elemental sulfur by the H2O2 left after Fe2+ oxidation
  (NMSU DAF model, SI Eq. B1.1): removed H2S = min(H2S_in, (r - 0.3045) x Fe / 0.998),
  with r the H2O2:Fe mass ratio (1.75 gives the 1.445 of the NMSU equation). Shown in
  the removal table and overridable in the same way as TOC.
Water recovery is calculated from the float volume (dry float mass / solids content).

Pump energy is the pressurised recycle: P = rho * g * H * (r * Q) / eta, plus an
auxiliary allowance for the air compressor, flocculators and float skimmer.
"""

from __future__ import annotations

import math

import numpy as np

from tea_models.technical_models.template_units import run_template
from tea_models.water_quality import get_default_removal_efficiencies


DEFAULTS = {
    "unit_kind": "daf",
    "energy_intensity": 0.0,
    "chemical_dose": 0.0,
    # Hydraulics and energy
    "recycle_ratio": 0.12,
    "pump_head": 51.0,  # m, saturator pressure about 5 bar
    "pump_efficiency": 0.70,
    "auxiliary_energy_intensity": 0.02,  # kWh/m3: air compressor, flocculators, skimmer
    # Chemicals
    "h2o2_to_iron_ratio": 1.75,  # mg H2O2 per mg feed Fe (pilot study)
    "ach_aluminum_content": 0.124,  # mass fraction Al in ACH product (23-24% Al2O3)
    "cod_to_toc_ratio": 4.0,  # used only to report COD
    # Float (sludge)
    "float_solids_content": 0.03,  # mass fraction of dry solids in the skimmed float
}

DEFAULT_TARGET_REMOVAL = 0.87  # used when the removal table has no TSS or Iron entry
OVERRIDE_TOLERANCE = 1e-4  # table value differing from the calculated default by more than this is an override

# Abada et al. 2022 jar tests (Fig. 2c-d and Fig. 3, DAF at pH 7.5 with chlorine, 12% recycle):
# (ACH mg Al/L, polymer mg/L, residual TSS mg/L, residual Fe mg/L). Residual TSS is the
# measured turbidity x 1.71 mg/L per NTU (feed TSS 134 mg/L / 78.3 NTU).
# Removal is calculated relative to the raw feed. The NMSU V1 model used the no-chemical
# DAF effluent (first row) as the basis, which left out the ~62% removed by DAF and the
# oxidant alone and overstated the doses needed for a given removal.
ABADA_FEED_TSS = 134.0  # mg/L (Abada et al. 2022, Table 1)
ABADA_FEED_FE = 15.6  # mg/L
ACH_POLYMER_DATA = [
    (0.0, 0.0, 51.4, 5.8),
    (25.0, 0.0, 22.3, 2.1),
    (50.0, 0.0, 18.8, 2.0),
    (75.0, 0.0, 30.8, 2.1),
    (25.0, 0.5, 22.3, 2.1),
    (25.0, 1.0, 11.1, 1.25),
    (25.0, 2.0, 7.7, 0.9),
    (25.0, 5.0, 6.8, 0.8),
    # Polymer only (anionic, 5 mg/L, no ACH): SI Fig. S1, 9.2 NTU and 2.38 mg/L Fe (preliminary test).
    (0.0, 5.0, 15.7, 2.38),
]
ACH_RANGE = (0.0, 75.0)
POLYMER_RANGE = (0.0, 5.0)

# Afzal et al. 2018 Fenton oxidation of produced water:
# (H2O2:Fe2+ molar ratio, H2O2 mol/L, COD removal %). The ratio-10 and ratio-75
# rows are swapped relative to the NMSU V1 table, which had them reversed; the
# corrected data peak at ratios 10-25 as in the paper (Fig. 2).
H2O2_COD_DATA = [
    (2, 0.001, 27.0), (2, 0.010, 38.5), (2, 0.101, 37.0), (2, 0.150, 30.0),
    (5, 0.001, 42.0), (5, 0.010, 51.0), (5, 0.101, 50.5), (5, 0.150, 42.0),
    (10, 0.001, 73.0), (10, 0.010, 93.0), (10, 0.101, 85.0), (10, 0.150, 73.0),
    (25, 0.001, 76.0), (25, 0.010, 91.0), (25, 0.101, 88.0), (25, 0.150, 73.0),
    (50, 0.001, 49.0), (50, 0.010, 78.0), (50, 0.101, 67.0), (50, 0.150, 64.0),
    (75, 0.001, 30.0), (75, 0.010, 60.0), (75, 0.101, 58.5), (75, 0.150, 52.0),
]
MOLAR_RATIO_RANGE = (2.0, 75.0)
H2O2_MOL_L_RANGE = (0.001, 0.150)

MW_FE = 55.845
MW_AL = 26.982
MW_H2O2 = 34.0147
MW_H2S = 34.081
MW_S = 32.065
H2O2_PER_FE = MW_H2O2 / (2.0 * MW_FE)  # mg H2O2 per mg Fe2+ oxidized to Fe3+ (0.3045)
H2O2_PER_H2S = MW_H2O2 / MW_H2S  # mg H2O2 per mg H2S oxidized to S (0.998)
AL_OH3_PER_AL = 78.003 / MW_AL  # kg Al(OH)3 per kg Al
FE_OH3_PER_FE = 106.867 / MW_FE  # kg Fe(OH)3 per kg Fe


def _ach_polymer_terms(ach, polymer):
    """Quadratic terms in ACH (A) and polymer (P) with the A x P interaction.

    The interaction is identified only by the polymer-only test. Without it the additive model
    under-predicts that test by 13 points (TSS) and 9 points (Fe) against a residual SD of 2-3
    points; with it adjusted R2 rises from 0.83 to 0.95 (TSS) and 0.85 to 0.90 (Fe).
    """
    ach = np.asarray(ach, dtype=float)
    polymer = np.asarray(polymer, dtype=float)
    return np.column_stack([np.ones_like(ach), ach, ach**2, polymer, polymer**2, ach * polymer])


def _fit_ach_polymer():
    data = np.array(ACH_POLYMER_DATA)
    tss_removal = (ABADA_FEED_TSS - data[:, 2]) / ABADA_FEED_TSS * 100.0
    fe_removal = (ABADA_FEED_FE - data[:, 3]) / ABADA_FEED_FE * 100.0
    terms = _ach_polymer_terms(data[:, 0], data[:, 1])
    tss_coef = np.linalg.lstsq(terms, tss_removal, rcond=None)[0]
    fe_coef = np.linalg.lstsq(terms, fe_removal, rcond=None)[0]
    return tss_coef, fe_coef, float(tss_removal.max()), float(fe_removal.max())


TSS_COEF, FE_COEF, MAX_MEASURED_TSS_REMOVAL, MAX_MEASURED_FE_REMOVAL = _fit_ach_polymer()


def predict_tss_fe_removal(ach, polymer):
    """Predicted TSS and Fe removal (%) for ACH (mg Al/L) and polymer (mg/L) doses."""
    terms = _ach_polymer_terms(np.atleast_1d(ach), np.atleast_1d(polymer))
    tss = np.clip(terms @ TSS_COEF, 0.0, 100.0)
    fe = np.clip(terms @ FE_COEF, 0.0, 100.0)
    return tss, fe


_ACH_GRID, _POLYMER_GRID = np.meshgrid(
    np.linspace(ACH_RANGE[0], ACH_RANGE[1], 751),
    np.linspace(POLYMER_RANGE[0], POLYMER_RANGE[1], 501),
)
_ACH_GRID = _ACH_GRID.ravel()
_POLYMER_GRID = _POLYMER_GRID.ravel()
_TSS_GRID, _FE_GRID = predict_tss_fe_removal(_ACH_GRID, _POLYMER_GRID)
_NO_CHEMICAL_TSS, _NO_CHEMICAL_FE = (float(v[0]) for v in predict_tss_fe_removal(0.0, 0.0))


# Relative chemical prices used only to choose the cheapest dose pair (default EPA WBS prices:
# ACH 0.4506 $/kg product at 12.4% Al, polymer 1.6344 $/kg). Costs use the prices in the cost inputs.
_SELECTION_PRICE_ACH_AL = 0.4506 / 0.124  # $/kg Al
_SELECTION_PRICE_POLYMER = 1.6344  # $/kg
_GRID_COST = _ACH_GRID * _SELECTION_PRICE_ACH_AL + _POLYMER_GRID * _SELECTION_PRICE_POLYMER


def select_ach_polymer_dose(target_tss_percent, target_fe_percent):
    """Cheapest ACH and polymer doses whose predicted TSS and Fe removals both meet the targets.

    Searched over the tested dose range (ACH 0-75 mg Al/L, polymer 0-5 mg/L). When no dose meets
    both targets, the dose whose predictions are closest to them is used (NMSU model criterion:
    minimise |R_TSS - target| + |R_Fe - target|).
    """
    meets = (_TSS_GRID >= target_tss_percent - 1e-9) & (_FE_GRID >= target_fe_percent - 1e-9)
    if meets.any():
        idx = int(np.argmin(np.where(meets, _GRID_COST, np.inf)))
    else:
        score = np.abs(_TSS_GRID - target_tss_percent) + np.abs(_FE_GRID - target_fe_percent)
        idx = int(np.argmin(score))
    return (
        float(_ACH_GRID[idx]),
        float(_POLYMER_GRID[idx]),
        float(_TSS_GRID[idx]),
        float(_FE_GRID[idx]),
    )


_COD_RATIOS = np.log10(sorted({row[0] for row in H2O2_COD_DATA}))
_COD_CONCS = np.log10(sorted({row[1] for row in H2O2_COD_DATA}))
_COD_GRID = np.array([
    [next(row[2] for row in H2O2_COD_DATA if row[0] == ratio and row[1] == conc) for conc in sorted({r[1] for r in H2O2_COD_DATA})]
    for ratio in sorted({r[0] for r in H2O2_COD_DATA})
])


def _interpolate_cod(log_ratio, log_conc):
    """Bilinear interpolation of the measured COD removals on log10(ratio) x log10(mol/L)."""
    i = int(np.clip(np.searchsorted(_COD_RATIOS, log_ratio) - 1, 0, len(_COD_RATIOS) - 2))
    j = int(np.clip(np.searchsorted(_COD_CONCS, log_conc) - 1, 0, len(_COD_CONCS) - 2))
    tx = (log_ratio - _COD_RATIOS[i]) / (_COD_RATIOS[i + 1] - _COD_RATIOS[i])
    ty = (log_conc - _COD_CONCS[j]) / (_COD_CONCS[j + 1] - _COD_CONCS[j])
    g = _COD_GRID
    return float(
        (1 - tx) * (1 - ty) * g[i, j] + tx * (1 - ty) * g[i + 1, j]
        + (1 - tx) * ty * g[i, j + 1] + tx * ty * g[i + 1, j + 1]
    )


def predict_cod_removal(molar_ratio, h2o2_mol_l):
    """COD removal (%) from the H2O2:Fe molar ratio and H2O2 concentration (mol/L).

    Interpolated between the measured points (Afzal et al. 2018) on log scales of
    ratio and concentration. Inputs are limited to the tested range. Below the
    lowest tested H2O2 concentration, removal is interpolated linearly to zero
    at zero dose.
    """
    if h2o2_mol_l <= 0.0:
        return 0.0
    ratio = min(max(molar_ratio, MOLAR_RATIO_RANGE[0]), MOLAR_RATIO_RANGE[1])
    conc = min(max(h2o2_mol_l, H2O2_MOL_L_RANGE[0]), H2O2_MOL_L_RANGE[1])
    removal = _interpolate_cod(math.log10(ratio), math.log10(conc))
    removal = min(max(removal, 0.0), 100.0)
    if h2o2_mol_l < H2O2_MOL_L_RANGE[0]:
        removal *= h2o2_mol_l / H2O2_MOL_L_RANGE[0]
    return removal


def _result(value, unit):
    return {"value": value, "unit": unit}


def _input(values, name, default):
    try:
        return float(values.get(name, default))
    except (TypeError, ValueError):
        return float(default)


def _quality_value(quality, parameter, default=0.0):
    try:
        return float((quality.get(parameter, {}) or {}).get("value", default) or default)
    except (TypeError, ValueError):
        return float(default)


def _fraction(removals, parameter, default):
    try:
        return min(max(float(removals.get(parameter, default)), 0.0), 1.0)
    except (TypeError, ValueError):
        return default


def calculated_toc_removal(feed_quality, h2o2_to_iron_ratio=None):
    """TOC (= COD) removal from the H2O2 dose set by feed iron (fraction)."""
    ratio_mass = DEFAULTS["h2o2_to_iron_ratio"] if h2o2_to_iron_ratio is None else max(float(h2o2_to_iron_ratio), 0.0)
    feed_fe = max(_quality_value(feed_quality or {}, "Iron"), 0.0)
    h2o2_mol_l = ratio_mass * feed_fe / 1000.0 / MW_H2O2
    return predict_cod_removal(ratio_mass * MW_FE / MW_H2O2, h2o2_mol_l) / 100.0


def calculated_h2s_removal(feed_quality, h2o2_to_iron_ratio=None):
    """H2S removal (fraction) by the H2O2 left after oxidizing the feed Fe2+ (SI Eq. B1.1)."""
    ratio_mass = DEFAULTS["h2o2_to_iron_ratio"] if h2o2_to_iron_ratio is None else max(float(h2o2_to_iron_ratio), 0.0)
    feed_fe = max(_quality_value(feed_quality or {}, "Iron"), 0.0)
    feed_h2s = max(_quality_value(feed_quality or {}, "H2S"), 0.0)
    if feed_h2s <= 0.0:
        return 0.0
    removed = min(feed_h2s, max(0.0, (ratio_mass - H2O2_PER_FE) * feed_fe / H2O2_PER_H2S))
    return removed / feed_h2s


def _apply_calculated(removals, parameter, calculated, calculated_at_default):
    """Use the calculated removal unless the table holds a different (user) value."""
    table_value = removals.get(parameter)
    if table_value is None:
        return calculated, False
    try:
        table_value = min(max(float(table_value), 0.0), 1.0)
    except (TypeError, ValueError):
        return calculated, False
    if abs(table_value - calculated_at_default) > OVERRIDE_TOLERANCE:
        return table_value, True
    return calculated, False


def run(unit_process, technical_inputs, stream):
    def get(name):
        return _input(technical_inputs, name, DEFAULTS[name])

    feed_quality = stream.get("water_quality", {}) or {}
    inlet_flow = max(float(stream.get("flow_m3_day", 0.0) or 0.0), 0.0)  # m3/day
    feed_fe = max(_quality_value(feed_quality, "Iron"), 0.0)
    feed_toc = max(_quality_value(feed_quality, "TOC"), 0.0)
    feed_tss = max(_quality_value(feed_quality, "TSS"), 0.0)
    feed_oil = max(_quality_value(feed_quality, "Oil"), 0.0)
    feed_h2s = max(_quality_value(feed_quality, "H2S"), 0.0)

    # Removal-efficiency table (TSS, Fe, oil and grease set by the user; TOC calculated unless overridden)
    table = technical_inputs.get("removal_efficiencies")
    if table is None:
        table = get_default_removal_efficiencies(unit_process, feed_quality)
    removals = dict(table)
    target_tss = _fraction(removals, "TSS", DEFAULT_TARGET_REMOVAL)
    target_fe = _fraction(removals, "Iron", DEFAULT_TARGET_REMOVAL)

    # 1) ACH and polymer doses
    ach_dose, polymer_dose, pred_tss, pred_fe = select_ach_polymer_dose(target_tss * 100.0, target_fe * 100.0)

    # 2) H2O2 dose and COD/TOC removal
    h2o2_ratio_mass = max(get("h2o2_to_iron_ratio"), 0.0)
    h2o2_dose = h2o2_ratio_mass * feed_fe  # mg/L
    h2o2_mol_l = h2o2_dose / 1000.0 / MW_H2O2
    h2o2_molar_ratio = h2o2_ratio_mass * MW_FE / MW_H2O2
    # The table shows the calculated values at the default H2O2 ratio; any other value is a user override.
    calculated_toc = calculated_toc_removal(feed_quality, h2o2_ratio_mass)
    toc_removal, toc_overridden = _apply_calculated(
        removals, "TOC", calculated_toc, calculated_toc_removal(feed_quality)
    )
    removals["TOC"] = toc_removal
    calculated_h2s = calculated_h2s_removal(feed_quality, h2o2_ratio_mass)
    h2s_removal, h2s_overridden = _apply_calculated(
        removals, "H2S", calculated_h2s, calculated_h2s_removal(feed_quality)
    )
    if feed_h2s > 0.0 or "H2S" in removals:
        removals["H2S"] = h2s_removal

    # 3) Float (sludge) and water recovery
    tss_removed = feed_tss * _fraction(removals, "TSS", 0.0)
    fe_removed = feed_fe * _fraction(removals, "Iron", 0.0)
    oil_removed = feed_oil * _fraction(removals, "Oil", 0.0)
    aluminum_kg_day = ach_dose * inlet_flow / 1000.0
    ach_content = max(get("ach_aluminum_content"), 1e-9)
    ach_kg_day = aluminum_kg_day / ach_content
    polymer_kg_day = polymer_dose * inlet_flow / 1000.0
    h2o2_kg_day = h2o2_dose * inlet_flow / 1000.0
    sulfur_kg_day = feed_h2s * h2s_removal * MW_S / MW_H2S * inlet_flow / 1000.0  # elemental S from H2S
    solids_kg_day = (
        tss_removed * inlet_flow / 1000.0
        + aluminum_kg_day * AL_OH3_PER_AL
        + fe_removed * inlet_flow / 1000.0 * FE_OH3_PER_FE
        + polymer_kg_day
        + sulfur_kg_day
    )
    oil_kg_day = oil_removed * inlet_flow / 1000.0
    float_dry_kg_day = solids_kg_day + oil_kg_day
    solids_content = min(max(get("float_solids_content"), 1e-6), 1.0)
    float_wet_m3_day = float_dry_kg_day / solids_content / 1000.0
    recovery = max(1.0 - float_wet_m3_day / inlet_flow, 0.0) if inlet_flow > 0.0 else 1.0

    template_inputs = {**technical_inputs, "removal_efficiencies": removals, "recovery": recovery}
    outputs = run_template(unit_process, template_inputs, stream, DEFAULTS)
    for key in ("surface_loading_rate", "daf_surface_area"):
        outputs.pop(key, None)

    # Energy: pressurised recycle pump plus auxiliary allowance
    recycle = max(get("recycle_ratio"), 0.0)
    pump_head = max(get("pump_head"), 0.0)
    pump_efficiency = max(get("pump_efficiency"), 1e-9)
    recycle_energy = 1000.0 * 9.80665 * pump_head * recycle / pump_efficiency / 3.6e6
    energy_intensity = recycle_energy + max(get("auxiliary_energy_intensity"), 0.0)

    cod_ratio = max(get("cod_to_toc_ratio"), 0.0)
    feed_cod = cod_ratio * feed_toc

    warnings = []
    if target_tss * 100.0 > MAX_MEASURED_TSS_REMOVAL + 1.0 or target_fe * 100.0 > MAX_MEASURED_FE_REMOVAL + 1.0:
        warnings.append(
            "TSS or Fe removal target is above the highest removal measured in the dosing data "
            f"({MAX_MEASURED_TSS_REMOVAL:.0f}% TSS, {MAX_MEASURED_FE_REMOVAL:.0f}% Fe); doses are extrapolated."
        )
    below_baseline = (
        target_tss * 100.0 < _NO_CHEMICAL_TSS - 1.0 and target_fe * 100.0 < _NO_CHEMICAL_FE - 1.0
    )
    if below_baseline and ach_dose == 0.0 and polymer_dose == 0.0:
        warnings.append(
            "TSS and Fe removal targets are below what DAF achieves with the oxidant alone "
            f"(about {_NO_CHEMICAL_TSS:.0f}% TSS, {_NO_CHEMICAL_FE:.0f}% Fe): no ACH or polymer is dosed."
        )
    elif pred_tss < target_tss * 100.0 - 1.0 or pred_fe < target_fe * 100.0 - 1.0:
        warnings.append("No ACH and polymer dose within 0-75 mg Al/L and 0-5 mg/L meets both removal targets.")
    if toc_overridden:
        warnings.append(f"TOC removal set in the removal table ({toc_removal:.1%}) replaces the calculated value ({calculated_toc:.1%}).")
    if h2s_overridden:
        warnings.append(f"H2S removal set in the removal table ({h2s_removal:.1%}) replaces the calculated value ({calculated_h2s:.1%}).")
    if feed_fe <= 0.0:
        warnings.append("Feed iron is zero or missing: no H2O2 is dosed and the calculated TOC and H2S removals are zero.")
    elif not H2O2_MOL_L_RANGE[0] <= h2o2_mol_l <= H2O2_MOL_L_RANGE[1]:
        warnings.append("H2O2 concentration is outside the tested range of the COD removal relationship.")

    outputs.update({
        "energy_intensity": _result(energy_intensity, "kWh/m3 feed"),
        "recycle_pump_energy": _result(recycle_energy, "kWh/m3 feed"),
        "pump_power": _result(energy_intensity * inlet_flow / 24.0, "kW"),
        "recycle_ratio": _result(recycle, "fraction"),
        "recycle_flow": _result(inlet_flow * recycle, "m3/day"),
        "target_tss_removal": _result(target_tss, "fraction"),
        "target_iron_removal": _result(target_fe, "fraction"),
        "ach_dose": _result(ach_dose, "mg Al/L"),
        "polymer_dose": _result(polymer_dose, "mg/L"),
        "predicted_tss_removal": _result(pred_tss / 100.0, "fraction"),
        "predicted_iron_removal": _result(pred_fe / 100.0, "fraction"),
        "feed_iron": _result(feed_fe, "mg/L"),
        "h2o2_dose": _result(h2o2_dose, "mg/L"),
        "h2o2_to_iron_molar_ratio": _result(h2o2_molar_ratio, "mol/mol"),
        "calculated_toc_removal": _result(calculated_toc, "fraction"),
        "toc_removal": _result(toc_removal, "fraction"),
        "toc_removal_source": _result("removal table (user)" if toc_overridden else "calculated", ""),
        "feed_h2s": _result(feed_h2s, "mg/L"),
        "calculated_h2s_removal": _result(calculated_h2s, "fraction"),
        "h2s_removal": _result(h2s_removal, "fraction"),
        "h2s_removal_source": _result("removal table (user)" if h2s_overridden else "calculated", ""),
        "h2s_removed": _result(feed_h2s * h2s_removal, "mg/L"),
        "elemental_sulfur_generation": _result(sulfur_kg_day, "kg/day"),
        "feed_cod": _result(feed_cod, "mg/L"),
        "outlet_cod": _result(feed_cod * (1.0 - toc_removal), "mg/L"),
        "aluminum_consumption": _result(aluminum_kg_day, "kg Al/day"),
        "ach_consumption": _result(ach_kg_day, "kg/day"),
        "polymer_consumption": _result(polymer_kg_day, "kg/day"),
        "h2o2_consumption": _result(h2o2_kg_day, "kg/day"),
        "chemical_consumption": _result(ach_kg_day + polymer_kg_day + h2o2_kg_day, "kg/day"),
        "float_solids_generation": _result(solids_kg_day, "kg dry/day"),
        "float_oil_generation": _result(oil_kg_day, "kg/day"),
        "float_dry_mass": _result(float_dry_kg_day, "kg/day"),
        "float_volume": _result(float_wet_m3_day, "m3/day"),
        "model_warnings": _result(warnings, ""),
    })
    return outputs

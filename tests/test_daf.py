import math

import pytest

from tea_models.cost_models import daf as daf_cost
from tea_models.cost_models.cost_utils import cost_index_factor_to_base
from tea_models.technical_models import daf


def _stream(flow=7909.6, fe=25.7, tss=375.0, oil=189.0, toc=103.6):
    quality = {
        "Iron": {"value": fe, "unit": "mg/L"},
        "TSS": {"value": tss, "unit": "mg/L"},
        "Oil": {"value": oil, "unit": "mg/L"},
        "TOC": {"value": toc, "unit": "mg/L"},
    }
    return {"flow_m3_day": flow, "water_quality": quality}


TABLE = {"Iron": 0.87, "TSS": 0.87, "Oil": 0.87}


def test_dose_fit_reproduces_jar_tests():
    tss, fe = daf.predict_tss_fe_removal([0.0, 25.0, 25.0], [0.0, 2.0, 5.0])
    # removal relative to the raw feed (TSS 134 mg/L, Fe 15.6 mg/L)
    assert tss[0] == pytest.approx(61.6, abs=1.0)  # DAF with oxidant, no coagulant
    assert fe[0] == pytest.approx(62.8, abs=1.5)
    assert tss[1] == pytest.approx(94.3, abs=1.0)
    assert fe[2] == pytest.approx(94.9, abs=1.0)
    assert daf.MAX_MEASURED_TSS_REMOVAL == pytest.approx(94.9, abs=0.1)


def test_target_below_no_chemical_removal_doses_nothing():
    stream = _stream()
    out = daf.run("DAF", {"removal_efficiencies": {"TSS": 0.5, "Iron": 0.5}}, stream)
    assert out["ach_dose"]["value"] == 0.0
    assert out["polymer_dose"]["value"] == 0.0
    assert any("oxidant alone" in w for w in out["model_warnings"]["value"])


def test_dose_selection_hits_both_targets():
    ach, polymer, tss, fe = daf.select_ach_polymer_dose(87.0, 87.0)
    assert 0.0 <= ach <= 75.0 and 0.0 <= polymer <= 5.0
    # cheapest dose meeting both targets: both reached, the binding one met closely
    assert tss >= 87.0 - 1e-6 and fe >= 87.0 - 1e-6
    assert min(tss, fe) == pytest.approx(87.0, abs=0.2)
    lower = daf.select_ach_polymer_dose(70.0, 70.0)
    assert lower[0] < ach and lower[1] < polymer


def test_cod_removal_increases_with_iron_and_is_zero_without_h2o2():
    ratio = 1.75 * daf.MW_FE / daf.MW_H2O2
    removals = [daf.predict_cod_removal(ratio, 1.75 * fe / 1000.0 / daf.MW_H2O2) for fe in (12.0, 19.5, 25.7, 49.8)]
    assert removals == sorted(removals)
    assert removals[-1] == pytest.approx(37.2, abs=0.5)
    assert daf.predict_cod_removal(10.0, 0.01) == pytest.approx(93.0)  # measured point (corrected ratio-10 row)
    assert daf.predict_cod_removal(75.0, 0.01) == pytest.approx(60.0)
    assert daf.predict_cod_removal(ratio, 0.0) == 0.0


def test_technical_model_reads_targets_and_calculates_toc():
    out = daf.run("DAF", {"removal_efficiencies": TABLE}, _stream())
    assert out["water_quality_out"]["TSS"]["value"] == pytest.approx(375.0 * 0.13)
    assert out["water_quality_out"]["Oil"]["value"] == pytest.approx(189.0 * 0.13)
    toc = out["toc_removal"]["value"]
    assert 0.3 < toc < 0.4
    assert out["toc_removal_source"]["value"] == "calculated"
    assert out["water_quality_out"]["TOC"]["value"] == pytest.approx(103.6 * (1.0 - toc))
    assert out["h2o2_dose"]["value"] == pytest.approx(1.75 * 25.7)
    assert out["ach_consumption"]["value"] == pytest.approx(out["ach_dose"]["value"] * 7909.6 / 1000.0 / 0.124)


def test_removal_table_shows_calculated_toc_and_accepts_override():
    from tea_models.water_quality import get_default_removal_efficiencies

    quality = _stream()["water_quality"]
    defaults = get_default_removal_efficiencies("DAF", quality)
    assert defaults["TSS"] == pytest.approx(0.87)
    assert defaults["TOC"] == pytest.approx(daf.calculated_toc_removal(quality))
    # Table at its default: calculated value is used
    out = daf.run("DAF", {"removal_efficiencies": defaults}, _stream())
    assert out["toc_removal_source"]["value"] == "calculated"
    # Default table with a different H2O2 ratio: still calculated, with the new ratio
    out = daf.run("DAF", {"removal_efficiencies": defaults, "h2o2_to_iron_ratio": 3.5}, _stream())
    assert out["toc_removal"]["value"] == pytest.approx(daf.calculated_toc_removal(quality, 3.5))
    # User edits the TOC entry: override wins
    out = daf.run("DAF", {"removal_efficiencies": {**defaults, "TOC": 0.20}}, _stream())
    assert out["toc_removal"]["value"] == pytest.approx(0.20)
    assert out["toc_removal_source"]["value"] == "removal table (user)"
    assert out["water_quality_out"]["TOC"]["value"] == pytest.approx(103.6 * 0.8)


def test_recovery_follows_float_volume():
    out = daf.run("DAF", {"removal_efficiencies": TABLE}, _stream())
    float_m3 = out["float_volume"]["value"]
    assert out["water_recovery"]["value"] == pytest.approx(1.0 - float_m3 / 7909.6)
    assert out["outlet_flow"]["value"] == pytest.approx(7909.6 - float_m3)
    wetter = daf.run("DAF", {"removal_efficiencies": TABLE, "float_solids_content": 0.02}, _stream())
    assert wetter["water_recovery"]["value"] < out["water_recovery"]["value"]
    assert "daf_surface_area" not in out


def test_energy_is_recycle_pump_plus_auxiliary():
    out = daf.run("DAF", {"removal_efficiencies": TABLE}, _stream())
    expected = 1000.0 * 9.80665 * 51.0 * 0.12 / 0.7 / 3.6e6 + 0.02
    assert out["energy_intensity"]["value"] == pytest.approx(expected)


def test_no_iron_means_no_h2o2_and_no_toc_removal():
    out = daf.run("DAF", {"removal_efficiencies": TABLE}, _stream(fe=0.0))
    assert out["h2o2_dose"]["value"] == 0.0
    assert out["water_quality_out"]["TOC"]["value"] == pytest.approx(103.6)
    assert any("iron" in w.lower() for w in out["model_warnings"]["value"])


def test_float_mass_balance():
    out = daf.run("DAF", {"removal_efficiencies": TABLE}, _stream())
    q = 7909.6
    expected_solids = (
        375.0 * 0.87 * q / 1000.0
        + out["aluminum_consumption"]["value"] * daf.AL_OH3_PER_AL
        + 25.7 * 0.87 * q / 1000.0 * daf.FE_OH3_PER_FE
        + out["polymer_consumption"]["value"]
    )
    assert out["float_solids_generation"]["value"] == pytest.approx(expected_solids)
    assert out["float_volume"]["value"] == pytest.approx(
        (expected_solids + 189.0 * 0.87 * q / 1000.0) / 0.03 / 1000.0
    )


def test_cost_model_capex_and_opex():
    tech = daf.run("DAF", {"removal_efficiencies": TABLE}, _stream())
    context = {"operating_days_per_year": 330.0, "electricity_price": 0.08, "investment_factor": 2.0, "base_currency_year": 2024}
    cost = daf_cost.run("DAF", tech, {}, context)
    bare = 313992.0 * (7909.6 / daf_cost.REFERENCE_FLOW_M3_DAY) ** 0.87 * cost_index_factor_to_base(context, 2018)
    assert cost["bare_equipment_capital_cost"]["value"] == pytest.approx(bare)
    assert cost["equipment_capital_cost"]["value"] == pytest.approx(bare)  # TIC = 1
    assert cost["installed_capital_cost"]["value"] == pytest.approx(2.0 * bare)
    chem_index = cost_index_factor_to_base(context, 2021)
    ach = tech["ach_consumption"]["value"] * 330.0 * 0.4506 * chem_index
    assert cost["ach_operating_cost"]["value"] == pytest.approx(ach)
    subtotal = (
        cost["energy_operating_cost"]["value"]
        + cost["chemical_operating_cost"]["value"]
        + 0.03 * bare
    )
    assert cost["total_annual_operating_cost"]["value"] == pytest.approx(1.2 * subtotal)
    assert cost["float_waste_volume"]["value"] == pytest.approx(tech["float_volume"]["value"] * 330.0)


def test_reference_cost_matches_watertap_curve_at_3_mgd():
    # WaterTAP zero-order DAF: 336,873 USD_2007 x (Q / 911.054 m3/h)^0.3182, at 3 MGD in 2018 $
    from tea_models.technical_models.helper_function import CostIndexFactor

    q = daf_cost.REFERENCE_FLOW_M3_DAY / 24.0
    watertap = 336873.359 * (q / 911.054) ** 0.3182 * CostIndexFactor(2007, 2018)
    assert watertap == pytest.approx(daf_cost.REFERENCE_CAPEX, rel=0.002)
    assert math.isclose(daf_cost.REFERENCE_FLOW_M3_DAY, 11356.2, rel_tol=1e-4)


def test_h2s_removal_follows_si_equation():
    # NMSU SI Eq. B1.1: removed H2S = min(H2S_in, 1.445 x Fe / 0.998) at 1.75 mg H2O2/mg Fe
    assert 1.75 - daf.H2O2_PER_FE == pytest.approx(1.445, abs=1e-3)
    assert daf.H2O2_PER_H2S == pytest.approx(0.998, abs=1e-3)
    quality = {**_stream(fe=12.0)["water_quality"], "H2S": {"value": 30.0, "unit": "mg/L"}}
    removed = 1.4455 * 12.0 / 0.998
    assert daf.calculated_h2s_removal(quality) == pytest.approx(removed / 30.0, rel=1e-3)
    quality["H2S"]["value"] = 5.0
    assert daf.calculated_h2s_removal(quality) == pytest.approx(1.0)


def test_h2s_in_removal_table_and_override():
    from tea_models.water_quality import get_default_removal_efficiencies

    stream = _stream(fe=12.0)
    stream["water_quality"]["H2S"] = {"value": 30.0, "unit": "mg/L"}
    defaults = get_default_removal_efficiencies("DAF", stream["water_quality"])
    assert defaults["H2S"] == pytest.approx(daf.calculated_h2s_removal(stream["water_quality"]))
    out = daf.run("DAF", {"removal_efficiencies": defaults}, stream)
    assert out["h2s_removal_source"]["value"] == "calculated"
    assert out["water_quality_out"]["H2S"]["value"] == pytest.approx(30.0 - 1.4455 * 12.0 / 0.998, rel=1e-3)
    assert out["elemental_sulfur_generation"]["value"] > 0.0
    out = daf.run("DAF", {"removal_efficiencies": {**defaults, "H2S": 0.9}}, stream)
    assert out["h2s_removal"]["value"] == pytest.approx(0.9)
    assert out["h2s_removal_source"]["value"] == "removal table (user)"


def test_no_h2s_in_feed_leaves_results_unchanged():
    out = daf.run("DAF", {"removal_efficiencies": TABLE}, _stream())
    assert "H2S" not in out["water_quality_out"]
    assert out["elemental_sulfur_generation"]["value"] == 0.0

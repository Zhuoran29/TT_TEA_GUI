import pytest

from tea_models.cost_models import electrocoagulation as ec_cost
from tea_models.cost_models.cost_utils import cost_index_factor_to_base
from tea_models.technical_models import electrocoagulation as ec


def _stream(flow=7909.6, tds=100000.0, tss=10.0):
    return {
        "flow_m3_day": flow,
        "water_quality": {
            "TDS": {"value": tds, "unit": "mg/L"},
            "TSS": {"value": tss, "unit": "mg/L"},
        },
    }


def test_al_dose_follows_nmsu_model_and_no_clarifier_volume():
    out = ec.run("Electrocoagulation", {"removal_efficiencies": {"TSS": 0.58}}, _stream())
    # area per flow = 567 m2 / 11,356 m3/d x (30 / 15 min); 200 A/m2; Faraday's law
    assert out["aluminum_dose"]["value"] == pytest.approx(160.8, abs=0.5)
    assert "clarifier_volume" not in out
    assert out["hydraulic_retention_time"]["unit"] == "min"


def test_cost_structure_tic_if_maintenance_no_labor_no_disposal():
    tech = ec.run("Electrocoagulation", {"removal_efficiencies": {"TSS": 0.58}}, _stream())
    context = {"operating_days_per_year": 330.0, "electricity_price": 0.08, "investment_factor": 2.0, "base_currency_year": 2024}
    cost = ec_cost.run("Electrocoagulation", tech, {}, context)
    bare = 1595666.0 * (7909.6 / 11356.0) ** 0.87 * cost_index_factor_to_base(context, 2024)
    assert cost["bare_equipment_capital_cost"]["value"] == pytest.approx(bare)
    assert cost["equipment_capital_cost"]["value"] == pytest.approx(bare)  # TIC 1
    assert cost["installed_capital_cost"]["value"] == pytest.approx(2.0 * bare)
    assert cost["maintenance_operating_cost"]["value"] == pytest.approx(0.03 * bare)
    for removed in ("labor_cost", "solid_disposal_operating_cost"):
        assert removed not in cost
    base = (
        cost["aluminum_operating_cost"]["value"]
        + cost["energy_operating_cost"]["value"]
        + cost["maintenance_operating_cost"]["value"]
    )
    assert cost["total_annual_operating_cost"]["value"] == pytest.approx(1.2 * base)


def test_recovery_follows_sludge_volume():
    out = ec.run("Electrocoagulation", {"removal_efficiencies": {"TSS": 0.58}}, _stream(tss=10.0))
    solids = (160.84 * 78.00 / 26.98 + 10.0 * 0.58) / 1000.0  # kg dry per m3 feed
    assert out["water_recovery"]["value"] == pytest.approx(1.0 - solids / 0.025 / 1000.0, rel=1e-3)
    wetter = ec.run("Electrocoagulation", {"removal_efficiencies": {"TSS": 0.58}, "sludge_solids_content": 0.0125}, _stream(tss=10.0))
    assert 1.0 - wetter["water_recovery"]["value"] == pytest.approx(2.0 * (1.0 - out["water_recovery"]["value"]), rel=1e-6)


def test_effluent_ph_rises_by_co2_stripping():
    pytest.importorskip("reaktoro")
    quality = {
        "pH": {"value": 6.4, "unit": ""},
        "Alkalinity": {"value": 132.0, "unit": "mg/L as CaCO3"},
        "TDS": {"value": 100000.0, "unit": "mg/L"},
        "Calcium": {"value": 1200.0, "unit": "mg/L"},
        "Magnesium": {"value": 295.0, "unit": "mg/L"},
        "Sodium": {"value": 33600.0, "unit": "mg/L"},
        "Chloride": {"value": 58900.0, "unit": "mg/L"},
        "Sulfate": {"value": 251.0, "unit": "mg/L"},
    }
    out = ec.run("Electrocoagulation", {}, {"flow_m3_day": 7909.6, "water_quality": quality})
    assert out["effluent_pH"]["value"] == pytest.approx(6.53, abs=0.03)
    assert out["water_quality_out"]["pH"]["value"] == pytest.approx(out["effluent_pH"]["value"])
    assert out["co2_stripped"]["value"] > 0.0


def test_ph_passed_through_without_alkalinity():
    quality = {"pH": {"value": 6.4, "unit": ""}, "TDS": {"value": 100000.0, "unit": "mg/L"}}
    out = ec.run("Electrocoagulation", {}, {"flow_m3_day": 7909.6, "water_quality": quality})
    assert out["water_quality_out"]["pH"]["value"] == pytest.approx(6.4)
    assert "effluent_pH" not in out

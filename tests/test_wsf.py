import pytest

from tea_models.cost_models import walnut_shell_filtration as wsf_cost
from tea_models.cost_models.cost_utils import cost_index_factor_to_base
from tea_models.technical_models import walnut_shell_filtration as wsf
from tea_models.water_quality import get_default_removal_efficiencies

QUALITY = {
    "Oil": {"value": 20.0, "unit": "mg/L"},
    "TSS": {"value": 50.0, "unit": "mg/L"},
    "TOC": {"value": 100.0, "unit": "mg/L"},
    "Iron": {"value": 3.0, "unit": "mg/L"},
}
CONTEXT = {"operating_days_per_year": 330.0, "electricity_price": 0.10, "investment_factor": 2.0, "base_currency_year": 2024}


def _tech(flow=7910.0):
    removals = get_default_removal_efficiencies("Walnut shell filtration", QUALITY)
    return wsf.run("Walnut shell filtration", {"removal_efficiencies": removals}, {"flow_m3_day": flow, "water_quality": QUALITY})


def test_default_removals_and_recovery():
    out = _tech()
    q = out["water_quality_out"]
    assert q["Oil"]["value"] == pytest.approx(20.0 * 0.2)
    assert q["TSS"]["value"] == pytest.approx(50.0 * 0.2)
    assert q["TOC"]["value"] == pytest.approx(100.0 * 0.4)
    assert q["Iron"]["value"] == pytest.approx(3.0 * 0.5)
    assert out["outlet_flow"]["value"] == pytest.approx(7910.0 * 0.99)
    assert out["energy_intensity"]["value"] == pytest.approx(0.17)
    assert "filter_area" not in out


def test_cost_model():
    tech = _tech()
    cost = wsf_cost.run("Walnut shell filtration", tech, {}, CONTEXT)
    bare = wsf_cost.reference_installed_capex(0.008993) * (7910.0 / wsf_cost.REFERENCE_FLOW_M3_DAY) ** 0.87 * cost_index_factor_to_base(CONTEXT, 2020)
    assert cost["bare_equipment_capital_cost"]["value"] == pytest.approx(bare)
    assert cost["equipment_capital_cost"]["value"] == pytest.approx(bare)
    assert cost["installed_capital_cost"]["value"] == pytest.approx(2.0 * bare)
    annual = 7910.0 * 330.0
    cleaning = annual * 0.0546 * cost_index_factor_to_base(CONTEXT, 2020)
    assert cost["media_cleaning_cost"]["value"] == pytest.approx(cleaning)
    subtotal = annual * 0.17 * 0.10 + cleaning + 0.03 * bare
    assert cost["total_annual_operating_cost"]["value"] == pytest.approx(1.2 * subtotal)


def test_v1_back_calculation_recovers_wsf_vendor_cost():
    # 0.008993 $/bbl x 7,200,000 bbl/yr / CRF(5%, 10 yr) = WSF vendor cost of 500,000 $
    assert wsf_cost.reference_crf() == pytest.approx(0.1295, abs=1e-4)
    assert wsf_cost.reference_installed_capex(0.008993) == pytest.approx(500000.0, rel=1e-3)
    tech = _tech(flow=wsf_cost.REFERENCE_FLOW_M3_DAY)
    cost = wsf_cost.run("Walnut shell filtration", tech, {}, {**CONTEXT, "base_currency_year": 2020})
    assert cost["bare_equipment_capital_cost"]["value"] == pytest.approx(500000.0, rel=1e-3)

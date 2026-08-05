import pytest

from tea_models.cost_models import ammonia_stripping as ammonia_stripping_cost
from tea_models.technical_models import ammonia_stripping


def test_ammonia_stripping_reads_feed_quality_and_targets_outlet_ammonia():
    stream = {
        "flow_m3_day": 1.0,
        "water_quality": {
            "Ammonia nitrogen": {"value": 11.0, "unit": "mg/L"},
            "TDS": {"value": 100000.0, "unit": "mg/L"},
        },
    }

    result = ammonia_stripping.run(
        "Ammonia stripping",
        {"target_ammonia_mg_l": 1.0},
        stream,
    )

    assert result["feed_ammonia"]["value"] == pytest.approx(11.0)
    assert result["outlet_ammonia"]["value"] == pytest.approx(1.0)
    assert result["ammonia_removal"]["value"] == pytest.approx(10.0 / 11.0)
    assert result["water_quality_out"]["Ammonia nitrogen"]["value"] == pytest.approx(1.0)
    assert result["water_quality_out"]["TDS"]["value"] == pytest.approx(100000.0)
    assert result["air_water_ratio"]["value"] == pytest.approx(26592.909090909088)


def test_ammonia_stripping_cost_uses_workbook_curve_at_one_mgd():
    technical_result = {"inlet_flow": {"value": ammonia_stripping_cost.M3_DAY_PER_MGD, "unit": "m3/day"}}

    result = ammonia_stripping_cost.run(
        "Ammonia stripping",
        technical_result,
        {},
        {"base_currency_year": 2021, "operating_days_per_year": 365},
    )

    assert result["installed_capital_cost"]["value"] == pytest.approx(2786001.3471833305)
    assert result["total_annual_operating_cost"]["value"] == pytest.approx(264383.27774303086)

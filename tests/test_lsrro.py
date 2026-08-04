import unittest

from tea_models.cost_models import lsrro as lsrro_cost
from tea_models.lsrro_core import BBL_TO_M3, calculate_recovery_fraction, predict_permeate
from tea_models.technical_models import lsrro


class LSRROModelTest(unittest.TestCase):
    def test_recovery_regression_uses_train_water_quality(self):
        quality = {
            "TDS": {"value": 108000.0, "unit": "mg/L"},
            "Hardness": {"value": 7250.0, "unit": "mg/L as CaCO3"},
            "Silica": {"value": 70.62, "unit": "mg/L"},
        }

        recovery, warnings = calculate_recovery_fraction(quality)

        self.assertAlmostEqual(recovery, 0.3778, places=4)
        self.assertEqual(warnings, [])

    def test_technical_model_predicts_lsrro_permeate_quality(self):
        stream = {
            "flow_m3_day": 50000.0 * BBL_TO_M3,
            "water_quality": {
                "TDS": {"value": 108000.0, "unit": "mg/L"},
                "Hardness": {"value": 7250.0, "unit": "mg/L as CaCO3"},
                "Silica": {"value": 70.62, "unit": "mg/L"},
                "Chloride": {"value": 63504.0, "unit": "mg/L"},
                "Ammonia nitrogen": {"value": 132.0, "unit": "mg/L"},
            },
        }

        result = lsrro.run("LSRRO", {}, stream)

        self.assertAlmostEqual(result["water_recovery"]["value"], 0.5, places=4)
        self.assertAlmostEqual(result["calculated_recovery"]["value"], 0.3778, places=4)
        self.assertAlmostEqual(result["energy_intensity"]["value"], 7.4687, places=4)
        self.assertAlmostEqual(
            result["water_quality_out"]["Chloride"]["value"],
            201.86,
            places=2,
        )
        self.assertAlmostEqual(
            result["water_quality_out"]["Ammonia nitrogen"]["value"],
            2.75,
            places=2,
        )
        self.assertGreater(result["brine_flow"]["value"], 0.0)
        self.assertIn("Chloride", result["brine_water_quality"])

    def test_negative_ammonia_regression_falls_back_to_average_removal(self):
        permeate, method = predict_permeate("Ammonia nitrogen", 50.0)

        self.assertEqual(method, "average_removal_fallback")
        self.assertAlmostEqual(permeate, 0.81, places=2)

    def test_cost_model_returns_unit_costs_without_lcow_or_crf(self):
        stream = {
            "flow_m3_day": 50000.0 * BBL_TO_M3,
            "water_quality": {
                "TDS": {"value": 108000.0, "unit": "mg/L"},
                "Hardness": {"value": 7250.0, "unit": "mg/L as CaCO3"},
                "Silica": {"value": 70.62, "unit": "mg/L"},
            },
        }
        technical = lsrro.run("LSRRO", {}, stream)
        context = {
            "operating_days_per_year": 365.0 * 0.90,
            "electricity_price": 0.05,
            "investment_factor": 1.66,
            "base_currency_year": 2024,
        }

        result = lsrro_cost.run("LSRRO", technical, {}, context)

        self.assertAlmostEqual(result["equipment_capital_cost"]["value"], 20.5e6)
        self.assertAlmostEqual(result["installed_capital_cost"]["value"], 34.03e6)
        self.assertNotIn("brine_disposal_operating_cost", result)
        self.assertNotIn("maintenance_replacement_cost", result)
        self.assertNotIn("lcow_usd_m3", result)
        self.assertNotIn("annualized_capex_usd_yr", result)


if __name__ == "__main__":
    unittest.main()

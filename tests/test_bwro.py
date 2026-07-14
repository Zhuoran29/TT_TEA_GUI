import unittest

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.unit_model_defaults import cost_defaults, technical_defaults
from treatment_config import get_treatment_train_config


class BWROIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.stream = {
            "flow_m3_day": 1000.0,
            "water_quality": {
                "TDS": {"value": 800.0, "unit": "mg/L"},
                "Chloride": {"value": 400.0, "unit": "mg/L"},
            },
        }
        self.technical = run_technical_model(
            "BWRO", dict(technical_defaults("BWRO")), self.stream
        )

    def test_technical_model_uses_feed_stream_and_product_sec(self):
        self.assertAlmostEqual(self.technical["inlet_flow"]["value"], 1000.0)
        self.assertAlmostEqual(self.technical["outlet_flow"]["value"], 800.0)
        self.assertAlmostEqual(self.technical["brine_flow"]["value"], 200.0)
        self.assertEqual(self.technical["energy_intensity"]["unit"], "kWh/m3 product")
        self.assertAlmostEqual(
            self.technical["required_feed_pressure"]["value"],
            8.233951318699553,
        )
        self.assertAlmostEqual(
            self.technical["energy_intensity"]["value"],
            0.33890732511027594,
        )

    def test_cost_model_preserves_product_rates_as_annual_costs(self):
        cost = run_cost_model(
            "BWRO",
            self.technical,
            dict(cost_defaults("BWRO")),
            {"operating_days_per_year": 330.0, "electricity_price": 0.1},
        )
        self.assertAlmostEqual(cost["annual_product_volume"]["value"], 264000.0)
        self.assertAlmostEqual(cost["annual_feed_volume"]["value"], 330000.0)
        self.assertAlmostEqual(
            cost["annual_product_volume"]["value"]
            + cost["annual_concentrate_volume"]["value"],
            cost["annual_feed_volume"]["value"],
        )
        self.assertAlmostEqual(
            cost["installed_capital_cost"]["value"], 1240845.608440998
        )
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"], 91688.97772055121
        )

    def test_legacy_ro_selection_and_train_positions_migrate_to_bwro(self):
        for water_type in ("Produced water", "Brackish groundwater"):
            train = get_treatment_train_config(
                "Surface water discharge", "Reverse osmosis (RO)", water_type
            )
            self.assertIn("BWRO", train["desalination"])
            self.assertNotIn("RO", train["desalination"])


if __name__ == "__main__":
    unittest.main()

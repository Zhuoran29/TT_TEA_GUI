import unittest

from tea_models.registry import run_technical_model


class PHAdjustmentTests(unittest.TestCase):
    def test_target_ph_input_sets_outlet_ph(self):
        stream = {
            "flow_m3_day": 1000.0,
            "water_quality": {
                "pH": {"value": 6.4, "unit": "-"},
                "TDS": {"value": 1000.0, "unit": "mg/L"},
            },
        }

        result = run_technical_model(
            "pH adjustment",
            {
                "recovery": 1.0,
                "target_pH": 8.2,
                "chemical_dose": 0.004,
                "energy_intensity": 0.003,
            },
            stream,
        )

        self.assertAlmostEqual(result["water_quality_out"]["pH"]["value"], 8.2)
        self.assertAlmostEqual(result["outlet_stream"]["water_quality"]["pH"]["value"], 8.2)
        self.assertAlmostEqual(result["water_quality_out"]["TDS"]["value"], 1000.0)


if __name__ == "__main__":
    unittest.main()

import unittest

from tea_models.water_quality import combine_streams


class WaterQualityStreamTests(unittest.TestCase):
    def test_combine_streams_adds_flow_and_weighted_quality(self):
        combined = combine_streams(
            {
                "flow_m3_day": 550.0,
                "water_quality": {
                    "TDS": {"value": 280000.0, "unit": "mg/L"},
                    "Chloride": {"value": 120000.0, "unit": "mg/L"},
                },
            },
            {
                "flow_m3_day": 90.0,
                "water_quality": {
                    "TDS": {"value": 4000.0, "unit": "mg/L"},
                    "Chloride": {"value": 1800.0, "unit": "mg/L"},
                },
            },
        )

        self.assertAlmostEqual(combined["flow_m3_day"], 640.0)
        self.assertAlmostEqual(
            combined["water_quality"]["TDS"]["value"],
            (550.0 * 280000.0 + 90.0 * 4000.0) / 640.0,
        )
        self.assertAlmostEqual(
            combined["water_quality"]["Chloride"]["value"],
            (550.0 * 120000.0 + 90.0 * 1800.0) / 640.0,
        )
        self.assertEqual(combined["water_quality"]["TDS"]["unit"], "mg/L")


if __name__ == "__main__":
    unittest.main()

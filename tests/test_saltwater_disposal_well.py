import unittest

from tea_models.registry import run_cost_model, run_technical_model


class SaltwaterDisposalWellTests(unittest.TestCase):
    def test_positive_disposal_flow_uses_single_well(self):
        technical = run_technical_model(
            "Saltwater disposal well",
            {
                "disposal_fraction": 1.0,
                "injection_well_capacity": 2000.0,
                "injection_pressure": 50.0,
                "pump_efficiency": 0.75,
                "energy_intensity": 0.0,
            },
            {"flow_m3_day": 5000.0, "water_quality": {}},
        )

        self.assertAlmostEqual(technical["disposed_flow"]["value"], 5000.0)
        self.assertEqual(technical["injection_well_count"]["value"], 1)

    def test_default_variable_cost_is_about_one_dollar_per_bbl(self):
        technical = run_technical_model(
            "Saltwater disposal well",
            {
                "disposal_fraction": 1.0,
                "injection_well_capacity": 2000.0,
                "injection_pressure": 50.0,
                "pump_efficiency": 0.75,
                "energy_intensity": 0.0,
            },
            {"flow_m3_day": 100.0, "water_quality": {}},
        )
        cost = run_cost_model(
            "Saltwater disposal well",
            technical,
            {},
            {"operating_days_per_year": 365.0, "electricity_price": 0.0, "investment_factor": 2.5},
        )

        self.assertAlmostEqual(cost["variable_operating_cost"]["value"], 100.0 * 365.0 * 6.29)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 0.0)
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            cost["variable_operating_cost"]["value"],
        )


if __name__ == "__main__":
    unittest.main()

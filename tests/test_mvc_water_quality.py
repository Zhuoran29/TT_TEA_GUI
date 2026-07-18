import unittest

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.water_quality import get_default_removal_efficiencies


class MVCWaterQualityTests(unittest.TestCase):
    def test_mvc_tds_removal_calibrates_130_gl_to_about_0_8_gl(self):
        stream = {
            "flow_m3_day": 1000.0,
            "water_quality": {
                "TDS": {"value": 130000.0, "unit": "mg/L"},
            },
        }
        technical = run_technical_model(
            "MVC",
            {
                "feed_tds_mass_fraction": 0.13,
                "feed_temperature": 25.0,
                "recovery": 0.45,
                "removal_efficiencies": get_default_removal_efficiencies(
                    "MVC",
                    stream["water_quality"],
                ),
            },
            stream,
        )

        self.assertAlmostEqual(
            technical["water_quality_out"]["TDS"]["value"],
            800.0,
            delta=1.0,
        )

    def test_mvc_column_multiplier_scales_capital_and_fixed_om(self):
        technical = {
            "inlet_flow": {"value": 1000.0, "unit": "m3/day"},
            "energy_intensity": {"value": 1.0, "unit": "kWh/m3 feed"},
            "evaporator_capex": {"value": 100.0, "unit": "USD"},
            "compressor_capex": {"value": 200.0, "unit": "USD"},
        }
        context = {
            "operating_days_per_year": 365.0,
            "electricity_price": 0.05,
            "investment_factor": 2.5,
        }
        base_cost = run_cost_model(
            "MVC",
            technical,
            {
                "capex_per_flow": 2100.0,
                "column_capex_multiplier": 1.0,
                "fixed_opex_fraction": 0.05,
                "variable_opex_per_m3": 0.0,
            },
            context,
        )
        standby_cost = run_cost_model(
            "MVC",
            technical,
            {
                "capex_per_flow": 2100.0,
                "column_capex_multiplier": 2.0,
                "fixed_opex_fraction": 0.05,
                "variable_opex_per_m3": 0.0,
            },
            context,
        )

        self.assertAlmostEqual(
            standby_cost["installed_capital_cost"]["value"],
            2.0 * base_cost["installed_capital_cost"]["value"],
        )
        self.assertAlmostEqual(
            standby_cost["fixed_operating_cost"]["value"],
            2.0 * base_cost["fixed_operating_cost"]["value"],
        )
        self.assertAlmostEqual(
            standby_cost["energy_operating_cost"]["value"],
            base_cost["energy_operating_cost"]["value"],
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from tea_models.registry import run_cost_model, run_technical_model


FLOW_M3_DAY = 7949.0
CONTEXT = {
    "operating_days_per_year": 365.0,
    "electricity_price": 0.05,
    "investment_factor": 2.5,
}


class GACIntegrationTests(unittest.TestCase):
    def test_feed_toc_model_matches_source_breakdown(self):
        technical = run_technical_model(
            "GAC",
            {
                "recovery": 0.995,
                "empty_bed_contact_time": 10.0,
                "media_bulk_density": 450.0,
                "energy_intensity": 0.14,
                "removal_efficiencies": {"TOC": 0.99},
            },
            {
                "flow_m3_day": FLOW_M3_DAY,
                "water_quality": {"TOC": {"value": 30.0, "unit": "mg/L"}},
            },
        )
        self.assertAlmostEqual(
            technical["breakthrough_bed_volumes"]["value"], 4000.0
        )
        self.assertAlmostEqual(
            technical["estimated_changeout_interval"]["value"], 27.77777777777778
        )

        cost = run_cost_model(
            "GAC",
            technical,
            {"capex_per_flow": 481.6, "fixed_opex_fraction": 0.04},
            CONTEXT,
        )
        annual_volume = FLOW_M3_DAY * 365.0
        self.assertAlmostEqual(cost["gac_media_cost_rate"]["value"], 0.642)
        self.assertAlmostEqual(cost["solid_disposal_cost_rate"]["value"], 0.012375)
        self.assertAlmostEqual(
            cost["energy_operating_cost"]["value"], annual_volume * 0.14 * 0.05
        )
        expected_variable = annual_volume * (0.642 + 0.012375 + 0.14 * 0.05)
        self.assertAlmostEqual(cost["variable_operating_cost"]["value"], expected_variable)
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            cost["fixed_operating_cost"]["value"] + expected_variable,
        )


class ZeoliteIntegrationTests(unittest.TestCase):
    def test_ammonia_cycle_and_cost_breakdown_match_source_model(self):
        technical = run_technical_model(
            "Zeolite",
            {
                "recovery": 0.995,
                "empty_bed_contact_time": 20.0,
                "media_bulk_density": 824.0,
                "energy_intensity": 0.04,
                "reference_feed_ammonia": 25.0,
                "reference_ammonia_removal": 0.90,
                "reference_breakthrough_bv": 645.0,
                "capacity_removal_coefficient": 0.55,
                "capacity_feed_coefficient": 0.0035,
                "capacity_factor_min": 0.45,
                "capacity_factor_max": 2.15,
                "removal_efficiencies": {"Ammonia nitrogen": 0.90},
            },
            {
                "flow_m3_day": FLOW_M3_DAY,
                "water_quality": {
                    "Ammonia nitrogen": {"value": 25.0, "unit": "mg/L"}
                },
            },
        )
        self.assertAlmostEqual(technical["breakthrough_bed_volumes"]["value"], 645.0)
        self.assertAlmostEqual(technical["cycle_duration"]["value"], 645.0 * 20.0 / 1440.0)

        cost = run_cost_model(
            "Zeolite",
            technical,
            {"capex_per_flow": 774.4, "fixed_opex_fraction": 0.04},
            CONTEXT,
        )
        positive_variable = sum(
            cost[name]["value"]
            for name in (
                "regeneration_salt_operating_cost",
                "zeolite_makeup_operating_cost",
                "zeolite_replacement_operating_cost",
                "solid_disposal_operating_cost",
                "energy_operating_cost",
            )
        )
        self.assertLess(cost["nh4cl_revenue_credit"]["value"], 0.0)
        self.assertAlmostEqual(
            cost["variable_operating_cost"]["value"],
            positive_variable + cost["nh4cl_revenue_credit"]["value"],
        )
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            cost["fixed_operating_cost"]["value"]
            + cost["variable_operating_cost"]["value"],
        )
        self.assertAlmostEqual(cost["regeneration_cycles"]["value"], 365.0 / (645.0 * 20.0 / 1440.0))


if __name__ == "__main__":
    unittest.main()

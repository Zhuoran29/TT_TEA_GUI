import unittest

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.technical_models.helper_function import CostIndexFactor


FLOW_M3_DAY = 7949.0
CONTEXT = {
    "operating_days_per_year": 365.0,
    "electricity_price": 0.05,
    "investment_factor": 2.5,
    "capital_recovery_factor": 0.08,
    "base_currency_year": 2024,
}


class GACIntegrationTests(unittest.TestCase):
    def test_bv_model_and_cost_breakdown_match_good_model(self):
        technical = run_technical_model(
            "GAC",
            {
                "recovery": 0.995,
                "empty_bed_contact_time": 10.0,
                "media_bulk_density": 450.0,
                "adsorber_bed_volume_m3": 78.783,
                "fresh_gac_mass_kg": 31513.0,
            },
            {
                "flow_m3_day": FLOW_M3_DAY,
                "water_quality": {"TOC": {"value": 30.0, "unit": "mg/L"}},
            },
        )
        expected_bv = 1.5e5 * 30.0**-1.85
        expected_changeout_days = expected_bv * 78.783 / FLOW_M3_DAY
        expected_usage = 31513.0 * 365.0 / expected_changeout_days
        self.assertAlmostEqual(technical["breakthrough_bed_volumes"]["value"], expected_bv)
        self.assertAlmostEqual(technical["estimated_changeout_interval"]["value"], expected_changeout_days)
        self.assertAlmostEqual(technical["annual_gac_usage"]["value"], expected_usage)

        cost = run_cost_model(
            "GAC",
            technical,
            {
                "reference_gac_capex": 1345660.0,
                "reference_capacity": 3760.0,
                "capex_scaling_exponent": 0.87,
                "gac_replacement_cost": 4.58,
                "gac_regeneration_cost": 4.28,
                "gac_replacement_regeneration_energy": 23.0,
                "regeneration_fraction": 0.80,
                "replacement_fraction": 0.20,
                "om_contingency_factor": 0.20,
            },
            CONTEXT,
        )
        cost_factor = CostIndexFactor(2025, 2024)
        replacement = expected_usage * 0.20 * 4.58 * cost_factor
        regeneration = expected_usage * 0.80 * 4.28 * cost_factor
        media_energy = expected_usage * 23.0 * 0.05
        self.assertAlmostEqual(cost["gac_replacement_operating_cost"]["value"], replacement)
        self.assertAlmostEqual(cost["gac_regeneration_operating_cost"]["value"], regeneration)
        self.assertAlmostEqual(cost["gac_replacement_regeneration_energy_cost"]["value"], media_energy)
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            (replacement + regeneration + media_energy) * 1.20,
        )

    def test_gac_reference_capex_scales_capital_only(self):
        technical = run_technical_model(
            "GAC",
            {"recovery": 0.995},
            {
                "flow_m3_day": FLOW_M3_DAY,
                "water_quality": {"TOC": {"value": 30.0, "unit": "mg/L"}},
            },
        )
        base_cost = run_cost_model(
            "GAC",
            technical,
            {"reference_gac_capex": 1345660.0, "reference_capacity": 3760.0},
            CONTEXT,
        )
        doubled_cost = run_cost_model(
            "GAC",
            technical,
            {"reference_gac_capex": 2.0 * 1345660.0, "reference_capacity": 3760.0},
            CONTEXT,
        )

        self.assertAlmostEqual(
            doubled_cost["installed_capital_cost"]["value"],
            2.0 * base_cost["installed_capital_cost"]["value"],
        )
        self.assertAlmostEqual(
            doubled_cost["total_annual_operating_cost"]["value"],
            base_cost["total_annual_operating_cost"]["value"],
        )


class ZeoliteIntegrationTests(unittest.TestCase):
    def test_ammonia_cycle_and_cost_breakdown_match_good_model(self):
        technical = run_technical_model(
            "Zeolite",
            {
                "recovery": 0.995,
                "empty_bed_contact_time": 20.0,
                "media_bulk_density": 824.0,
                "energy_intensity": 0.02,
                "ammonia_removal": 0.95,
                "aec_mg_n_g": 4.0,
            },
            {
                "flow_m3_day": FLOW_M3_DAY,
                "water_quality": {
                    "Ammonia nitrogen": {"value": 25.0, "unit": "mg/L"}
                },
            },
        )
        bench_bv = 482.3 + (95.0 - 99.8) * (558.7 - 482.3) / (89.4 - 99.8)
        bench_feed_avg = sum(
            [
                24.9, 24.9, 23.9, 24.5, 24.8, 25.3, 25.3, 25.0, 24.8,
                24.8, 25.3, 24.5, 24.5, 21.6, 21.6,
            ]
        ) / 15.0
        adjusted_bv = bench_bv * bench_feed_avg / 25.0
        self.assertAlmostEqual(technical["bench_breakthrough_bv"]["value"], bench_bv)
        self.assertAlmostEqual(technical["breakthrough_bed_volumes"]["value"], adjusted_bv)
        self.assertAlmostEqual(technical["cycle_duration"]["value"], adjusted_bv * 20.0 / 1440.0)

        cost = run_cost_model(
            "Zeolite",
            technical,
            {
                "equipment_capex_per_gpm": 150.0,
                "zeolite_price": 4.41,
                "nh4cl_price": 57.5,
                "om_contingency_factor": 0.20,
            },
            CONTEXT,
        )
        self.assertLess(cost["nh4cl_revenue_credit"]["value"], 0.0)
        positive_opex = (
            cost["energy_operating_cost"]["value"]
            + cost["zeolite_media_replacement_cost"]["value"]
        )
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            positive_opex * 1.20 + cost["nh4cl_revenue_credit"]["value"],
        )

    def test_zeolite_capex_per_gpm_scales_capital_only(self):
        technical = run_technical_model(
            "Zeolite",
            {"recovery": 0.995, "ammonia_removal": 0.95},
            {
                "flow_m3_day": FLOW_M3_DAY,
                "water_quality": {
                    "Ammonia nitrogen": {"value": 25.0, "unit": "mg/L"}
                },
            },
        )
        base_cost = run_cost_model(
            "Zeolite",
            technical,
            {"equipment_capex_per_gpm": 150.0},
            CONTEXT,
        )
        doubled_cost = run_cost_model(
            "Zeolite",
            technical,
            {"equipment_capex_per_gpm": 300.0},
            CONTEXT,
        )

        self.assertAlmostEqual(
            doubled_cost["installed_capital_cost"]["value"],
            2.0 * base_cost["installed_capital_cost"]["value"],
        )
        self.assertAlmostEqual(
            doubled_cost["total_annual_operating_cost"]["value"],
            base_cost["total_annual_operating_cost"]["value"],
        )


if __name__ == "__main__":
    unittest.main()

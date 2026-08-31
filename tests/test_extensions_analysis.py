import copy
import unittest

from tea_models.analyses.scenario_comparison import (
    BBL_PER_M3,
    comparison_rows,
    create_scenario_snapshot,
    water_quality_comparison_rows,
    water_quality_for_snapshot,
)
from tea_models.analyses.sensitivity import apply_system_parameter, tornado_rows
from tea_models.tea_engine import calculate_crf, ordered_units_from_train


def sample_state():
    return {
        "project_name": "Example",
        "influent_type": "Produced water",
        "conc_level": "Low",
        "ffp_scenarios": ["Surface water discharge"],
        "desal_type": "MVC",
        "treatment_train": {"pretreatment": ["3-phase separator"]},
        "tea_context": {"operating_days_per_year": 365.0, "base_currency_year": 2024},
        "feedwater_quality": {"water_quality": {"TDS": {"value": 100.0, "unit": "mg/L"}}},
        "tea_unit_inputs": {"technical": {}, "cost": {}, "removal_efficiencies": {}},
        "tea_results_signature": "signature",
        "tea_results": {
            "levelized_cost_of_water": BBL_PER_M3,
            "levelized_cost_unit": "$/m3 feed",
            "total_capital_cost": 1000.0,
            "total_annual_operating_cost": 100.0,
            "total_annual_cost": BBL_PER_M3 * 365.0,
            "final_product_flow": BBL_PER_M3,
            "final_product_flow_unit": "bbl/day",
            "electricity_intensity_kwh_per_bbl_feed": 0.5,
            "thermal_energy_intensity_kwh_per_bbl_feed": 0.2,
            "unit_results": [],
            "water_quality_trace": [
                {
                    "sequence": 0,
                    "water_quality": {"TDS": {"value": 100.0, "unit": "mg/L"}},
                },
                {
                    "sequence": 1,
                    "water_quality": {"TDS": {"value": 10.0, "unit": "mg/L"}},
                },
            ],
        },
    }


class ScenarioComparisonTests(unittest.TestCase):
    def test_snapshot_is_deep_copy(self):
        state = sample_state()
        snapshot = create_scenario_snapshot("Baseline", state)
        state["tea_results"]["total_capital_cost"] = 9999.0
        state["treatment_train"]["pretreatment"].append("Ultrafiltration")

        self.assertEqual(snapshot["results"]["total_capital_cost"], 1000.0)
        self.assertEqual(snapshot["treatment_train"]["pretreatment"], ["3-phase separator"])

    def test_comparison_normalizes_flow_and_lcow_to_bbl(self):
        snapshot = create_scenario_snapshot("Baseline", sample_state())
        row = comparison_rows([snapshot])[0]

        self.assertAlmostEqual(row["Feed LCOW ($/bbl feed)"], 1.0)
        self.assertAlmostEqual(row["Product LCOW ($/bbl product)"], 1.0)
        self.assertAlmostEqual(row["Product flow (m3/day)"], 1.0)

    def test_water_quality_uses_union_and_leaves_missing_values_blank(self):
        first = create_scenario_snapshot("First", sample_state())
        second_state = sample_state()
        second_state["feedwater_quality"]["water_quality"] = {
            "Boron": {"value": 2.0, "unit": "mg/L"}
        }
        second = create_scenario_snapshot("Second", second_state)

        rows = water_quality_comparison_rows([first, second], "influent")
        tds = next(row for row in rows if row["Parameter"] == "TDS")
        boron = next(row for row in rows if row["Parameter"] == "Boron")

        self.assertEqual(tds["First"], 100.0)
        self.assertEqual(tds["Second"], "")
        self.assertEqual(boron["First"], "")
        self.assertEqual(boron["Second"], 2.0)

    def test_conflicting_water_quality_units_are_kept_on_separate_rows(self):
        first = create_scenario_snapshot("First", sample_state())
        second_state = sample_state()
        second_state["feedwater_quality"]["water_quality"]["TDS"] = {
            "value": 0.1,
            "unit": "g/L",
        }
        second = create_scenario_snapshot("Second", second_state)

        rows = water_quality_comparison_rows([first, second], "influent")
        tds_rows = [row for row in rows if row["Parameter"] == "TDS"]

        self.assertEqual([row["Unit"] for row in tds_rows], ["mg/L", "g/L"])
        self.assertEqual(tds_rows[0]["Second"], "")
        self.assertEqual(tds_rows[1]["First"], "")

    def test_effluent_uses_final_non_brine_unit_for_older_snapshots(self):
        snapshot = create_scenario_snapshot("Legacy", sample_state())
        snapshot["results"].pop("water_quality_trace")
        snapshot["results"]["unit_results"] = [
            {
                "sequence": 1,
                "section": "Post-treatment",
                "technical_results": {
                    "water_quality_out": {"TDS": {"value": 5.0, "unit": "mg/L"}}
                },
            },
            {
                "sequence": 2,
                "section": "Brine management - Disposal",
                "technical_results": {
                    "water_quality_out": {"TDS": {"value": 500.0, "unit": "mg/L"}}
                },
            },
        ]

        quality = water_quality_for_snapshot(snapshot, "effluent")
        self.assertEqual(quality["TDS"]["value"], 5.0)


class SensitivityHelpersTests(unittest.TestCase):
    def test_feed_flow_updates_all_dependent_flow_fields_without_mutating_baseline(self):
        context = {
            "feed_flow_m3_day": 10.0,
            "feed_flow_bbl_day": 10.0 * BBL_PER_M3,
            "feed_flow_display_unit": "bbl/day",
        }
        quality = {"flow": {"value": 10.0 * BBL_PER_M3, "unit": "bbl/day"}}
        original_context = copy.deepcopy(context)
        original_quality = copy.deepcopy(quality)

        varied_context, varied_quality = apply_system_parameter(
            context, quality, "feed_flow", 20.0
        )

        self.assertEqual(context, original_context)
        self.assertEqual(quality, original_quality)
        self.assertAlmostEqual(varied_context["feed_flow_bbl_day"], 20.0 * BBL_PER_M3)
        self.assertAlmostEqual(varied_context["feed_flow_display_value"], 20.0 * BBL_PER_M3)
        self.assertAlmostEqual(varied_quality["flow"]["value"], 20.0 * BBL_PER_M3)

    def test_discount_rate_recalculates_crf(self):
        context = {
            "discount_rate_percent": 8.0,
            "project_life_years": 20.0,
            "capital_recovery_factor": 0.0,
        }
        varied, _ = apply_system_parameter(context, {}, "discount_rate", 10.0)
        self.assertAlmostEqual(varied["capital_recovery_factor"], calculate_crf(10.0, 20.0))

    def test_tornado_sort_uses_largest_absolute_effect(self):
        rows = [
            {"Parameter": "A", "Case": "Low", "Output impact (%)": -2.0},
            {"Parameter": "A", "Case": "High", "Output impact (%)": 2.0},
            {"Parameter": "B", "Case": "Low", "Output impact (%)": -5.0},
            {"Parameter": "B", "Case": "High", "Output impact (%)": 4.0},
        ]
        self.assertEqual(tornado_rows(rows)[0]["Parameter"], "B")

    def test_ordered_units_preserves_legacy_unit_migrations(self):
        train = {
            "pretreatment": [],
            "desalination": ["RO", "VMD"],
            "posttreatment": [],
            "brine_category": "Brine disposal",
            "brine": [],
        }
        units = ordered_units_from_train(train)
        self.assertEqual([unit["unit_process"] for unit in units], [
            "BWRO", "Vacuum membrane distillation (VMD)"
        ])


if __name__ == "__main__":
    unittest.main()

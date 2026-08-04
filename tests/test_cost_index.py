import unittest

from tea_models.cost_models.cost_utils import escalate_cost, scaled_capex_from_unit_cost
from tea_models.technical_models.helper_function import CostIndexFactor


class CostIndexAndScalingTests(unittest.TestCase):
    def test_cost_year_metadata_escalates_to_base_currency_year(self):
        value = escalate_cost(
            100.0,
            {"_cost_years": {"capex_per_flow": 2024}},
            "capex_per_flow",
            {"base_currency_year": 2025},
        )

        self.assertAlmostEqual(value, 100.0 * CostIndexFactor(2024, 2025))

    def test_scaling_exponent_keeps_linear_default(self):
        capex = scaled_capex_from_unit_cost(
            100.0,
            2500.0,
            {"reference_capacity": 1000.0, "capex_scaling_exponent": 1.0},
            {"base_currency_year": 2024},
        )

        self.assertAlmostEqual(capex, 250000.0)

    def test_scaling_exponent_changes_capacity_curve(self):
        capex = scaled_capex_from_unit_cost(
            100.0,
            4000.0,
            {"reference_capacity": 1000.0, "capex_scaling_exponent": 0.6},
            {"base_currency_year": 2024},
        )

        self.assertAlmostEqual(capex, 100.0 * 1000.0 * 4.0**0.6)


if __name__ == "__main__":
    unittest.main()

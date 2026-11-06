import unittest

from tea_models.cost_models import lsrro as lsrro_cost
from tea_models.lsrro_core import (
    BBL_TO_M3,
    INTERPOLATED_COLUMNS,
    calculate_recovery_fraction,
    load_design_table,
    lookup_design,
    predict_permeate,
)
from tea_models.technical_models import lsrro


def _row(tds, rec, stages, sec, lcow):
    row = {key: 1.0 for key in INTERPOLATED_COLUMNS}
    row.update(feed_tds_g_l=tds, recovery=rec, stages=float(stages), sec_kwh_m3_product=sec,
               equipment_capex_usd_per_m3d_feed=100.0 * sec, watertap_lcow_usd_m3_product=lcow)
    return row


# {TDS: {recovery: {stages: row}}}; at 50 g/L, 1 stage is infeasible at 60% recovery
SYNTHETIC = {
    50.0: {0.4: {1: _row(50.0, 0.4, 1, 10.0, 1.0), 2: _row(50.0, 0.4, 2, 12.0, 1.2)},
           0.6: {2: _row(50.0, 0.6, 2, 20.0, 2.0)}},
    70.0: {0.4: {1: _row(70.0, 0.4, 1, 30.0, 3.0), 2: _row(70.0, 0.4, 2, 31.0, 3.5)},
           0.5: {1: _row(70.0, 0.5, 1, 40.0, 4.0), 2: _row(70.0, 0.5, 2, 41.0, 4.5)}},
}
FEED = {
    "TDS": {"value": 108000.0, "unit": "mg/L"},
    "Hardness": {"value": 7250.0, "unit": "mg/L as CaCO3"},
    "Silica": {"value": 70.62, "unit": "mg/L"},
    "Chloride": {"value": 63504.0, "unit": "mg/L"},
    "Ammonia nitrogen": {"value": 132.0, "unit": "mg/L"},
}
CONTEXT = {"operating_days_per_year": 365.0 * 0.90, "electricity_price": 0.05, "investment_factor": 1.66, "base_currency_year": 2024}


class DesignTableTests(unittest.TestCase):
    def test_interpolation_within_one_stage_count(self):
        design, warnings = lookup_design(70.0, 0.45, SYNTHETIC)
        self.assertEqual(design["stages"], 1)
        self.assertAlmostEqual(design["sec_kwh_m3_product"], 35.0)
        self.assertEqual(warnings, [])

    def test_stage_count_feasible_at_all_neighbors_is_used(self):
        # 1 stage is infeasible at 50 g/L and 60%, so the 2-stage designs are interpolated
        design, _ = lookup_design(50.0, 0.5, SYNTHETIC)
        self.assertEqual(design["stages"], 2)
        self.assertAlmostEqual(design["sec_kwh_m3_product"], 16.0)

    def test_grid_point_returns_lowest_lcow_design(self):
        design, _ = lookup_design(50.0, 0.4, SYNTHETIC)
        self.assertEqual(design["stages"], 1)
        self.assertAlmostEqual(design["sec_kwh_m3_product"], 10.0)

    def test_tds_interpolation(self):
        design, _ = lookup_design(60.0, 0.4, SYNTHETIC)
        self.assertEqual(design["stages"], 1)
        self.assertAlmostEqual(design["sec_kwh_m3_product"], 20.0)

    def test_recovery_above_feasible_range_is_clamped_with_warning(self):
        design, warnings = lookup_design(70.0, 0.55, SYNTHETIC)
        self.assertAlmostEqual(design["sec_kwh_m3_product"], 40.0)
        self.assertTrue(any("feasible range" in w for w in warnings))

    def test_tds_outside_table_is_clamped_with_warning(self):
        design, warnings = lookup_design(30.0, 0.4, SYNTHETIC)
        self.assertAlmostEqual(design["sec_kwh_m3_product"], 10.0)
        self.assertTrue(any("outside the WaterTAP" in w for w in warnings))

    def test_table_reproduces_watertap_reference_point(self):
        # direct WaterTAP solve at 108 g/L, 37.8%: 3 stages, SEC 20.46 kWh/m3 product
        design, warnings = lookup_design(108.0, 0.378)
        self.assertEqual(design["stages"], 3)
        self.assertAlmostEqual(design["sec_kwh_m3_product"], 20.46, delta=0.03 * 20.46)
        self.assertGreater(design["pump_capex_usd_per_m3d_feed"], design["erd_capex_usd_per_m3d_feed"])
        self.assertEqual(warnings, [])

    def test_table_has_one_lowest_lcow_design_per_point(self):
        for line in load_design_table().values():
            for designs in line.values():
                self.assertEqual(sum(row["lowest_lcow"] for row in designs.values()), 1)


class LSRROModelTest(unittest.TestCase):
    def test_recovery_regression_uses_train_water_quality(self):
        recovery, warnings = calculate_recovery_fraction(FEED)
        self.assertAlmostEqual(recovery, 0.3778, places=4)
        self.assertEqual(warnings, [])

    def test_default_recovery_is_the_correlation_and_energy_from_table(self):
        stream = {"flow_m3_day": 50000.0 * BBL_TO_M3, "water_quality": FEED}
        result = lsrro.run("LSRRO", {}, stream)
        self.assertAlmostEqual(result["water_recovery"]["value"], 0.3778, places=4)
        design, _ = lookup_design(108.0, result["water_recovery"]["value"])
        self.assertAlmostEqual(result["energy_intensity"]["value"], design["sec_kwh_m3_product"] * 0.3778, places=2)
        self.assertAlmostEqual(result["water_quality_out"]["Chloride"]["value"], 201.86, places=2)
        self.assertAlmostEqual(result["water_quality_out"]["Ammonia nitrogen"]["value"], 2.75, places=2)
        self.assertIn("Chloride", result["brine_water_quality"])

    def test_manual_recovery_overrides_correlation(self):
        stream = {"flow_m3_day": 1000.0, "water_quality": FEED}
        result = lsrro.run("LSRRO", {"recovery": 0.30}, stream)
        self.assertAlmostEqual(result["water_recovery"]["value"], 0.30)
        self.assertAlmostEqual(result["outlet_flow"]["value"], 300.0)

    def test_negative_ammonia_regression_falls_back_to_average_removal(self):
        permeate, method = predict_permeate("Ammonia nitrogen", 50.0)
        self.assertEqual(method, "average_removal_fallback")
        self.assertAlmostEqual(permeate, 0.81, places=2)

    def test_cost_structure(self):
        stream = {"flow_m3_day": 50000.0 * BBL_TO_M3, "water_quality": FEED}
        technical = lsrro.run("LSRRO", {}, stream)
        cost = lsrro_cost.run("LSRRO", technical, {}, CONTEXT)
        bare = cost["bare_equipment_capital_cost"]["value"]
        self.assertAlmostEqual(
            bare,
            cost["membrane_equipment_cost"]["value"] + cost["pump_equipment_cost"]["value"] + cost["erd_equipment_cost"]["value"],
        )
        index = 798.8 / 603.1
        expected_bare = (
            technical["membrane_equipment_cost_per_feed"]["value"]
            + technical["pump_equipment_cost_per_feed"]["value"]
            + technical["erd_equipment_cost_per_feed"]["value"]
        ) * index * 50000.0 * BBL_TO_M3
        self.assertAlmostEqual(bare, expected_bare, delta=1e-6 * bare)
        direct = cost["equipment_capital_cost"]["value"]
        self.assertAlmostEqual(direct, 2.0 * bare)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 1.66 * direct)
        self.assertAlmostEqual(cost["maintenance_operating_cost"]["value"], 0.02 * direct)
        subtotal = sum(cost[k]["value"] for k in (
            "electricity_operating_cost", "membrane_replacement_cost", "maintenance_operating_cost", "antiscalant_cost", "cip_cost"))
        self.assertAlmostEqual(cost["total_annual_operating_cost"]["value"], 1.2 * subtotal)
        self.assertNotIn("labor_cost", cost)

    def test_capex_scales_with_exponent(self):
        stream = {"flow_m3_day": 50000.0 * BBL_TO_M3, "water_quality": FEED}
        big = dict(stream, flow_m3_day=2 * stream["flow_m3_day"])
        c1 = lsrro_cost.run("LSRRO", lsrro.run("LSRRO", {}, stream), {}, CONTEXT)
        c2 = lsrro_cost.run("LSRRO", lsrro.run("LSRRO", {}, big), {}, CONTEXT)
        self.assertAlmostEqual(c2["bare_equipment_capital_cost"]["value"] / c1["bare_equipment_capital_cost"]["value"], 2 ** 0.81, places=6)


if __name__ == "__main__":
    unittest.main()

import math
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
    TOC = 30.0

    def _technical(self, flow=FLOW_M3_DAY, **inputs):
        return run_technical_model(
            "GAC",
            {"recovery": 0.995, **inputs},
            {"flow_m3_day": flow, "water_quality": {"TOC": {"value": self.TOC, "unit": "mg/L"}}},
        )

    def test_bed_sizing_parallel_vessels_and_bed_life(self):
        technical = self._technical()
        bed_volume = FLOW_M3_DAY / 1440.0 * 10.0
        self.assertAlmostEqual(technical["media_bed_volume"]["value"], bed_volume)
        self.assertEqual(technical["operating_vessels"]["value"], math.ceil(bed_volume / 40.0))
        self.assertEqual(technical["redundant_vessels"]["value"], 1)
        n_op = technical["operating_vessels"]["value"]
        self.assertAlmostEqual(technical["bed_volume_per_vessel"]["value"], bed_volume / n_op)
        self.assertAlmostEqual(technical["total_contactor_volume"]["value"], (n_op + 1) * bed_volume / n_op)
        self.assertAlmostEqual(technical["fresh_gac_mass"]["value"], 400.0 * bed_volume)

        expected_bv = 1.5e5 * self.TOC**-1.85
        changeout_days = expected_bv * 10.0 / 1440.0
        self.assertAlmostEqual(technical["breakthrough_bed_volumes"]["value"], expected_bv)
        self.assertAlmostEqual(technical["estimated_changeout_interval"]["value"], changeout_days)
        self.assertAlmostEqual(
            technical["annual_gac_usage"]["value"], 400.0 * bed_volume * 365.0 / changeout_days
        )
        # carbon usage per m3 is independent of bed size
        self.assertAlmostEqual(technical["carbon_usage_rate"]["value"], 400.0 / expected_bv)

        kwh_per_m3 = 1000.0 * 9.80665 * 10.0 / 0.70 / 3.6e6
        self.assertAlmostEqual(technical["energy_intensity"]["value"], kwh_per_m3)
        self.assertAlmostEqual(technical["pump_power"]["value"], kwh_per_m3 * FLOW_M3_DAY / 24.0)
        self.assertNotIn("chemical_dose", technical)
        self.assertNotIn("regenerant_dose", technical)
        self.assertNotIn("chemical_consumption", technical)

    def test_capital_reproduces_watertap_reference_design(self):
        # WaterTAP reference: one 78.783 m3 bed (EBCT 600 s) plus one redundant vessel.
        flow = 78.783 / 10.0 * 1440.0
        technical = self._technical(flow=flow, max_bed_volume_per_vessel=1000.0)
        cost = run_cost_model(
            "GAC",
            technical,
            {"installation_factor": 1.0},
            {**CONTEXT, "investment_factor": 1.0, "base_currency_year": 2020},
        )
        self.assertAlmostEqual(cost["contactor_capital_cost"]["value"], 277758.9, delta=1.0)
        self.assertAlmostEqual(cost["adsorbent_initial_charge_cost"]["value"], 115064.3, delta=1.0)
        self.assertAlmostEqual(cost["other_process_capital_cost"]["value"], 272362.6, delta=1.0)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 665185.8, delta=2.0)

    def test_capital_factors_and_operating_cost_breakdown(self):
        technical = self._technical()
        cost = run_cost_model("GAC", technical, {}, CONTEXT)
        index = CostIndexFactor(2020, 2024)
        bare = cost["bare_equipment_capital_cost"]["value"]
        self.assertAlmostEqual(cost["equipment_capital_cost"]["value"], 1.15 * bare)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 2.5 * 1.15 * bare)

        usage = technical["annual_gac_usage"]["value"]
        regeneration = usage * 0.80 * 4.28352 * index
        makeup = usage * 0.20 * 4.58223 * index
        electricity = technical["pump_power"]["value"] * 24.0 * 365.0 * 0.05
        maintenance = 0.03 * 1.15 * bare
        self.assertAlmostEqual(cost["gac_regeneration_operating_cost"]["value"], regeneration)
        self.assertAlmostEqual(cost["gac_replacement_operating_cost"]["value"], makeup)
        self.assertAlmostEqual(cost["spent_gac_solid_waste"]["value"], usage * 0.20)
        self.assertAlmostEqual(cost["electricity_operating_cost"]["value"], electricity)
        self.assertAlmostEqual(cost["maintenance_operating_cost"]["value"], maintenance)
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            (regeneration + makeup + electricity + maintenance) * 1.20,
        )

    def test_media_costs_scale_with_operating_days_but_maintenance_does_not(self):
        technical = self._technical()
        full = run_cost_model("GAC", technical, {}, CONTEXT)
        part = run_cost_model("GAC", technical, {}, {**CONTEXT, "operating_days_per_year": 182.5})
        self.assertAlmostEqual(
            part["gac_regeneration_operating_cost"]["value"],
            0.5 * full["gac_regeneration_operating_cost"]["value"],
        )
        self.assertAlmostEqual(
            part["maintenance_operating_cost"]["value"], full["maintenance_operating_cost"]["value"]
        )
        self.assertAlmostEqual(
            part["installed_capital_cost"]["value"], full["installed_capital_cost"]["value"]
        )


class ZeoliteIntegrationTests(unittest.TestCase):
    STREAM = {"flow_m3_day": FLOW_M3_DAY, "water_quality": {"Ammonia nitrogen": {"value": 25.0, "unit": "mg/L"}}}

    def test_ammonia_cycle_from_bench_curve(self):
        technical = run_technical_model(
            "Zeolite",
            {"recovery": 0.995, "empty_bed_contact_time": 20.0, "removal_efficiencies": {"Ammonia nitrogen": 0.95}},
            self.STREAM,
        )
        bench_bv = 482.3 + (95.0 - 99.8) * (558.7 - 482.3) / (89.4 - 99.8)
        bench_feed_avg = sum(
            [24.9, 24.9, 23.9, 24.5, 24.8, 25.3, 25.3, 25.0, 24.8, 24.8, 25.3, 24.5, 24.5, 21.6, 21.6]
        ) / 15.0
        adjusted_bv = bench_bv * bench_feed_avg / 25.0
        self.assertAlmostEqual(technical["bench_breakthrough_bv"]["value"], bench_bv)
        self.assertAlmostEqual(technical["breakthrough_bed_volumes"]["value"], adjusted_bv)
        self.assertAlmostEqual(technical["cycle_duration"]["value"], adjusted_bv * 20.0 / 1440.0)
        self.assertAlmostEqual(technical["media_inventory"]["value"], FLOW_M3_DAY / 1440.0 * 20.0 * 824.0)
        self.assertNotIn("chemical_dose", technical)

        bed_volume = FLOW_M3_DAY / 1440.0 * 20.0
        fresh_brine = 90.0 * bed_volume / 5.0
        nacl_per_regen = fresh_brine * (997.0 + 735.0 * 0.10) * 0.10
        cycles = 365.0 / (adjusted_bv * 20.0 / 1440.0)
        self.assertAlmostEqual(technical["annual_nacl_consumption"]["value"], nacl_per_regen * cycles)
        self.assertAlmostEqual(technical["spent_brine_generation"]["value"], fresh_brine * cycles)
        n_removed = FLOW_M3_DAY * 25.0 * 0.95 / 1000.0 * 365.0
        self.assertAlmostEqual(technical["annual_naoh_consumption"]["value"], n_removed / 14.0067 * 39.997)
        kwh_per_m3 = 1000.0 * 9.80665 * 10.0 / 0.70 / 3.6e6
        self.assertAlmostEqual(technical["energy_intensity"]["value"], kwh_per_m3)

    def test_removal_comes_from_removal_table(self):
        technical = run_technical_model("Zeolite", {"removal_efficiencies": {"Ammonia nitrogen": 0.90}}, self.STREAM)
        self.assertAlmostEqual(technical["ammonia_removal"]["value"], 0.90)
        self.assertAlmostEqual(technical["outlet_ammonia"]["value"], 25.0 * 0.10)
        bench_bv = 482.3 + (90.0 - 99.8) * (558.7 - 482.3) / (89.4 - 99.8)
        self.assertAlmostEqual(technical["bench_breakthrough_bv"]["value"], bench_bv)
        # Without a table entry the model falls back to the 95% default
        default = run_technical_model("Zeolite", {}, self.STREAM)
        self.assertAlmostEqual(default["ammonia_removal"]["value"], 0.95)

    def test_full_removal_does_not_fail(self):
        technical = run_technical_model("Zeolite", {"removal_efficiencies": {"Ammonia nitrogen": 1.0}}, self.STREAM)
        self.assertAlmostEqual(technical["bench_breakthrough_bv"]["value"], 390.7)

    def test_cost_breakdown(self):
        technical = run_technical_model("Zeolite", {}, self.STREAM)
        cost = run_cost_model("Zeolite", technical, {}, CONTEXT)
        bare = 3305.1 * FLOW_M3_DAY**0.6961 * CostIndexFactor(2021, 2024)
        self.assertAlmostEqual(cost["bare_equipment_capital_cost"]["value"], bare)
        self.assertAlmostEqual(cost["equipment_capital_cost"]["value"], 1.15 * bare)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 2.5 * 1.15 * bare)
        electricity = FLOW_M3_DAY * 365.0 * technical["energy_intensity"]["value"] * 0.05
        chem_index = CostIndexFactor(2014, 2024)
        nacl = technical["annual_nacl_consumption"]["value"] / 1000.0 * 40.0 * chem_index
        naoh = technical["annual_naoh_consumption"]["value"] / 1000.0 * 300.0 * chem_index
        maintenance = 0.02 * 1.15 * bare
        self.assertAlmostEqual(cost["energy_operating_cost"]["value"], electricity)
        self.assertAlmostEqual(cost["nacl_operating_cost"]["value"], nacl)
        self.assertAlmostEqual(cost["naoh_operating_cost"]["value"], naoh)
        self.assertAlmostEqual(cost["maintenance_operating_cost"]["value"], maintenance)
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"], (electricity + nacl + naoh + maintenance) * 1.20
        )
        self.assertNotIn("nh4cl_revenue_credit", cost)
        self.assertAlmostEqual(cost["zeolite_media_replacement_cost"]["value"], 0.0)

    def test_media_replacement_uses_aec_mass(self):
        technical = run_technical_model("Zeolite", {"aec_mg_n_g": 4.0}, self.STREAM)
        n_kg_day = FLOW_M3_DAY * 25.0 * 0.95 / 1000.0
        mass = n_kg_day * technical["service_time"]["value"] * 1000.0 / 4.0
        self.assertAlmostEqual(technical["zeolite_mass_from_aec"]["value"], mass)
        base = run_cost_model("Zeolite", technical, {}, CONTEXT)
        cost = run_cost_model("Zeolite", technical, {"media_replacement_fraction_per_cycle": 0.1}, CONTEXT)
        replaced = mass * 0.1 * technical["cycles_per_year"]["value"]
        self.assertAlmostEqual(cost["spent_zeolite_solid_waste"]["value"], replaced)
        self.assertAlmostEqual(
            cost["zeolite_media_replacement_cost"]["value"], replaced * 4.41 * CostIndexFactor(2014, 2024)
        )
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"] - base["total_annual_operating_cost"]["value"],
            1.2 * cost["zeolite_media_replacement_cost"]["value"],
        )


if __name__ == "__main__":
    unittest.main()

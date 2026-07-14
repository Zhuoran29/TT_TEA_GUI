import unittest

from tea_models.registry import run_cost_model, run_technical_model
from treatment_config import get_treatment_train_config


UNIT = "Vacuum membrane distillation (VMD)"
REFERENCE_FLOW = 0.0223 * 3785.41


class VMDIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.technical_inputs = {
            "feed_tds_mass_fraction": 0.035,
            "feed_temperature": 25.0,
            "recovery": 0.50,
            "recycle_ratio": 6.169,
            "specific_electric_energy": 91.43,
            "reference_feed_flow": REFERENCE_FLOW,
            "reference_recovery": 0.50,
            "reference_membrane_area": 103.1817,
            "reference_heat_exchanger_area": 291.08,
            "reference_heater_power": 268.454,
            "reference_chiller_power": 274.402,
        }
        self.cost_inputs = {
            "low_pressure_pump_cost": 889.0,
            "heat_exchanger_material_factor": 1.0,
            "heat_exchanger_unit_cost": 300.0,
            "mixer_unit_cost": 361.0,
            "heater_unit_cost": 0.066,
            "heater_efficiency": 0.99,
            "chiller_unit_cost": 0.20,
            "chiller_cop": 7.0,
            "membrane_cost": 56.0,
            "membrane_replacement_fraction": 0.20,
            "fixed_opex_fraction": 0.03,
        }
        self.context = {
            "operating_days_per_year": 365.25 * 0.90,
            "electricity_price": 0.07,
            "investment_factor": 2.0,
            "base_currency_year": 2018,
        }

    def test_reference_design_and_capex_match_workbook_cache(self):
        technical = run_technical_model(
            UNIT,
            self.technical_inputs,
            {"flow_m3_day": REFERENCE_FLOW, "water_quality": {}},
        )
        self.assertAlmostEqual(technical["membrane_area"]["value"], 103.1817)
        self.assertAlmostEqual(technical["heat_exchanger_area"]["value"], 291.08)
        self.assertAlmostEqual(technical["total_electric_power"]["value"], 321.5846170620834)

        cost = run_cost_model(UNIT, technical, self.cost_inputs, self.context)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 269663.8342377185)
        self.assertAlmostEqual(cost["fixed_operating_cost"]["value"], 8089.915027131555)
        self.assertAlmostEqual(cost["energy_operating_cost"]["value"], 177597.67744947204)
        self.assertAlmostEqual(cost["membrane_replacement_cost"]["value"], 1155.63504)
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            cost["fixed_operating_cost"]["value"]
            + cost["energy_operating_cost"]["value"]
            + cost["membrane_replacement_cost"]["value"],
        )

    def test_saved_md_name_and_scenario_selection_migrate_to_vmd(self):
        for water_type in ("Produced water", "Brackish groundwater"):
            for legacy_name in ("Membrane desalination (MD)", "MD", "VMD"):
                train = get_treatment_train_config(
                    "Surface water discharge", legacy_name, water_type
                )
                self.assertIn(UNIT, train["desalination"])
                self.assertNotIn("MD", train["desalination"])
                self.assertNotIn("VMD", train["desalination"])


if __name__ == "__main__":
    unittest.main()

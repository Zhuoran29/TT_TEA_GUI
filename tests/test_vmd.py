import unittest

from tea_models.registry import run_cost_model, run_technical_model
from treatment_config import get_treatment_train_config


UNIT = "Vacuum membrane distillation (VMD)"
REFERENCE_FLOW = 0.0223 * 3785.41


class VMDIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.technical_inputs = {
            "feed_temperature": 25.0,
            "recovery": 0.50,
        }
        self.cost_inputs = {
            "low_pressure_pump_cost": 889.0,
            "heat_exchanger_material_factor": 1.0,
            "heat_exchanger_unit_cost": 300.0,
            "mixer_unit_cost": 361.0,
            "heater_unit_cost": 0.066,
            "chiller_unit_cost": 0.20,
            "chiller_cop": 7.0,
            "membrane_cost": 56.0,
            "membrane_replacement_fraction": 0.20,
            "fixed_opex_fraction": 0.03,
        }
        self.context = {
            "operating_days_per_year": 365.25 * 0.90,
            "electricity_price": 0.07,
            "thermal_energy_price": 0.01,
            "investment_factor": 2.0,
            "base_currency_year": 2018,
        }

    def test_surrogate_outputs_and_capex_match_embedded_formula(self):
        technical = run_technical_model(
            UNIT,
            self.technical_inputs,
            {"flow_m3_day": REFERENCE_FLOW, "water_quality": {}},
        )
        self.assertAlmostEqual(technical["feed_mass_flow"]["value"], 1.051883489557225)
        self.assertAlmostEqual(technical["membrane_area"]["value"], 76.61984664025967)
        self.assertAlmostEqual(technical["heat_exchanger_area"]["value"], 296.2170603920535)
        self.assertAlmostEqual(technical["heater_thermal_duty"]["value"], 475.76362730245467)
        self.assertAlmostEqual(technical["chiller_thermal_duty"]["value"], 498.3007038906829)
        self.assertAlmostEqual(technical["auxiliary_electric_power"]["value"], 80.61417345500023)
        self.assertAlmostEqual(technical["energy_intensity"]["value"], 22.91948522390843)
        self.assertAlmostEqual(technical["thermal_energy_intensity"]["value"], 165.3678871063947)
        self.assertEqual(technical["thermal_energy_intensity"]["unit"], "kWh/m3 feed")

        cost = run_cost_model(UNIT, technical, self.cost_inputs, self.context)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 319253.55213608686)
        self.assertAlmostEqual(cost["fixed_operating_cost"]["value"], 9577.606564082605)
        self.assertAlmostEqual(cost["energy_operating_cost"]["value"], 44519.82220391151)
        self.assertAlmostEqual(cost["thermal_energy_operating_cost"]["value"], 45888.271550166704)
        self.assertAlmostEqual(cost["membrane_replacement_cost"]["value"], 858.1422823709083)
        self.assertAlmostEqual(
            cost["total_annual_operating_cost"]["value"],
            cost["fixed_operating_cost"]["value"]
            + cost["energy_operating_cost"]["value"]
            + cost["thermal_energy_operating_cost"]["value"]
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

    def test_upw_vmd_default_train_uses_requested_polishing_sequence(self):
        expected = {
            "pretreatment": ["3-phase separator", "DAF", "Ultrafiltration"],
            "desalination": [UNIT],
            "posttreatment": ["GAC", "Zeolite", "Ion exchange"],
        }
        for water_type in ("Produced water", "Brackish groundwater"):
            train = get_treatment_train_config(
                "Feedwater to UPW production",
                UNIT,
                water_type,
            )
            for stage, units in expected.items():
                self.assertEqual(train[stage], units)


if __name__ == "__main__":
    unittest.main()

import unittest

from tea_models.registry import run_cost_model, run_technical_model


CONTEXT = {
    "operating_days_per_year": 365.0,
    "electricity_price": 0.05,
    "investment_factor": 2.5,
    "capital_recovery_factor": 0.08,
    "base_currency_year": 2024,
}


class GoodPretreatmentModelTests(unittest.TestCase):
    def test_ec_loss_flow_enters_brine_stream_and_cost_excludes_brine_disposal(self):
        technical = run_technical_model(
            "Electrocoagulation",
            {
                "recovery": 0.98,
                "hydraulic_retention_time": 30.0,
                "current_density_mA_cm2": 20.0,
                "electrode_gap_m": 0.02,
                "removal_efficiencies": {"TSS": 0.58, "TDS": 0.10},
            },
            {
                "flow_m3_day": 8000.0,
                "water_quality": {
                    "TDS": {"value": 100000.0, "unit": "mg/L"},
                    "TSS": {"value": 10.0, "unit": "mg/L"},
                },
            },
        )
        self.assertAlmostEqual(technical["brine_flow"]["value"], 160.0)
        self.assertGreater(technical["aluminum_consumption"]["value"], 0.0)
        cost = run_cost_model("Electrocoagulation", technical, {}, CONTEXT)
        self.assertNotIn("brine_disposal_operating_cost", cost)
        self.assertGreater(cost["solid_disposal_operating_cost"]["value"], 0.0)

    def test_uf_pump_energy_and_bisulfite_cost_are_active(self):
        technical = run_technical_model(
            "Ultrafiltration",
            {"recovery": 0.96, "sodium_bisulfite_dose_mg_l": 5.0},
            {"flow_m3_day": 8000.0, "water_quality": {"TSS": {"value": 100.0, "unit": "mg/L"}}},
        )
        self.assertGreater(technical["energy_intensity"]["value"], 0.0)
        self.assertAlmostEqual(technical["sodium_bisulfite_consumption"]["value"], 40.0)
        cost = run_cost_model("Ultrafiltration", technical, {}, CONTEXT)
        self.assertGreater(cost["sodium_bisulfite_operating_cost"]["value"], 0.0)

    def test_wsf_reference_cost_basis_returns_capex_and_opex(self):
        technical = run_technical_model(
            "Walnut shell filtration",
            {"recovery": 0.99, "energy_intensity": 0.17},
            {"flow_m3_day": 8000.0, "water_quality": {"Oil": {"value": 50.0, "unit": "mg/L"}}},
        )
        cost = run_cost_model("Walnut shell filtration", technical, {}, CONTEXT)
        self.assertGreater(cost["installed_capital_cost"]["value"], 0.0)
        self.assertGreater(cost["baseline_variable_operating_cost"]["value"], 0.0)

    def test_chemical_softening_falls_back_if_reaktoro_unavailable(self):
        technical = run_technical_model(
            "Chemical softening",
            {
                "recovery": 0.97,
                "lime_dose_mg_l": 10.0,
                "soda_ash_dose_mg_l": 4301.0,
                "target_neutral_pH": 8.0,
                "removal_efficiencies": {"Calcium": 0.42},
            },
            {
                "flow_m3_day": 8000.0,
                "water_quality": {
                    "pH": {"value": 7.5, "unit": "-"},
                    "Calcium": {"value": 1200.0, "unit": "mg/L"},
                    "Magnesium": {"value": 295.0, "unit": "mg/L"},
                    "Barium": {"value": 2.2, "unit": "mg/L"},
                    "Strontium": {"value": 235.0, "unit": "mg/L"},
                    "Sodium": {"value": 33600.0, "unit": "mg/L"},
                    "Chloride": {"value": 58900.0, "unit": "mg/L"},
                    "Sulfate": {"value": 251.0, "unit": "mg/L"},
                    "Alkalinity": {"value": 132.0, "unit": "mg/L as CaCO3"},
                    "Silica": {"value": 47.5, "unit": "mg/L"},
                },
            },
        )
        self.assertAlmostEqual(technical["brine_flow"]["value"], 240.0)
        cost = run_cost_model("Chemical softening", technical, {}, CONTEXT)
        self.assertGreater(cost["chemical_operating_cost"]["value"], 0.0)


if __name__ == "__main__":
    unittest.main()

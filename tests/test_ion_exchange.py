import unittest

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.unit_model_defaults import cost_defaults, technical_defaults


class IonExchangeEnergyTests(unittest.TestCase):
    def test_ion_exchange_uses_watertap_style_pressure_drop_energy(self):
        stream = {"flow_m3_day": 1000.0, "water_quality": {}}
        technical = run_technical_model(
            "Ion exchange",
            dict(technical_defaults("Ion exchange")),
            stream,
        )

        self.assertAlmostEqual(technical["pressure_drop"]["value"], 70.0)
        self.assertAlmostEqual(technical["main_pump_energy_intensity"]["value"], 0.1915, places=4)
        self.assertAlmostEqual(technical["energy_intensity"]["value"], 0.3015, places=4)
        self.assertAlmostEqual(technical["main_pump_power"]["value"], 7.98, places=2)

    def test_ion_exchange_edi_has_higher_auxiliary_energy(self):
        stream = {"flow_m3_day": 1000.0, "water_quality": {}}
        technical = run_technical_model(
            "Ion exchange / EDI",
            dict(technical_defaults("Ion exchange / EDI")),
            stream,
        )

        self.assertAlmostEqual(technical["pressure_drop"]["value"], 95.0)
        self.assertAlmostEqual(technical["energy_intensity"]["value"], 0.55, places=2)

    def test_ion_exchange_default_cost_exposes_column_multiplier_without_adder(self):
        stream = {"flow_m3_day": 1000.0, "water_quality": {}}
        technical = run_technical_model(
            "Ion exchange",
            dict(technical_defaults("Ion exchange")),
            stream,
        )
        context = {
            "operating_days_per_year": 365.0,
            "electricity_price": 0.05,
            "thermal_energy_price": 0.0,
            "investment_factor": 2.5,
        }
        defaults = dict(cost_defaults("Ion exchange"))
        cost = run_cost_model("Ion exchange", technical, defaults, context)
        bare_cost = run_cost_model(
            "Ion exchange",
            technical,
            {**defaults, "column_capex_multiplier": 1.0},
            context,
        )

        self.assertAlmostEqual(cost["column_capex_multiplier"]["value"], 1.0)
        self.assertAlmostEqual(
            cost["installed_capital_cost"]["value"],
            bare_cost["installed_capital_cost"]["value"],
        )
        self.assertAlmostEqual(
            cost["variable_operating_cost"]["value"],
            bare_cost["variable_operating_cost"]["value"],
        )


if __name__ == "__main__":
    unittest.main()

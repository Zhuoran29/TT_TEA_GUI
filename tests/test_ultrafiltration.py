import unittest

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.unit_model_defaults import cost_defaults, technical_defaults
from tea_models.water_quality import get_default_removal_efficiencies


FEED = {"TSS": 10.0, "Turbidity": 5.0, "Oil": 5.0, "TOC": 20.0, "TDS": 100000.0}
CONTEXT = {"operating_days_per_year": 365.0, "electricity_price": 0.05, "investment_factor": 2.0, "base_currency_year": 2024}


def _run(flow=8000.0, technical=None):
    stream = {"flow_m3_day": flow, "water_quality": {k: {"value": v, "unit": "mg/L"} for k, v in FEED.items()}}
    removals = get_default_removal_efficiencies("Ultrafiltration", stream["water_quality"])
    inputs = {**technical_defaults("Ultrafiltration"), **(technical or {}), "removal_efficiencies": removals}
    tech = run_technical_model("Ultrafiltration", inputs, stream)
    cost = run_cost_model("Ultrafiltration", tech, dict(cost_defaults("Ultrafiltration")), CONTEXT)
    return tech, cost


class UltrafiltrationTests(unittest.TestCase):
    def test_removals_and_recovery(self):
        tech, _cost = _run()
        out = tech["water_quality_out"]
        self.assertAlmostEqual(out["TSS"]["value"], 0.5, places=6)
        self.assertAlmostEqual(out["Oil"]["value"], 0.5, places=6)
        self.assertAlmostEqual(out["TOC"]["value"], 13.0, places=6)
        self.assertAlmostEqual(out["TDS"]["value"], 100000.0, places=3)
        self.assertAlmostEqual(tech["water_recovery"]["value"], 0.99)
        self.assertAlmostEqual(tech["backwash_flow"]["value"], 80.0, places=6)
        self.assertNotIn("membrane_area", tech)

    def test_pump_energy_and_bisulfite(self):
        tech, _cost = _run()
        flow_gpm = 8000.0 * 264.172052 / 1440.0
        kw = flow_gpm * 50.0 / 3960.0 * 0.7457 / (0.75 * 0.95 * 0.98)
        self.assertAlmostEqual(tech["energy_intensity"]["value"], kw * 24.0 / 8000.0, places=9)
        self.assertAlmostEqual(tech["sodium_bisulfite_consumption"]["value"], 40.0)

    def test_cost_structure(self):
        tech, cost = _run()
        bare = 2.54e6 * (8000.0 * 264.172052 / 970000.0) ** 0.87
        self.assertAlmostEqual(cost["bare_equipment_capital_cost"]["value"], bare, delta=1.0)
        direct = cost["equipment_capital_cost"]["value"]
        self.assertAlmostEqual(direct, 1.43 * cost["bare_equipment_capital_cost"]["value"], places=3)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 2.0 * direct, places=3)
        self.assertAlmostEqual(cost["maintenance_operating_cost"]["value"], 0.02 * direct, places=3)
        subtotal = (
            cost["energy_operating_cost"]["value"]
            + cost["sodium_bisulfite_operating_cost"]["value"]
            + cost["maintenance_operating_cost"]["value"]
        )
        self.assertAlmostEqual(cost["total_annual_operating_cost"]["value"], 1.2 * subtotal, places=3)
        self.assertNotIn("labor_cost", cost)


if __name__ == "__main__":
    unittest.main()

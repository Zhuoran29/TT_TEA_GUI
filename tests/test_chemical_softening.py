import unittest

import pytest

from tea_models.cost_models.chemical_softening import DEFAULTS as COST_DEFAULTS
from tea_models.registry import run_cost_model, run_technical_model
from tea_models.technical_models.chemical_softening import radium_removal
from tea_models.unit_model_defaults import technical_defaults


CONTEXT = {"operating_days_per_year": 365.0, "electricity_price": 0.05, "investment_factor": 2.0, "base_currency_year": 2024}
FEED = {
    "pH": 7.5, "TDS": 90000.0, "Conductivity": 130000.0, "Hardness": 2436.0, "Alkalinity": 52.8,
    "Calcium": 696.0, "Magnesium": 171.1, "Barium": 1.23, "Strontium": 225.6, "Sodium": 32256.0,
    "Chloride": 49476.0, "Sulfate": 145.6, "Silica": 31.4, "Radium-226": 237.0, "Gross Alpha": 760.0,
}


def _stream():
    return {"flow_m3_day": 8000.0, "water_quality": {k: {"value": v, "unit": "mg/L"} for k, v in FEED.items()}}


class RadiumTests(unittest.TestCase):
    def test_si_equation(self):
        self.assertAlmostEqual(radium_removal(0.0), 0.80)
        self.assertAlmostEqual(radium_removal(5000.0), 0.875)
        self.assertAlmostEqual(radium_removal(10.0), (80.0 + 15.0 * 10.0 / 5010.0) / 100.0)


class ChemicalSofteningReaktoroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pytest.importorskip("reaktoro")
        cls.tech = run_technical_model("Chemical softening", dict(technical_defaults("Chemical softening")), _stream())

    def out(self, parameter):
        return self.tech["water_quality_out"][parameter]["value"]

    def test_hardness_follows_calcium_and_magnesium(self):
        calc = lambda ca, mg: 2.497 * ca + 4.118 * mg
        expected = 2436.0 * calc(self.out("Calcium"), self.out("Magnesium")) / calc(696.0, 171.1)
        self.assertAlmostEqual(self.out("Hardness"), expected, places=6)
        self.assertLess(self.out("Hardness"), 0.1 * 2436.0)

    def test_tds_includes_added_sodium_and_sulfate(self):
        self.assertGreater(self.out("Sodium"), 32256.0)
        self.assertGreater(self.out("Sulfate"), 145.6)
        self.assertNotAlmostEqual(self.out("TDS"), 90000.0, places=0)
        self.assertAlmostEqual(self.out("Conductivity") / 130000.0, self.out("TDS") / 90000.0)

    def test_radionuclides_follow_si_equation(self):
        ra = radium_removal(10.0)
        self.assertAlmostEqual(self.out("Radium-226"), 237.0 * (1.0 - ra))
        self.assertAlmostEqual(self.out("Gross Alpha"), 760.0 * (1.0 - ra))

    def test_recovery_from_sludge(self):
        solids = self.tech["solid_waste_generation"]["value"]
        self.assertAlmostEqual(self.tech["water_recovery"]["value"], 1.0 - solids / 0.10 / 1000.0)

    def test_cost_structure(self):
        cost = run_cost_model("Chemical softening", self.tech, {}, CONTEXT)
        bare = 25829456.94 * (8000.0 / 3785.41) ** 0.87
        self.assertAlmostEqual(cost["bare_equipment_capital_cost"]["value"], bare, delta=1.0)
        self.assertAlmostEqual(cost["equipment_capital_cost"]["value"], 1.43 * bare, delta=1.0)
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 2.0 * 1.43 * bare, delta=2.0)
        subtotal = (
            cost["chemical_operating_cost"]["value"]
            + cost["energy_operating_cost"]["value"]
            + cost["maintenance_operating_cost"]["value"]
        )
        self.assertAlmostEqual(cost["maintenance_operating_cost"]["value"], 0.02 * 1.43 * bare, delta=1.0)
        self.assertAlmostEqual(cost["total_annual_operating_cost"]["value"], 1.2 * subtotal)
        self.assertNotIn("solid_disposal_operating_cost", cost)
        self.assertNotIn("labor_cost", cost)
        self.assertGreater(cost["solid_waste"]["value"], 0.0)


if __name__ == "__main__":
    unittest.main()

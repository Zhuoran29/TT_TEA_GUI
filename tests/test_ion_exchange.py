import unittest

from tea_models.registry import run_cost_model, run_technical_model
from tea_models.unit_model_defaults import cost_defaults, technical_defaults
from tea_models.water_quality import get_default_removal_efficiencies


FEED = {
    "TDS": 738.0,
    "Conductivity": 1135.0,
    "Sodium": 280.0,
    "Chloride": 420.0,
    "Calcium": 4.0,
    "Magnesium": 0.6,
    "Hardness": 12.5,
    "Barium": 0.3,
    "Strontium": 2.0,
    "Sulfate": 8.0,
    "Bicarbonate": 10.0,
    "Alkalinity": 8.2,
    "Boron": 0.4,
    "Ammonia nitrogen": 3.0,
}
CONTEXT = {"operating_days_per_year": 365.0, "electricity_price": 0.05, "investment_factor": 2.0, "base_currency_year": 2021}


def _stream(quality=FEED, flow=3316.0):
    return {"flow_m3_day": flow, "water_quality": {k: {"value": v, "unit": "mg/L"} for k, v in quality.items()}}


def _run(unit, extra_removals=None, quality=FEED, technical=None):
    stream = _stream(quality)
    removals = get_default_removal_efficiencies(unit, stream["water_quality"])
    removals.update(extra_removals or {})
    inputs = {**technical_defaults(unit), **(technical or {}), "removal_efficiencies": removals}
    tech = run_technical_model(unit, inputs, stream)
    cost = run_cost_model(unit, tech, dict(cost_defaults(unit)), CONTEXT)
    return tech, cost


def _out(tech, parameter):
    return tech["water_quality_out"][parameter]["value"]


class SelectiveIonExchangeTests(unittest.TestCase):
    def test_default_targets_cations_and_swaps_in_sodium(self):
        tech, _cost = _run("Ion exchange")
        self.assertAlmostEqual(_out(tech, "Hardness"), 12.5 * 0.05, places=6)
        self.assertAlmostEqual(_out(tech, "Barium"), 0.3 * 0.05, places=6)
        # Na rises by the equivalents removed; Cl, sulfate and TDS unchanged
        load = max(4.0 / 20.039 + 0.6 / 12.153, 12.5 / 50.04) + 0.3 / 68.664 + 2.0 / 43.81
        self.assertAlmostEqual(_out(tech, "Sodium"), 280.0 + 0.95 * load * 22.99, places=3)
        self.assertAlmostEqual(_out(tech, "Chloride"), 420.0)
        self.assertAlmostEqual(_out(tech, "Sulfate"), 8.0)
        self.assertAlmostEqual(_out(tech, "TDS"), 738.0, delta=1.0)
        self.assertAlmostEqual(tech["anion_resin_volume"]["value"], 0.0)

    def test_treated_fraction_from_bed_removal(self):
        tech, _cost = _run("Ion exchange")
        self.assertAlmostEqual(tech["cation_treated_fraction"]["value"], 0.95 / 0.99, places=6)
        self.assertAlmostEqual(tech["cation_resin_volume"]["value"], 3316.0 * 0.95 / 0.99 * 2.5 / 1440.0, places=6)

    def test_anion_target_adds_cl_form_bed(self):
        tech, cost = _run("Ion exchange", {"Sulfate": 0.95})
        self.assertAlmostEqual(_out(tech, "Sulfate"), 8.0 * 0.05, places=6)
        self.assertAlmostEqual(_out(tech, "Chloride"), 420.0 + 0.95 * 8.0 / 48.03 * 35.453, places=3)
        # Alkalinity is left alone unless it is a target
        self.assertAlmostEqual(_out(tech, "Bicarbonate"), 10.0)
        self.assertGreater(cost["anion_bed_capital_cost"]["value"], 0.0)

    def test_sodium_chloride_tds_entries_are_ignored_with_warning(self):
        tech, _cost = _run("Ion exchange", {"Sodium": 0.9, "TDS": 0.9, "Boron": 0.9})
        self.assertAlmostEqual(_out(tech, "Boron"), 0.4)
        self.assertGreater(_out(tech, "Sodium"), 280.0)
        self.assertTrue(any("does not remove" in w for w in tech["model_warnings"]["value"]))

    def test_run_length_from_capacity_and_cap(self):
        hard = {**FEED, "Calcium": 80.0, "Magnesium": 12.0, "Hardness": 250.0}
        tech, _cost = _run("Ion exchange", quality=hard)
        load = max(80.0 / 20.039 + 12.0 / 12.153, 250.0 / 50.04) + 0.3 / 68.664 + 2.0 / 43.81
        self.assertAlmostEqual(tech["cation_bed_volumes_per_cycle"]["value"], 1000.0 * 1.24 / (0.99 * load), places=3)
        # salt per equivalent at the EPA design point: 240 g/L / 1.24 eq/L = 3.31 x stoichiometric
        self.assertAlmostEqual(tech["cation_regeneration_ratio"]["value"], 240.0 / 1.24 / 58.443, places=3)
        soft, _ = _run("Ion exchange")
        self.assertAlmostEqual(soft["cation_bed_volumes_per_cycle"]["value"], 1000.0)

    def test_recovery_from_waste_bed_volumes(self):
        tech, _cost = _run("Ion exchange")
        waste_bv = 240.0 / 107.8 + 12.0 + 3.0
        fraction = 0.95 / 0.99
        self.assertAlmostEqual(tech["water_recovery"]["value"], 1.0 - fraction * waste_bv / 1000.0, places=6)

    def test_brine_mass_balance_includes_regenerant(self):
        tech, _cost = _run("Ion exchange")
        q_in = tech["inlet_flow"]["value"]
        q_out = tech["outlet_flow"]["value"]
        q_b = tech["brine_flow"]["value"]
        nacl_kg_day = tech["annual_nacl_consumption"]["value"] / 365.0
        tds_mass = 738.0 * q_in - _out(tech, "TDS") * q_out + nacl_kg_day * 1000.0
        self.assertAlmostEqual(tech["brine_water_quality"]["TDS"]["value"], tds_mass / q_b, places=3)

    def test_cost_structure(self):
        tech, cost = _run("Ion exchange")
        defaults = cost_defaults("Ion exchange")
        direct = cost["equipment_capital_cost"]["value"]
        self.assertAlmostEqual(cost["installed_capital_cost"]["value"], 2.0 * direct)
        self.assertAlmostEqual(
            direct,
            1.15 * (cost["bare_equipment_capital_cost"]["value"] + cost["initial_resin_cost"]["value"]),
        )
        nacl_t = tech["annual_nacl_consumption"]["value"] / 1000.0
        self.assertAlmostEqual(cost["nacl_operating_cost"]["value"], nacl_t * defaults["salt_price"], delta=1e-6 * nacl_t * 1000)
        subtotal = (
            cost["chemical_operating_cost"]["value"]
            + cost["resin_replacement_cost"]["value"]
            + cost["energy_operating_cost"]["value"]
            + cost["maintenance_operating_cost"]["value"]
        )
        self.assertAlmostEqual(cost["total_annual_operating_cost"]["value"], 1.2 * subtotal)


class DemineralizationTests(unittest.TestCase):
    def test_all_ions_removed_and_bypass(self):
        tech, _cost = _run("Ion exchange (demineralization)", {"TDS": 0.35})
        for parameter in ("TDS", "Sodium", "Chloride", "Hardness", "Ammonia nitrogen", "Boron"):
            self.assertAlmostEqual(_out(tech, parameter), FEED[parameter] * 0.65, places=6)
        self.assertAlmostEqual(tech["cation_treated_fraction"]["value"], 0.35 / 0.99, places=6)

    def test_regenerant_load_and_cost(self):
        tech, cost = _run("Ion exchange (demineralization)")
        cations = max(4.0 / 20.039 + 0.6 / 12.153, 12.5 / 50.04) + 0.3 / 68.664 + 2.0 / 43.81 + 280.0 / 22.99 + 3.0 / 14.007
        anions = 420.0 / 35.453 + 8.0 / 48.03 + 0.4 / 10.81 + max(10.0 / 61.017, 8.2 / 50.04)
        load = max(cations, anions, 738.0 / 58.443)
        self.assertAlmostEqual(tech["cation_ionic_load"]["value"], 0.99 * load, places=6)
        self.assertAlmostEqual(tech["anion_bed_volumes_per_cycle"]["value"], 1000.0 * 0.5 / (0.99 * load), places=4)
        self.assertGreater(cost["naoh_operating_cost"]["value"], cost["hcl_operating_cost"]["value"])
        self.assertLess(tech["water_recovery"]["value"], 0.8)

    def test_tds_sets_load_when_ions_do_not_add_up(self):
        quality = {"TDS": 738.0, "Sodium": 39.6, "Chloride": 75.6}
        tech, _cost = _run("Ion exchange (demineralization)", quality=quality)
        self.assertAlmostEqual(tech["cation_ionic_load"]["value"], 0.99 * 738.0 / 58.443, places=6)

    def test_tds_fallback_without_ions(self):
        tech, _cost = _run("Ion exchange (demineralization)", quality={"TDS": 584.4})
        self.assertAlmostEqual(tech["cation_ionic_load"]["value"], 0.99 * 584.4 / 58.443, places=6)
        self.assertTrue(any("estimated from TDS" in w for w in tech["model_warnings"]["value"]))


class IonExchangeEDITests(unittest.TestCase):
    def test_ion_exchange_edi_keeps_template_energy(self):
        stream = {"flow_m3_day": 1000.0, "water_quality": {}}
        technical = run_technical_model(
            "Ion exchange / EDI",
            dict(technical_defaults("Ion exchange / EDI")),
            stream,
        )
        self.assertAlmostEqual(technical["pressure_drop"]["value"], 95.0)
        self.assertAlmostEqual(technical["energy_intensity"]["value"], 0.55, places=2)


if __name__ == "__main__":
    unittest.main()

import unittest

from treatment_config import get_treatment_train_config


ALLOWED_POSTTREATMENT = {
    "Ammonia stripping",
    "GAC",
    "Zeolite",
    "Ion exchange",
    "pH adjustment",
}


class MVCTreatmentTrainDefaultsTests(unittest.TestCase):
    def assert_train(self, scenario, desal_type, pretreatment, desalination, posttreatment):
        config = get_treatment_train_config(scenario, desal_type, "Produced water")

        self.assertEqual(config["pretreatment"], pretreatment)
        self.assertEqual(config["desalination"], desalination)
        self.assertEqual(config["posttreatment"], posttreatment)
        self.assertTrue(set(config["posttreatment"]).issubset(ALLOWED_POSTTREATMENT))

    def test_powerplant_cooling_water_mvc_default_train(self):
        self.assert_train(
            "Powerplant cooling water",
            "Mechanical Vapor Compression (MVC)",
            ["DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["MVC"],
            ["GAC", "pH adjustment"],
        )

    def test_data_center_cooling_water_mvc_default_train(self):
        self.assert_train(
            "Data center cooling water",
            "Mechanical Vapor Compression (MVC)",
            ["DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["MVC"],
            ["GAC", "GAC", "pH adjustment"],
        )

    def test_fracturing_recirculation_mvc_default_train(self):
        self.assert_train(
            "On-site O&G hydraulic fracturing recirculation",
            "Mechanical Vapor Compression (MVC)",
            ["3-phase separator", "DAF", "Chemical softening", "Bag filter", "Antiscalant / pH adjustment"],
            ["MVC"],
            ["pH adjustment"],
        )

    def test_powerplant_cooling_water_vmd_default_train(self):
        self.assert_train(
            "Powerplant cooling water",
            "Vacuum membrane distillation (VMD)",
            ["DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["Vacuum membrane distillation (VMD)"],
            ["GAC", "pH adjustment"],
        )

    def test_data_center_cooling_water_vmd_default_train(self):
        self.assert_train(
            "Data center cooling water",
            "Vacuum membrane distillation (VMD)",
            ["DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["Vacuum membrane distillation (VMD)"],
            ["Ion exchange", "GAC", "pH adjustment"],
        )

    def test_fracturing_recirculation_vmd_default_train(self):
        self.assert_train(
            "On-site O&G hydraulic fracturing recirculation",
            "Vacuum membrane distillation (VMD)",
            ["3-phase separator", "DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["Vacuum membrane distillation (VMD)"],
            ["pH adjustment"],
        )

    def test_powerplant_cooling_water_lsrro_default_train(self):
        self.assert_train(
            "Powerplant cooling water",
            "Low-salt rejection reverse osmosis (LSRRO)",
            ["DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["LSRRO"],
            ["GAC", "pH adjustment"],
        )

    def test_data_center_cooling_water_lsrro_default_train(self):
        self.assert_train(
            "Data center cooling water",
            "Low-salt rejection reverse osmosis (LSRRO)",
            ["DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["LSRRO"],
            ["GAC", "pH adjustment"],
        )

    def test_fracturing_recirculation_lsrro_default_train(self):
        self.assert_train(
            "On-site O&G hydraulic fracturing recirculation",
            "Low-salt rejection reverse osmosis (LSRRO)",
            ["3-phase separator", "DAF", "Chemical softening", "Ultrafiltration", "Antiscalant / pH adjustment"],
            ["LSRRO"],
            ["pH adjustment"],
        )


if __name__ == "__main__":
    unittest.main()

import csv
import unittest
from pathlib import Path

TABLES = Path(__file__).resolve().parents[1] / "data" / "input_tables"


class InputTableTests(unittest.TestCase):
    def test_every_row_has_the_header_field_count(self):
        for name in ("technical_inputs.csv", "cost_inputs.csv"):
            with open(TABLES / name, newline="") as handle:
                rows = list(csv.reader(handle))
            width = len(rows[0])
            bad = [i + 1 for i, row in enumerate(rows) if row and len(row) != width]
            self.assertEqual(bad, [], f"{name}: lines with a wrong field count (unquoted comma?)")


if __name__ == "__main__":
    unittest.main()

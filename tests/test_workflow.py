import copy
import shutil
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from stock_screening.liquidity import screen_liquidity, verify_result
from stock_screening.market import load_snapshot


DEMO = Path(__file__).resolve().parents[1] / "examples" / "demo"
CUTOFF = "2025-03-09"
THRESHOLD = "100000000"


class WorkflowTests(unittest.TestCase):
    def test_expected_screening_result(self):
        snapshot = load_snapshot(DEMO, CUTOFF)
        self.assertEqual(len(snapshot.sessions), 20)
        self.assertEqual(snapshot.sessions[0], date(2025, 2, 7))
        self.assertEqual(snapshot.sessions[-1], date(2025, 3, 7))
        self.assertNotIn(date(2025, 2, 17), snapshot.sessions)

        report = screen_liquidity(snapshot, THRESHOLD)
        self.assertEqual(
            [(row["symbol"], row["avg_amount_cny"]) for row in report["matches"]],
            [("990001.SH", "130000000.00")],
        )
        self.assertEqual(report["below_or_equal_count"], 2)
        self.assertEqual(report["incomplete"][0]["symbol"], "990003.SZ")
        self.assertEqual(report["incomplete"][0]["missing_dates"], ["2025-02-26"])

    def test_verification_checks_amounts_and_request(self):
        snapshot = load_snapshot(DEMO, CUTOFF)
        report = screen_liquidity(snapshot, THRESHOLD)
        self.assertTrue(verify_result(snapshot, THRESHOLD, report)["verified"])

        modified = copy.deepcopy(report)
        modified["matches"][0]["avg_amount_cny"] = "139000000.00"
        check = verify_result(snapshot, THRESHOLD, modified)
        self.assertFalse(check["verified"])
        self.assertEqual(check["mismatched_fields"], ["matches"])
        self.assertFalse(verify_result(snapshot, "140000000", report)["verified"])

    def test_duplicate_quote_fails(self):
        with TemporaryDirectory() as directory:
            bundle = Path(directory) / "data"
            shutil.copytree(DEMO, bundle)
            with (bundle / "quotes.csv").open("a", encoding="utf-8") as stream:
                stream.write("990001.SH,2025-03-07,130000000\n")
            with self.assertRaisesRegex(ValueError, "duplicate quote"):
                load_snapshot(bundle, CUTOFF)

    def test_insufficient_calendar_fails(self):
        with self.assertRaisesRegex(ValueError, "does not cover as_of"):
            load_snapshot(DEMO, "2025-03-11")
        with self.assertRaisesRegex(ValueError, "21 open sessions, need 22"):
            load_snapshot(DEMO, CUTOFF, 22)

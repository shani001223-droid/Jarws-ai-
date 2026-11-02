"""Offline capture-overlap audit tests; synthetic data only, no network."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from cloud_backend.paper_evaluation import PaperEvaluationError
from scripts import capture_spot_history as capture
from scripts import compare_spot_captures as compare

NOW = 1_800_000_000_000
STEP = 900_000


def capture_fixture(shift=0, symbol="BTCUSDT", revise_volume=False):
    now = NOW + shift * STEP
    first = (now // STEP - 499) * STEP
    binance, kraken = [], []
    for i in range(500):
        t = first + i * STEP
        base = "11" if revise_volume and i == 200 else "10"
        binance.append([t, "100", "101", "99", "100", base,
                        t + STEP - 1, "1100" if base == "11" else "1000",
                        5, "4", "400", "0"])
        kraken.append([t // 1000, "100", "101", "99", "100",
                       "100", "10", 5])
    key = "XXBTZUSD" if symbol == "BTCUSDT" else "XETHZUSD"
    peer = {"error": [], "result": {key: kraken, "last": "0"}}
    return capture.capture_spot_history(
        symbol, fetch_json=lambda u: peer if "kraken.com" in u else binance,
        clock=lambda: now / 1000)


def save_pair(directory, prefix, pair):
    data, receipt = pair
    source = directory / (prefix + ".json")
    proof = directory / (prefix + ".receipt")
    source.write_text(json.dumps(data), encoding="utf-8")
    proof.write_text("HOSHI_CAPTURE_RECEIPT " + json.dumps(receipt) + "\n",
                     encoding="utf-8")
    return source, proof


class CaptureOverlapTests(unittest.TestCase):
    def test_one_new_closed_bar_and_exact_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, old_receipt = save_pair(root, "old", capture_fixture())
            new, new_receipt = save_pair(root, "new", capture_fixture(1))
            result = compare.compare_capture_files(old, old_receipt, new, new_receipt)
            self.assertEqual(result["overlapping_identical_closed_bars"], 498)
            self.assertEqual(result["newer_closed_bars"], 1)
            self.assertEqual(result["newer_first_open_at_ms"], NOW)
            self.assertFalse(result["orders_enabled"])
            self.assertFalse(result["independent_venue_authenticated"])
            self.assertFalse(result["forward_paper_fills_verified"])
            self.assertFalse(result["profitability_verified"])

    def test_revised_old_volume_refused_despite_individually_valid_receipts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(1, revise_volume=True))
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "historical_capture_candle_revised"):
                compare.compare_capture_files(old, proof_old, new, proof_new)

    def test_same_snapshot_is_not_forward_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture())
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "captures_not_chronologically_newer"):
                compare.compare_capture_files(old, proof_old, new, proof_new)

    def test_sparse_overlap_or_wrong_market_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            for suffix, pair, reason in (
                ("gap", capture_fixture(490), "insufficient_contiguous_capture_overlap"),
                ("symbol", capture_fixture(1, "ETHUSDT"), "incompatible_capture_identity"),
            ):
                with self.subTest(suffix=suffix):
                    new, proof_new = save_pair(root, suffix, pair)
                    with self.assertRaisesRegex(PaperEvaluationError, reason):
                        compare.compare_capture_files(old, proof_old, new, proof_new)

    def test_tampered_receipt_or_data_fails_without_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, proof_old = save_pair(root, "old", capture_fixture())
            new, proof_new = save_pair(root, "new", capture_fixture(1))
            command = ["--earlier", str(old), "--earlier-receipt", str(proof_old),
                       "--later", str(new), "--later-receipt", str(proof_new)]
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(compare.main(command), 0)
            self.assertEqual(json.loads(stdout.getvalue())["newer_closed_bars"], 1)
            data = json.loads(new.read_text(encoding="utf-8"))
            data["candles"][80][5] += 1
            new.write_text(json.dumps(data), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(compare.main(command), 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("WAIT:", stderr.getvalue())
            self.assertNotIn("BTCUSDT", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

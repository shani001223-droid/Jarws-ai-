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
            self.assertEqual(result["fully_post_capture_closed_bars"], 1)
            self.assertEqual(result["partial_at_capture_closed_bars"], 0)
            self.assertEqual(result["first_fully_post_capture_open_at_ms"], NOW)
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

    def test_new_bars_must_close_after_earlier_capture_time(self):
        # The first receipt can still pass its own binding when its data
        # is one interval stale. That old receipt must not make a candle
        # already closed at the earlier capture look like forward evidence.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stale_pair = capture_fixture()
            stale_pair[1]["captured_at_ms"] = NOW + STEP
            stale_pair[1]["source_fetched_at"] = {
                "binance": (NOW + STEP) // 1000,
                "kraken": (NOW + STEP) // 1000,
            }
            old, old_receipt = save_pair(root, "stale", stale_pair)
            new, new_receipt = save_pair(root, "later", capture_fixture(2))
            with self.assertRaisesRegex(
                    PaperEvaluationError, "new_closed_bar_not_after_earlier_capture"):
                compare.compare_capture_files(old, old_receipt, new, new_receipt)
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(old_receipt),
                    "--later", str(new), "--later-receipt", str(new_receipt),
                ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())

    def test_partial_bar_not_counted_as_fully_post_capture(self):
        # The next 15m bar began before the old receipt was taken, so
        # its close alone cannot establish one entire prospective bar.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            earlier_pair = capture_fixture()
            earlier_pair[1]["captured_at_ms"] = NOW + 1
            old, proof_old = save_pair(root, "old", earlier_pair)
            partial, partial_receipt = save_pair(root, "partial", capture_fixture(1))
            with self.assertRaisesRegex(
                    PaperEvaluationError, "no_full_post_capture_closed_candle"):
                compare.compare_capture_files(old, proof_old, partial, partial_receipt)
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(proof_old),
                    "--later", str(partial), "--later-receipt", str(partial_receipt),
                ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())

            later, proof_later = save_pair(root, "later", capture_fixture(2))
            report = compare.compare_capture_files(old, proof_old, later, proof_later)
            self.assertEqual(report["newer_closed_bars"], 2)
            self.assertEqual(report["partial_at_capture_closed_bars"], 1)
            self.assertEqual(report["fully_post_capture_closed_bars"], 1)
            self.assertEqual(report["first_fully_post_capture_open_at_ms"], NOW + STEP)

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


    def test_optional_prospective_replay_scores_only_fully_new_bars(self):
        # The first extra bar opened one millisecond before the old receipt.
        # It can warm the replay but cannot be a scored entry interval.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            earlier = capture_fixture()
            earlier[1]["captured_at_ms"] = NOW + 1
            old, proof_old = save_pair(root, "old", earlier)
            later, proof_later = save_pair(root, "later", capture_fixture(2))
            ordinary = compare.compare_capture_files(old, proof_old, later, proof_later)
            self.assertNotIn("prospective_paper_replay", ordinary)
            result = compare.compare_capture_files(
                old, proof_old, later, proof_later,
                prospective_strategy="trend_pullback")
            replay = result["prospective_paper_replay"]
            self.assertEqual(replay["first_scored_entry_at_ms"], NOW + STEP)
            self.assertEqual(replay["scored_closed_bars"], 1)
            self.assertEqual(replay["prior_closed_warmup_bars"], 64)
            self.assertEqual(replay["strategy_resolved_trade_count"], 0)
            self.assertEqual(replay["terminal_forced_mark_count"], 0)
            self.assertEqual(replay["simulation"]["trade_count"], 0)
            self.assertEqual(replay["simulation"]["net_pnl"], 0)
            self.assertIsNone(replay["win_probability"])
            self.assertFalse(replay["forward_paper_fills_verified"])
            self.assertFalse(replay["independent_venue_authenticated"])
            self.assertFalse(replay["profitability_verified"])
            self.assertTrue(all(t["entry_time"] >= NOW + STEP
                                for t in replay["simulation"]["trades"]))
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(proof_old),
                    "--later", str(later), "--later-receipt", str(proof_later),
                    "--prospective-replay", "breakout_retest",
                ]), 0)
            cli = json.loads(output.getvalue())["prospective_paper_replay"]
            self.assertEqual(cli["strategy"], "breakout_retest")
            self.assertEqual(cli["first_scored_entry_at_ms"], NOW + STEP)
            self.assertEqual(errors.getvalue(), "")

    def test_prospective_replay_refuses_invalid_or_partial_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            earlier = capture_fixture()
            earlier[1]["captured_at_ms"] = NOW + 1
            old, proof_old = save_pair(root, "old", earlier)
            partial, proof_partial = save_pair(root, "partial", capture_fixture(1))
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "no_full_post_capture_closed_candle"):
                compare.compare_capture_files(
                    old, proof_old, partial, proof_partial,
                    prospective_strategy="trend_pullback")
            with self.assertRaisesRegex(PaperEvaluationError,
                                        "unsupported_prospective_strategy"):
                compare.compare_capture_files(
                    old, proof_old, partial, proof_partial,
                    prospective_strategy="unbounded_scalp")
            output, errors = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(errors):
                self.assertEqual(compare.main([
                    "--earlier", str(old), "--earlier-receipt", str(proof_old),
                    "--later", str(partial), "--later-receipt", str(proof_partial),
                    "--prospective-replay", "trend_pullback",
                ]), 2)
            self.assertEqual(output.getvalue(), "")
            self.assertIn("WAIT:", errors.getvalue())


if __name__ == "__main__":
    unittest.main()

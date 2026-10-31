"""Deterministic public spot capture contracts; no external requests or orders."""
import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from cloud_backend.paper_evaluation import evaluate_chronological
from cloud_backend.market_data_quality import MarketDataQualityError
from cloud_backend.trading_research import Candle
from scripts import capture_spot_history as capture

NOW = 1_800_000_000_000
STEP = 900_000


def fixtures():
    first = (NOW // STEP - 499) * STEP
    binance, kraken = [], []
    for i in range(500):
        t = first + i * STEP
        binance.append([t, "100", "101", "99", "100", "10",
                        t + STEP - 1, "1000", 5, "4", "400", "0"])
        kraken.append([t // 1000, "100", "101", "99", "100",
                       "100", "10", 5])
    return binance, {"error": [], "result": {"XXBTZUSD": kraken, "last": "0"}}


class CaptureTests(unittest.TestCase):
    def test_manual_capture_has_evaluator_compatible_hash_and_20_bar_receipt(self):
        b, k = fixtures()
        urls = []
        def fetch(url):
            urls.append(url)
            return k if "kraken.com" in url else b
        dataset, receipt = capture.capture_spot_history(
            "BTCUSDT", fetch_json=fetch, clock=lambda: NOW / 1000)
        self.assertEqual(len(urls), 2)
        self.assertIn("data-api.binance.vision", urls[0])
        self.assertIn("api.kraken.com", urls[1])
        self.assertEqual(len(dataset["candles"]), 499)
        self.assertEqual(receipt["cross_checked_closed_bars"], 20)
        self.assertEqual(receipt["historical_cross_checked_closed_bars"], 499)
        self.assertEqual(receipt["historical_ohlc_cross_checked_bars"], 499)
        self.assertEqual(receipt["max_historical_close_difference_pct"], 0)
        self.assertEqual(receipt["max_historical_ohlc_difference_pct"], 0)
        self.assertFalse(receipt["orders_enabled"])
        bars = [Candle(*row) for row in dataset["candles"]]
        report = evaluate_chronological(bars, "BTCUSDT", "trend_pullback")
        self.assertEqual(report["input_candle_sha256"],
                         receipt["input_candle_sha256"])
        self.assertEqual(report["holdout"]["trade_count"], 0)
        self.assertEqual(report["holdout"]["net_pnl"], 0)

    def test_hidden_older_venue_disagreement_refuses_dataset(self):
        b, k = fixtures()
        k["result"]["XXBTZUSD"][-12][2] = "106"
        k["result"]["XXBTZUSD"][-12][4] = "105"
        with self.assertRaisesRegex(MarketDataQualityError,
                                    "cross_source_price_disagreement"):
            capture.capture_spot_history(
                "BTCUSDT", fetch_json=lambda u: k if "kraken.com" in u else b,
                clock=lambda: NOW / 1000)


    def test_disagreement_far_before_latest_twenty_refuses_capture(self):
        b, k = fixtures()
        # An old close disagrees, although the original latest-20 gate passes.
        k["result"]["XXBTZUSD"][-80][2] = "106"
        k["result"]["XXBTZUSD"][-80][4] = "105"
        with self.assertRaisesRegex(MarketDataQualityError,
                                    "historical_venue_price_disagreement"):
            capture.capture_spot_history(
                "BTCUSDT", fetch_json=lambda u: k if "kraken.com" in u else b,
                clock=lambda: NOW / 1000)

    def test_hidden_historical_wick_or_open_disagreement_refuses_capture(self):
        # Same close on both venues is insufficient: a forged wick could
        # create fake stops/targets in a historical paper replay.
        for field in (1, 2, 3):
            with self.subTest(field=field):
                b, k = fixtures()
                row = k["result"]["XXBTZUSD"][-80]
                if field == 1:
                    # Valid OHLC: only the open breaches the 2% venue bound.
                    row[1], row[2] = "102.5", "103"
                else:
                    row[field] = "70" if field == 3 else "130"
                with self.assertRaisesRegex(MarketDataQualityError,
                                            "historical_venue_ohlc_disagreement"):
                    capture.capture_spot_history(
                        "BTCUSDT",
                        fetch_json=lambda u: k if "kraken.com" in u else b,
                        clock=lambda: NOW / 1000)

    def test_shorter_kraken_history_is_not_full_coverage(self):
        b, k = fixtures()
        k["result"]["XXBTZUSD"].pop(0)
        with self.assertRaisesRegex(MarketDataQualityError,
                                    "insufficient_historical_venue_overlap"):
            capture.capture_spot_history(
                "BTCUSDT", fetch_json=lambda u: k if "kraken.com" in u else b,
                clock=lambda: NOW / 1000)

    def test_historical_alignment_guard_rejects_shifted_peers(self):
        a = [Candle(i * STEP, 100., 101., 99., 100., 10.,
                    (i + 1) * STEP - 1) for i in range(240)]
        b = [Candle((i + 1) * STEP, 100., 101., 99., 100., 10.,
                    (i + 2) * STEP - 1) for i in range(240)]
        with self.assertRaisesRegex(MarketDataQualityError,
                                    "historical_venue_time_mismatch"):
            capture.verify_historical_overlap(a, b)

    def test_small_historical_quote_deviation_is_recorded(self):
        a = [Candle(i * STEP, 100., 101., 99., 100., 10.,
                    (i + 1) * STEP - 1) for i in range(240)]
        b = [Candle(i * STEP, 100., 102., 99., 101., 10.,
                    (i + 1) * STEP - 1) for i in range(240)]
        check = capture.verify_historical_overlap(a, b)
        self.assertEqual(check["historical_cross_checked_closed_bars"], 240)
        self.assertGreater(check["max_historical_close_difference_pct"], 0)
        self.assertLess(check["max_historical_close_difference_pct"], 2)
        self.assertEqual(check["historical_ohlc_cross_checked_bars"], 240)
        self.assertGreaterEqual(check["max_historical_ohlc_difference_pct"],
                                check["max_historical_close_difference_pct"])

    def test_unsupported_pair_never_calls_network(self):
        with self.assertRaises(MarketDataQualityError):
            capture.capture_spot_history("SOLUSDT",
                                         fetch_json=lambda _: self.fail("network called"))

    def test_stale_or_missing_source_fails_closed(self):
        b, k = fixtures()
        with self.assertRaises(MarketDataQualityError):
            capture.capture_spot_history(
                "BTCUSDT", fetch_json=lambda u: k if "kraken.com" in u else b,
                clock=lambda: NOW / 1000 + 7200)
        with self.assertRaises(OSError):
            capture.capture_spot_history(
                "BTCUSDT", fetch_json=lambda _: (_ for _ in ()).throw(OSError("offline")))

    def test_cli_failure_emits_no_dataset_or_prices(self):
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(capture, "capture_spot_history",
                          side_effect=MarketDataQualityError("secret provider details")):
            with redirect_stdout(output), redirect_stderr(errors):
                status = capture.main(["--symbol", "BTCUSDT"])
        self.assertEqual(status, 2)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("WAIT:", errors.getvalue())
        self.assertNotIn("secret provider details", errors.getvalue())

    def test_cli_success_keeps_receipt_off_evaluator_json(self):
        b, k = fixtures()
        data, receipt = capture.capture_spot_history(
            "BTCUSDT", fetch_json=lambda u: k if "kraken.com" in u else b,
            clock=lambda: NOW / 1000)
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(capture, "capture_spot_history", return_value=(data, receipt)):
            with redirect_stdout(output), redirect_stderr(errors):
                status = capture.main(["--symbol", "BTCUSDT"])
        self.assertEqual(status, 0)
        self.assertEqual(set(json.loads(output.getvalue())),
                         {"symbol", "interval", "candles"})
        self.assertIn(receipt["input_candle_sha256"], errors.getvalue())

    def test_receipt_binding_is_unsigned_and_fail_closed(self):
        b, k = fixtures()
        data, receipt = capture.capture_spot_history(
            "BTCUSDT", fetch_json=lambda u: k if "kraken.com" in u else b,
            clock=lambda: NOW / 1000)
        from cloud_backend.paper_evaluation import attach_capture_receipt, PaperEvaluationError
        report = evaluate_chronological([Candle(*row) for row in data["candles"]],
                                        "BTCUSDT", "trend_pullback")
        bound = attach_capture_receipt(report, receipt)
        self.assertEqual(bound["capture_receipt"]["status"],
                         "local_unsigned_receipt_matches_candles")
        self.assertFalse(bound["independent_venue_verified"])
        self.assertFalse(bound["capture_receipt"]["independent_venue_authenticated"])
        self.assertEqual(bound["capture_receipt"]["historical_ohlc_comparison_bars_claimed"],
                         len(data["candles"]))
        self.assertNotIn("capture_receipt", report)
        for key, bad in (
            ("input_candle_sha256", "0" * 64),
            ("historical_cross_checked_closed_bars", 20),
            ("closed_bars", True),
            ("historical_ohlc_cross_checked_bars", 20),
            ("max_historical_ohlc_difference_pct", 3.0),
            ("symbol", "ETHUSDT"),
            ("first_open_at_ms", receipt["first_open_at_ms"] + STEP),
            ("captured_at_ms", receipt["captured_at_ms"] + 10 * STEP),
            ("max_historical_close_difference_pct", 3.0),
            ("sources", ["fake"]),
        ):
            with self.subTest(key=key), self.assertRaises(PaperEvaluationError):
                attach_capture_receipt(report, {**receipt, key: bad})

    def test_cli_consumes_actual_capture_receipt_line_without_trusting_it(self):
        import subprocess
        import sys
        import tempfile
        from pathlib import Path
        b, k = fixtures()
        dataset, receipt = capture.capture_spot_history(
            "BTCUSDT", fetch_json=lambda u: k if "kraken.com" in u else b,
            clock=lambda: NOW / 1000)
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            source, proof = Path(tmp) / "candles.json", Path(tmp) / "receipt.txt"
            source.write_text(json.dumps(dataset), encoding="utf-8")
            proof.write_text("HOSHI_CAPTURE_RECEIPT " + json.dumps(receipt) + "\n",
                             encoding="utf-8")
            command = [sys.executable, "-m", "scripts.evaluate_trading_paper",
                       "--input", str(source), "--capture-receipt", str(proof)]
            good = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(good.returncode, 0, good.stderr)
            result = json.loads(good.stdout)
            self.assertFalse(result["independent_venue_verified"])
            self.assertEqual(result["capture_receipt"]["historical_close_comparison_bars_claimed"],
                             len(dataset["candles"]))
            dataset["candles"][80][5] += 1  # valid OHLCV, different input fingerprint
            source.write_text(json.dumps(dataset), encoding="utf-8")
            bad = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, "")
            proof.write_text('HOSHI_CAPTURE_RECEIPT {"symbol":"BTCUSDT","symbol":"BTCUSDT"}',
                             encoding="utf-8")
            duplicate = subprocess.run(command, cwd=root, capture_output=True,
                                       text=True, timeout=30)
            self.assertEqual(duplicate.returncode, 2)
            self.assertEqual(duplicate.stdout, "")


if __name__ == "__main__":
    unittest.main()

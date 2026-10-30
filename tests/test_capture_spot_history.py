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


if __name__ == "__main__":
    unittest.main()

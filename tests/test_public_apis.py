"""Keyless, read-only public API regression tests; no live network dependency."""
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from cloud_backend import main


class JsonResponse:
    def __init__(self, data):
        self.body = json.dumps(data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, _limit=-1):
        return self.body


class PublicApiTests(unittest.TestCase):
    def setUp(self):
        with main._PUBLIC_LOCK:
            main._PUBLIC_CACHE.clear()

    def test_public_sources_never_require_secret(self):
        result = main.public_sources()
        self.assertFalse(result["key_required"])
        self.assertEqual(result["mode"], "read-only")
        self.assertIn("binance_spot", result["sources"])
        self.assertTrue(all(data["authentication"] == "none" for data in result["sources"].values()))

    def test_market_price_and_short_cache(self):
        payload = {"lastPrice": "70000.23", "priceChangePercent": "1.72",
                   "quoteVolume": "1234567.5"}
        with patch("cloud_backend.main.urlopen", return_value=JsonResponse(payload)) as open_url:
            first = main.public_market("BTCUSDT")
            second = main.public_market("BTCUSDT")
        self.assertEqual(first, second)
        self.assertEqual(first["price"], 70000.23)
        self.assertEqual(first["market"], "spot")
        self.assertEqual(open_url.call_count, 1)
        self.assertTrue(open_url.call_args.args[0].full_url.startswith("https://data-api.binance.vision/"))

    def test_rejects_unknown_pairs_and_timeframes_before_network(self):
        with patch("cloud_backend.main.urlopen") as fetch:
            with self.assertRaises(main.HTTPException) as bad:
                main.public_market("BTCUSDT&x=1")
            self.assertEqual(bad.exception.status_code, 422)
            with self.assertRaises(main.HTTPException) as bad_interval:
                main.public_candles("BTCUSDT", "5m&limit=5000")
            self.assertEqual(bad_interval.exception.status_code, 422)
            fetch.assert_not_called()

    def test_candle_indicators_use_source_prices(self):
        rows = []
        for i in range(80):
            op = 100 + i
            rows.append([i * 300000, str(op), str(op+2), str(op-2), str(op+1), "10"])
        with patch("cloud_backend.main.urlopen", return_value=JsonResponse(rows)):
            result = main.public_candles("BTCUSDT", "5m")
        self.assertEqual(len(result["candles"]), 80)
        self.assertAlmostEqual(result["indicators"]["sma20"], 170.5)
        self.assertEqual(result["indicators"]["rsi14"], 100)
        self.assertTrue(result["indicators"]["ema9"] > 0)

    def test_provider_failure_is_reported_without_secret_or_fake_price(self):
        with patch("cloud_backend.main.urlopen", side_effect=URLError("sensitive upstream details")):
            with self.assertRaises(main.HTTPException) as error:
                main.public_market("ETHUSDT")
        self.assertEqual(error.exception.status_code, 503)
        self.assertNotIn("sensitive", error.exception.detail)

    def test_fear_and_greed_requires_attribution(self):
        payload = {"data": [{"value": "48", "value_classification": "Neutral", "timestamp": "1790000000"}]}
        with patch("cloud_backend.main.urlopen", return_value=JsonResponse(payload)):
            result = main.public_sentiment()
        self.assertEqual(result["value"], 48)
        self.assertEqual(result["source"], "Alternative.me")
        self.assertIn("Alternative.me", result["attribution"])

    def test_defi_chains_limit_and_order(self):
        payload = [{"name": "Chain A", "tvl": 100}, {"name": "Chain B", "tvl": 350}]
        with patch("cloud_backend.main.urlopen", return_value=JsonResponse(payload)):
            result = main.public_defi()
        self.assertEqual(result["chains"][0]["name"], "Chain B")
        self.assertLessEqual(len(result["chains"]), 10)

    def test_btc_fee_estimates_are_not_futures_fees(self):
        with patch("cloud_backend.main.urlopen", return_value=JsonResponse(
            {"fastestFee": 5, "halfHourFee": 4, "hourFee": 3}
        )):
            result = main.public_bitcoin_fees()
        self.assertEqual(result["units"], "sat/vB")
        self.assertIn("not Binance", result["note"])

    def test_weather_coordinates_are_rounded_for_privacy(self):
        payload = {"current": {"temperature_2m": 29, "relative_humidity_2m": 64,
                               "weather_code": 2, "time": "2026-10-26T08:00"}}
        with patch("cloud_backend.main.urlopen", return_value=JsonResponse(payload)) as fetch:
            result = main.public_weather(24.86, 67.01)
        self.assertEqual(result["latitude"], 24.9)
        self.assertEqual(result["longitude"], 67.0)
        self.assertIn("latitude=24.9", fetch.call_args.args[0].full_url)


if __name__ == "__main__":
    unittest.main()

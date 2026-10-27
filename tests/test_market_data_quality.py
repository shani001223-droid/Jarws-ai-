"""Dual-source spot market quality tests. Deterministic fixtures; no orders."""
import unittest
from unittest.mock import patch

from fastapi import Response
from cloud_backend import market_data_quality as mq, main


NOW = 1_800_000_000_000


def fixtures(interval="15m", now=NOW):
    step = mq.INTERVALS[interval]
    start = (now // step - 80) * step
    binance, kraken = [], []
    for i in range(81):
        t = start + i * step
        # The last row is a still-forming bar; never use its volume or close.
        binance.append([t, "100", "101", "99", "100", "10", t+step-1,
                        "1000", 5, "4", "400", "0"])
        kraken.append([t//1000, "100", "101", "99", "100", "100", "10", 5])
    return binance, {"error": [], "result": {"XXBTZUSD": kraken, "last": "0"}}


class QualityUnitTests(unittest.TestCase):
    def test_verified_independent_sources_report_real_units_and_closed_bar(self):
        for tf in mq.INTERVALS:
            with self.subTest(tf=tf):
                b, k = fixtures(tf)
                result = mq.verify_spot_market("BTCUSDT", tf, b, k, NOW,
                                               NOW//1000, NOW//1000)
                self.assertEqual(result["status"], "verified_sources_agree")
                self.assertEqual(result["binance_last_base_volume"], 10)
                self.assertEqual(result["binance_last_quote_volume_usdt"], 1000)
                self.assertEqual(result["kraken_last_base_volume"], 10)
                self.assertEqual(result["last_closed_at"], b[-2][6])
                self.assertFalse(result["orders_enabled"])

    def test_numeric_string_close_time_does_not_break_quote_volume_selection(self):
        b, k = fixtures()
        b[-1][6] = str(b[-1][6])
        result = mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW,
                                       NOW//1000, NOW//1000)
        self.assertEqual(result["binance_last_quote_volume_usdt"], 1000)

    def test_fixed_host_allowlist_and_no_user_url(self):
        b, k = mq.public_urls("ETHUSDT", "1h")
        self.assertIn("data-api.binance.vision", b)
        self.assertIn("api.kraken.com", k)
        self.assertIn("ETHUSD", k)
        for pair, tf in (("DOGEUSDT", "15m"), ("BTCUSDT&evil=1", "15m"),
                         ("BTCUSDT", "1m"), ("BTCUSD", "15m")):
            with self.assertRaises(mq.MarketDataQualityError):
                mq.public_urls(pair, tf)

    def test_quote_volume_taker_volume_and_trade_count_are_validated(self):
        for column, value in ((7, "50000"), (7, "-1"), (7, "nan"),
                              (8, 0), (8, "1.0"), (9, "11"), (10, "1001")):
            with self.subTest(column=column, value=value):
                b, k = fixtures()
                b[12][column] = value
                with self.assertRaises(mq.MarketDataQualityError):
                    mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW,
                                          NOW//1000, NOW//1000)

    def test_rejects_stale_gapped_and_mismatched_sources(self):
        b, k = fixtures()
        k["result"]["XXBTZUSD"][-2][2] = "111"
        k["result"]["XXBTZUSD"][-2][4] = "110"
        with self.assertRaises(mq.MarketDataQualityError):
            mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW, NOW//1000, NOW//1000)
        b, k = fixtures()
        k["result"]["XXBTZUSD"][-2][0] += 900
        with self.assertRaises(mq.MarketDataQualityError):
            mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW, NOW//1000, NOW//1000)
        b, k = fixtures()
        with self.assertRaises(mq.MarketDataQualityError):
            mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW, NOW//1000-500, NOW//1000)
        b, k = fixtures()
        with self.assertRaises(mq.MarketDataQualityError):
            mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW+3_600_000,
                                  (NOW+3_600_000)//1000, (NOW+3_600_000)//1000)

    def test_rejects_bad_kraken_schema_and_zero_recent_volume(self):
        b, k = fixtures()
        k["error"] = ["EQuery:Invalid"]
        with self.assertRaises(mq.MarketDataQualityError):
            mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW, NOW//1000, NOW//1000)
        b, k = fixtures()
        b[-2][5] = "0"
        b[-2][7] = "0"
        b[-2][8] = 0
        b[-2][9] = "0"
        b[-2][10] = "0"
        with self.assertRaises(mq.MarketDataQualityError):
            mq.verify_spot_market("BTCUSDT", "15m", b, k, NOW, NOW//1000, NOW//1000)


class QualityApiTests(unittest.TestCase):
    def test_real_endpoint_uses_only_fixed_urls_and_returns_no_store(self):
        b, k = fixtures()
        urls = []
        def fetch(key, url, ttl):
            urls.append(url)
            return (k if "kraken.com" in url else b), NOW//1000
        response = Response()
        with patch.object(main, "_public_data", side_effect=fetch), patch.object(main.time, "time", return_value=NOW/1000):
            result = main.trading_data_quality(response, "BTCUSDT", "15m")
        self.assertEqual(len(urls), 2)
        self.assertEqual(result["status"], "verified_sources_agree")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_api_rejects_disagreeing_sources_without_claiming_verified(self):
        b, k = fixtures()
        k["result"]["XXBTZUSD"][-2][2] = "111"
        k["result"]["XXBTZUSD"][-2][4] = "110"
        def fetch(key, url, ttl):
            return (k if "kraken.com" in url else b), NOW//1000
        with patch.object(main, "_public_data", side_effect=fetch), patch.object(main.time, "time", return_value=NOW/1000):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_data_quality(Response(), "BTCUSDT", "15m")
        self.assertEqual(err.exception.status_code, 503)
        self.assertIn("No current-market claim", err.exception.detail)

    def test_unsupported_pair_no_network_and_upstream_failure_releases_slot(self):
        with patch.object(main, "_public_data") as fetch:
            with self.assertRaises(main.HTTPException) as err:
                main.trading_data_quality(Response(), "SOLUSDT", "15m")
            self.assertEqual(err.exception.status_code, 422)
            fetch.assert_not_called()
        with patch.object(main, "_public_data", side_effect=main.HTTPException(status_code=503)):
            for _ in range(3):
                with self.assertRaises(main.HTTPException) as err:
                    main.trading_data_quality(Response(), "BTCUSDT", "15m")
                self.assertEqual(err.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()

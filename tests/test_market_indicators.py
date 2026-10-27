"""Task 39: independent known-value indicator and API safety regression tests."""
from dataclasses import replace
import math
import unittest
from unittest.mock import patch

from fastapi import Response
from cloud_backend import main
from cloud_backend.market_indicators import (
    MarketIndicatorsError, analyze_market_indicators,
)
from cloud_backend.trading_research import INTERVALS, closed_candles

DAY = 86_400_000
NOW = 1_800_000_000_000
FRAMES = ("15m", "1h", "4h")


def history(tf, *, slope=0, volume=10, count=120, now=NOW):
    step = INTERVALS[tf]
    start = (now // step - count) * step
    rows = []
    for i in range(count):
        t = start + i * step
        price = 200 + slope * i
        rows.append([t, price, price + 1, price - 1, price,
                     volume, t + step - 1])
    return closed_candles(rows, tf, now)


def histories(**kwargs):
    return {tf: history(tf, **kwargs) for tf in FRAMES}


class IndicatorUnitTests(unittest.TestCase):
    def test_constant_known_values_and_full_utc_session(self):
        result = analyze_market_indicators(histories(), "BTCUSDT")
        self.assertEqual(result["formula_version"], "spot-indicators-v1")
        self.assertFalse(result["orders_enabled"])
        self.assertEqual(result["mode"], "indicators-research-only")
        for frame in result["timeframes"].values():
            values = frame["values"]
            for key in ("ema9", "ema20", "ema21", "ema50"):
                self.assertAlmostEqual(values[key], 200)
            self.assertAlmostEqual(values["rsi14"], 50)
            self.assertAlmostEqual(values["atr14"], 2)
            self.assertAlmostEqual(values["volume_sma20_base"], 10)
            self.assertAlmostEqual(values["volume_ratio20"], 1)
            self.assertTrue(frame["vwap_full_session_from_open"])
            self.assertAlmostEqual(values["utc_session_vwap"], 200)

    def test_linear_ramp_matches_closed_form_ema_and_wilder_rsi(self):
        rising = analyze_market_indicators(histories(slope=1), "ETHUSDT")
        for frame in rising["timeframes"].values():
            v = frame["values"]
            # Linear ramp with SMA seed: EMA(N) = last close - (N-1)/2.
            for period in (9, 20, 21, 50):
                self.assertAlmostEqual(v["ema" + str(period)],
                                       frame["last_close"] - (period - 1) / 2)
            self.assertAlmostEqual(v["rsi14"], 100)
            self.assertAlmostEqual(v["atr14"], 2)
        falling = analyze_market_indicators(histories(slope=-1), "BTCUSDT")
        for frame in falling["timeframes"].values():
            self.assertAlmostEqual(frame["values"]["rsi14"], 0)

    def test_vwap_null_when_session_is_partial_or_zero_volume(self):
        partial_now = DAY * 21000 + 20 * 3_600_000
        data = histories()
        data["15m"] = history("15m", count=65, now=partial_now)
        result = analyze_market_indicators(data, "BTCUSDT")
        self.assertFalse(result["timeframes"]["15m"]["vwap_full_session_from_open"])
        self.assertIsNone(result["timeframes"]["15m"]["values"]["utc_session_vwap"])
        zeros = analyze_market_indicators(histories(volume=0), "BTCUSDT")
        for frame in zeros["timeframes"].values():
            self.assertTrue(frame["vwap_full_session_from_open"])
            self.assertIsNone(frame["values"]["utc_session_vwap"])
            self.assertIsNone(frame["values"]["volume_ratio20"])
            self.assertEqual(frame["values"]["volume_sma20_base"], 0)

    def test_no_lookahead_when_future_bars_are_appended(self):
        data = histories()
        earlier = {tf: bars[:90] for tf, bars in data.items()}
        first = analyze_market_indicators(earlier, "BTCUSDT")
        # Deliberately alter only the later candles; the 90-bar result must
        # not depend on any of those future observations.
        changed = {}
        for tf, bars in data.items():
            changed[tf] = bars[:90] + [
                replace(b, high=b.high + 1000, close=b.close + 100,
                        open=b.open + 100, low=b.low + 100)
                for b in bars[90:]
            ]
        second = analyze_market_indicators(
            {tf: bars[:90] for tf, bars in changed.items()}, "BTCUSDT")
        self.assertEqual(first, second)

    def test_rejects_invalid_histories_nonfinite_values_and_pairs(self):
        valid = histories()
        for pair in ("DOGEUSDT", "BTCUSDT&test=1", ""):
            with self.assertRaises(MarketIndicatorsError):
                analyze_market_indicators(valid, pair)
        for bad in ({}, {"15m": valid["15m"]}, {"15m": [], "1h": [], "4h": []}):
            with self.assertRaises(MarketIndicatorsError):
                analyze_market_indicators(bad, "BTCUSDT")
        altered = histories()
        altered["1h"][4] = replace(altered["1h"][4], volume=math.nan)
        with self.assertRaises(MarketIndicatorsError):
            analyze_market_indicators(altered, "BTCUSDT")
        altered = histories()
        altered["4h"][3] = replace(altered["4h"][3], time=altered["4h"][3].time + 1)
        with self.assertRaises(MarketIndicatorsError):
            analyze_market_indicators(altered, "BTCUSDT")
        altered = histories()
        altered["15m"][-1] = replace(altered["15m"][-1], volume=1e19)
        with self.assertRaises(MarketIndicatorsError):
            analyze_market_indicators(altered, "BTCUSDT")


class IndicatorApiTests(unittest.TestCase):
    def test_read_only_api_uses_existing_bounded_source_and_no_store(self):
        data = histories()
        seen = []
        def get_history(pair, tf):
            seen.append((pair, tf))
            return data[tf], NOW // 1000
        response = Response()
        with patch.object(main, "_research_history", side_effect=get_history), patch.object(
                main.time, "time", return_value=NOW / 1000):
            result = main.trading_market_indicators(response, "BTCUSDT")
        self.assertEqual({tf for _, tf in seen}, set(FRAMES))
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertFalse(result["independently_cross_checked"])
        self.assertFalse(result["orders_enabled"])
        self.assertNotIn("entry", result)

    def test_invalid_pair_rejected_before_fetch_and_stale_source_fails_closed(self):
        with patch.object(main, "_research_history") as fetch:
            with self.assertRaises(main.HTTPException) as err:
                main.trading_market_indicators(Response(), "SOLUSDT")
            self.assertEqual(err.exception.status_code, 422)
            fetch.assert_not_called()
        with patch.object(main, "_research_history",
                          return_value=(history("15m"), NOW // 1000 - 500)), patch.object(
                main.time, "time", return_value=NOW / 1000):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_market_indicators(Response(), "BTCUSDT")
            self.assertEqual(err.exception.status_code, 503)

    def test_missing_provider_does_not_fabricate_values(self):
        with patch.object(main, "_research_history",
                          side_effect=main.HTTPException(status_code=503)):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_market_indicators(Response(), "BTCUSDT")
            self.assertEqual(err.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()

"""Task 38: deterministic multi-timeframe confirmed swing structure tests."""
import unittest
from unittest.mock import patch

from fastapi import Response

from cloud_backend import main
from cloud_backend.market_structure import (
    MarketStructureError, analyze_market_structure,
)
from cloud_backend.trading_research import INTERVALS, closed_candles

NOW = 1_800_000_000_000
WAVE = (0, 1, 3, 1, 0, -1, -3, -1)


def history(tf, slope=0.16, flat=False):
    step = INTERVALS[tf]
    start = (NOW // step - 90) * step
    rows = []
    for i in range(90):
        t = start + i * step
        price = 100 if flat else 100 + slope*i + WAVE[i % 8]
        rows.append([t, price, price + .2, price - .2, price,
                     10, t + step - 1])
    return closed_candles(rows, tf, NOW)


def frames(slopes=(.16, .16, .16)):
    return {tf: history(tf, slope) for tf, slope in zip(("15m", "1h", "4h"), slopes)}


class StructureUnitTests(unittest.TestCase):
    def test_uptrend_is_confirmed_only_after_two_closed_bars(self):
        result = analyze_market_structure(frames(), "BTCUSDT")
        self.assertEqual(result["alignment"], "all_three_bullish_structure")
        self.assertFalse(result["orders_enabled"])
        for tf in ("15m", "1h", "4h"):
            f = result["timeframes"][tf]
            self.assertEqual(f["structure"], "higher_highs_higher_lows")
            self.assertGreater(len(f["confirmed_swing_highs"]), 1)
            self.assertGreater(len(f["confirmed_swing_lows"]), 1)
            self.assertTrue(all(s["confirmed_at"] > s["pivot_at"]
                                and s["confirmed_at"] <= f["last_closed_at"]
                                for s in f["confirmed_swing_highs"] + f["confirmed_swing_lows"]))
            self.assertEqual(f["pivot_confirmation_bars"], 2)
            self.assertLessEqual(f["support"], f["last_close"])
            if f["resistance"] is not None:
                self.assertGreaterEqual(f["resistance"], f["last_close"])

    def test_downtrend_and_mixed_timeframes_are_not_trade_signals(self):
        down = analyze_market_structure(frames((-.16, -.16, -.16)), "ETHUSDT")
        self.assertEqual(down["alignment"], "all_three_bearish_structure")
        mixed = analyze_market_structure(frames((.16, -.16, .16)), "BTCUSDT")
        self.assertEqual(mixed["alignment"], "mixed_timeframes")
        self.assertNotIn("entry", str(mixed["timeframes"]))

    def test_flat_ties_do_not_fabricate_pivots(self):
        flat = {tf: history(tf, flat=True) for tf in ("15m", "1h", "4h")}
        result = analyze_market_structure(flat, "BTCUSDT")
        self.assertEqual(result["alignment"], "insufficient_confirmation")
        for frame in result["timeframes"].values():
            self.assertEqual(frame["confirmed_swing_highs"], [])
            self.assertEqual(frame["confirmed_swing_lows"], [])
            self.assertIsNone(frame["support"])
            self.assertIsNone(frame["resistance"])

    def test_last_two_bars_cannot_be_unconfirmed_swings(self):
        bars = frames()
        b = bars["15m"]
        # A dramatic high in the last closed bar cannot be a confirmed pivot.
        from dataclasses import replace
        b[-1] = replace(b[-1], high=b[-1].high + 1000)
        result = analyze_market_structure(bars, "BTCUSDT")
        self.assertTrue(all(s["price"] < 500 for s in
                            result["timeframes"]["15m"]["confirmed_swing_highs"]))

    def test_rejects_missing_or_tampered_candle_histories(self):
        valid = frames()
        for invalid in ({}, {"15m": valid["15m"]}, {"15m": [], "1h": [], "4h": []}):
            with self.assertRaises(MarketStructureError):
                analyze_market_structure(invalid, "BTCUSDT")
        with self.assertRaises(MarketStructureError):
            analyze_market_structure(valid, "DOGEUSDT")
        from dataclasses import replace
        tampered = frames()
        tampered["1h"][20] = replace(tampered["1h"][20], time=tampered["1h"][20].time + 1)
        with self.assertRaises(MarketStructureError):
            analyze_market_structure(tampered, "BTCUSDT")


class StructureApiTests(unittest.TestCase):
    def test_read_only_endpoint_uses_closed_histories_and_no_store(self):
        data = frames()
        seen = []
        def get_history(pair, tf):
            seen.append((pair, tf))
            return data[tf], NOW//1000
        response = Response()
        with patch.object(main, "_research_history", side_effect=get_history), patch.object(
                main.time, "time", return_value=NOW/1000):
            result = main.trading_market_structure(response, "BTCUSDT")
        self.assertEqual(result["alignment"], "all_three_bullish_structure")
        self.assertEqual({tf for _, tf in seen}, set(data))
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertFalse(result["orders_enabled"])

    def test_invalid_pair_does_not_fetch_and_source_error_fails_closed(self):
        with patch.object(main, "_research_history") as fetch:
            with self.assertRaises(main.HTTPException) as err:
                main.trading_market_structure(Response(), "SOLUSDT")
            self.assertEqual(err.exception.status_code, 422)
            fetch.assert_not_called()
        with patch.object(main, "_research_history",
                          side_effect=main.HTTPException(status_code=503)):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_market_structure(Response(), "BTCUSDT")
            self.assertEqual(err.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()

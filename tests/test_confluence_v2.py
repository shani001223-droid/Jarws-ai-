"""Synthetic fixtures, NOT live charts, returns or calibrated probabilities."""
from dataclasses import replace
from datetime import datetime
import math
import unittest

from cloud_backend.trading_research import Candle, INTERVALS
from cloud_backend.strategy_engine import (
    confluence_score, time_filter, ConfluenceError, _active_patterns, _liquidity,
)

NOW = int(datetime.fromisoformat("2026-10-27T14:30:00+00:00").timestamp() * 1000)
WAVE = (0, 1, 3, 1, 0, -1, -3, -1)


def frames():
    result = {}
    for tf, step in INTERVALS.items():
        start = (NOW // step - 90) * step
        bars = []
        for i in range(90):
            price = 100 + .16*i + WAVE[i % 8]
            bars.append(Candle(start+i*step, price-.1, price+.4, price-.4, price, 10, start+(i+1)*step-1))
        result[tf] = bars
    # Low confirmed at index 79, sweep at 83, displacement B=86,
    # closed FVG formation C=87, later partial retest at 89.
    tail = [(109,110,108,109.3), (109.3,110,108,109), (109,109.5,107,108),
            (108,109,108,108.5), (108.5,109.5,108.1,109.1), (109.1,110,108.8,109.8),
            (109.8,110,109,109.4), (109.4,110.2,109,109.8), (109.8,111.5,106.8,108.8),
            (108.8,109.7,108.6,109.2), (109.2,110,108.8,109.5), (109,114,108.9,113.5),
            (113.5,114,112,113), (113,114,112.4,113), (113,113.2,111.1,111.5)]
    for i, (o, h, lo, c) in enumerate(tail, 75):
        result["15m"][i] = replace(result["15m"][i], open=o, high=h, low=lo, close=c)
    return result


def mirrored(histories):
    return {tf: [replace(b, open=250-b.open, high=250-b.low,
                        low=250-b.high, close=250-b.close) for b in bars]
            for tf, bars in histories.items()}


class ConfluenceTests(unittest.TestCase):
    def test_actual_five_rules_can_score_100_without_probability_or_orders(self):
        for direction, data in (("long", frames()), ("short", mirrored(frames()))):
            result = confluence_score(data, "BTCUSDT", NOW, direction)
            self.assertEqual(result["score"], 100)
            self.assertEqual(result["decision"], "paper_watchlist_only")
            self.assertTrue(all(x["passed"] for x in result["evidence"].values()))
            self.assertEqual(result["score"], sum(x["points"] for x in result["evidence"].values()))
            self.assertIsNone(result["win_probability"])
            self.assertFalse(result["orders_enabled"])
            self.assertFalse(result["independently_cross_checked"])

    def test_fvg_has_numeric_bounds_and_cannot_use_formation_bar_as_retest(self):
        bars = frames()["15m"]
        formed = bars[87].close_time
        patterns = _active_patterns(bars, "long")
        p = next(x for x in patterns if x["gap"]["formed_at"] == formed)
        self.assertEqual(p["gap"]["low"], 110)
        self.assertEqual(p["gap"]["high"], 112)
        self.assertTrue(p["retested"])
        self.assertTrue(p["ob_overlap"])
        self.assertGreater(p["observed_at"], formed)
        self.assertFalse(any(x["gap"]["formed_at"] == formed for x in _active_patterns(bars[:88], "long")))

    def test_full_mitigation_invalidates_fvg_including_equality(self):
        for low in (110, 109.9):
            data = frames()
            data["15m"][-1] = replace(data["15m"][-1], low=low)
            result = confluence_score(data, "ETHUSDT", NOW)
            self.assertFalse(result["evidence"]["fvg_retest"]["passed"])
            self.assertEqual(result["decision"], "wait")

    def test_no_retest_and_no_displacement_do_not_get_gap_points(self):
        data = frames()
        data["15m"][-1] = replace(data["15m"][-1], open=113, low=112.5, high=114, close=113)
        self.assertFalse(confluence_score(data, "BTCUSDT", NOW)["evidence"]["fvg_retest"]["passed"])
        data = frames()
        data["15m"][86] = replace(data["15m"][86], open=113.4)
        self.assertFalse(confluence_score(data, "BTCUSDT", NOW)["evidence"]["fvg_retest"]["passed"])

    def test_target_already_traded_through_cannot_earn_liquidity_points(self):
        data = frames()
        data["15m"][-1] = replace(data["15m"][-1], high=200)
        passed, details = _liquidity(data, "long")
        self.assertFalse(passed)
        self.assertIsNone(details["target"])

    def test_conflicting_htf_trend_abstains(self):
        data = frames()
        data["4h"] = mirrored(data)["4h"]
        result = confluence_score(data, "BTCUSDT", NOW)
        self.assertFalse(result["evidence"]["htf_trend"]["passed"])
        self.assertLess(result["score"], 100)
        self.assertEqual(result["decision"], "wait")

    def test_flat_history_has_no_fabricated_price_pattern(self):
        data = {tf: [replace(b, open=100, high=100, low=100, close=100) for b in bars]
                for tf, bars in frames().items()}
        result = confluence_score(data, "BTCUSDT", NOW)
        self.assertEqual(result["score"], 20)  # Time window only.
        self.assertEqual(result["decision"], "wait")

    def test_stale_future_gapped_and_nonfinite_bars_fail_instead_of_scoring(self):
        data = frames()
        for invalid in ({}, {"15m": data["15m"]}):
            with self.assertRaises(ConfluenceError):
                confluence_score(invalid, "BTCUSDT", NOW)
        for changed in (replace(data["15m"][30], close=math.nan),
                        replace(data["15m"][30], time=data["15m"][30].time+1),
                        replace(data["15m"][30], high=1e13),
                        replace(data["15m"][30], volume=True)):
            bad = frames(); bad["15m"][30] = changed
            with self.assertRaises(ConfluenceError):
                confluence_score(bad, "BTCUSDT", NOW)
        for timestamp in (NOW-900_000, NOW+28_800_000, True, -1):
            with self.assertRaises(ConfluenceError):
                confluence_score(data, "BTCUSDT", timestamp)

    def test_unsupported_pair_and_side_are_rejected(self):
        for symbol, direction in (("DOGEUSDT", "long"), ("BTCUSDT", "buy-now")):
            with self.assertRaises(ConfluenceError):
                confluence_score(frames(), symbol, NOW, direction)

    def test_ny_dst_boundaries_weekends_and_half_open_windows(self):
        def check(timestamp):
            return time_filter(int(datetime.fromisoformat(timestamp).timestamp()*1000))
        summer = check("2026-07-07T14:30:00+00:00")
        winter = check("2026-01-06T15:30:00+00:00")
        self.assertEqual(summer["active_windows"], ["silver_bullet_am"])
        self.assertEqual(winter["active_windows"], ["silver_bullet_am"])
        self.assertIn("-04:00", summer["local_time"])
        self.assertIn("-05:00", winter["local_time"])
        self.assertFalse(check("2026-07-07T15:00:00+00:00")["passed"])  # 11:00 NY, exclusive end.
        self.assertTrue(check("2026-07-07T14:00:00+00:00")["passed"])
        self.assertFalse(check("2026-10-31T14:30:00+00:00")["passed"])
        # US/UK DST change on different dates; use NY, not a fixed UTC offset.
        self.assertEqual(check("2026-03-10T14:30:00+00:00")["active_windows"], ["silver_bullet_am"])


if __name__ == "__main__":
    unittest.main()

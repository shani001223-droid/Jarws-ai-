"""Task 40: six evidence-family gates, stale data and read-only API tests."""
from dataclasses import replace
import math
import unittest
from unittest.mock import patch

from fastapi import Response
from cloud_backend import main
from cloud_backend.setup_assessment import SetupAssessmentError, _evaluate, assess_spot_setup
from cloud_backend.trading_research import INTERVALS, closed_candles

NOW = 1_800_000_000_000
FRAMES = ("15m", "1h", "4h")


def sample_analysis():
    structure = {"symbol": "BTCUSDT", "market": "spot", "orders_enabled": False,
                 "mode": "structure-research-only",
                 "alignment": "all_three_bullish_structure", "timeframes": {}}
    indicators = {"symbol": "BTCUSDT", "market": "spot", "orders_enabled": False,
                  "mode": "indicators-research-only",
                  "formula_version": "spot-indicators-v1", "timeframes": {}}
    for tf in FRAMES:
        structure["timeframes"][tf] = {"last_closed_at": 1000, "last_close": 112,
                                       "structure": "higher_highs_higher_lows",
                                       "pivot_confirmation_bars": 2}
        indicators["timeframes"][tf] = {
            "last_closed_at": 1000, "last_close": 112,
            "vwap_full_session_from_open": True,
            "values": {"ema9": 110, "ema20": 108, "ema21": 109, "ema50": 100,
                       "rsi14": 60, "atr14": 1, "volume_sma20_base": 10,
                       "volume_ratio20": 1.5, "utc_session_vwap": 105}}
    return structure, indicators


def history(tf, slope=0.16, count=90):
    step = INTERVALS[tf]
    start = (NOW // step - count) * step
    wave = (0, 1, 3, 1, 0, -1, -3, -1)
    rows = []
    for i in range(count):
        t = start + i * step
        p = 100 + slope*i + wave[i % len(wave)]
        rows.append([t, p, p + .2, p - .2, p, 10, t + step - 1])
    return closed_candles(rows, tf, NOW)


def histories():
    return {tf: history(tf) for tf in FRAMES}


class AssessmentUnitTests(unittest.TestCase):
    def test_all_six_evidence_families_required_for_watchlist(self):
        structure, metrics = sample_analysis()
        result = _evaluate(structure, metrics)
        self.assertEqual(result["decision"], "paper_watchlist_only")
        self.assertEqual(result["positive_families"], 6)
        self.assertEqual(result["families_checked"], 6)
        self.assertFalse(result["orders_enabled"])
        self.assertFalse(result["independently_cross_checked"])
        self.assertFalse(result["entry_stop_tp_available"])
        for forbidden in ("confidence", "win_probability", "entry", "stop", "tp", "target"):
            self.assertNotIn(forbidden, result)

    def test_each_family_can_veto_watchlist(self):
        cases = (
            lambda s, m: (s["timeframes"]["1h"].update(structure="mixed_structure"),
                          s.update(alignment="mixed_timeframes")),
            lambda s, m: m["timeframes"]["1h"]["values"].update(ema9=99),
            lambda s, m: m["timeframes"]["15m"]["values"].update(rsi14=75),
            lambda s, m: m["timeframes"]["15m"]["values"].update(volume_ratio20=1),
            lambda s, m: m["timeframes"]["15m"]["values"].update(utc_session_vwap=None),
            lambda s, m: m["timeframes"]["15m"]["values"].update(atr14=0),
        )
        for mutate in cases:
            with self.subTest(mutate=mutate):
                structure, metrics = sample_analysis()
                mutate(structure, metrics)
                result = _evaluate(structure, metrics)
                self.assertEqual(result["decision"], "wait")
                self.assertLess(result["positive_families"], 6)

    def test_mismatched_or_invalid_analysis_fails_closed(self):
        mutations = (
            lambda s, m: m.update(symbol="ETHUSDT"),
            lambda s, m: m["timeframes"]["4h"].update(last_closed_at=999),
            lambda s, m: m["timeframes"]["4h"].update(last_close=111),
            lambda s, m: m["timeframes"]["15m"]["values"].update(rsi14=math.nan),
            lambda s, m: m["timeframes"]["15m"]["values"].update(rsi14=True),
            lambda s, m: m["timeframes"]["15m"]["values"].update(rsi14=120),
            lambda s, m: m.update(formula_version="unknown"),
            lambda s, m: s.update(orders_enabled=True),
            lambda s, m: m["timeframes"].pop("4h"),
            lambda s, m: s["timeframes"]["1h"].update(structure="mixed_structure"),
            lambda s, m: s["timeframes"]["1h"].update(pivot_confirmation_bars=0),
            lambda s, m: s["timeframes"]["1h"].update(pivot_confirmation_bars=True),
            lambda s, m: s["timeframes"]["1h"].update(structure="future_pivot"),
            lambda s, m: s.update(mode="order-engine"),
            lambda s, m: m.update(mode="order-engine"),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                structure, metrics = sample_analysis()
                mutate(structure, metrics)
                with self.assertRaises(SetupAssessmentError):
                    _evaluate(structure, metrics)

    def test_real_analyzers_use_same_closed_histories(self):
        data = histories()
        result = assess_spot_setup(data, "BTCUSDT")
        self.assertEqual(result["mode"], "paper-watchlist-research-only")
        self.assertFalse(result["orders_enabled"])
        self.assertEqual(result["last_closed_at"],
                         {tf: bars[-1].close_time for tf, bars in data.items()})
        self.assertIn(result["decision"], ("wait", "paper_watchlist_only"))

    def test_invalid_pair_and_tampered_history_rejected(self):
        with self.assertRaises(SetupAssessmentError):
            assess_spot_setup(histories(), "SOLUSDT")
        altered = histories()
        altered["1h"][10] = replace(altered["1h"][10], volume=-1)
        with self.assertRaises(SetupAssessmentError):
            assess_spot_setup(altered, "BTCUSDT")


class AssessmentApiTests(unittest.TestCase):
    def test_read_only_api_fetches_three_frames(self):
        data = histories()
        calls = []
        def source(pair, tf):
            calls.append((pair, tf))
            return data[tf], NOW // 1000
        response = Response()
        with patch.object(main, "_research_history", side_effect=source), patch.object(
                main.time, "time", return_value=NOW / 1000):
            result = main.trading_setup_assessment(response, "BTCUSDT")
        self.assertEqual({tf for _, tf in calls}, set(FRAMES))
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertFalse(result["orders_enabled"])
        self.assertFalse(result["independently_cross_checked"])

    def test_bad_pair_pre_network_and_stale_source_503(self):
        with patch.object(main, "_research_history") as fetch:
            with self.assertRaises(main.HTTPException) as err:
                main.trading_setup_assessment(Response(), "SOLUSDT")
            self.assertEqual(err.exception.status_code, 422)
            fetch.assert_not_called()
        with patch.object(main, "_research_history",
                          return_value=(history("15m"), NOW // 1000 - 500)), patch.object(
                main.time, "time", return_value=NOW / 1000):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_setup_assessment(Response(), "BTCUSDT")
            self.assertEqual(err.exception.status_code, 503)

    def test_provider_error_is_503_not_fabricated_signal(self):
        with patch.object(main, "_research_history",
                          side_effect=main.HTTPException(status_code=503)):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_setup_assessment(Response(), "BTCUSDT")
            self.assertEqual(err.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()

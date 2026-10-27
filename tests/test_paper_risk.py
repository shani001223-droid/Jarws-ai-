"""Task 41: hypothetical risk sizing and read-only HTTP route regression."""
from dataclasses import replace
import math
import unittest
from unittest.mock import patch

from fastapi import Response
from cloud_backend import main
from cloud_backend.paper_risk import PaperRiskError, build_paper_risk, assess_paper_risk
from cloud_backend.trading_research import INTERVALS, closed_candles

NOW = 1_800_000_000_000
FRAMES = ("15m", "1h", "4h")
FAMILIES = ("confirmed_structure", "ema_trend", "rsi_momentum",
            "volume_participation", "session_vwap", "atr_volatility_guard")


def sample_analysis():
    assessment = {
        "symbol": "BTCUSDT", "market": "spot", "mode": "paper-watchlist-research-only",
        "orders_enabled": False, "version": "spot-setup-assessment-v1",
        "independently_cross_checked": False, "entry_stop_tp_available": False,
        "structure_alignment": "all_three_bullish_structure",
        "decision": "paper_watchlist_only", "positive_families": 6,
        "families_checked": 6, "last_closed_at": {tf: 1000 for tf in FRAMES},
        "evidence": {key: {"status": "supports_watchlist"} for key in FAMILIES},
    }
    structure = {
        "symbol": "BTCUSDT", "market": "spot", "mode": "structure-research-only",
        "orders_enabled": False, "alignment": "all_three_bullish_structure",
        "timeframes": {tf: {"last_closed_at": 1000, "last_close": 112,
                             "support": 110.5, "pivot_confirmation_bars": 2}
                       for tf in FRAMES},
    }
    indicators = {
        "symbol": "BTCUSDT", "market": "spot", "mode": "indicators-research-only",
        "orders_enabled": False, "formula_version": "spot-indicators-v1",
        "timeframes": {tf: {"last_closed_at": 1000, "last_close": 112,
                             "values": {"atr14": 1}} for tf in FRAMES},
    }
    return assessment, structure, indicators


def history(tf, count=90):
    step = INTERVALS[tf]
    start = (NOW // step - count) * step
    wave = (0, 1, 3, 1, 0, -1, -3, -1)
    rows = []
    for i in range(count):
        t = start + i * step
        price = 100 + .16*i + wave[i % len(wave)]
        rows.append([t, price, price + .2, price - .2, price, 10, t + step - 1])
    return closed_candles(rows, tf, NOW)


def histories():
    return {tf: history(tf) for tf in FRAMES}


class PaperRiskUnitTests(unittest.TestCase):
    def test_cash_and_risk_caps_and_hypothetical_targets(self):
        result = build_paper_risk(*sample_analysis(), equity_usdt=100, risk_pct=.5)
        self.assertEqual(result["decision"], "paper_plan_only")
        self.assertFalse(result["orders_enabled"])
        self.assertFalse(result["independently_cross_checked"])
        plan = result["paper_plan"]
        self.assertLessEqual(plan["estimated_stop_loss_including_costs_usdt"], .5 + 1e-9)
        self.assertLessEqual(plan["estimated_notional_usdt"], 100)
        self.assertEqual(plan["side"], "long")
        self.assertLess(plan["reference_stop"], plan["reference_entry_close"])
        self.assertEqual([x["multiple_before_costs"] for x in plan["targets"]], [1, 2])
        self.assertGreater(plan["targets"][1]["reference_price"],
                           plan["targets"][0]["reference_price"])
        self.assertFalse(plan["fills_simulated"])
        self.assertFalse(plan["exchange_order_validated"])

    def test_unconfirmed_watchlist_and_missing_support_are_wait(self):
        a, s, i = sample_analysis()
        a["decision"] = "wait"
        a["positive_families"] = 5
        a["evidence"]["session_vwap"]["status"] = "does_not_support"
        result = build_paper_risk(a, s, i)
        self.assertEqual(result["reason_code"], "setup_not_confirmed")
        self.assertIsNone(result["paper_plan"])
        a, s, i = sample_analysis()
        s["timeframes"]["15m"]["support"] = None
        self.assertEqual(build_paper_risk(a, s, i)["reason_code"],
                         "no_confirmed_support")
        s["timeframes"]["15m"]["support"] = 90
        self.assertEqual(build_paper_risk(a, s, i)["reason_code"],
                         "stop_distance_outside_guardrails")

    def test_forged_identity_and_snapshot_rejected(self):
        cases = (
            lambda a, s, i: a.update(orders_enabled=True),
            lambda a, s, i: a.update(positive_families=5),
            lambda a, s, i: a.update(structure_alignment="mixed_timeframes"),
            lambda a, s, i: s["timeframes"]["15m"].update(last_close=111),
            lambda a, s, i: i["timeframes"]["1h"].update(last_closed_at=999),
            lambda a, s, i: i.update(formula_version="unknown"),
            lambda a, s, i: s["timeframes"]["15m"].update(pivot_confirmation_bars=0),
            lambda a, s, i: a.update(entry_stop_tp_available=True),
        )
        for mutate in cases:
            with self.subTest(mutate=mutate):
                a, s, i = sample_analysis()
                mutate(a, s, i)
                with self.assertRaises(PaperRiskError):
                    build_paper_risk(a, s, i)

    def test_bad_risk_parameters_rejected(self):
        for settings in ({"equity_usdt": math.nan}, {"equity_usdt": True},
                         {"risk_pct": 2}, {"fee_bps": 0},
                         {"slippage_bps": math.inf}):
            with self.subTest(settings=settings):
                with self.assertRaises(PaperRiskError):
                    build_paper_risk(*sample_analysis(), **settings)

    def test_cost_model_can_veto_plan(self):
        cheap = build_paper_risk(*sample_analysis(), fee_bps=1, slippage_bps=1)
        expensive = build_paper_risk(*sample_analysis(), fee_bps=100,
                                     slippage_bps=100)
        self.assertEqual(cheap["decision"], "paper_plan_only")
        self.assertEqual(expensive["decision"], "wait")
        self.assertEqual(expensive["reason_code"], "estimated_costs_erase_reward")

    def test_real_analyzers_shared_closed_candles(self):
        result = assess_paper_risk(histories(), "BTCUSDT")
        self.assertEqual(result["mode"], "hypothetical-paper-risk-only")
        self.assertFalse(result["orders_enabled"])
        self.assertEqual(result["last_closed_at"],
                         {tf: bars[-1].close_time for tf, bars in histories().items()})
        self.assertIn(result["decision"], ("wait", "paper_plan_only"))
        with self.assertRaises(PaperRiskError):
            assess_paper_risk(histories(), "SOLUSDT")
        corrupted = histories()
        corrupted["1h"][10] = replace(corrupted["1h"][10], volume=-1)
        with self.assertRaises(PaperRiskError):
            assess_paper_risk(corrupted, "BTCUSDT")


class PaperRiskApiTests(unittest.TestCase):
    def test_read_only_route_fetches_same_three_frames(self):
        data, calls = histories(), []
        def source(pair, tf):
            calls.append((pair, tf))
            return data[tf], NOW // 1000
        response = Response()
        with patch.object(main, "_research_history", side_effect=source), patch.object(
                main.time, "time", return_value=NOW / 1000):
            result = main.trading_paper_risk(response, "BTCUSDT", 100, .5, 10, 5)
        self.assertEqual(set(calls), {("BTCUSDT", tf) for tf in FRAMES})
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertFalse(result["orders_enabled"])
        routes = [r for r in main.app.routes if r.path == "/api/trading/paper-risk"]
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].methods, {"GET"})

    def test_invalid_pair_and_budget_fail_before_network(self):
        with patch.object(main, "_research_history") as fetch:
            for pair, equity in (("SOLUSDT", 100), ("BTCUSDT", 0)):
                with self.assertRaises(main.HTTPException) as err:
                    main.trading_paper_risk(Response(), pair, equity, .5, 10, 5)
                self.assertEqual(err.exception.status_code, 422)
            fetch.assert_not_called()

    def test_stale_and_unavailable_provider_fail_closed(self):
        with patch.object(main, "_research_history",
                          return_value=(history("15m"), NOW // 1000 - 500)), patch.object(
                main.time, "time", return_value=NOW / 1000):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_paper_risk(Response(), "BTCUSDT", 100, .5, 10, 5)
            self.assertEqual(err.exception.status_code, 503)
        with patch.object(main, "_research_history",
                          side_effect=main.HTTPException(status_code=503)):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_paper_risk(Response(), "BTCUSDT", 100, .5, 10, 5)
            self.assertEqual(err.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()

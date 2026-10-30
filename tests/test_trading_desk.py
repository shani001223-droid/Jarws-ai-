"""Trading-only desk: synthetic candles, real analyzers and no paid API calls."""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import Mock, patch
import unittest

from fastapi.testclient import TestClient
from cloud_backend import main, trading_desk as desk
from cloud_backend.brain import KnowledgeError
from test_paper_risk import NOW, FRAMES, histories, sample_analysis


class TradingDeskTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        self.data = histories()

    def test_real_analyzers_share_one_set_of_three_fetched_histories(self):
        calls = []
        def source(pair, tf):
            calls.append((pair, tf))
            return self.data[tf], NOW // 1000
        with patch.object(main, "_research_history", side_effect=source), patch.object(
                main.time, "time", return_value=NOW / 1000):
            response = self.client.get("/api/trading/desk")
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual(len(calls), 3)
        self.assertEqual(set(calls), {("BTCUSDT", tf) for tf in FRAMES})
        self.assertEqual(result["version"], "hoshi-trading-desk-v1")
        self.assertEqual(result["expires_at_ms"], NOW + 60_000)
        self.assertFalse(result["orders_enabled"])
        self.assertIsNone(result["win_probability"])
        self.assertEqual(result["knowledge_version"], "hoshi-trading-knowledge-v2")
        self.assertEqual(result["v3_runtime_integration"], "pending")
        self.assertEqual(response.headers["cache-control"], "no-store")
        for tf in FRAMES:
            self.assertEqual(result["timeframes"][tf]["last_close"], self.data[tf][-1].close)
            self.assertEqual(result["timeframes"][tf]["last_closed_at"], self.data[tf][-1].close_time)

    def test_invalid_symbol_or_risk_never_fetches(self):
        with patch.object(main, "_research_history") as fetch:
            for query in ("symbol=SOLUSDT", "symbol=../main.py", "equity_usdt=0",
                          "risk_pct=2", "risk_pct=NaN", "fee_bps=0", "slippage_bps=inf"):
                with self.subTest(query=query):
                    self.assertEqual(self.client.get("/api/trading/desk?" + query).status_code, 422)
            fetch.assert_not_called()
        self.assertEqual(self.client.post("/api/trading/desk", json={"score": 100}).status_code, 405)

    @unittest.skipUnless(shutil.which("node"), "Node needed for cross-language UI contract")
    def test_client_accepts_actual_backend_snapshot(self):
        result = desk.build_trading_desk(self.data, "BTCUSDT", NOW, NOW // 1000)
        script = ("const fs=require('node:fs'),d=require('./hoshi-trading-desk.js');"
                  "const x=JSON.parse(fs.readFileSync(0,'utf8'));"
                  "d.validate(x,{symbol:'BTCUSDT',equity_usdt:100,risk_pct:.5,fee_bps:10,slippage_bps:5},"
                  + str(NOW) + ");")
        checked = subprocess.run([shutil.which("node"), "-e", script],
                                 input=json.dumps(result), text=True, capture_output=True,
                                 timeout=10, cwd=Path(__file__).resolve().parents[1])
        self.assertEqual(checked.returncode, 0, checked.stderr)

    def test_stale_future_and_noninteger_source_times_are_wait_and_sanitized(self):
        slots = Mock(); slots.acquire.return_value = True
        for stamp in (NOW // 1000 - 121, NOW // 1000 + 6, True, float("nan"), 1.5):
            with self.subTest(stamp=stamp), patch.object(main, "_RESEARCH_SLOTS", slots), patch.object(
                    main, "_research_history", side_effect=lambda pair, tf: (self.data[tf], stamp)), patch.object(
                    main.time, "time", return_value=NOW / 1000):
                response = self.client.get("/api/trading/desk")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["detail"]["decision"], "wait")
                self.assertIsNone(response.json()["detail"]["paper_plan"])
                self.assertNotIn('"score":', response.text)
        self.assertEqual(slots.release.call_count, 5)

    def test_candle_corruption_and_future_closes_fail_closed(self):
        for corrupt in ("volume", "future"):
            data = histories()
            if corrupt == "volume":
                data["1h"][10] = replace(data["1h"][10], volume=-1)
            else:
                data["15m"] = [replace(b, time=b.time+900000, close_time=b.close_time+900000)
                               for b in data["15m"]]
            with self.subTest(corrupt=corrupt), patch.object(main, "_research_history",
                    side_effect=lambda pair, tf: (data[tf], NOW // 1000)), patch.object(
                    main.time, "time", return_value=NOW / 1000):
                self.assertEqual(self.client.get("/api/trading/desk").status_code, 503)

    def test_broken_bundle_blocks_network_and_never_exposes_private_paths(self):
        with patch.object(main, "load_knowledge", side_effect=KnowledgeError("/private/key")), patch.object(
                main, "_research_history") as fetch:
            response = self.client.get("/api/trading/desk")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private", response.text)
        fetch.assert_not_called()

    def test_busy_and_provider_errors_release_capacity_safely(self):
        slots = Mock(); slots.acquire.return_value = False
        with patch.object(main, "_RESEARCH_SLOTS", slots), patch.object(main, "_research_history") as fetch:
            self.assertEqual(self.client.get("/api/trading/desk").status_code, 429)
            slots.release.assert_not_called(); fetch.assert_not_called()
        slots.acquire.return_value = True
        with patch.object(main, "_RESEARCH_SLOTS", slots), patch.object(main, "_research_history",
                side_effect=RuntimeError("secret upstream key")):
            response = self.client.get("/api/trading/desk")
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("secret", response.text)
            slots.release.assert_called_once()

    def test_confluence_vetoes_an_otherwise_cost_bounded_paper_plan(self):
        # Deliberately synthetic positive analyzer seam; these are not real trades.
        setup, structure, indicators = sample_analysis()
        for tf in FRAMES:
            structure["timeframes"][tf].update(structure="higher_highs_higher_lows", resistance=120)
            indicators["timeframes"][tf]["values"].update(rsi14=60, ema20=110, ema50=109)
        for score in (80, 100):
            confluence = {"score": score, "decision": "paper_watchlist_only" if score == 100 else "wait"}
            with patch.object(desk, "confluence_score", return_value=confluence), patch.object(
                    desk, "analyze_market_structure", return_value=structure), patch.object(
                    desk, "analyze_market_indicators", return_value=indicators), patch.object(
                    desk, "_evaluate", return_value=setup):
                result = desk.build_trading_desk(self.data, "BTCUSDT", NOW, NOW // 1000)
            if score == 80:
                self.assertEqual(result["decision"], "wait")
                self.assertIsNone(result["paper_plan"])
            else:
                self.assertEqual(result["decision"], "paper_plan_only")
                self.assertLessEqual(result["paper_plan"]["estimated_stop_loss_including_costs_usdt"], .5)


if __name__ == "__main__":
    unittest.main()

"""Deterministic financial/data-boundary tests. No exchange account or live orders."""
import json
import math
import unittest
from dataclasses import replace
from unittest.mock import patch

from cloud_backend import trading_research as tr, main


def bars(n=80, start=0):
    return [tr.Candle(start+i*900000, 100, 101, 99, 100, 10,
                      start+(i+1)*900000-1) for i in range(n)]


def rows(tf="15m", n=80, now=1_800_000_000_000):
    step = tr.INTERVALS[tf]
    start = (now//step-n)*step
    return [[start+i*step, "100", "101", "99", "100", "10", start+(i+1)*step-1]
            for i in range(n)]


def one_signal(history, _strategy):
    return {"stop": 95, "reference_entry": 100} if len(history) == 64 else None


class CandleTests(unittest.TestCase):
    def test_excludes_forming_candle_and_checks_freshness_at_candle_boundary(self):
        now = 1_800_000_000_000
        data = rows(now=now)
        data.append([now, "100", "101", "99", "100", "10", now+899999])
        result = tr.closed_candles(data, "15m", now)
        self.assertEqual(len(result), 80)
        self.assertLess(result[-1].close_time, now)
        with self.assertRaises(ValueError):
            tr.closed_candles(data[:-1], "15m", now+1_100_000)

    def test_rejects_nonfinite_negative_and_inconsistent_prices(self):
        for column, value in [(1,"nan"),(2,"inf"),(3,"-1"),(4,"102"),(5,"-1")]:
            data = rows(); data[30][column] = value
            with self.subTest(column=column), self.assertRaises(ValueError):
                tr.closed_candles(data, "15m", 1_800_000_000_000)

    def test_rejects_duplicates_gaps_bad_close_times_and_future_bars(self):
        for index, column, delta in [(20,0,-900000),(20,0,900000),(20,6,1),(79,0,900000*2)]:
            data = rows();data[index][column] += delta
            with self.subTest(index=index,column=column), self.assertRaises(ValueError):
                tr.closed_candles(data,"15m",1_800_000_000_000)

    def test_shared_research_parser_refuses_lossy_provider_timestamps(self):
        # The mobile desk calls this shared parser, not the separate
        # Binance/Kraken quality endpoint. Previously int(float) truncated
        # fractional millisecond identities into apparently valid bars.
        for tf in tr.INTERVALS:
            for column in (0, 6):
                for invalid in (True, 1.5, "1e3", "01800000000000", -1):
                    with self.subTest(tf=tf, column=column, invalid=invalid):
                        data = rows(tf)
                        data[20][column] = invalid
                        with self.assertRaisesRegex(ValueError, "Invalid candle timestamp"):
                            tr.closed_candles(data, tf, 1_800_000_000_000)
            # Even an exactly representable float is not an exact JSON
            # integer type; a tiny fraction can disappear in binary64.
            data = rows(tf)
            data[20][0] = float(data[20][0])
            with self.assertRaisesRegex(ValueError, "Invalid candle timestamp"):
                tr.closed_candles(data, tf, 1_800_000_000_000)
            data = rows(tf)
            data[20][0] = str(data[20][0])
            data[20][6] = str(data[20][6])
            self.assertEqual(len(tr.closed_candles(data, tf, 1_800_000_000_000)), 80)
        with self.assertRaisesRegex(ValueError, "Invalid candle clock"):
            tr.closed_candles(rows(), "15m", True)

    def test_shared_candle_parser_refuses_boolean_ohlcv_even_if_row_is_coherent(self):
        # Every case would pass the previous float(True) coercion and
        # ordinary OHLC validation. The shared mobile desk must refuse it.
        plausible = {
            1: [True, 2, .5, 1.5, 10],
            2: [.8, True, .5, .9, 10],
            3: [1.5, 2, True, 1.5, 10],
            4: [.8, 2, .5, True, 10],
            5: [1, 2, .5, 1.5, True],
        }
        for tf in tr.INTERVALS:
            for column, values in plausible.items():
                with self.subTest(tf=tf, column=column):
                    data = rows(tf)
                    data[20][1:6] = values
                    with self.assertRaisesRegex(ValueError, "Invalid candle numeric field"):
                        tr.closed_candles(data, tf, 1_800_000_000_000)
        self.assertEqual(len(tr.closed_candles(rows(), "15m", 1_800_000_000_000)), 80)

    def test_refuses_finite_extreme_ohlcv_before_indicator_overflow(self):
        # 1e308 is finite as a float, but repeated EMA sums overflow.
        # Coherent extreme candles must never become market observations.
        for tf in tr.INTERVALS:
            with self.subTest(tf=tf):
                data = rows(tf)
                for row in data:
                    row[1:6] = ["1e308"] * 5
                with self.assertRaisesRegex(ValueError, "Invalid candle values/timing"):
                    tr.closed_candles(data, tf, 1_800_000_000_000)
        data = rows()
        data[20][5] = "1e308"
        with self.assertRaisesRegex(ValueError, "Invalid candle values/timing"):
            tr.closed_candles(data, "15m", 1_800_000_000_000)
        self.assertEqual(len(tr.closed_candles(rows(), "15m", 1_800_000_000_000)), 80)

    def test_flat_market_has_neutral_rsi_finite_atr_and_no_setup(self):
        data = bars()
        ind = tr.indicators(data)
        self.assertEqual(ind["rsi14"][-1],50)
        self.assertEqual(ind["atr14"][-1],2)
        self.assertEqual(ind["ema20"][-1],100)
        self.assertEqual(tr.snapshot(data)["regime"],"range")
        self.assertTrue(all(tr.setup(data,s) is None for s in tr.STRATEGIES))

    def test_ema_is_sma_seeded_and_future_data_cannot_change_past_indicators(self):
        data = [replace(b,close=100+i,open=100+i,high=102+i,low=98+i) for i,b in enumerate(bars())]
        first=tr.indicators(data[:65]);full=tr.indicators(data)
        self.assertEqual(full["ema20"][19],109.5)
        self.assertEqual(full["ema50"][49],124.5)
        for key in first:
            self.assertEqual(first[key],full[key][:65])

    def test_levels_exclude_signal_candle(self):
        data=bars();data[-1]=replace(data[-1],high=200,low=50)
        result=tr.snapshot(data)
        self.assertEqual(result["support"],99)
        self.assertEqual(result["resistance"],101)


class StrategyTests(unittest.TestCase):
    def test_trend_pullback_requires_price_and_volume_confirmation(self):
        data=[replace(b,open=100+i*.1,close=100+i*.1+.05,
                      high=100+i*.1+.2,low=100+i*.1-.2) for i,b in enumerate(bars())]
        e20=tr.indicators(data)["ema20"][-1]
        data[-1]=replace(data[-1],low=e20-.1,volume=20)
        self.assertIsNotNone(tr.setup(data,"trend_pullback"))
        data[-1]=replace(data[-1],volume=0)
        self.assertIsNone(tr.setup(data,"trend_pullback"))

    def test_breakout_retest_requires_prior_break_and_valid_current_retest(self):
        data=bars()
        data[-3]=replace(data[-3],open=100,high=103,low=100,close=102,volume=20)
        data[-2]=replace(data[-2],open=102,high=103,low=101.5,close=102)
        data[-1]=replace(data[-1],open=101.2,high=103,low=101,close=102.5,volume=20)
        self.assertIsNotNone(tr.setup(data,"breakout_retest"))
        data[-1]=replace(data[-1],low=98)
        self.assertIsNone(tr.setup(data,"breakout_retest"))

    def test_research_waits_when_higher_timeframe_disagrees(self):
        histories={tf:bars() for tf in tr.INTERVALS}
        with patch.object(tr,"setup",return_value={"side":"long"}):
            result=tr.research(histories,"BTCUSDT",123)
        self.assertEqual(result["decision"],"wait")
        self.assertEqual(result["proposals"],[])
        self.assertFalse(result["orders_enabled"])


class SimulatorTests(unittest.TestCase):
    def test_next_open_fill_costs_and_stop_first_on_ambiguous_bar(self):
        data=bars(66);data[64]=replace(data[64],open=102,high=120,low=90,close=100)
        cfg=tr.SimulationConfig()
        with patch.object(tr,"setup",side_effect=one_signal):
            result=tr.backtest(data,"trend_pullback",cfg)
        trade=result["trades"][0]
        self.assertAlmostEqual(trade["entry"],102*1.0005)
        self.assertAlmostEqual(trade["exit"],95*.9995)
        self.assertEqual(trade["entry_time"],data[64].time)
        self.assertEqual(trade["reason"],"stop")
        self.assertEqual(trade["exit_time"], data[64].close_time)
        self.assertEqual(trade["exit_time_precision"], "bar_close_upper_bound_intrabar_unknown")
        self.assertTrue(trade["stop_target_same_bar"])
        self.assertEqual(trade["reference_stop"], 95)
        self.assertGreater(trade["reference_target"], trade["entry"])
        self.assertIsNone(trade["gap_beyond_stop_pct"])
        self.assertEqual(result["execution_diagnostics"]["stop_first_ambiguous_count"], 1)
        self.assertEqual(result["execution_diagnostics"]["gap_stop_count"], 0)
        self.assertIsNone(result["execution_diagnostics"]["max_gap_beyond_stop_pct"])
        self.assertAlmostEqual(trade["net_pnl"],-5)
        self.assertAlmostEqual(trade["risk_budget_at_entry_usdt"], 5)
        self.assertAlmostEqual(trade["planned_stop_loss_usdt"], 5)
        self.assertFalse(trade["risk_budget_breached"])
        self.assertFalse(trade["planned_stop_loss_exceeded"])
        self.assertAlmostEqual(trade["realized_loss_to_budget_multiple"], 1)
        self.assertEqual(result["execution_diagnostics"]["risk_budget_breach_count"], 0)
        self.assertEqual(result["execution_diagnostics"]["planned_stop_loss_exceeded_count"], 0)
        self.assertFalse(trade["utc_day_gross_loss_cap_breached"])
        self.assertAlmostEqual(trade["utc_day_gross_realized_loss_after_exit_usdt"], 5)
        self.assertEqual(result["execution_diagnostics"]["utc_gross_loss_cap_breach_days"], 0)
        self.assertAlmostEqual(result["execution_diagnostics"]["max_utc_day_gross_realized_loss_usdt"], 5)
        self.assertGreater(trade["fees"],0)
        self.assertAlmostEqual(result["ending_equity"],995)

    def test_exact_stop_at_open_is_not_misclassified_as_adverse_gap(self):
        # The stop is met at the OPEN, before the same candle's target wick.
        # No below-stop gap occurred; its gap diagnostic must stay empty.
        data = bars(67)
        data[65] = replace(data[65], open=95, high=120, low=94, close=100)
        with patch.object(tr, "setup", side_effect=one_signal):
            result = tr.backtest(data, "trend_pullback", tr.SimulationConfig())
        trade = result["trades"][0]
        self.assertEqual(trade["reason"], "stop_at_open")
        self.assertEqual(trade["exit_time"], data[65].time)
        self.assertEqual(trade["exit_time_precision"], "bar_open_exact")
        self.assertAlmostEqual(trade["exit"], 95 * .9995)
        self.assertIsNone(trade["gap_beyond_stop_pct"])
        self.assertFalse(trade["stop_target_same_bar"])
        self.assertEqual(result["execution_diagnostics"]["gap_stop_count"], 0)
        self.assertIsNone(result["execution_diagnostics"]["max_gap_beyond_stop_pct"])
        self.assertLess(trade["net_pnl"], 0)

    def test_target_gap_open_precedes_intrabar_stop_without_gap_windfall(self):
        # Synthetic OHLC, not market evidence: target is crossed at the
        # next bar OPEN, so a later intrabar low cannot fill stop first.
        for opening in (110.15, 115):
            data = bars(67)
            data[65] = replace(data[65], open=opening, high=116, low=90, close=100)
            with self.subTest(opening=opening), patch.object(
                    tr, "setup", side_effect=one_signal):
                result = tr.backtest(data, "trend_pullback", tr.SimulationConfig())
            trade = result["trades"][0]
            self.assertEqual(trade["reason"], "target_gap_open")
            self.assertEqual(trade["exit_time"], data[65].time)
            self.assertEqual(trade["exit_time_precision"], "bar_open_exact")
            self.assertAlmostEqual(trade["exit"], trade["reference_target"]*.9995)
            self.assertLessEqual(trade["exit"], opening*.9995 + 1e-8)
            self.assertFalse(trade["stop_target_same_bar"])
            self.assertIsNone(trade["gap_beyond_stop_pct"])
            self.assertGreater(trade["net_pnl"], 0)
            self.assertEqual(result["execution_diagnostics"]["stop_first_ambiguous_count"], 0)
            self.assertEqual(result["execution_diagnostics"]["gap_stop_count"], 0)

    def test_target_gap_drawdown_excludes_post_exit_intrabar_low(self):
        # Both candles open above the planned target and therefore exit
        # immediately at the same conservative target price. The later
        # lows cannot change the already-closed trade's drawdown.
        outcomes = []
        for low in (90, 111):
            data = bars(67)
            data[65] = replace(data[65], open=115, high=116, low=low, close=115)
            with patch.object(tr, "setup", side_effect=one_signal):
                outcomes.append(tr.backtest(data, "trend_pullback",
                                            tr.SimulationConfig()))
        self.assertEqual([x["trades"][0]["reason"] for x in outcomes],
                         ["target_gap_open", "target_gap_open"])
        self.assertAlmostEqual(outcomes[0]["max_drawdown_pct"],
                               outcomes[1]["max_drawdown_pct"])
        self.assertAlmostEqual(outcomes[0]["net_pnl"], outcomes[1]["net_pnl"])

    def test_stop_gap_open_precedes_intrabar_target(self):
        data = bars(67)
        data[65] = replace(data[65], open=80, high=120, low=79, close=100)
        with patch.object(tr, "setup", side_effect=one_signal):
            result = tr.backtest(data, "trend_pullback", tr.SimulationConfig())
        trade = result["trades"][0]
        self.assertEqual(trade["reason"], "gap_stop")
        self.assertEqual(trade["exit_time"], data[65].time)
        self.assertEqual(trade["exit_time_precision"], "bar_open_exact")
        self.assertAlmostEqual(trade["exit"], 80*.9995)
        self.assertFalse(trade["stop_target_same_bar"])
        self.assertLess(trade["net_pnl"], 0)
        self.assertEqual(result["execution_diagnostics"]["gap_stop_count"], 1)

    def test_gap_beyond_stop_uses_actual_open_and_can_exceed_planned_risk(self):
        data=bars(67);data[65]=replace(data[65],open=80,high=81,low=79,close=80)
        with patch.object(tr,"setup",side_effect=one_signal):
            result=tr.backtest(data,"trend_pullback",tr.SimulationConfig())
        self.assertEqual(result["trades"][0]["reason"],"gap_stop")
        self.assertAlmostEqual(result["trades"][0]["exit"],80*.9995)
        self.assertLess(result["net_pnl"],-5)
        self.assertFalse(result["trades"][0]["stop_target_same_bar"])
        self.assertAlmostEqual(result["trades"][0]["gap_beyond_stop_pct"],
                               (95-80)/95*100)
        self.assertEqual(result["execution_diagnostics"]["gap_stop_count"], 1)
        self.assertEqual(result["execution_diagnostics"]["stop_first_ambiguous_count"], 0)
        self.assertAlmostEqual(result["execution_diagnostics"]["max_gap_beyond_stop_pct"],
                               (95-80)/95*100)
        trade = result["trades"][0]
        self.assertAlmostEqual(trade["risk_budget_at_entry_usdt"], 5)
        self.assertAlmostEqual(trade["planned_stop_loss_usdt"], 5)
        self.assertTrue(trade["risk_budget_breached"])
        self.assertTrue(trade["planned_stop_loss_exceeded"])
        self.assertGreater(trade["realized_loss_to_budget_multiple"], 1)
        self.assertEqual(result["execution_diagnostics"]["risk_budget_breach_count"], 1)
        self.assertEqual(result["execution_diagnostics"]["planned_stop_loss_exceeded_count"], 1)
        self.assertAlmostEqual(result["execution_diagnostics"]["max_loss_to_risk_budget_multiple"],
                               trade["realized_loss_to_budget_multiple"])
        self.assertTrue(trade["utc_day_gross_loss_cap_breached"])
        self.assertGreater(trade["utc_day_gross_realized_loss_after_exit_usdt"], 10)
        self.assertEqual(result["execution_diagnostics"]["utc_daily_gross_loss_cap_usdt"], 10)
        self.assertEqual(result["execution_diagnostics"]["utc_gross_loss_cap_breach_days"], 1)
        self.assertAlmostEqual(result["execution_diagnostics"]["max_utc_day_gross_realized_loss_usdt"],
                               -trade["net_pnl"])

    def test_daily_cap_and_cooldown_do_not_allow_unbounded_reentries(self):
        data=bars(85)
        # Both entries and stops are feasible on all bars; $1 daily loss then pause.
        data=[replace(b,low=94) for b in data]
        with patch.object(tr,"setup",return_value={"stop":95,"reference_entry":100}):
            result=tr.backtest(data,"trend_pullback",tr.SimulationConfig(daily_loss_limit=1))
        self.assertEqual(result["trade_count"],1)
        self.assertAlmostEqual(result["net_pnl"],-1)
        self.assertEqual(result["execution_diagnostics"]["utc_gross_loss_cap_breach_days"], 0)

    def test_position_size_accounts_for_costs_and_cash_without_leverage(self):
        cfg=tr.SimulationConfig(equity=10)
        qty=tr.risk_size(10,100,99.999,0,cfg)
        self.assertLessEqual(qty*100*1.001,10)
        self.assertEqual(tr.risk_size(10,100,99,10,cfg),0)
        self.assertEqual(tr.risk_size(10,100,101,0,cfg),0)

    def test_no_trades_reports_unknown_metrics_and_valid_json(self):
        result=tr.backtest(bars(),"trend_pullback",tr.SimulationConfig())
        self.assertEqual(result["trade_count"],0)
        self.assertIsNone(result["win_rate_pct"])
        self.assertIsNone(result["profit_factor"])
        self.assertEqual(result["execution_diagnostics"]["gap_stop_count"], 0)
        self.assertEqual(result["execution_diagnostics"]["stop_first_ambiguous_count"], 0)
        self.assertIsNone(result["execution_diagnostics"]["max_gap_beyond_stop_pct"])
        self.assertEqual(result["execution_diagnostics"]["risk_budget_breach_count"], 0)
        self.assertEqual(result["execution_diagnostics"]["planned_stop_loss_exceeded_count"], 0)
        self.assertIsNone(result["execution_diagnostics"]["max_loss_to_risk_budget_multiple"])
        self.assertEqual(result["execution_diagnostics"]["utc_gross_loss_cap_breach_days"], 0)
        self.assertEqual(result["execution_diagnostics"]["max_utc_day_gross_realized_loss_usdt"], 0)
        json.dumps(result,allow_nan=False)
        self.assertIn("NOT applied",str(result["limitations"]))

    def test_invalid_config_and_strategy_are_rejected(self):
        for kwargs in ({"equity":math.inf},{"risk_pct":50},{"fee_bps":0},{"slippage_bps":-1}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                tr.SimulationConfig(**kwargs)
        with self.assertRaises(ValueError):
            tr.backtest(bars(),"unknown",tr.SimulationConfig())


class ApiTests(unittest.TestCase):
    def test_allowlisted_fixed_urls_three_timeframes_and_spot_label(self):
        now=1_800_000_000
        def fetch(key,url,ttl):
            tf=url.split("interval=")[1].split("&")[0]
            self.assertTrue(url.startswith("https://data-api.binance.vision/api/v3/klines?symbol=BTCUSDT&"))
            return rows(tf,now=now*1000),now
        with patch.object(main,"_public_data",side_effect=fetch) as p,patch.object(main.time,"time",return_value=now):
            result=main.trading_research("BTCUSDT")
        self.assertEqual(p.call_count,3)
        self.assertEqual(set(result["timeframes"]),{"15m","1h","4h"})
        self.assertEqual(result["market"],"spot")

    def test_actual_mobile_desk_refuses_fractional_provider_timestamp(self):
        # Exercise the real FastAPI route and _research_history with mocked
        # transport. No synthetic price is presented as a live market quote.
        from fastapi.testclient import TestClient
        now = 1_800_000_000_000
        def fetch(key, url, ttl):
            tf = url.split("interval=")[1].split("&")[0]
            data = rows(tf, now=now)
            if tf == "15m":
                data[20][0] = float(data[20][0]) + .75
            return data, now // 1000
        with patch.object(main, "_public_data", side_effect=fetch), patch.object(
                main.time, "time", return_value=now / 1000), patch.object(
                main, "load_knowledge", return_value=None):
            response = TestClient(main.app).get("/api/trading/desk?symbol=BTCUSDT")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("paper_plan_only", response.text)
        self.assertNotIn("reference_entry", response.text)

    def test_mobile_desk_refuses_finite_but_overflowing_market_prices(self):
        # Exercise the actual FastAPI route with synthetic provider fixtures.
        # Never return a 500, nonfinite analysis or executable paper plan.
        from fastapi.testclient import TestClient
        now = 1_800_000_000_000
        def fetch(key, url, ttl):
            tf = url.split("interval=")[1].split("&")[0]
            data = rows(tf, now=now)
            if tf == "15m":
                for row in data:
                    row[1:6] = ["1e308"] * 5
            return data, now // 1000
        with patch.object(main, "_public_data", side_effect=fetch), patch.object(
                main.time, "time", return_value=now / 1000), patch.object(
                main, "load_knowledge", return_value=None):
            response = TestClient(main.app).get("/api/trading/desk?symbol=BTCUSDT")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("paper_plan_only", response.text)
        self.assertNotIn("reference_entry", response.text)

    def test_actual_mobile_desk_refuses_boolean_provider_volume(self):
        from fastapi.testclient import TestClient
        now = 1_800_000_000_000
        def fetch(key, url, ttl):
            tf = url.split("interval=")[1].split("&")[0]
            data = rows(tf, now=now)
            if tf == "15m":
                data[20][5] = True  # previously float(True) == 1.0
            return data, now // 1000
        with patch.object(main, "_public_data", side_effect=fetch), patch.object(
                main.time, "time", return_value=now / 1000), patch.object(
                main, "load_knowledge", return_value=None):
            response = TestClient(main.app).get("/api/trading/desk?symbol=BTCUSDT")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("paper_plan_only", response.text)
        self.assertNotIn("reference_entry", response.text)

    def test_unknown_pair_no_network_and_stale_data_no_result(self):
        with patch.object(main,"_public_data") as p:
            with self.assertRaises(main.HTTPException) as e:main.trading_research("BTCUSDT&x=1")
            self.assertEqual(e.exception.status_code,422);p.assert_not_called()
        with patch.object(main,"_public_data",return_value=(rows(),0)),patch.object(main.time,"time",return_value=1_900_000_000):
            with self.assertRaises(main.HTTPException) as e:main.trading_backtest(main.TradingBacktestRequest())
            self.assertEqual(e.exception.status_code,503)

    def test_schema_rejects_live_flags_leverage_and_nonfinite_numbers(self):
        for kwargs in ({"live":True},{"leverage":20},{"risk_pct":2},{"equity":math.nan}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):main.TradingBacktestRequest(**kwargs)

    def test_simulation_api_never_places_orders_and_releases_slot_on_failure(self):
        with patch.object(main,"_research_history",return_value=(bars(),123)):
            result=main.trading_backtest(main.TradingBacktestRequest())
        self.assertFalse(result["orders_enabled"])
        self.assertEqual(result["mode"],"historical-paper-simulation")
        for _ in range(3):
            with patch.object(main,"_research_history",side_effect=main.HTTPException(status_code=503)):
                with self.assertRaises(main.HTTPException) as e:main.trading_backtest(main.TradingBacktestRequest())
                self.assertEqual(e.exception.status_code,503)


if __name__=="__main__":unittest.main()

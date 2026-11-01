"""Offline chronological paper evaluation of the existing 15m research rules.

This is NOT the 15m/1h/4h V2 desk, independent-venue validation, a calibrated
forecast, or live/forward trading. Never fetches data or places orders.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math

try:
    from .trading_research import Candle, INTERVALS, STRATEGIES, RULE_VERSION, SimulationConfig, backtest, MAX_SAFE_CANDLE_NUMBER
except ImportError:  # direct backend imports
    from trading_research import Candle, INTERVALS, STRATEGIES, RULE_VERSION, SimulationConfig, backtest, MAX_SAFE_CANDLE_NUMBER

VERSION = "spot-chronological-paper-evaluation-v1"
MIN_BARS = 240
MAX_BARS = 500
WARMUP_BARS = 64
STEP_MS = INTERVALS["15m"]


class PaperEvaluationError(ValueError):
    """Invalid or unverifiable operator-supplied historical data."""


def _checked(bars):
    if not isinstance(bars, (list, tuple)) or not MIN_BARS <= len(bars) <= MAX_BARS:
        raise PaperEvaluationError("invalid_sample_length")
    previous = None
    for bar in bars:
        if type(bar) is not Candle:
            raise PaperEvaluationError("invalid_candle_type")
        if (type(bar.time) is not int or type(bar.close_time) is not int
                or bar.time < 0 or bar.time % STEP_MS
                or bar.close_time != bar.time + STEP_MS - 1
                or (previous is not None and bar.time != previous + STEP_MS)):
            raise PaperEvaluationError("missing_duplicate_or_misaligned_bar")
        values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        # Keep offline paper inputs at least as numerically safe as the
        # shared live-desk candle parser. Finite 1e308 OHLCV can overflow
        # indicator/PnL arithmetic; huge Python ints can overflow isfinite().
        try:
            numeric_safe = all(
                type(v) in (int, float) and math.isfinite(v)
                and abs(v) <= MAX_SAFE_CANDLE_NUMBER for v in values
            )
        except (OverflowError, TypeError, ValueError):
            numeric_safe = False
        if (not numeric_safe
                or min(values[:4]) <= 0 or bar.volume < 0
                or not bar.low <= min(bar.open, bar.close)
                <= max(bar.open, bar.close) <= bar.high):
            raise PaperEvaluationError("invalid_ohlcv")
        previous = bar.time
    return list(bars)


def _sample_quality(bars, *, previous_close=None):
    """Descriptive OHLCV counts only; no exchange provenance or trade veto.

    Compare differences without division to keep extreme but finite valid
    OHLCV values from producing infinite percentage diagnostics.
    """
    zero_volume = flat_ohlc = large_open_gaps = wide_ranges = 0
    prior = previous_close
    for bar in bars:
        zero_volume += bar.volume == 0
        flat_ohlc += bar.open == bar.high == bar.low == bar.close
        if prior is not None:
            large_open_gaps += abs(bar.open - prior) >= prior * .02
        wide_ranges += bar.high - bar.low >= bar.open * .10
        prior = bar.close
    return {
        "bars": len(bars),
        "first_open_at_ms": bars[0].time,
        "last_close_at_ms": bars[-1].close_time,
        "zero_volume_bars": zero_volume,
        "flat_ohlc_bars": flat_ohlc,
        "open_gap_ge_2pct_bars": large_open_gaps,
        "intrabar_range_ge_10pct_bars": wide_ranges,
    }



def _execution_bar_quality(bars, trades):
    """Disclose suspicious OHLCV bars crossed by modeled paper positions.

    Intrabar/close exits include the exit candle conservatively; exact
    opening exits exclude post-exit OHLC range/flatness, while retaining the
    exit opening gap and zero-volume execution warnings.
    This is NOT a fill-quality verification, liquidity estimate or trade veto.
    """
    flags = []
    index = {}
    previous_close = None
    for i, bar in enumerate(bars):
        index[bar.time] = i
        flags.append({
            "zero_volume": bar.volume == 0,
            "flat_ohlc": bar.open == bar.high == bar.low == bar.close,
            "open_gap_ge_2pct": (previous_close is not None
                                   and abs(bar.open - previous_close)
                                   >= previous_close * .02),
            "intrabar_range_ge_10pct": bar.high - bar.low >= bar.open * .10,
        })
        previous_close = bar.close
    result = {
        "trade_count": len(trades),
        "exit_open_only_count": 0,
        "entry_zero_volume_count": 0,
        "exit_zero_volume_count": 0,
        "trades_spanning_zero_volume_count": 0,
        "trades_spanning_flat_ohlc_count": 0,
        "trades_spanning_open_gap_ge_2pct_count": 0,
        "trades_spanning_intrabar_range_ge_10pct_count": 0,
        "trades_spanning_any_flag_count": 0,
        "trade_exposures": [],
    }
    # Synthetic test doubles may supply only entry/PnL, with no exit
    # timestamp. Do not fabricate zero exposure or erase negative trades:
    # explicitly mark the supplemental quality report unavailable.
    if any(type(trade) is dict and "exit_time" not in trade for trade in trades):
        for key in result:
            if key != "trade_count":
                result[key] = None
        result["status"] = "unavailable_incomplete_trade_exit_timestamps"
        return result
    result["status"] = "evaluated_modeled_only"
    for trade in trades:
        entry = index.get(trade["entry_time"])
        # Open and close timestamps both map to the containing 15m candle.
        exit_index = index.get((trade["exit_time"] // STEP_MS) * STEP_MS)
        if entry is None or exit_index is None or exit_index < entry:
            raise PaperEvaluationError("paper_trade_outside_candle_sample")
        # An exact open-triggered stop/target exit cannot be exposed to the
        # exit candle's later high/low or flat-close behavior. Its opening gap
        # and zero total candle volume still matter for modeled execution.
        # Intrabar/close exits and older records without precision remain
        # conservatively exposed to the entire exit candle.
        exit_open_only = trade.get("exit_time_precision") == "bar_open_exact"
        if exit_open_only and trade["exit_time"] != bars[exit_index].time:
            raise PaperEvaluationError("invalid_paper_exit_time_precision")
        span = flags[entry:exit_index + 1]
        if exit_open_only:
            span = flags[entry:exit_index] + [{
                "zero_volume": flags[exit_index]["zero_volume"],
                "flat_ohlc": False,
                "open_gap_ge_2pct": flags[exit_index]["open_gap_ge_2pct"],
                "intrabar_range_ge_10pct": False,
            }]
        exposed = {
            "entry_time": trade["entry_time"],
            "exit_time": trade["exit_time"],
            "exit_open_only": exit_open_only,
            "entry_zero_volume": flags[entry]["zero_volume"],
            "exit_zero_volume": flags[exit_index]["zero_volume"],
            "spanned_zero_volume": any(x["zero_volume"] for x in span),
            "spanned_flat_ohlc": any(x["flat_ohlc"] for x in span),
            "spanned_open_gap_ge_2pct": any(x["open_gap_ge_2pct"] for x in span),
            "spanned_intrabar_range_ge_10pct": any(
                x["intrabar_range_ge_10pct"] for x in span),
        }
        result["trade_exposures"].append(exposed)
        result["exit_open_only_count"] += exit_open_only
        result["entry_zero_volume_count"] += exposed["entry_zero_volume"]
        result["exit_zero_volume_count"] += exposed["exit_zero_volume"]
        result["trades_spanning_zero_volume_count"] += exposed["spanned_zero_volume"]
        result["trades_spanning_flat_ohlc_count"] += exposed["spanned_flat_ohlc"]
        result["trades_spanning_open_gap_ge_2pct_count"] += exposed["spanned_open_gap_ge_2pct"]
        result["trades_spanning_intrabar_range_ge_10pct_count"] += (
            exposed["spanned_intrabar_range_ge_10pct"])
        result["trades_spanning_any_flag_count"] += any(
            exposed[key] for key in (
                "spanned_zero_volume", "spanned_flat_ohlc",
                "spanned_open_gap_ge_2pct", "spanned_intrabar_range_ge_10pct"))
    return result


def _trade_outcome_concentration(trades):
    """Describe concentration of modeled resolved PnL, not predictive odds.

    Terminal forced marks are reported separately; they are not resolved
    strategy trades. All loss streaks are chronological by entry time.
    """
    result = {
        "trade_count_including_terminal_marks": len(trades),
        "strategy_resolved_trade_count": None,
        "terminal_forced_mark_count": None,
        "distinct_strategy_resolved_entry_utc_days": None,
        "max_consecutive_strategy_resolved_losses": None,
        "worst_strategy_resolved_net_pnl_usdt": None,
        "largest_win_share_of_resolved_gross_profit_pct": None,
        "largest_loss_share_of_resolved_gross_loss_pct": None,
    }
    if any(type(t) is not dict or type(t.get("entry_time")) is not int
           or t["entry_time"] < 0 or type(t.get("net_pnl")) not in (int, float)
           or not math.isfinite(t["net_pnl"])
           or type(t.get("terminal_forced_mark", False)) is not bool
           for t in trades):
        result["status"] = "unavailable_incomplete_trade_outcomes"
        return result
    resolved = sorted(
        (t for t in trades if not t.get("terminal_forced_mark", False)),
        key=lambda t: t["entry_time"])
    result["strategy_resolved_trade_count"] = len(resolved)
    result["terminal_forced_mark_count"] = len(trades) - len(resolved)
    result["distinct_strategy_resolved_entry_utc_days"] = len({
        t["entry_time"] // 86_400_000 for t in resolved})
    streak = maximum = 0
    for t in resolved:
        streak = streak + 1 if t["net_pnl"] < 0 else 0
        maximum = max(maximum, streak)
    result["max_consecutive_strategy_resolved_losses"] = maximum
    if not resolved:
        result["status"] = "no_strategy_resolved_trades"
        return result
    wins = [t["net_pnl"] for t in resolved if t["net_pnl"] > 0]
    losses = [-t["net_pnl"] for t in resolved if t["net_pnl"] < 0]
    result["worst_strategy_resolved_net_pnl_usdt"] = min(
        t["net_pnl"] for t in resolved)
    result["largest_win_share_of_resolved_gross_profit_pct"] = (
        max(wins) / sum(wins) * 100 if wins else None)
    result["largest_loss_share_of_resolved_gross_loss_pct"] = (
        max(losses) / sum(losses) * 100 if losses else None)
    result["status"] = "descriptive_modeled_only"
    return result


def evaluate_chronological(bars, symbol: str, strategy: str,
                           config: SimulationConfig | None = None, *,
                           include_cost_guard_sensitivity: bool = False,
                           include_holdout_cost_stress: bool = False) -> dict:
    """Fixed 70/30 chronological split; 64 prior bars warm the holdout.

    Signals may use only bars already closed at that moment. A signal at the
    last warmup close can enter no earlier than the first holdout bar's open.
    The existing backtest handles next-open fills, fees, adverse slippage,
    stop-first same-bar ambiguity, gap stops and daily loss caps.
    """
    if type(include_cost_guard_sensitivity) is not bool:
        raise PaperEvaluationError("invalid_cost_guard_flag")
    if type(include_holdout_cost_stress) is not bool:
        raise PaperEvaluationError("invalid_holdout_cost_stress_flag")
    if symbol not in ("BTCUSDT", "ETHUSDT") or strategy not in STRATEGIES:
        raise PaperEvaluationError("unsupported_symbol_or_strategy")
    cfg = SimulationConfig() if config is None else config
    if type(cfg) is not SimulationConfig or any(
            type(getattr(cfg, name)) not in (int, float)
            for name in ("equity", "risk_pct", "daily_loss_limit", "fee_bps", "slippage_bps")):
        raise PaperEvaluationError("invalid_simulation_config")
    try:
        SimulationConfig(**asdict(cfg))  # revalidate even if dataclass was mutated
    except (TypeError, ValueError, OverflowError) as exc:
        raise PaperEvaluationError("invalid_simulation_config") from exc
    candles = _checked(bars)
    split = len(candles) * 7 // 10
    if split < WARMUP_BARS or len(candles) - split < WARMUP_BARS:
        raise PaperEvaluationError("insufficient_holdout")
    first_holdout = candles[split].time
    train = backtest(candles[:split], strategy, cfg)
    holdout = backtest(candles[split - WARMUP_BARS:], strategy, cfg,
                       entry_not_before=first_holdout)
    if any(t["entry_time"] < first_holdout for t in holdout["trades"]):
        raise PaperEvaluationError("lookahead_or_warmup_trade")
    payload = json.dumps([asdict(b) for b in candles], sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    # Keep negative and zero-trade outcomes exactly as the engine produced them.
    # Exclude redundant raw candle arrays from summaries; retain input hash.
    train_summary = {k: v for k, v in train.items() if k != "input_candles"}
    holdout_summary = {k: v for k, v in holdout.items() if k != "input_candles"}
    result = {
        "version": VERSION, "rule_version": RULE_VERSION, "symbol": symbol,
        "strategy": strategy, "market": "spot", "interval": "15m",
        "mode": "offline-historical-paper-evaluation", "orders_enabled": False,
        "win_probability": None, "independent_venue_verified": False,
        "input_provenance": "operator_supplied_unverified",
        "input_candle_sha256": hashlib.sha256(payload).hexdigest(),
        "paper_execution_bar_quality": {
            "status": "descriptive_modeled_trades_operator_supplied_unverified",
            "training": _execution_bar_quality(candles[:split], train["trades"]),
            "holdout": _execution_bar_quality(
                candles[split - WARMUP_BARS:], holdout["trades"]),
            "counts_overlap": True,
            "trade_rule_or_filter": False,
            "authenticated_market_data": False,
            "observed_exchange_fills": False,
        },
        "sample_quality": {
            "status": "descriptive_operator_supplied_unverified",
            "thresholds": {
                "open_gap": "absolute next open vs previous close >= 2 percent",
                "intrabar_range": "high minus low >= 10 percent of open",
            },
            "training": _sample_quality(candles[:split]),
            "holdout": _sample_quality(
                candles[split:], previous_close=candles[split - 1].close),
            "full_sample": _sample_quality(candles),
            "authenticated_market_data": False,
            "trade_rule_or_filter": False,
        },
        "outcome_concentration": {
            "status": "descriptive_operator_supplied_unverified",
            "training": _trade_outcome_concentration(train["trades"]),
            "holdout": _trade_outcome_concentration(holdout["trades"]),
            "terminal_marks_excluded_from_resolved_metrics": True,
            "authenticated_market_data": False,
            "forward_verified": False,
            "calibrated_win_probability": None,
        },
        "split": {
            "method": "fixed_chronological_70_30_no_tuning",
            "total_bars": len(candles), "training_bars": split,
            "holdout_scored_bars": len(candles) - split,
            "holdout_prior_warmup_bars": WARMUP_BARS,
            "training_end_at": candles[split - 1].close_time,
            "holdout_first_entry_earliest_at": first_holdout,
            "holdout_end_at": candles[-1].close_time,
        },
        "training": train_summary, "holdout": holdout_summary,
        "holdout_no_trades": holdout["trade_count"] == 0,
        "limitations": [
            "Operator-supplied candles are NOT authenticated or cross-venue verified.",
            "Sample-quality and modeled-trade bar-exposure flags are descriptive only; they neither validate venue data nor veto trades. Exact bar-open exits exclude post-exit OHLC range/flatness, but retain opening-gap and zero-volume warnings; uncertain intrabar exits include the full exit bar.",
            "One fixed chronological holdout on one short sample is not independent replication.",
            "The existing 15m research rule is NOT the 3-timeframe V2 desk or V3 engine.",
            "Prior 64 closed bars are context only; warmup entries are prohibited at the engine boundary.",
            "No optimization, resampling, survivorship correction or multiple-testing correction.",
            "Next-open fills, fixed fees/slippage and stop-first ambiguous bars; real gaps, liquidity and impact can be worse.",
            "Zero-volume next-open bars refuse new modeled entries; existing positions still have uncertain modeled exits and descriptive zero-volume exposure flags.",
            "Zero and negative results are retained; no profit, win-rate or forward-performance guarantee.",
            "Resolved-trade concentration, worst loss and loss streak are descriptive on the same unverified sample; terminal forced marks are excluded, not hidden.",
        ],
    }

    if include_cost_guard_sensitivity:
        # Same holdout and input; this is a counterfactual policy, not independent evidence.
        guarded = backtest(candles[split - WARMUP_BARS:], strategy, cfg,
                           entry_not_before=first_holdout,
                           reject_nonpositive_original_net_upside=True)
        if any(t["entry_time"] < first_holdout for t in guarded["trades"]):
            raise PaperEvaluationError("lookahead_or_warmup_trade")
        result["holdout_original_target_cost_guard_sensitivity"] = {
            "status": "same_holdout_counterfactual_not_independent",
            "guard_rule": "reject_if_modeled_original_target_net_upside_nonpositive",
            "baseline_trade_count": holdout["trade_count"],
            "baseline_net_pnl_usdt": holdout["net_pnl"],
            "guarded_holdout": {k: v for k, v in guarded.items() if k != "input_candles"},
            "guarded_outcome_concentration": _trade_outcome_concentration(guarded["trades"]),
            "guarded_paper_execution_bar_quality": _execution_bar_quality(
                candles[split - WARMUP_BARS:], guarded["trades"]),
            "independent_venue_verified": False,
            "forward_verified": False,
            "limitations": [
                "Both scenarios use the same unverified candles and modeled costs.",
                "This policy comparison is not an independent test or evidence of profitability.",
                "Zero trades and negative outcomes remain in the report.",
            ],
        }
    if include_holdout_cost_stress:
        # Same exact scored holdout, doubled modeled costs; not independent.
        available = cfg.fee_bps <= 50 and cfg.slippage_bps <= 50
        stressed = None
        if available:
            stress_cfg = SimulationConfig(**{
                **asdict(cfg), "fee_bps": cfg.fee_bps * 2,
                "slippage_bps": cfg.slippage_bps * 2})
            stressed = backtest(candles[split - WARMUP_BARS:], strategy,
                                stress_cfg, entry_not_before=first_holdout)
            if any(t["entry_time"] < first_holdout for t in stressed["trades"]):
                raise PaperEvaluationError("lookahead_or_warmup_trade")
        result["holdout_double_cost_sensitivity"] = {
            "status": ("evaluated_same_holdout_not_independent" if available
                       else "unavailable_config_exceeds_engine_bounds"),
            "baseline_trade_count": holdout["trade_count"],
            "baseline_net_pnl_usdt": holdout["net_pnl"],
            "double_costs_trade_count": stressed["trade_count"] if stressed is not None else None,
            "double_costs_net_pnl_usdt": stressed["net_pnl"] if stressed is not None else None,
            "double_costs_holdout": ({k: v for k, v in stressed.items()
                                     if k != "input_candles"} if stressed is not None else None),
            "double_costs_outcome_concentration": (
                _trade_outcome_concentration(stressed["trades"])
                if stressed is not None else None),
            "double_costs_paper_execution_bar_quality": (
                _execution_bar_quality(candles[split - WARMUP_BARS:],
                                       stressed["trades"]) if stressed is not None else None),
            "independent_venue_verified": False,
            "forward_verified": False,
            "limitations": [
                "Same unverified candles and same chronological holdout; not independent or forward evidence.",
                "Double-cost stress is unavailable, never silently capped, beyond engine bounds.",
                "All zero/negative trades, modeled gaps, ambiguity, drawdown and forced marks remain visible.",
                "Modeled fills are not observed exchange execution or a calibrated win probability.",
            ],
        }
    return result


def evaluate_rolling_robustness(bars, symbol: str, strategy: str,
                                config: SimulationConfig | None = None, *,
                                include_cost_guard_sensitivity: bool = False,
                                include_holdout_cost_stress: bool = False) -> dict:
    """Optional fixed-window/cost stress study on the SAME unverified input.

    The 40-60%, 60-80% and 80-100% windows do not overlap in scored bars.
    Each has exactly 64 prior closed bars of warmup, and a separate cash/risk
    reset. This is a robustness diagnostic, NOT independent venue/forward proof.
    """
    report = evaluate_chronological(
        bars, symbol, strategy, config,
        include_cost_guard_sensitivity=include_cost_guard_sensitivity,
        include_holdout_cost_stress=include_holdout_cost_stress)
    candles = _checked(bars)
    cfg = SimulationConfig() if config is None else config
    stress_available = cfg.fee_bps <= 50 and cfg.slippage_bps <= 50
    stress_cfg = (SimulationConfig(**{
        **asdict(cfg),
        "fee_bps": cfg.fee_bps * 2,
        "slippage_bps": cfg.slippage_bps * 2,
    }) if stress_available else None)
    windows = []
    for n in range(2, 5):
        start = len(candles) * n // 5
        end = len(candles) * (n + 1) // 5
        first_scored = candles[start].time
        segment = candles[start - WARMUP_BARS:end]
        base = backtest(segment, strategy, cfg, entry_not_before=first_scored)
        stressed = (backtest(segment, strategy, stress_cfg,
                             entry_not_before=first_scored) if stress_cfg else None)
        for scenario in (base, stressed):
            if scenario is not None and any(
                    t["entry_time"] < first_scored for t in scenario["trades"]):
                raise PaperEvaluationError("lookahead_or_warmup_trade")
        windows.append({
            "window_index": n - 1,
            "first_scored_entry_at": first_scored,
            "last_scored_close_at": candles[end - 1].close_time,
            "scored_bars": end - start,
            "prior_warmup_bars": WARMUP_BARS,
            "baseline": {k: v for k, v in base.items() if k != "input_candles"},
            "baseline_outcome_concentration": _trade_outcome_concentration(base["trades"]),
            "baseline_paper_execution_bar_quality": _execution_bar_quality(segment, base["trades"]),
            "double_costs_outcome_concentration": (
                _trade_outcome_concentration(stressed["trades"])
                if stressed is not None else None),
            "double_costs_paper_execution_bar_quality": (
                _execution_bar_quality(segment, stressed["trades"])
                if stressed is not None else None),
            "double_costs": ({k: v for k, v in stressed.items()
                              if k != "input_candles"} if stressed else None),
            "double_costs_status": ("evaluated" if stressed is not None
                                    else "unavailable_config_exceeds_engine_bounds"),
            "baseline_no_trades": base["trade_count"] == 0,
            "double_costs_no_trades": (stressed["trade_count"] == 0
                                       if stressed is not None else None),
        })
    report["rolling_robustness"] = {
        "status": "exploratory_same_series_not_independent",
        "windows": windows,
        "scored_windows": 3,
        "independent_venue_verified": False,
        "forward_verified": False,
        "cost_scenario": ("double_fee_and_slippage" if stress_available
                          else "unavailable_engine_limits"),
        "limitations": [
            "All windows use the same operator-supplied unverified series.",
            "Scored windows are disjoint but share earlier history; no independent data.",
            "Each window resets cash, daily loss state and open positions; never sum returns as a continuous account.",
            "The primary 70/30 holdout overlaps later rolling windows; not independent confirmations.",
            "Double-cost stress is omitted, not silently capped, when fees or slippage exceed engine bounds.",
            "Zero trades, losses, adverse gaps and drawdown are retained; no profitable or forward result is implied.",
        ],
    }
    return report

def attach_capture_receipt(report: dict, receipt: dict) -> dict:
    """Bind an optional UNSIGNED manual capture receipt to a paper report.

    Matching a local JSON receipt to candles is useful reproducibility evidence,
    NOT authenticated Binance/Kraken data, independent evaluation, or a
    calibrated win probability. Never promote independent_venue_verified.
    """
    if type(report) is not dict or type(receipt) is not dict:
        raise PaperEvaluationError("invalid_capture_receipt")
    split = report.get("split")
    if type(split) is not dict or report.get("input_provenance") != "operator_supplied_unverified":
        raise PaperEvaluationError("invalid_capture_report")
    count = split.get("total_bars")
    last_close = split.get("holdout_end_at")
    expected = {
        "mode": "manual_public_spot_capture_no_orders",
        "symbol": report.get("symbol"),
        "interval": "15m",
        "orders_enabled": False,
        "quality_status": "verified_sources_agree",
        "closed_bars": count,
        "historical_cross_checked_closed_bars": count,
        "historical_ohlc_cross_checked_bars": count,
        "cross_checked_closed_bars": 20,
        "input_candle_sha256": report.get("input_candle_sha256"),
        "sources": ["Binance Spot BTC/ETH USDT", "Kraken Spot BTC/ETH USD"],
    }
    for key, value in expected.items():
        if key not in receipt or type(receipt[key]) is not type(value) or receipt[key] != value:
            raise PaperEvaluationError("capture_receipt_mismatch")
    first = receipt.get("first_open_at_ms")
    captured = receipt.get("captured_at_ms")
    if (type(count) is not int or type(last_close) is not int
            or type(first) is not int or type(captured) is not int
            or first < 0 or first + count * STEP_MS - 1 != last_close
            or not last_close <= captured <= last_close + 2 * STEP_MS):
        raise PaperEvaluationError("capture_receipt_time_mismatch")
    fetched = receipt.get("source_fetched_at")
    if (type(fetched) is not dict or set(fetched) != {"binance", "kraken"}
            or any(type(v) is not int or v < captured // 1000 - 120
                   or v > captured // 1000 + 5 for v in fetched.values())
            or abs(fetched["binance"] - fetched["kraken"]) > 120):
        raise PaperEvaluationError("capture_receipt_fetch_mismatch")
    historical_max = receipt.get("max_historical_close_difference_pct")
    ohlc_max = receipt.get("max_historical_ohlc_difference_pct")
    recent_max = receipt.get("max_last_twenty_close_difference_pct")
    if any(type(v) not in (int, float) or not math.isfinite(v)
           or v < 0 or v > 2 for v in (historical_max, ohlc_max, recent_max)):
        raise PaperEvaluationError("capture_receipt_deviation_invalid")
    # Rounded maximums are calculated from the same bars; OHLC includes close.
    if recent_max > historical_max or historical_max > ohlc_max:
        raise PaperEvaluationError("capture_receipt_deviation_mismatch")
    try:
        canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"),
                               allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise PaperEvaluationError("invalid_capture_receipt") from exc
    result = dict(report)
    result["capture_receipt"] = {
        "status": "local_unsigned_receipt_matches_candles",
        "receipt_sha256": hashlib.sha256(canonical).hexdigest(),
        "historical_close_comparison_bars_claimed": count,
        "historical_ohlc_comparison_bars_claimed": count,
        "max_historical_close_difference_pct_claimed": historical_max,
        "max_historical_ohlc_difference_pct_claimed": ohlc_max,
        "independent_venue_authenticated": False,
        "forward_paper_verified": False,
    }
    result["limitations"] = list(report["limitations"]) + [
        "The optional local capture receipt is unsigned and user-supplied; matching its hash, timestamps and claimed cross-venue OHLC does NOT authenticate either exchange or independently verify fills/volume.",
    ]
    return result

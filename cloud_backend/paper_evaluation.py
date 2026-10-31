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
    from .trading_research import Candle, INTERVALS, STRATEGIES, RULE_VERSION, SimulationConfig, backtest
except ImportError:  # direct backend imports
    from trading_research import Candle, INTERVALS, STRATEGIES, RULE_VERSION, SimulationConfig, backtest

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
        if (any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
                or min(values[:4]) <= 0 or bar.volume < 0
                or not bar.low <= min(bar.open, bar.close)
                <= max(bar.open, bar.close) <= bar.high):
            raise PaperEvaluationError("invalid_ohlcv")
        previous = bar.time
    return list(bars)


def evaluate_chronological(bars, symbol: str, strategy: str,
                           config: SimulationConfig | None = None) -> dict:
    """Fixed 70/30 chronological split; 64 prior bars warm the holdout.

    Signals may use only bars already closed at that moment. A signal at the
    last warmup close can enter no earlier than the first holdout bar's open.
    The existing backtest handles next-open fills, fees, adverse slippage,
    stop-first same-bar ambiguity, gap stops and daily loss caps.
    """
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
    return {
        "version": VERSION, "rule_version": RULE_VERSION, "symbol": symbol,
        "strategy": strategy, "market": "spot", "interval": "15m",
        "mode": "offline-historical-paper-evaluation", "orders_enabled": False,
        "win_probability": None, "independent_venue_verified": False,
        "input_provenance": "operator_supplied_unverified",
        "input_candle_sha256": hashlib.sha256(payload).hexdigest(),
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
            "One fixed chronological holdout on one short sample is not independent replication.",
            "The existing 15m research rule is NOT the 3-timeframe V2 desk or V3 engine.",
            "Prior 64 closed bars are context only; warmup entries are prohibited at the engine boundary.",
            "No optimization, resampling, survivorship correction or multiple-testing correction.",
            "Next-open fills, fixed fees/slippage and stop-first ambiguous bars; real gaps, liquidity and impact can be worse.",
            "Zero and negative results are retained; no profit, win-rate or forward-performance guarantee.",
        ],
    }


def evaluate_rolling_robustness(bars, symbol: str, strategy: str,
                                config: SimulationConfig | None = None) -> dict:
    """Optional fixed-window/cost stress study on the SAME unverified input.

    The 40-60%, 60-80% and 80-100% windows do not overlap in scored bars.
    Each has exactly 64 prior closed bars of warmup, and a separate cash/risk
    reset. This is a robustness diagnostic, NOT independent venue/forward proof.
    """
    report = evaluate_chronological(bars, symbol, strategy, config)
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

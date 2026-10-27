"""HOSHI CONFLUENCE V2: reproducible, closed-candle PAPER research only.

Five correlated conditions, 20 points each. Not confidence, profitability,
market-wide liquidity or institutional-intent detection. Never submits orders.
"""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import math

try:
    from .market_structure import _checked, _swings, _regime, MarketStructureError
    from .trading_research import INTERVALS, ema
except ImportError:  # Render's direct uvicorn main:app
    from market_structure import _checked, _swings, _regime, MarketStructureError
    from trading_research import INTERVALS, ema

VERSION = "hoshi-confluence-v2"
NY = ZoneInfo("America/New_York")
WINDOWS = {"london": (120, 300), "new_york": (420, 600),
           "silver_bullet_am": (600, 660), "silver_bullet_pm": (840, 900)}
WEIGHTS = {"htf_trend": 20, "liquidity_target": 20, "location_order_block": 20,
           "fvg_retest": 20, "killzone_time": 20}


class ConfluenceError(ValueError):
    """Unverifiable snapshot; return no score, not a fabricated zero."""


def time_filter(now_ms: int) -> dict:
    if isinstance(now_ms, bool) or not isinstance(now_ms, int) or not 0 <= now_ms <= 4_102_444_800_000:
        raise ConfluenceError("invalid_decision_time")
    local = datetime.fromtimestamp(now_ms / 1000, timezone.utc).astimezone(NY)
    minute = local.hour * 60 + local.minute
    active = [name for name, (start, end) in WINDOWS.items()
              if local.weekday() < 5 and start <= minute < end]
    return {"passed": bool(active), "timezone": "America/New_York",
            "local_time": local.isoformat(), "active_windows": active,
            "weekday_only": True,
            "note": "HOSHI research windows; crypto trades 24/7. Not a news/holiday clearance."}


def _validate(histories: dict, symbol: str, now_ms: int) -> None:
    time_filter(now_ms)
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise ConfluenceError("unsupported_pair")
    if not isinstance(histories, dict) or set(histories) != set(INTERVALS):
        raise ConfluenceError("missing_timeframes")
    for tf, step in INTERVALS.items():
        try:
            bars = histories[tf]
            _checked(bars, tf)
            if any(isinstance(b.time, bool) or isinstance(b.close_time, bool)
                   or not isinstance(b.close_time, int) or b.high > 1e12 or b.volume > 1e18
                   for b in bars):
                raise ConfluenceError("invalid_history")
            # All bars must be closed at decision time; require the most recent
            # expected close for every frame, allowing 120s source delay.
            age = now_ms - bars[-1].close_time
            if not 0 < age <= step + 120_000:
                raise ConfluenceError("stale_or_future_candles")
        except (MarketStructureError, ValueError, KeyError, TypeError, ArithmeticError) as exc:
            raise ConfluenceError("invalid_or_stale_history") from exc


def _trend(histories, direction):
    wanted = "higher_highs_higher_lows" if direction == "long" else "lower_highs_lower_lows"
    details = {}
    for tf in ("1h", "4h"):
        bars = histories[tf]
        highs, lows = _swings(bars)
        e20, e50 = ema([b.close for b in bars], 20)[-1], ema([b.close for b in bars], 50)[-1]
        close = bars[-1].close
        aligned = close > e20 > e50 if direction == "long" else close < e20 < e50
        state = _regime(highs, lows)
        details[tf] = {"structure": state, "ema_aligned": aligned}
    passed = all(d["structure"] == wanted and d["ema_aligned"] for d in details.values())
    return passed, details


def _sweep(bars, direction):
    """Find a last-12-bar reclaim of a level confirmed BEFORE the event."""
    highs, lows = _swings(bars)
    levels = lows if direction == "long" else highs
    for bar in reversed(bars[-12:]):
        known = [x for x in levels if x["confirmed_at"] < bar.time]
        # Only the most recent known pivot is the predeclared sweep reference.
        if not known:
            continue
        x = known[-1]
        swept = (bar.low < x["price"] < bar.close if direction == "long"
                 else bar.close < x["price"] < bar.high)
        later = [b for b in bars if b.time > bar.time]
        reclaimed = (all(b.close > x["price"] for b in later) if direction == "long"
                     else all(b.close < x["price"] for b in later))
        if swept and reclaimed:
            return {"level": x["price"], "confirmed_at": x["confirmed_at"],
                    "swept_at": bar.close_time, "kind": "ssl_reclaim" if direction == "long" else "bsl_reclaim"}
    return None


def _liquidity(histories, direction):
    bars = histories["1h"]
    highs, lows = _swings(bars)
    price = histories["15m"][-1].close
    targets = []
    for x in (highs if direction == "long" else lows):
        later = [b for b in bars if b.close_time > x["confirmed_at"]]
        # Include newer 15m bars after the latest 1h candle as well.
        later += [b for b in histories["15m"] if b.close_time > x["confirmed_at"]]
        valid = (x["price"] > price and all(b.high < x["price"] for b in later)
                 if direction == "long" else
                 x["price"] < price and all(b.low > x["price"] for b in later))
        if valid:
            targets.append(x)
    target = (min(targets, key=lambda x: x["price"]) if direction == "long" else
              max(targets, key=lambda x: x["price"])) if targets else None
    sweep = _sweep(histories["15m"], direction)
    return bool(target and sweep), {"target_kind": "bsl_reference" if direction == "long" else "ssl_reference",
                                   "target": target, "sweep": sweep,
                                   "actual_resting_liquidity_known": False}


def _active_patterns(bars, direction):
    """Three closed bars form a gap; a later bar must retest an unfilled gap.

    Origin = latest opposite candle in the five before displacement. No pivot,
    gap or order block is available before its confirmation bar closes.
    """
    last = bars[-1]
    patterns = []
    for i in range(max(21, len(bars) - 64), len(bars) - 1):
        a, b, c = bars[i-2:i+1]
        bull = direction == "long"
        gap = (a.high, c.low) if bull else (c.high, a.low)
        if gap[0] >= gap[1]:
            continue
        prior = bars[i-21:i-1]  # 20 bars strictly before B
        baseline = math.fsum(abs(x.close-x.open) for x in prior) / 20
        body = b.close - b.open if bull else b.open - b.close
        preceding = bars[i-6:i-1]
        broke = b.close > max(x.high for x in preceding) if bull else b.close < min(x.low for x in preceding)
        if baseline <= 0 or body < 1.5 * baseline or not broke:
            continue
        origins = [x for x in preceding if (x.close < x.open if bull else x.close > x.open)]
        if not origins:
            continue
        ob = origins[-1]
        later = bars[i+1:]
        gap_unfilled = all(x.low > gap[0] for x in later) if bull else all(x.high < gap[1] for x in later)
        ob_valid = all(x.close >= ob.low for x in later) if bull else all(x.close <= ob.high for x in later)
        if not gap_unfilled or not ob_valid:
            continue
        overlap = last.low <= gap[1] and last.high >= gap[0]
        close_holds = last.close >= sum(gap)/2 if bull else last.close <= sum(gap)/2
        ob_overlap = last.low <= ob.high and last.high >= ob.low
        patterns.append({"gap": {"low": gap[0], "high": gap[1], "formed_at": c.close_time},
                         "order_block": {"low": ob.low, "high": ob.high, "origin_at": ob.close_time,
                                         "confirmed_at": c.close_time},
                         "retested": bool(overlap and close_holds), "ob_overlap": ob_overlap,
                         "observed_at": last.close_time})
    return patterns


def _location(histories, direction, patterns):
    highs, lows = _swings(histories["1h"])
    if not highs or not lows:
        return False, {"reason": "missing_confirmed_range", "range": None}
    high, low = highs[-1]["price"], lows[-1]["price"]
    price = histories["15m"][-1].close
    if not low < high or not low <= price <= high:
        return False, {"reason": "outside_or_invalid_range", "range": None}
    midpoint = (high + low) / 2
    in_zone = price <= midpoint if direction == "long" else price >= midpoint
    # The SAME later-bar pattern must meet both gap and OB criteria.
    matching = [x for x in patterns if x["retested"] and x["ob_overlap"]]
    return bool(in_zone and matching), {"range": {"low": low, "high": high, "midpoint": midpoint},
                                        "zone": "discount" if direction == "long" else "premium",
                                        "in_zone": in_zone, "order_block_overlap": bool(matching)}


def confluence_score(histories: dict, symbol: str, now_ms: int, direction: str = "long") -> dict:
    if direction not in ("long", "short"):
        raise ConfluenceError("unsupported_direction")
    _validate(histories, symbol, now_ms)
    trend, trend_detail = _trend(histories, direction)
    liquidity, liquidity_detail = _liquidity(histories, direction)
    patterns = _active_patterns(histories["15m"], direction)
    location, location_detail = _location(histories, direction, patterns)
    retested = [p for p in patterns if p["retested"]]
    clock = time_filter(now_ms)
    values = {"htf_trend": (trend, trend_detail), "liquidity_target": (liquidity, liquidity_detail),
              "location_order_block": (location, location_detail),
              "fvg_retest": (bool(retested), {"pattern": retested[-1] if retested else None}),
              "killzone_time": (clock["passed"], clock)}
    evidence = {key: {"passed": bool(passed), "weight": WEIGHTS[key],
                      "points": WEIGHTS[key] if passed else 0, "details": details}
                for key, (passed, details) in values.items()}
    score = sum(x["points"] for x in evidence.values())
    return {"version": VERSION, "symbol": symbol, "market": "spot", "direction": direction,
            "mode": "paper-research-only", "score": score, "score_max": 100,
            "score_semantics": "weighted_rule_coverage_not_win_probability",
            "win_probability": None, "orders_enabled": False,
            "decision": "paper_watchlist_only" if score == 100 else "wait",
            "as_of": now_ms, "last_closed_at": {tf: b[-1].close_time for tf, b in histories.items()},
            "evidence": evidence, "independently_cross_checked": False,
            "note": "Five correlated heuristic checks on one venue. No risk/entry plan, orders, calibrated accuracy, live news clearance or demonstrated profitability. Short is a bearish study, not spot short execution."}

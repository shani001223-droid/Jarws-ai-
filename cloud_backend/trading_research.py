"""Bounded spot research and historical paper simulation. Never submits orders.

All decisions use closed candles only. Rules are experiments, not validated alpha.
Indicators use SMA-seeded EMA and Wilder RSI/ATR; no model or keys are required.
"""
from dataclasses import dataclass, asdict
import math

INTERVALS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}
STRATEGIES = ("trend_pullback", "breakout_retest")
RULE_VERSION = "spot-long-v1"


@dataclass(frozen=True)
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int


def _exact_candle_timestamp_ms(value):
    """Never truncate or round provider candle identities into valid bars.

    Binance uses integer millisecond timestamps. Canonical ASCII decimal
    strings remain compatible with existing normalized offline inputs.
    """
    if type(value) is int:
        stamp = value
    elif (type(value) is str and value.isascii() and value.isdecimal()
          and 1 <= len(value) <= 16
          and (len(value) == 1 or value[0] != "0")):
        stamp = int(value)
    else:
        raise ValueError("Invalid candle timestamp")
    if not 0 <= stamp <= 9_999_999_999_999_999:
        raise ValueError("Invalid candle timestamp")
    return stamp


def closed_candles(rows, interval, now_ms):
    """Reject malformed/gapped/stale data, exclude the still-forming last bar."""
    step = INTERVALS[interval]
    if type(now_ms) is not int or now_ms < 0:
        raise ValueError("Invalid candle clock")
    if not isinstance(rows, list) or not 65 <= len(rows) <= 500:
        raise ValueError("Expected 65–500 candles")
    candles = []
    previous = None
    for row in rows:
        if not isinstance(row, list) or len(row) < 7:
            raise ValueError("Malformed candle")
        t, end = _exact_candle_timestamp_ms(row[0]), _exact_candle_timestamp_ms(row[6])
        # Python float(True) == 1.0: boolean provider OHLCV is not a
        # market observation, even when a coherent-looking row can be formed.
        # Keep numeric strings supported by the existing public spot feeds.
        raw_values = row[1:6]
        if any(type(value) not in (str, int, float) for value in raw_values):
            raise ValueError("Invalid candle numeric field")
        try:
            o, h, lo, c, v = map(float, raw_values)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("Invalid candle numeric field") from exc
        if (not all(math.isfinite(x) for x in (o, h, lo, c, v))
                or min(o, h, lo, c) <= 0 or v < 0
                or not lo <= min(o, c) <= max(o, c) <= h
                or t < 0 or t % step or end != t + step - 1
                or (previous is not None and t != previous + step)
                or t > now_ms):
            raise ValueError("Invalid candle values/timing")
        previous = t
        if end < now_ms:
            candles.append(Candle(t, o, h, lo, c, v, end))
    if len(candles) < 64 or not 0 <= now_ms - candles[-1].close_time <= step + 120_000:
        raise ValueError("Stale or insufficient closed candles")
    return candles


def ema(values, period):
    out = [None] * len(values)
    if len(values) >= period:
        value = sum(values[:period]) / period
        out[period - 1] = value
        for i in range(period, len(values)):
            value += (values[i] - value) * 2 / (period + 1)
            out[i] = value
    return out


def indicators(bars):
    closes = [b.close for b in bars]
    e20, e50 = ema(closes, 20), ema(closes, 50)
    atr, rsi = [None] * len(bars), [None] * len(bars)
    tr = [max(b.high - b.low,
              abs(b.high - bars[i-1].close) if i else 0,
              abs(b.low - bars[i-1].close) if i else 0) for i, b in enumerate(bars)]
    if len(bars) >= 14:
        a = sum(tr[:14]) / 14
        atr[13] = a
        for i in range(14, len(bars)):
            a = (a * 13 + tr[i]) / 14
            atr[i] = a
    if len(bars) >= 15:
        diff = [closes[i] - closes[i-1] for i in range(1, len(bars))]
        gain = sum(max(d, 0) for d in diff[:14]) / 14
        loss = sum(max(-d, 0) for d in diff[:14]) / 14
        for i in range(14, len(bars)):
            if i > 14:
                gain = (gain * 13 + max(diff[i-1], 0)) / 14
                loss = (loss * 13 + max(-diff[i-1], 0)) / 14
            rsi[i] = 50.0 if gain == loss == 0 else (100.0 if loss == 0 else 100 - 100 / (1 + gain/loss))
    return {"ema20": e20, "ema50": e50, "atr14": atr, "rsi14": rsi}


def snapshot(bars):
    ind = indicators(bars)
    last = bars[-1]
    a, e20, e50 = (ind[k][-1] for k in ("atr14", "ema20", "ema50"))
    delta = e20 - ind["ema20"][-4]
    regime = "range"
    if a > 0 and abs(e20 - e50) > a * .5:
        if e20 > e50 and delta > a * .1:
            regime = "trend_up"
        elif e20 < e50 and delta < -a * .1:
            regime = "trend_down"
    return {"last_closed_at": last.close_time, "last_close": last.close,
            "regime": regime, "indicators": {k: v[-1] for k, v in ind.items()},
            "support": min(b.low for b in bars[-21:-1]),
            "resistance": max(b.high for b in bars[-21:-1]),
            "levels_method": "Previous 20 closed candles; excludes current signal candle"}


def setup(bars, strategy, ind=None):
    """Spot long hypotheses. Signal at close, hypothetical fill NEXT bar only."""
    if strategy not in STRATEGIES:
        raise ValueError("Unknown strategy")
    if len(bars) < 64:
        return None
    ind = ind or indicators(bars)
    b = bars[-1]
    a, e20, e50 = (ind[k][-1] for k in ("atr14", "ema20", "ema50"))
    avg_volume = sum(x.volume for x in bars[-21:-1]) / 20
    if a <= 0 or avg_volume <= 0 or b.volume < avg_volume or b.close <= b.open:
        return None
    level = None
    if strategy == "trend_pullback":
        if not (e20 > e50 and e20 > ind["ema20"][-4]
                and b.low <= e20 + .25 * a and b.close > e20):
            return None
        level = e20
    else:
        # A breakout in one of the five PRIOR bars, followed by today's retest.
        for j in range(len(bars)-2, len(bars)-7, -1):
            resistance = max(x.high for x in bars[j-20:j])
            if (bars[j].close > resistance and bars[j-1].close <= resistance
                    and resistance - .25*a <= b.low <= resistance + .25*a
                    and b.close > resistance
                    and all(x.close >= resistance - .5*a for x in bars[j+1:])):
                level = resistance
                break
        if level is None:
            return None
    stop = min(b.low, level) - .25*a
    distance = b.close - stop
    if not .5*a <= distance <= 4*a:
        return None
    return {"strategy": strategy, "side": "long", "signal_at": b.close_time,
            "reference_entry": b.close, "stop": stop,
            "reference_target": b.close + 2*distance,
            "reward_risk_before_costs": 2,
            "reason": "Closed price structure + volume confirmation; experimental rules"}


def research(histories, symbol, fetched_at):
    frames = {tf: snapshot(bars) for tf, bars in histories.items()}
    proposals = []
    for name in STRATEGIES:
        candidate = setup(histories["15m"], name)
        if candidate and frames["1h"]["regime"] == frames["4h"]["regime"] == "trend_up":
            proposals.append(candidate)
    return {"symbol": symbol, "market": "spot", "mode": "research-only", "orders_enabled": False,
            "source": "Binance Spot", "fetched_at": fetched_at, "rule_version": RULE_VERSION,
            "timeframes": frames, "proposals": proposals,
            "decision": "paper_candidate" if proposals else "wait",
            "reason": "15m setup requires BOTH 1h and 4h uptrend; missing confirmation means WAIT.",
            "note": "Spot long research only; no futures quotes, short selling, orders or profit guarantee."}


@dataclass(frozen=True)
class SimulationConfig:
    equity: float = 1000
    risk_pct: float = .5
    daily_loss_limit: float = 10
    fee_bps: float = 10
    slippage_bps: float = 5

    def __post_init__(self):
        limits = ((self.equity, 10, 100_000), (self.risk_pct, .1, 1),
                  (self.daily_loss_limit, .1, 1000), (self.fee_bps, 1, 100),
                  (self.slippage_bps, 1, 100))
        if any(not math.isfinite(v) or not low <= v <= high for v, low, high in limits):
            raise ValueError("Simulation settings out of bounds")


def risk_size(cash, entry, stop, day_loss, cfg):
    """Risk includes estimated stop slippage and both commissions. No leverage."""
    slip, fee = cfg.slippage_bps/10_000, cfg.fee_bps/10_000
    exit_price = stop * (1-slip)
    per_unit = entry - exit_price + (entry+exit_price)*fee
    budget = min(cash*cfg.risk_pct/100, cfg.daily_loss_limit-day_loss)
    if stop <= 0 or entry <= stop or per_unit <= 0 or budget <= 1e-8 or cash <= 0:
        return 0
    return min(budget/per_unit, cash/(entry*(1+fee)))


def backtest(bars, strategy, cfg, *, entry_not_before=None):
    """Bounded, single-position, long-only exploratory test on supplied history.

    Uses 15m rules only (NOT the multi-timeframe research filter). Fees/slippage
    charged each side; gaps stop at open; same-bar stop/target resolves stop-first.
    UTC daily GROSS realized losses enforce pause; gap losses can exceed budget.
    """
    if strategy not in STRATEGIES or not 64 <= len(bars) <= 500:
        raise ValueError("Invalid test input")
    # Warmup bars may form signals, but must never open or finance positions.
    # The last warmup close may still signal an entry at the first scored open.
    if entry_not_before is not None and (
            type(entry_not_before) is not int
            or entry_not_before % INTERVALS["15m"]
            or not bars[0].time <= entry_not_before <= bars[-1].time):
        raise ValueError("Invalid scored-entry boundary")
    cash, peak, max_dd = cfg.equity, cfg.equity, 0.0
    fee, slip = cfg.fee_bps/10_000, cfg.slippage_bps/10_000
    position, pending = None, None
    trades, day_losses, cooldown_until = [], {}, -1
    ambiguous_stop_target_count, gap_stop_count, max_gap_beyond_stop_pct = 0, 0, None
    risk_budget_breach_count, planned_stop_loss_exceeded_count = 0, 0
    max_loss_to_risk_budget_multiple = None
    for i, b in enumerate(bars):
        day = b.time // 86_400_000
        # Expire any warmup-only pending signal at its very next bar. Never
        # carry a stale warmup signal forward across the scoring boundary.
        if pending and entry_not_before is not None and b.time < entry_not_before:
            pending = None
        if pending and not position:
            entry = b.open*(1+slip)
            # Revalidate risk after a price gap; a gapped invalid setup is skipped.
            stop = pending["stop"]
            if 0 < entry-stop <= 4*(pending["reference_entry"]-stop):
                qty = risk_size(cash, entry, stop, day_losses.get(day, 0), cfg)
                if qty > 0:
                    budget = min(cash*cfg.risk_pct/100,
                                 cfg.daily_loss_limit-day_losses.get(day, 0))
                    estimated_exit = stop*(1-slip)
                    planned_loss = qty*(entry-estimated_exit + fee*(entry+estimated_exit))
                    position = {"entry": entry, "stop": stop, "target": entry+2*(entry-stop),
                                "qty": qty, "entry_time": b.time, "entry_index": i,
                                "risk_budget_at_entry": budget,
                                "planned_stop_loss": planned_loss}
            pending = None
        if position:
            p = position
            # Worst adverse excursion for this bar, including a gap below stop.
            adverse = b.open if b.open < p["stop"] else (p["stop"] if b.low <= p["stop"] else b.low)
            marked = cash + p["qty"]*((adverse*(1-slip)-p["entry"])
                                     - fee*(adverse*(1-slip)+p["entry"]))
            max_dd = max(max_dd, (peak-marked)/peak*100)
            # OHLC bars cannot reveal whether the stop or target traded first.
            # Report this uncertainty, while keeping the conservative stop-first fill.
            stop_target_same_bar = (b.open > p["stop"] and b.low <= p["stop"]
                                    and b.high >= p["target"])
            reason, raw_exit = None, None
            if b.open <= p["stop"]:
                reason, raw_exit = "gap_stop", b.open
            elif b.low <= p["stop"]:
                reason, raw_exit = "stop", p["stop"]
            elif b.high >= p["target"]:
                reason, raw_exit = "target", p["target"]
            elif i == len(bars)-1:
                reason, raw_exit = "end_of_sample", b.close
            elif i >= p["entry_index"] + 96:
                reason, raw_exit = "time_exit", b.close
            if reason:
                gap_beyond_stop_pct = None
                if reason == "gap_stop":
                    gap_stop_count += 1
                    gap_beyond_stop_pct = max(0.0, (p["stop"]-b.open)/p["stop"]*100)
                    max_gap_beyond_stop_pct = max(
                        max_gap_beyond_stop_pct or 0.0, gap_beyond_stop_pct)
                if reason == "stop" and stop_target_same_bar:
                    ambiguous_stop_target_count += 1
                exit_price = raw_exit*(1-slip)
                costs = p["qty"]*fee*(p["entry"]+exit_price)
                pnl = p["qty"]*(exit_price-p["entry"])-costs
                realized_loss = max(0.0, -pnl)
                budget_breached = realized_loss > p["risk_budget_at_entry"] + 1e-8
                stop_loss_exceeded = realized_loss > p["planned_stop_loss"] + 1e-8
                if budget_breached:
                    risk_budget_breach_count += 1
                if stop_loss_exceeded:
                    planned_stop_loss_exceeded_count += 1
                if realized_loss:
                    multiple = realized_loss/p["risk_budget_at_entry"]
                    max_loss_to_risk_budget_multiple = max(
                        max_loss_to_risk_budget_multiple or 0.0, multiple)
                cash += pnl
                day_losses[day] = day_losses.get(day, 0)+realized_loss
                trades.append({"entry_time": p["entry_time"], "exit_time": b.close_time,
                               "entry": p["entry"], "exit": exit_price, "quantity": p["qty"],
                               "fees": costs, "net_pnl": pnl, "reason": reason,
                               "reference_stop": p["stop"],
                               "reference_target": p["target"],
                               "stop_target_same_bar": reason == "stop" and stop_target_same_bar,
                               "gap_beyond_stop_pct": gap_beyond_stop_pct,
                               "risk_budget_at_entry_usdt": p["risk_budget_at_entry"],
                               "planned_stop_loss_usdt": p["planned_stop_loss"],
                               "risk_budget_breached": budget_breached,
                               "planned_stop_loss_exceeded": stop_loss_exceeded,
                               "realized_loss_to_budget_multiple": (
                                   realized_loss/p["risk_budget_at_entry"]
                                   if realized_loss else None)})
                position, cooldown_until = None, i+2
        peak = max(peak, cash)
        max_dd = max(max_dd, (peak-cash)/peak*100)
        if not position and i >= 63 and i < len(bars)-1 and i >= cooldown_until:
            pending = setup(bars[:i+1], strategy)
    wins = sum(t["net_pnl"] > 0 for t in trades)
    gross_profit = sum(max(0, t["net_pnl"]) for t in trades)
    gross_loss = sum(max(0, -t["net_pnl"]) for t in trades)
    return {"mode": "historical-paper-simulation", "orders_enabled": False,
            "rule_version": RULE_VERSION, "strategy": strategy, "interval": "15m",
            "config": asdict(cfg), "bars": len(bars),
            "start_at": bars[0].time, "end_at": bars[-1].close_time,
            "trade_count": len(trades), "win_rate_pct": wins/len(trades)*100 if trades else None,
            "initial_equity": cfg.equity, "ending_equity": cash, "net_pnl": cash-cfg.equity,
            "max_drawdown_pct": max_dd, "fees_paid": sum(t["fees"] for t in trades),
            "execution_diagnostics": {
                "stop_first_ambiguous_count": ambiguous_stop_target_count,
                "gap_stop_count": gap_stop_count,
                "max_gap_beyond_stop_pct": max_gap_beyond_stop_pct,
                "risk_budget_breach_count": risk_budget_breach_count,
                "planned_stop_loss_exceeded_count": planned_stop_loss_exceeded_count,
                "max_loss_to_risk_budget_multiple": max_loss_to_risk_budget_multiple,
                "ambiguous_bar_policy": "stop_first_when_stop_and_target_both_touched",
            },
            "expectancy": (cash-cfg.equity)/len(trades) if trades else None,
            "profit_factor": gross_profit/gross_loss if gross_loss else None,
            "trades": trades,
            "input_candles": [asdict(b) for b in bars],
            "limitations": ["Short exploratory sample, not out-of-sample validation or forward demo.",
                            "Single-timeframe test; multi-timeframe research gate is NOT applied.",
                            "Spot long only, no leverage or funding; one position, two-bar cooldown.",
                            "Next-open fills, fixed adverse slippage, stop-first ambiguous candles; ambiguity and gap diagnostics are observed OHLC scenarios, not authenticated execution paths.",
                            "UTC gross realized daily loss cap; per-entry budget is a sizing limit, not a guaranteed loss limit; gaps may exceed it.",
                            "Does not model partial fills, liquidity impact or intra-bar equity peaks."]}

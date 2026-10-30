"""Independent, fail-closed public spot candle/volume quality gate.

Only fixed Binance Spot BTC/ETH USDT and Kraken Spot BTC/ETH USD endpoints
are supported. No trading credentials, orders, user-supplied URLs or signals.
"""
from __future__ import annotations

import math

try:
    from .trading_research import INTERVALS, closed_candles
except ImportError:  # direct Uvicorn main:app from cloud_backend/
    from trading_research import INTERVALS, closed_candles

PAIRS = {"BTCUSDT": "XBTUSD", "ETHUSDT": "ETHUSD"}
KRAKEN_INTERVALS = {"15m": 15, "1h": 60, "4h": 240}
MAX_CLOSE_DIFFERENCE_PCT = 2.0
CROSS_CHECK_BARS = 20  # compare a bounded history, not only the final three closes


class MarketDataQualityError(ValueError):
    """Data is not sufficiently verified for a current-market claim."""


def public_urls(symbol: str, interval: str) -> tuple[str, str]:
    """Fixed hosts and pair/interval allowlists; never interpolate raw input."""
    if symbol not in PAIRS or interval not in INTERVALS:
        raise MarketDataQualityError("unsupported_pair_or_interval")
    return (
        "https://data-api.binance.vision/api/v3/klines?symbol="
        + symbol + "&interval=" + interval + "&limit=500",
        "https://api.kraken.com/0/public/OHLC?pair="
        + PAIRS[symbol] + "&interval=" + str(KRAKEN_INTERVALS[interval]),
    )


def _number(value) -> float:
    if isinstance(value, bool):
        raise MarketDataQualityError("invalid_numeric_field")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MarketDataQualityError("invalid_numeric_field") from exc
    if not math.isfinite(result):
        raise MarketDataQualityError("invalid_numeric_field")
    return result


def _count(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise MarketDataQualityError("invalid_trade_count")
    try:
        count = int(value)
    except (ValueError, OverflowError) as exc:
        raise MarketDataQualityError("invalid_trade_count") from exc
    if count < 0 or str(count) != str(value):
        raise MarketDataQualityError("invalid_trade_count")
    return count


def _volume_check(low: float, high: float, base: float, quote: float,
                  trades: int) -> None:
    if base < 0 or quote < 0 or trades < 0:
        raise MarketDataQualityError("invalid_volume")
    if base == 0:
        if quote != 0 or trades != 0:
            raise MarketDataQualityError("inconsistent_zero_volume")
    elif (trades < 1 or quote < low * base * 0.999
          or quote > high * base * 1.001):
        raise MarketDataQualityError("inconsistent_quote_volume")


def _validate_candles(rows: list, interval: str, now_ms: int):
    try:
        bars = closed_candles(rows, interval, now_ms)
    except (ValueError, TypeError, IndexError, OverflowError, KeyError) as exc:
        raise MarketDataQualityError("invalid_or_stale_candles") from exc
    if bars[-1].volume <= 0 or sum(b.volume for b in bars[-20:]) <= 0:
        raise MarketDataQualityError("missing_recent_volume")
    return bars


def binance_candles(payload, interval: str, now_ms: int):
    """Validate actual 12-field Binance spot kline and base/quote volumes."""
    if not isinstance(payload, list) or not 65 <= len(payload) <= 500:
        raise MarketDataQualityError("invalid_binance_payload")
    for row in payload:
        if not isinstance(row, list) or len(row) != 12:
            raise MarketDataQualityError("invalid_binance_row")
        low, high, base = (_number(row[i]) for i in (3, 2, 5))
        quote = _number(row[7])
        trades = _count(row[8])
        buy_base, buy_quote = _number(row[9]), _number(row[10])
        _volume_check(low, high, base, quote, trades)
        if (buy_base < 0 or buy_quote < 0 or buy_base > base + 1e-9
                or buy_quote > quote + 1e-7):
            raise MarketDataQualityError("invalid_taker_volume")
    return _validate_candles(payload, interval, now_ms)


def kraken_candles(payload, interval: str, now_ms: int):
    """Validate independent Kraken OHLC spot base volume (USD quote market)."""
    if not isinstance(payload, dict) or payload.get("error") != []:
        raise MarketDataQualityError("invalid_kraken_response")
    result = payload.get("result")
    if not isinstance(result, dict) or "last" not in result:
        raise MarketDataQualityError("invalid_kraken_response")
    names = [key for key in result if key != "last"]
    if len(names) != 1 or not isinstance(result[names[0]], list):
        raise MarketDataQualityError("invalid_kraken_pair")
    raw = result[names[0]]
    if not 65 <= len(raw) <= 720:
        raise MarketDataQualityError("invalid_kraken_history")
    step = INTERVALS[interval]
    normalized = []
    for row in raw[-500:]:
        if not isinstance(row, list) or len(row) != 8:
            raise MarketDataQualityError("invalid_kraken_row")
        epoch = _number(row[0])
        if epoch < 0 or not epoch.is_integer():
            raise MarketDataQualityError("invalid_kraken_time")
        start = int(epoch) * 1000
        o, h, low, close, vwap, base = (_number(row[i]) for i in range(1, 7))
        count = _count(row[7])
        if base < 0 or count < 0 or (base > 0 and not low <= vwap <= h):
            raise MarketDataQualityError("invalid_kraken_volume")
        if (base == 0 and count != 0) or (base > 0 and count == 0):
            raise MarketDataQualityError("invalid_kraken_volume")
        normalized.append([start, o, h, low, close, base, start + step - 1])
    return _validate_candles(normalized, interval, now_ms)


def verify_spot_market(symbol: str, interval: str, binance_payload,
                       kraken_payload, now_ms: int, binance_fetched_at: int,
                       kraken_fetched_at: int) -> dict:
    """Require 20 aligned closed bars and bounded cross-venue price agreement.

    Exchange volumes are intentionally NOT compared numerically: they measure
    separate venues and BTC/USDT vs BTC/USD quote markets.
    """
    public_urls(symbol, interval)
    first = binance_candles(binance_payload, interval, now_ms)
    second = kraken_candles(kraken_payload, interval, now_ms)
    if len(first) < CROSS_CHECK_BARS or len(second) < CROSS_CHECK_BARS:
        raise MarketDataQualityError("insufficient_overlap")
    differences = []
    for a, b in zip(first[-CROSS_CHECK_BARS:], second[-CROSS_CHECK_BARS:]):
        if a.time != b.time:
            raise MarketDataQualityError("cross_source_time_mismatch")
        difference = abs(a.close - b.close) / ((a.close + b.close) / 2) * 100
        if difference > MAX_CLOSE_DIFFERENCE_PCT:
            raise MarketDataQualityError("cross_source_price_disagreement")
        differences.append(difference)
    # Reject bool/noninteger timestamps and future-dated cache responses.
    # The two venues must be recent relative to the SAME server clock.
    if (type(now_ms) is not int or now_ms < 0
            or type(binance_fetched_at) is not int
            or type(kraken_fetched_at) is not int
            or abs(binance_fetched_at - kraken_fetched_at) > 120
            or min(binance_fetched_at, kraken_fetched_at) < now_ms // 1000 - 120
            or max(binance_fetched_at, kraken_fetched_at) > now_ms // 1000 + 5):
        raise MarketDataQualityError("stale_fetch")
    last = first[-1]
    # Real Binance quote volume (USDT) is separately checked against OHLC.
    # Use validated open-time identity rather than comparing raw API types.
    # The provider may encode integer timestamps as decimal strings.
    final_closed_row = (binance_payload[-1]
                        if int(binance_payload[-1][0]) == last.time
                        else binance_payload[-2])
    quote_volume = _number(final_closed_row[7])
    return {
        "symbol": symbol, "interval": interval, "market": "spot",
        "mode": "public-market-data-quality", "status": "verified_sources_agree",
        "orders_enabled": False, "last_closed_at": last.close_time,
        "last_closed_price_usdt": last.close,
        "source_fetched_at": {"binance": binance_fetched_at, "kraken": kraken_fetched_at},
        "sources": ["Binance Spot BTC/ETH USDT", "Kraken Spot BTC/ETH USD"],
        "binance_last_base_volume": last.volume,
        "binance_last_quote_volume_usdt": quote_volume,
        "kraken_last_base_volume": second[-1].volume,
        "cross_checked_closed_bars": CROSS_CHECK_BARS,
        "max_last_twenty_close_difference_pct": round(max(differences), 4),
        "max_last_three_close_difference_pct": round(max(differences[-3:]), 4),
        "max_allowed_difference_pct": MAX_CLOSE_DIFFERENCE_PCT,
        "note": "Independent venue price comparison only; venue volumes are not interchangeable. No signal, order, leverage or profit prediction.",
    }

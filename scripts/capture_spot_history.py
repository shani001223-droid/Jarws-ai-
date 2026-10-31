"""Bounded read-only public spot capture for the existing offline paper evaluator.

Run manually: python -m scripts.capture_spot_history --symbol BTCUSDT > private.json
The JSON on stdout is directly usable by scripts.evaluate_trading_paper.
A separate provenance receipt goes to stderr. Neither is a signed market
attestation, forward test, signal, trade, or evidence of profitability.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import sys
import time
from urllib.request import HTTPRedirectHandler, Request, build_opener

from cloud_backend.market_data_quality import (
    MarketDataQualityError, MAX_CLOSE_DIFFERENCE_PCT, binance_candles,
    kraken_candles, public_urls, verify_spot_market,
)

INTERVAL = "15m"
MAX_RESPONSE_BYTES = 1_000_000


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise MarketDataQualityError("provider_redirect_refused")


def _fetch_json(url: str):
    """Fetch ONLY a caller-provided fixed public_urls URL; refuse redirects.

    The caller never accepts user-provided URLs. Bound both advertised and
    actual response bytes; never use keys, cookies or account credentials.
    """
    opener = build_opener(_NoRedirect)
    request = Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "HoshiOfflineSpotResearch/1.0",
    })
    with opener.open(request, timeout=8) as response:
        if response.status != 200:
            raise MarketDataQualityError("provider_unavailable")
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise MarketDataQualityError("invalid_provider_content_type")
        declared = response.headers.get("Content-Length")
        if declared is not None:
            if not declared.isdecimal() or int(declared) > MAX_RESPONSE_BYTES:
                raise MarketDataQualityError("oversized_provider_response")
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if not body or len(body) > MAX_RESPONSE_BYTES:
            raise MarketDataQualityError("oversized_or_empty_provider_response")
    try:
        return json.loads(body.decode("utf-8"),
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              MarketDataQualityError("invalid_provider_json")))
    except (UnicodeError, ValueError) as exc:
        raise MarketDataQualityError("invalid_provider_json") from exc


def verify_historical_overlap(binance_bars, kraken_bars):
    """Require independent OHLC agreement for EVERY captured historical bar.

    The fixed Kraken USD market is a quality cross-check, not an exchange
    signature or a replacement for Binance USDT volume/fill provenance.
    A partial overlap must never be presented as full-history verification.
    """
    if len(kraken_bars) < len(binance_bars):
        raise MarketDataQualityError("insufficient_historical_venue_overlap")
    peers = kraken_bars[-len(binance_bars):]
    close_differences = []
    ohlc_differences = []
    for a, b in zip(binance_bars, peers):
        if a.time != b.time:
            raise MarketDataQualityError("historical_venue_time_mismatch")
        close_deviation = abs(a.close - b.close) / ((a.close + b.close) / 2) * 100
        if close_deviation > MAX_CLOSE_DIFFERENCE_PCT:
            raise MarketDataQualityError("historical_venue_price_disagreement")
        # A forged historical wick/open can change paper stops and targets
        # while leaving both venues' closes identical. Refuse such datasets.
        deviations = [close_deviation]
        for field in ("open", "high", "low"):
            left, right = getattr(a, field), getattr(b, field)
            difference = abs(left - right) / ((left + right) / 2) * 100
            if difference > MAX_CLOSE_DIFFERENCE_PCT:
                raise MarketDataQualityError("historical_venue_ohlc_disagreement")
            deviations.append(difference)
        close_differences.append(close_deviation)
        ohlc_differences.append(max(deviations))
    return {
        "historical_cross_checked_closed_bars": len(close_differences),
        "max_historical_close_difference_pct": round(max(close_differences), 4),
        "historical_ohlc_cross_checked_bars": len(ohlc_differences),
        "max_historical_ohlc_difference_pct": round(max(ohlc_differences), 4),
    }


def capture_spot_history(symbol: str, *, fetch_json=None, clock=None):
    """Capture 240-500 closed Binance bars with full-overlap Kraken close check.

    Returns (evaluator_input, independent_quality_receipt). The quality check
    covers ALL emitted OHLC prices, NOT base/quote volumes or fills. The
    operator must independently retain and inspect the receipt; a SHA is not
    an exchange signature. Failure produces no partially valid data.
    """
    binance_url, kraken_url = public_urls(symbol, INTERVAL)
    fetch = _fetch_json if fetch_json is None else fetch_json
    now = time.time if clock is None else clock
    binance = fetch(binance_url)
    binance_fetched_at = int(now())
    kraken = fetch(kraken_url)
    kraken_fetched_at = int(now())
    now_ms = int(now() * 1000)
    quality = verify_spot_market(
        symbol, INTERVAL, binance, kraken, now_ms,
        binance_fetched_at, kraken_fetched_at,
    )
    bars = binance_candles(binance, INTERVAL, now_ms)
    if not 240 <= len(bars) <= 500:
        raise MarketDataQualityError("insufficient_evaluation_history")
    historical = verify_historical_overlap(
        bars, kraken_candles(kraken, INTERVAL, now_ms, expected_symbol=symbol))
    # Same canonical Candle serialization/hash as paper_evaluation.py.
    canonical = json.dumps([asdict(bar) for bar in bars], sort_keys=True,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    dataset = {
        "symbol": symbol, "interval": INTERVAL,
        "candles": [[bar.time, bar.open, bar.high, bar.low, bar.close,
                     bar.volume, bar.close_time] for bar in bars],
    }
    receipt = {
        "mode": "manual_public_spot_capture_no_orders",
        "symbol": symbol, "interval": INTERVAL, "orders_enabled": False,
        "captured_at_ms": now_ms,
        "closed_bars": len(bars),
        "first_open_at_ms": bars[0].time,
        "last_closed_at_ms": bars[-1].close_time,
        "input_candle_sha256": hashlib.sha256(canonical).hexdigest(),
        "quality_status": quality["status"],
        "cross_checked_closed_bars": quality["cross_checked_closed_bars"],
        **historical,
        "max_last_twenty_close_difference_pct": quality[
            "max_last_twenty_close_difference_pct"],
        "source_fetched_at": quality["source_fetched_at"],
        "sources": quality["sources"],
        "limitations": [
            "Every emitted Binance OHLC bar is compared to a timestamp-aligned Kraken OHLC bar.",
            "Cross-venue OHLC comparison is not signed provenance; volume, fills and liquidity are NOT independently authenticated.",
            "BTC/USDT and BTC/USD (or ETH pairs) are different quote markets.",
            "The SHA-256 binds local candle content; it is not a provider signature.",
            "Public APIs can be unavailable or geographically restricted.",
            "No independent forward paper fills, profitability, live orders or deployment.",
        ],
    }
    return dataset, receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manual bounded BTC/ETH public spot capture")
    parser.add_argument("--symbol", choices=("BTCUSDT", "ETHUSDT"), required=True)
    args = parser.parse_args(argv)
    try:
        dataset, receipt = capture_spot_history(args.symbol)
    except (OSError, ValueError, TypeError, OverflowError, MarketDataQualityError):
        print("WAIT: public spot history unavailable or unverifiable; no dataset emitted.",
              file=sys.stderr)
        return 2
    print(json.dumps(dataset, separators=(",", ":"), allow_nan=False))
    print("HOSHI_CAPTURE_RECEIPT " + json.dumps(receipt, sort_keys=True,
                                                separators=(",", ":"), allow_nan=False),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

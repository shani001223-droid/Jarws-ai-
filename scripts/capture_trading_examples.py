"""Manual, keyless snapshot capture for three FIXED public chart examples.

Not called by the server or CI; no user URLs, model calls or trading orders.
Outputs source facts, not positive setup claims or performance evidence.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cloud_backend.trading_research import closed_candles
from cloud_backend.market_structure import _frame as structure_frame
from cloud_backend.market_indicators import _frame as indicator_frame
from cloud_backend.strategy_engine import _active_patterns, _sweep, time_filter

CHARTS = (("BTCUSDT", "15m"), ("ETHUSDT", "1h"), ("BTCUSDT", "4h"))


def capture(pair_tf):
    pair, tf = pair_tf
    url = f"https://data-api.binance.vision/api/v3/klines?symbol={pair}&interval={tf}&limit=500"
    request = Request(url, headers={"User-Agent": "HOSHI-ReadOnly-Example-Capture/2"})
    with urlopen(request, timeout=12) as response:
        raw = response.read(200_001)
    if len(raw) > 200_000:
        raise ValueError("source_too_large")
    now = int(time.time()*1000)
    bars = closed_candles(json.loads(raw), tf, now)
    last = bars[-1]
    span = last.high-last.low
    return {"symbol": pair, "timeframe": tf,
            "source": "Binance Spot public OHLCV, one venue",
            "retrieved_at": datetime.fromtimestamp(now/1000, timezone.utc).isoformat(),
            "as_of_ms": now, "last_closed_at": last.close_time,
            "last_closed_utc": datetime.fromtimestamp(last.close_time/1000, timezone.utc).isoformat(),
            "source_url": url,
            "replay_url": url.replace("limit=500", f"limit={len(bars)}&endTime={last.close_time}"),
            "bars_used": len(bars), "last_candle": asdict(last),
            "candle_series_sha256": sha256(json.dumps([asdict(b) for b in bars], sort_keys=True).encode()).hexdigest(),
            "structure": structure_frame(bars, tf), "indicators": indicator_frame(bars, tf),
            "body_fraction": abs(last.close-last.open)/span if span else None,
            "lower_wick_fraction": (min(last.open,last.close)-last.low)/span if span else None,
            "upper_wick_fraction": (last.high-max(last.open,last.close))/span if span else None,
            "active_bull_gap_patterns": _active_patterns(bars,"long"),
            "active_bear_gap_patterns": _active_patterns(bars,"short"),
            "recent_ssl_reclaim": _sweep(bars,"long"), "recent_bsl_reclaim": _sweep(bars,"short"),
            "clock": time_filter(now), "orders_enabled": False}


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as pool:
        observations = list(pool.map(capture, CHARTS))
    result = {"kind": "dated_source_observations_not_current_signal", "version": "hoshi-example-snapshot-v1",
              "note": "Single-venue point-in-time facts. Re-fetch before using as current. No profitability, independent source or institutional-intent claim.",
              "charts": observations}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    target = ROOT / "modules" / f"chart_examples_snapshot_{stamp}.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    for x in observations:
        print(x["symbol"], x["timeframe"], x["last_closed_utc"], "close", x["last_candle"]["close"])

# Hoshi Task 39 — Reproducible spot technical indicators

**Scope:** development-only, read-only BTCUSDT/ETHUSDT Binance Spot analysis.
`GET /api/trading/indicators?symbol=BTCUSDT` returns independent 15m, 1h,
4h snapshots from the same bounded, freshness-checked, gap-rejecting
`_research_history` reader as Task 38. The endpoint shares the two-slot
research semaphore and has no order client, credentials, leverage, execution,
signals, entry/SL/TP, calibrated confidence, or profit promise.

## Exact formulas (version `spot-indicators-v1`)

- EMA9, EMA20, EMA21, EMA50: initialize at the arithmetic mean of the first
  N **closed** prices; thereafter `EMA_t = EMA_(t-1) + 2/(N+1)*(C_t-EMA_(t-1))`.
- RSI14: first Wilder average gains and losses from the first 14 consecutive
  close differences (15 candles). Subsequently smooth each with
  `(13*previous + current)/14`. Return 50 when both are zero, 100 when
  losses are zero, and 0 when gains are zero.
- ATR14: true range is max(high-low, |high-previous close|,
  |low-previous close|). The first bar uses high-low. Seed the first 14 TR
  with an arithmetic mean; thereafter `ATR_t = (13*ATR_(t-1)+TR_t)/14`.
- Volume SMA20: mean of the last 20 **closed** base-volume candles, including
  the latest. Volume ratio = latest base volume / that mean; null when mean=0.
- UTC-session VWAP: typical price `(high+low+close)/3`, weighted by base
  volume from the 00:00 UTC opening candle through the latest closed bar.
  If the input history does not contain the session opening candle or total
  volume is zero, VWAP is null rather than a mislabeled partial-session value.

The EMA20/50, RSI14 and ATR14 calculations reuse the existing
`trading_research.py` implementation, so research/backtest formulas are
not forked. Indicators are lagging descriptions, not independent signals or
validated profitability evidence. All output is JSON with formula version,
per-timeframe closed timestamps, source, freshness metadata and
`orders_enabled: false`.

## Validation and limits

The source reader requires 64–500 continuous, aligned closed bars, finite
positive OHLC, nonnegative volume and a recent last close. The indicator
module revalidates candle structure, rejects implausibly huge price/volume
values to bound arithmetic, and rejects non-finite output. The endpoint
rejects unsupported symbols before fetching, limits parallel requests and
returns 503 for missing/stale/malformed data. No fallback to invented prices.

`tests/test_market_indicators.py` covers flat/rising/falling known-value
EMA/RSI/ATR, zero-volume and partial-session VWAP, prefix independence,
malformed candles, unsupported pairs, authenticated-free read-only endpoint
contracts, provider failure and stale timestamps. CI links and the sole
task checkmark belong in `HOSHI_60_TASK_MASTER_ROADMAP.md` after passing.

**Important:** this is **single-venue Binance Spot**. Task 37's separate
Binance/Kraken comparison does not automatically cross-check these exact
indicator candles. Offline mocked CI is not proof of live exchange
availability, real-time accuracy, physical Realme Note 50 acceptance,
production deployment or a safe trading strategy. No real trades.

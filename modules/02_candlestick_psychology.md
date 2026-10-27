# Candlestick Psychology

Knowledge version: `hoshi-trading-knowledge-v2`. Language: English definitions with Roman Urdu-ready explanations.

## Evidence boundary

Educational knowledge, not a signal or a win-probability model. Prices, stops,
position sizes and outcomes must not be invented. Each link below opens a live
chart for inspection; the conditional walkthrough is **not a verified live
pattern detection**, replay result, or recommendation. Record venue, symbol,
timeframe, closed-candle UTC timestamps, timezone and source retrieval time
before calling an observation current. Reject missing/stale candles. Multiple
features derived from one OHLCV history are correlated evidence.

## Definition

A candle summarizes transactions over an interval: open, high, low, close
and venue volume. Body/range, upper/lower wick and close location describe
relative buying/selling pressure within that interval; they cannot reveal a
participant's motives. Engulfing bodies, rejection wicks, inside bars and
strong closes are context-dependent descriptions, not predictions.

## Application Zone

Inspect CLOSED bars near a premarked level and within HTF context. Compare
body size with the preceding 20 closed bodies and volume with a stated baseline.
A lower wick at support plus subsequent close above resistance is stronger
observational evidence than a wick alone. Separate the pattern observation from
its later confirmation and execution price; record spread/slippage.

## Failure Zone

An open candle can change shape before closing. News, low volume, gaps,
exchange outages and tight ranges create false rejection/engulfing patterns.
A high wick does not prove a stop hunt, and bullish colour is not buying volume.
Hoshi has OHLCV rather than aggressor-classified tick flow.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — At a confirmed low, measure lower wick divided by range and close location. Require the next closed bar to confirm rejection; a close below the wick invalidates the example.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — Compare an engulfing body with the preceding body at 1h resistance. If the higher timeframe still trends up, record a possible pullback, not a proven reversal. Identify the exact invalidating high.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Find an inside bar and mark the mother-bar high/low before price escapes. A close beyond one boundary followed by immediate re-entry is a failed break; do not relabel it a winner.

## Dated source observations — 27 October 2026

These three examples add actual source observations to the conditional chart
walkthroughs above. They are **point-in-time measurements**, not a claim that a
profitable setup exists now. After this date, treat them as historical examples.
[Captured values, timestamps, source/replay URLs and series digests](chart_examples_snapshot_20261027.json)
are retained for review. The macro series are daily/weekly and lag retrieval.
For 1h/4h OB/FVG observations the same geometric detector is demonstrated on
that frame; the actual V2 API uses 15m for entry-pattern checks.

| Chart / series | Closed bar / observation date | Observed fact and limit |
| --- | --- | --- |
| BTCUSDT 15m | 2026-10-27T12:44:59.999000+00:00 | close=80345 USDT; body/range=0.478781; lower wick/range=0.317341; upper wick/range=0.203878. These are candle measurements, not participant motives. |
| ETHUSDT 1h | 2026-10-27T11:59:59.999000+00:00 | close=2316.04 USDT; body/range=0.0458167; lower wick/range=0.343625; upper wick/range=0.610558. These are candle measurements, not participant motives. |
| BTCUSDT 4h | 2026-10-27T11:59:59.999000+00:00 | close=79910 USDT; body/range=0.157364; lower wick/range=0.458092; upper wick/range=0.384544. These are candle measurements, not participant motives. |

## Sources and attribution

- https://www.cmegroup.com/education/courses/technical-analysis

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

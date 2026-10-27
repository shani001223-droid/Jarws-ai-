# FVG and Imbalances

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

A three-candle bullish Fair Value Gap (FVG) exists when candle A.high <
candle C.low; the gap is [A.high, C.low]. A bearish FVG uses C.high < A.low and
bounds [C.high, A.low]. Candle B is the displacement candle. A price gap between
wick ranges is not proof of absent transactions or a guaranteed future fill.

## Application Zone

Wait for C to close, then inspect a LATER bar for overlap with the gap.
Hoshi V2 requires B's body >=1.5 times the prior 20-body mean, B closing beyond
the preceding five-bar extreme, and an opposite origin candle for OB context.
The gap is fully mitigated once a later bull low reaches its lower edge (bear
high reaches upper edge). Retest must occur before full mitigation and close
on the directional half of the gap. Bound all searches to the last 64 bars.

## Failure Zone

Microgaps can be smaller than spread/fees. A same-formation-bar retest leaks
timing information. News can pass through every gap; some gaps never fill.
Repeatedly drawing a new gap to excuse an invalidated one makes testing unfalsifiable.
A full mitigation on the current bar also disqualifies this strict V2 rule.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — Label A/B/C on three CLOSED bars and calculate the positive-width bull gap. Look for a later overlap; if C is the latest closed bar, there cannot yet be a confirmed later-bar retest.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — Mirror the test for a bearish gap. A later high at or above the upper edge is full mitigation, so it no longer earns an active-gap score even if price subsequently falls.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Compare a visible gap with B body below the 20-body threshold against one above it. Both may be geometric gaps, but only the latter meets V2 displacement; record the rule version and both outcomes.

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
| BTCUSDT 15m | 2026-10-27T12:44:59.999000+00:00 | close=80345 USDT; active qualified gaps bull=1, bear=0; later-bar retest matches=0. No later-bar retest matched; WAIT for this condition. |
| ETHUSDT 1h | 2026-10-27T11:59:59.999000+00:00 | close=2316.04 USDT; active qualified gaps bull=0, bear=0; later-bar retest matches=0. No later-bar retest matched; WAIT for this condition. |
| BTCUSDT 4h | 2026-10-27T11:59:59.999000+00:00 | close=79910 USDT; active qualified gaps bull=0, bear=1; later-bar retest matches=0. No later-bar retest matched; WAIT for this condition. |

## Sources and attribution

- https://www.youtube.com/@InnerCircleTrader
- https://www.cmegroup.com/education/courses/technical-analysis

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

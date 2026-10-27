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

## Sources and attribution

- https://www.youtube.com/@InnerCircleTrader
- https://www.cmegroup.com/education/courses/technical-analysis

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

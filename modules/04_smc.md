# SMC

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

Smart Money Concepts is a family of chart heuristics: swing structure,
sweeps, displacement, order blocks, gaps and premium/discount. Terms are not a
standardized exchange taxonomy. Observed price action cannot establish a single
institutional controller or guaranteed manipulation. Define measurable rules
before testing; avoid narrative fitting after seeing the outcome.

## Application Zone

Use a sequence: confirmed HTF bias -> pre-existing reference level ->
possible sweep -> displacement -> later retest. Each event must exist as of the
decision timestamp. Separate internal 15m swings from external 1h/4h structure.
Require explicit invalidation and record NO SETUP when the sequence is absent.

## Failure Zone

SMC fails in sustained trends where fading every high is costly, in thin
markets, and when an analyst changes swing radii after a loss. OB/FVG/sweep may
all come from one impulse; counting them as independent statistical probabilities
inflates confidence. A liquidity narrative cannot substitute for actual data.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — Mark a confirmed low before a wick moves below it. Only a closed reclaim is a sweep candidate; sustained closes below it describe continuation, so reject the reversal narrative.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — After a candidate sweep, require a closed break of a previously confirmed opposing swing. Inspect a later gap retest; no break or no retest means no complete sequence.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Compare internal bullish 15m structure with external bearish 4h structure. Keep both labels, and reject an all-aligned score rather than hiding the conflicting evidence.

## Sources and attribution

- https://www.youtube.com/@InnerCircleTrader
- https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

# Order Blocks

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

An order block (OB) is a discretionary price-action label. Hoshi operationally
uses the full high-low range of the most recent opposite-colour candle among
five bars before a qualifying displacement. Displacement must close beyond the
prior five-bar extreme, with body at least 1.5 times the preceding 20-body mean.
This does NOT prove that institutional orders are waiting in the zone.

## Application Zone

Combine an OB with independently observed HTF direction, the dealing-range
midpoint and a later FVG retest. Bullish OB = bearish origin candle before bullish
displacement; bearish OB mirrors it. Formation is known only at confirmation.
Use a later retest, never a hypothetical fill before the impulse has closed.
Store origin, bounds, displacement time and invalidation rule.

## Failure Zone

Different educators choose bodies/wicks differently; do not mix versions.
A bullish close below the OB low (bearish above OB high) invalidates Hoshi's zone.
Repeated touches, news and a wrong dealing range weaken the hypothesis. A huge
OB may make risk unacceptable; an OB is not a free limit-order fill.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — Find a bearish candle followed by a bullish five-bar break. Mark its full wick range only after displacement closes. On a later revisit, log whether the low holds; do not call the origin institutional accumulation.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — Mirror the exercise for a bearish block above price. Require 1h/4h bearish evidence for confluence; an isolated red displacement in an uptrend is insufficient.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Compare a first revisit with a third revisit of an older block. Close beyond the invalidating edge means discard it even if a neighbouring FVG remains drawn.

## Sources and attribution

- https://www.youtube.com/@InnerCircleTrader
- https://www.cmegroup.com/education/courses/technical-analysis

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

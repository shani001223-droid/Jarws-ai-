# Liquidity: Inducement, Turtle Soup, BSL and SSL

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

Liquidity is executable capacity and transaction cost, not merely a chart
line. BSL/SSL are heuristics for possible buy-side interest above highs and
sell-side interest below lows; OHLCV does not expose actual stop inventories.
Inducement is a hypothesis about a tempting internal level. Turtle Soup-style
false-break research tests a prior extreme being exceeded then reclaimed.

## Application Zone

Define the high/low and lookback before the event. For Hoshi V2 a sweep uses
a previously confirmed 15m pivot, penetration by a wick and a closed reclaim.
The opposing target is a previously confirmed, still unbreached 1h pivot beyond
current price. Log when a level first became known; remove swept target levels.
A previous-20-bar Turtle Soup example excludes the current bar from its baseline.

## Failure Zone

A breakout can continue rather than reverse; equal highs/lows can attract
interest without ever trading there. Spread, venue fragmentation and a single
large print distort apparent sweeps. Do not claim resting liquidity amounts,
liquidations or market-wide order flow without the appropriate source.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — Mark a prior confirmed low and look for low below it plus close above it. A close below fails the reclaim test. Verify the reference existed before the wick; hindsight-selected lows are invalid.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — Mark the previous 20 closed highs excluding the candidate bar. A breakout and re-entry is a false-break candidate, but a later move above the invalidating high ends the reversal hypothesis.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Identify an unbreached confirmed 1h high above current price as a possible BSL target. If any later bar already exceeded it, remove it; a crossed target cannot earn liquidity confluence.

## Sources and attribution

- https://www.cmegroup.com/education/courses/market-liquidity
- https://www.youtube.com/@InnerCircleTrader

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

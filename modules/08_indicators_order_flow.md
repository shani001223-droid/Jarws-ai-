# Indicators and Order Flow

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

EMA smooths closing price; RSI summarizes gains/losses; ATR summarizes true
range; VWAP is volume-weighted price over a defined session. Actual order flow
requires trades/quotes with venue timestamps and aggressor-side or order-book
information. Candle colour, total volume and RSI are not bid/ask delta, CVD,
DOM depth or proof of absorption.

## Application Zone

Reuse Hoshi's SMA-seeded EMA9/20/21/50, Wilder RSI14/ATR14 and complete UTC
session HLC3 VWAP. Compare price/structure first and use indicators as descriptive
checks. State the venue, sampling, session and incomplete-data handling. VWAP is
null without the session's opening candle or positive session volume. Introduce
real flow only through a separately validated, timestamped feed.

## Failure Zone

EMA lags; RSI can remain extreme through a trend; volume can be venue-specific
or distorted. ATR is not a maximum future loss. A partial-session VWAP silently
labelled full-session is wrong. Tick data from another venue or unsynchronized
clocks invalidates delta/price comparisons; current Hoshi has no such flow feed.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — Compare close, EMA20/50 and RSI14 using closed bars. An RSI above 70 does not itself prove a short; inspect whether 1h/4h structure still supports the trend.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — Calculate complete UTC-session VWAP and volume ratio20. If the 00:00 opening bar is missing, report unavailable rather than substituting a convenient partial VWAP.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Compare an unusually wide 4h candle with ATR14 and volume. Label volatility/participation only. Without aggressor-classified trades leave delta/CVD/absorption unavailable.

## Sources and attribution

- https://www.cmegroup.com/education/courses/technical-analysis
- https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

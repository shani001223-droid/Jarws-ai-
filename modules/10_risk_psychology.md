# Risk and Psychology

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

Risk is the distribution of possible losses, including tail events,
execution failure and correlated exposure. A confluence score is not expected
return or probability. Define cash-at-risk, invalidation, fees, slippage, portfolio
limits and a stopping rule before a paper entry. Psychology means repeatable
behaviour, recordkeeping and avoiding loss-chasing, not confident prediction.

## Application Zone

For an EDUCATIONAL paper example only: cash risk = paper equity * chosen
risk fraction; units <= cash risk / (entry-stop distance + estimated round-trip
cost per unit). Check min notional, tick size and total concurrent exposure;
reject zero/negative distance and unaffordable positions. Risk/reward uses net
costs. Journal intended rule version, evidence, decision time and actual simulated
fills. Compare against a baseline on held-out/walk-forward data.

## Failure Zone

Stops can gap/slip; fees can exceed a tiny target. Several BTC/ETH positions
can share one exposure. High win rate can hide large losses, and backtest tuning
can overfit. Drawdowns, revenge trading, fatigue and changing rules after losses
invalidate the process. Never use leverage or real orders through this upgrade;
never present 99.999% accuracy or profit as a guarantee.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — Choose a hypothetical 100 USDT paper account and 0.5% educational risk budget (0.50 USDT). Use an explicitly observed entry/stop distance plus cost estimate; if minimum notional cannot fit, record no paper trade.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — Write down two correlated BTC/ETH paper positions. Sum cash risks and stress a shared adverse move; treating each chart as independent understates the portfolio risk.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Replay 30 fixed-rule observations with actual simulated net costs, then inspect losses and drawdown. This small sample does not establish alpha or probability; freeze rules and test a later held-out period.

## Sources and attribution

- https://www.cmegroup.com/education/courses/trade-and-risk-management
- https://www.sec.gov/files/algo_trading_report_2020.pdf

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

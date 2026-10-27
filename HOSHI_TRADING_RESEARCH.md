# Hoshi spot research lab

Development extension in the canonical Hoshi repository and draft PR #24.
No exchange credentials, order client, real/demo exchange orders, paid service,
LLM calls or production deployment are introduced.

## Usage

Open Trading, select BTC or ETH, then use **Research BTC / ETH** or **Test
strategy**. Simulation settings are under the expandable settings section.
Alternatively say/type `BTC research karo` or `ETH market analyse kro` to open
read-only research. Automatic chart marking, arbitrary screen control and futures
quotes remain unavailable. Existing SOL/BNB public charts remain available, but
the research buttons are disabled for those pairs.

Results can be exported as JSON. The historical simulation export includes all
input closed candles, rule version, cost settings, trades and limitations. Local
simulation-summary storage is a separate default-OFF opt-in; at most ten summaries
are retained on the device. Clear deletes summaries; opting out deletes them and
the consent flag. This journal is not a forward-demo portfolio or a cloud backup.

## Data and formulas

`GET /api/trading/research?symbol=BTCUSDT` requests fixed Binance Spot keyless
klines for 15m, 1h and 4h concurrently. Each response is bounded to 500 candles;
cache TTL is 30 seconds, upstream timeout 7 seconds and at most two research/test
requests execute concurrently. Unsupported pairs are rejected before fetching.
No caller-supplied URLs are accepted. The browser timeout is 25 seconds.

Candles must have finite positive OHLC, nonnegative volume, correct interval
boundaries and close times, and strictly continuous ordered timestamps. At least
64 closed candles are required. A bar whose close time has not passed is excluded.
The newest closed candle must be no more than one interval plus two minutes old.
Malformed, gapped or stale input returns 503 without a proposal or fake prices.

- EMA20/50: initial arithmetic mean over the period, then alpha `2/(period+1)`.
- ATR14: Wilder smoothing of true range, initially the first 14 true ranges.
- RSI14: Wilder gain/loss smoothing of close differences; flat prices return 50.
- S/R: minimum low / maximum high of the prior 20 closed bars, excluding the
  current signal bar. These are rolling levels, not pivot or liquidity forecasts.
- Regime: EMA20/50 separation greater than 0.5 ATR plus a three-bar EMA20 change
  greater than 0.1 ATR in the same direction; otherwise range. Thresholds are
  versioned experimental assumptions, not optimized or validated parameters.

## Two experimental long-only rules

Both require a green closed candle, positive average prior-20-bar volume, current
volume at least that average and positive ATR. Stops sit 0.25 ATR below the lower
of the candle low and setup level. Signal-close stop distance must be 0.5–4 ATR.
Reference targets are two times the price distance to the stop, before costs.

1. Trend pullback: EMA20 above EMA50, EMA20 rising over three bars, candle low no
   higher than EMA20 + 0.25 ATR, close above EMA20.
2. Breakout + retest: a close above the prior-20-bar high within the preceding
   five bars; current low within 0.25 ATR of that breakout level and close above
   it. Intervening closes must not invalidate the level by more than 0.5 ATR.

Current research permits a paper hypothesis only when both 1h and 4h regimes are
uptrends as well. Otherwise it returns WAIT, without weakening the conditions.
Reference entry is a closed price, not an order fill; no calibrated confidence
percentage or profit guarantee is provided.

## Historical simulation contract

`POST /api/trading/backtest` accepts symbol, strategy, virtual equity (10–100000),
risk percent (0.1–1), daily gross realized loss cap (0.1–1000 USDT), per-side
commission (1–100 bps) and adverse slippage (1–100 bps). Defaults: 1000 virtual
USDT, 0.5% risk, 10 USDT loss cap, 10 bps commission and 5 bps slippage. Extra
fields (including live flags/leverage) are rejected. Defaults are assumptions,
not the user's actual balance, fee tier or a recommended investment size.

The bounded test uses the latest available 15m candles only. It DOES NOT apply the
multi-timeframe research gate: results are labeled explicitly to avoid confusing
the two experiments. Signals are computed from prefixes of history, with fills
at the next bar open plus adverse slippage. Entry gaps revalidate the stop and
reject a distance over four times the original signal distance. One position is
allowed, without leverage; size is limited by cash and estimated stop loss plus
both fees and stop slippage. Daily remaining gross realized loss budget further
caps size. Profits do not replenish that day's loss budget. Day boundaries use
UTC. After an exit, two bars must elapse before another signal; positions time
out after 96 bars (24h), or close at the sample end.

Gap-through stops fill at the open, not the stop. When both stop and target are
touched in the same candle, stop wins. Commission and slippage apply to both
sides. A gap can exceed the planned risk/loss limit. Equity drawdown uses
conservative adverse-bar valuation and closed equity peaks; it does not model
all intrabar equity peaks, partial fills, market impact or exchange outages.
No leverage/funding/short-selling assumptions are mixed into spot results.

Reports show net PnL, count, win rate, expectancy, profit factor, fees and drawdown.
Undefined metrics remain null, not invented perfect scores. Roughly five days
of 15m history is a SHORT EXPLORATORY SAMPLE, not out-of-sample validation,
walk-forward testing, a forward-demo run or proof of profitable trading.

## Validation and remaining boundaries

Offline tests exercise finite values/timing/freshness, exclusion of forming bars,
indicator prefix invariance, both strategy rules, higher-timeframe disagreement,
next-open fills, ambiguous candles, gaps, cost-aware sizing, daily caps and
unavailable providers. Browser tests cover the actual controls with mocked API
responses, inert untrusted text, JSON download, explicit local journal consent,
deletion, late results after pair changes, errors and mobile viewport widths.

A public-data smoke request from the coding environment timed out after about
7 seconds on 26 October 2026. Therefore live upstream availability and any real
market result are NOT verified. Tests use fixtures. Physical Realme Note 50 QA,
production release, forward demo, long-history out-of-sample evaluation, verified
news/social feeds, derivatives data and annotated chart exports remain pending.
Task status and CI evidence belong only in `HOSHI_60_TASK_MASTER_ROADMAP.md`.

References: [Binance Spot market data](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md),
[Freqtrade strategy validation](https://www.freqtrade.io/en/stable/strategy-101/),
[TradingView backtesting limitations](https://www.tradingview.com/pine-script-docs/concepts/strategies/).

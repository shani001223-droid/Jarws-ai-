# Market Structure

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

Market structure is the sequence of confirmed swing highs/lows across timeframes.
HH/HL describe an uptrend; LH/LL a downtrend; other sequences remain mixed.
BOS here means a closed bar beyond a previously confirmed swing in the established
direction; CHoCH/MSS is a candidate opposing break, not automatic trend reversal.
A strict pivot uses two lower highs (or higher lows) on EACH side. It becomes
available only after the second right bar closes. Flat ties are not pivots.

## Application Zone

Use 4h context, 1h intermediate structure and 15m observations. Define the
range and candidate levels BEFORE the proposed entry. Distinguish a close-through
from a wick probe; compare both swing highs AND lows. Mark the pivot time and the
later confirmation time. Reuse Hoshi's existing market_structure.py definitions;
do not invent a second incompatible HH/HL detector.

## Failure Zone

Ranges generate repeated opposing breaks; one giant news candle may erase
several levels. Missing confirmed swings means insufficient confirmation, not
bullish. A pivot drawn retroactively at its own timestamp leaks future data.
Cross-venue spot/futures differences and revised history can alter levels.

## 3 Live Chart Examples

1. **[BTCUSDT, 15m](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=15)** — Wait for two bars to the right of a high, then mark its confirmation. If a later closed bar exceeds it, compare the previous low before labelling BOS; a wick-only excursion is not this rule.

2. **[ETHUSDT, 1h](https://www.tradingview.com/chart/?symbol=BINANCE%3AETHUSDT&interval=60)** — Compare the last two confirmed highs and lows. HH plus LL is mixed, so preserve WAIT even if the latest candle is green. Invalidate the uptrend interpretation after a confirmed opposing swing sequence.

3. **[BTCUSDT, 4h](https://www.tradingview.com/chart/?symbol=BINANCE%3ABTCUSDT&interval=240)** — Mark the latest confirmed 4h range and inspect the 1h/15m view separately. A 15m bullish break against 4h lower highs is countertrend evidence, not all-timeframe confluence.

## Sources and attribution

- https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

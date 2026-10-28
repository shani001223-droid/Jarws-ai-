# Trend, momentum and volatility indicators: calculations before signals

Reviewed: 28 October 2026. The historical examples use Binance Spot BTCUSDT,
native one-minute candles and USDT per BTC. Calculations are original,
explicitly seeded educational diagnostics. They are neither current prices
nor vendor-chart parity, calibrated accuracy or a running Hoshi strategy.

## What is it?

An indicator transforms observed market data into a simpler description.
A trend filter summarizes the level or direction of past prices. A momentum
measure describes recent price changes or where the close sits within a
range. A volatility measure describes dispersion or movement size. These
questions overlap but are not interchangeable: a strong negative trend can
have rising momentum while price still falls, and a large volatility reading
does not specify direction.

The useful starting point is a data contract: instrument, venue, bar interval,
price field, session boundaries, adjustment policy, missing-bar treatment,
formula, seed and availability time. The label “RSI 14” alone does not define
those choices. Fourteen one-minute changes describe a different object from
fourteen daily changes. A spot close is different from a futures settlement,
an index value, or a broker's bid-based CFD candle.

This chapter covers moving averages, RSI, MACD, rate of change, stochastic
position, ATR, Bollinger-style bands and directional-movement interpretation.
Volume, VWAP, profiles, delta and order books have separate declared chapters;
a price oscillator cannot replace their genuinely different inputs. The
curriculum remains expandable rather than a claim to catalogue every
indicator ever named.

## Why does it form?

Indicator behavior follows the transformation. A simple average rises when
the entering price exceeds the price leaving its window, even if the latest
price itself falls. An exponential average can rise while price is below
its recent peak because its update compares the current price with the
previous average. These are arithmetic effects, not independent discoveries
of hidden demand.

Similarly, an oscillator can weaken while price makes another high. If that
new high required a smaller incremental change than an earlier surge, a
momentum divergence may result without a reversal. Confirming a swing using
future right-hand candles adds a separate recognition delay. A backtest
cannot timestamp that divergence at the earlier high merely because the
finished chart makes it obvious.

Smoothing trades responsiveness for stability. A short lookback reacts more
quickly to small disturbances; a longer one can remain aligned with an older
move after conditions change. No universal period solves both problems.
Stacking several transformations of the same close series can make a single
piece of evidence look like several independent confirmations. Hoshi must
record that shared input instead of adding arbitrary confidence points for
every colored indicator on a chart.

## Application zone

### Moving averages and rate of change

For closes `C`, the n-period simple moving average is the mean of the last
n completed closes. The exponential moving average uses
`EMA_t = alpha*C_t + (1-alpha)*EMA_(t-1)`, with the common
`alpha = 2/(n+1)`. This chapter seeds each EMA with its first n-close simple
average. The checked TA-Lib v0.6.4 implementation documents seed and
compatibility differences; naming an EMA does not guarantee identical chart
history or initialization. No C implementation is copied into Hoshi.

The twelve-period rate of change here is
`100*(C_t/C_(t-12)-1)`. It has a percentage scale, unlike a raw average-price
difference. A crossover rule needs two observations: a previous relation
and a new relation. Merely being above an average is a state, not proof that
a crossover just occurred. Freeze whether equality counts, whether a
completed close is required, and whether the next observation must remain
on the new side before discussing signals.

### RSI and MACD

RSI compares smoothed positive and negative close changes. This study seeds
fourteen gains and losses with their means, then updates each using weight
`1/14`. It calculates `100*gain/(gain+loss)`. Zero loss with positive gain
produces 100; zero gain with positive loss produces zero. When both are zero,
Hoshi records null as an explicit flat-denominator convention rather than
manufacturing an oversold signal. This convention differs from some library
outputs. Fidelity's guide attributes RSI to Wilder and warns that extreme
readings can persist in strong trends; 70 and 30 are descriptive conventions,
not guaranteed reversal levels.

The versioned MACD calculation subtracts a 26-period EMA from a 12-period
EMA. Its signal is a nine-period EMA of the available MACD values; the
histogram subtracts signal from MACD. The line's sign answers whether fast
and slow averages are ordered positively. The histogram's sign answers
whether the line exceeds its own smoother. Those signs can disagree. Both
are in price units, so a histogram magnitude cannot be compared directly
between BTCUSDT and a low-priced instrument. The signal needs additional
warmup beyond the first available slow EMA.

### Range position, volatility and directional movement

Fast stochastic `%K` is `100*(close-lowest_low)/(highest_high-lowest_low)`
over the declared fourteen candles. It locates a close inside a recent
range; it is not the fraction of traders who are bullish. A three-period
average of `%K` is a common `%D`, while slow variants apply further smoothing.
The receipt computes only fast `%K`. A zero range is undefined and remains
null, with no invented crossover.

True range is the largest of high minus low, absolute high minus previous
close, and absolute low minus previous close. The first captured candle lacks
its prior captured close, so this study starts true ranges at the next bar.
ATR seeds fourteen such ranges and smooths with weight `1/14`. It measures
movement size in price units, not the probability of a stop being hit. An
ATR multiple may define a paper-risk sensitivity, but it does not cap a gap
or guarantee that an order exits at its stop price.

The band's middle is a twenty-close SMA. This receipt explicitly uses the
population standard deviation of those twenty closes, dividing squared
deviations by twenty, and places boundaries two deviations away. John
Bollinger's own rules distinguish a band tag from an automatic reversal
signal and caution against treating band containment as a normal-distribution
probability. A squeeze describes relative compression, without knowing which
direction a later break will take.

Directional movement separates upward high expansion from downward low
expansion, retaining the larger positive move and setting ties to zero.
Smoothed directional movements are scaled by smoothed true range to form
positive and negative DI. DX compares their absolute difference with their
sum; ADX smooths that strength measure. Missing warmup or a zero denominator
needs an explicit convention. A rising ADX can describe a strengthening
downtrend as well as an uptrend; direction comes from other information.
Fidelity's checked ADX explanation supports that distinction. ADX is explained
here but no historical ADX value or implementation parity is claimed in the
receipt.

## Failure zones

**Initialization:** a recursive series remembers its seed after the nominal
lookback has passed. Removing twenty early bars changes RSI, EMA, MACD and
ATR at the same later timestamp. Having enough candles to output a number
is different from proving that truncation has negligible effect. Hoshi
should retain the seed-start timestamp and a convergence check rather than
silently assuming another platform will match.

**False independence:** RSI, ROC, MACD and a moving-average relation all
reuse past prices. Four aligned readings do not establish four independent
reasons, and four disagreements do not justify changing settings until all
agree. Freeze the role of each feature before testing it. A price-derived
feature can describe a regime; actual liquidity or global-flow evidence
requires separate inputs and source clocks.

**Regime and scale:** oscillators near an extreme can accompany continuation.
Average crossings can alternate rapidly in a range. Volatility expands after
a shock and may remain elevated when its direction reverses. Periods and
thresholds are modeling choices, not constants of nature. Neither an
overbought label nor a band touch is an instruction to short an instrument
that the available spot account cannot short.

**Availability:** an unfinished candle's high, low and close can move until
the bar closes. Historical indicator values calculated from the finished
candle cannot be supplied to a decision made earlier inside it. Higher-frame
values must use the last completed higher-frame bar or an explicitly marked
developing estimate, never the future final value.

**Execution and validation:** the following examples deliberately show price
paths without simulated fills. They lack contemporaneous spread, historical
arrival delay, order-book priority and complete account constraints. They
are three already-inspected teaching windows, not untouched evaluation
periods. No pattern works 100%, and no combination of these numbers is a
calibrated probability of profit.

## Three real historical examples with dates

All cases use the candle at fixed zero-based index sixty: 61 captured bars
are available through that candle. Selection does not depend on its
indicator reading or subsequent result. Features use only that prefix;
future paths occupy a separate five-bar outcome. The source was captured
on 28 October 2026 around 01:59 UTC, much later than these events.
One-minute candle labels below are opening timestamps; each candle's close
is known only at its recorded end, immediately before the next minute.

### Example 1 — 15 May 2023, 07:30 UTC: the same timestamp changes histogram sign

The 07:30–07:31 candle closes 27,453.59; earliest possible post-close feature
availability is 07:31 UTC, or 03:31 New York EDT, before any unknown transport
delay. Using history from 06:30, SMA20 is 27,455.0660, EMA20 is 27,450.4845
and RSI14 is 49.7914. The close is below its SMA but above its EMA. Neither
relation establishes a newly occurring crossover.

MACD is negative 6.9164, its signal negative 7.3859, giving a positive
0.4695 histogram. Starting the same calculations twenty minutes later, with
history from 06:50, leaves SMA20 unchanged but changes the histogram to
negative 0.6517. This is an actual initialization-sensitive sign disagreement,
not a claim that either history is the exchange's official indicator.
The fifth subsequent candle, labeled 07:35 and ending just before 07:36,
closes 27,436.04, a raw close change of
approximately negative 0.06393%. The positive first histogram did not ensure
an immediate rise; no entry, stop or strategy loss is inferred.

### Example 2 — 5 January 2024, 15:30 UTC: MACD line and histogram disagree

At 15:30–15:31 UTC, the close is 43,638.05, below SMA20 of 43,725.4375 and
EMA20 of 43,710.3090. This is 10:30–10:31 New York EST. RSI14 is 42.2849
and fast stochastic `%K` is 33.3363. Both are below their scale midpoints
without meeting the conventional extreme thresholds discussed above.

MACD is positive 3.2320 but below its positive 11.5464 signal; the histogram
is negative 8.3144. Calling MACD simply “bullish” conceals that difference.
The shorter-history RSI becomes 40.8391, while the full twenty-close SMA and
fourteen-bar stochastic position remain unchanged. ATR14 is approximately
59.2371 with the longer seed, describing range scale rather than direction.
The next five closes rise overall to 43,731.11 in the 15:35 candle ending
just before 15:36, approximately
positive 0.21325% from the observation close. A negative histogram state did
not prevent that rebound; it was not a fully defined short trade.

### Example 3 — 8 August 2024, 18:30 UTC: high range position with continuation

The 18:30–18:31 UTC candle, 14:30–14:31 New York EDT, closes 59,607.46.
SMA20 is 59,496.0775 and EMA20 is 59,516.7052. RSI14 is 59.7995, while fast
stochastic `%K` is much higher at 93.6468. This disagreement is expected:
one balances smoothed changes; the other locates the close inside fourteen
bars' high-low range. They do not measure the same ratio.

MACD is 23.2788, its signal 11.5448 and its histogram positive 11.7339.
The upper twenty-close band is approximately 59,618.8165, above the close;
the first subsequent candle's high reaches 59,629.14. That band tag does not
establish an automatic short entry. The fifth subsequent close, in the
18:35 candle ending just before 18:36, is
59,650.78, approximately positive 0.07268% from the observation close.
The path includes intervening fluctuations, and the account's executable
return remains unknown. The example supports the narrow warning that an
extreme range-position oscillator need not reverse immediately.

## How to use it to HUNT a trade

Begin with a supported observed instrument and a frozen hypothesis. For
example, a paper-study specification might use a completed higher-frame
trend as context, one momentum feature as a state description, a separately
observed liquidity event as a trigger, and measured costs to decide whether
the available distance can support risk. Those are proposed research roles,
not a strategy proven by this chapter.

Validate inputs before calculating: monotonically increasing timestamps,
expected interval spacing, finite positive prices, coherent OHLC, correct
session and sufficient warmup. Keep zero-range and flat-change cases explicit.
Compare recursive indicators across longer prefixes; if a relevant decision
changes with plausible history truncation, mark the state unstable or wait.
Do not round intermediate calculations to make a crossover appear.

Freeze threshold, crossing, equality and cancellation rules before evaluating
untouched chronological periods. Retain no-trade outcomes, whipsaws,
ambiguous intrabar paths, costs and drawdowns. For divergence, store the
actual later recognition time of every required pivot. A five-minute outcome
is not evidence for an hourly holding period or a different venue.

Hoshi's default user answer should remain concise and grounded in current
verified inputs. These historical readings must never be returned as live
levels. Missing source clocks, unsupported instruments or uncalibrated
feature combinations require `WAIT`; `win_probability` remains null.
Completing this source chapter does not install these calculations in the
brain, enable orders or complete runtime/evaluation release gates.

## Sources

Primary implementation/provider materials actually checked on 28 October 2026;
briefly paraphrased, with original calculations and case analysis above:

1. [TA-Lib v0.6.4 RSI implementation](https://raw.githubusercontent.com/TA-Lib/ta-lib/v0.6.4/src/ta_func/ta_RSI.c)
   and [EMA implementation](https://raw.githubusercontent.com/TA-Lib/ta-lib/v0.6.4/src/ta_func/ta_EMA.c),
   plus [ADX directional-movement definition](https://raw.githubusercontent.com/TA-Lib/ta-lib/v0.6.4/src/ta_func/ta_ADX.c).
   Smoothing/seed conventions checked; code not republished, parity unclaimed.
2. Fidelity's own indicator guides: [RSI](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/RSI),
   [MACD](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/macd),
   [ATR](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/atr)
   and [fast stochastic](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/fast-stochastic).
   Definition and formula references, not independent tests of profitable signals.
3. John Bollinger's [Bollinger Band Rules](https://www.bollingerbands.com/bollinger-band-rules).
   Original inventor's cautions; no claimed normal-distribution success rate.
4. Fidelity, [ADX: trend strength](https://www.fidelity.com/viewpoints/active-investor/average-directional-index-ADX),
   page dated 19 March 2026. Only methodological distinctions are used;
   its dated stock-market commentary is not a current October observation.
5. [Binance native-minute source receipt](../05_ICT_COMPLETE/ict_intraday_observations_20261028.json),
   [indicator observations](indicator_observations_20261028.json)
   and [original replay arithmetic](../../scripts/v3_indicator_evidence.py).
   Exact requests, historical event/capture clocks and SHA-256 lineage are
   preserved under the recorded noncommercial source-data conditions.

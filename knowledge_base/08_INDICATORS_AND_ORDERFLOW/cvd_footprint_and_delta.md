# CVD, footprint and delta: executed aggression without invented intent

Reviewed on 28 October 2026. Examples use historical Binance Spot BTCUSDT
aggregate trades, with prices in USDT per BTC and quantities in BTC. The
retained data and data-derived case observations carry the recorded Binance
Vision CC BY-NC-SA 4.0 conditions for noncommercial educational research.
These calculations remain outside Hoshi's runtime and enable no real orders.

## What is it?

Volume delta is the difference between two explicitly classified groups of
executed quantity. In this chapter, buyer-taker quantity is positive and
seller-taker quantity negative. A cumulative volume delta, or CVD, sums those
signed quantities from a declared reset. A footprint arranges the classified
executions into price rows inside a time interval. Together they describe
how observed trading was distributed by side, price and time.

Every execution has a buyer and seller. Positive delta does not mean there
were more buyers than sellers in some headcount sense. It means more base
quantity was executed by the buyer-taker side under the selected
classification. A marketable limit order can be a taker; “taker” is not a
synonym for a particular order-type name or an institutional participant.

For the checked Binance aggregate schema, the maker flag says whether the
buyer was the maker. When true, the buyer was passive and the seller the
taker, so this method subtracts the aggregate quantity. When false, it adds
buyer-taker quantity. The record supplies an exchange classification rather
than requiring a guess from a candle's color. It does not supply participant
identity, opening versus closing position, or an explanation of motive.

## Why does it form?

Trading requires both executable interest and counterparties willing to
provide liquidity. An aggressive order can execute against several resting
orders, while new orders and cancellations change the available book.
Price response therefore depends on more than the signed quantity in a
completed interval. A modest aggressive imbalance can accompany a large
move through a sparse book; a much larger imbalance can accompany little
movement when counterparty liquidity remains available.

This gives a disciplined interpretation of apparent absorption. Repeated
aggressive executions with limited price progress may motivate a hypothesis
about passive response. That observation alone cannot prove one hidden
iceberg, a particular bank, trapped positions, spoofing, or a future reversal.
Several traders, replenishment, cross-venue hedging and changing order sizes
can produce similar aggregate prints. The current dataset contains no
historical depth or participant identifiers to discriminate between them.

The same arithmetic explains CVD disagreements. Extending the reset backward
adds older signed volume to every later reading. A positive latest-minute
delta can coexist with negative cumulative delta over an hour. A final
positive delta can also conceal a negative early path and a larger positive
intermediate peak. Treating those four states as one “buying pressure” label
throws away information needed to evaluate a causal trade hypothesis.

## Application zone

### Preserve classification, units and reset

Hoshi's original offline method processes aggregate records in exchange-ID
order. Each quantity contributes exactly once. Aggregation combines executions
according to the provider's documented price/taker/time rule; the number of
aggregate rows is different from the number of underlying trades. Quantity
delta, trade-count delta and quote-value delta are different measurements.
The receipt uses BTC quantity and never substitutes a count of prints.

CVD resets to zero at the beginning of each fixed minute in the event-path
examples. Its high and low include the zero starting state. Each prefix
value depends only on events through that aggregate ID. The final minute
delta is known only after the whole minute; the retrospective highest value
cannot be called the eventual maximum while the minute is still forming.
Historical exchange timestamps also do not establish actual client arrival
times, which remain unknown.

For context, the receipt separately sums native kline deltas from the start
of the captured window through index sixty, and from index thirty through
sixty. A kline's classified quantity delta is `2*taker_buy_base-total_base`.
These bar-end sums do not recover the full intrabar CVD extrema over those
longer intervals. Their exact anchors are fixed before comparing them;
neither is described as a complete exchange trading-day CVD.

### Distinguish footprint comparisons

The original footprint uses the same absolute-zero, half-open one-USDT rows
as the preceding profile chapter. Each row stores buyer-taker quantity,
seller-taker quantity and their same-row difference. A horizontal comparison
uses both sides in that row. A diagonal comparison pairs buyer-taker quantity
at a row with seller-taker quantity one row below, or seller-taker quantity
with buyer-taker quantity one row above.

Sierra Chart's Numbers Bars documentation describes the corresponding
same-price and neighboring-price comparison distinctions. Hoshi's price rows
are research aggregations, not claims about the historical minimum tick or
that platform's settings. Here a research flag requires a ratio of at least
three and at least 0.01 BTC on both compared sides. These are explicit
unvalidated thresholds. A zero opposing denominator produces a null ratio,
not infinite confidence; a huge ratio against negligible quantity fails the
minimum-size condition.

Consecutive flagged rows can motivate a separately defined “stacked”
imbalance hypothesis, but this chapter implements no stacked-entry rule.
The raw footprint row counts are descriptive features. They are not votes
that can be added to an evidence score without checking shared inputs,
position overlap, missing global context and subsequent failure cases.

### Keep estimated and classified delta separate

Sierra's CVD documentation explains its bid/ask-volume method and reset
dependence. TradingView's CVD documentation describes an estimate built from
lower-timeframe price-direction and volume classifications. Those provider
methods need not equal Binance's maker-flag classification. Hoshi does not
claim platform parity or endorse a vendor's general accuracy statements.

For a simple counterfactual, the receipt also labels the entire minute's
volume by that minute's candle color. That deliberately coarse surrogate
is not described as TradingView's complete multi-intrabar implementation.
It demonstrates how assigning all volume one sign can erase genuine
two-sided execution. A green candle can contain substantial seller-taker
volume, and a red candle substantial buyer-taker volume.

## Failure zones

**Unavailable classifications:** an OHLCV bar alone does not reveal exact
aggressor-side executions. A price-direction estimate should retain its own
name, method and limitations. Without trade flags or a documented quote-based
classifier and suitable feed, exact CVD and footprint fields remain
unsupported. Filling them with confident-looking numbers would manufacture
evidence.

**Missing events:** dropped or duplicated records alter cumulative sums and
may fabricate a divergence. The archive subsets retain contiguous aggregate
and underlying trade-ID ranges, boundary neighbors and SHA-256 digests.
Their total quantities, OHLC and execution counts reconcile with the native
minute source. This chapter additionally reconciles buyer-taker base and
quote values with the source kline's corresponding fields. Even a rehashed
maker-side alteration must fail those independent totals.

**Future recognition:** a divergence requires declared comparable price and
CVD reference points, with their actual recognition times. Searching backward
for visually convenient highs after a reversal changes the experiment.
Comparing today's developing CVD with yesterday's final-session CVD without
matching anchors also changes the meaning. Different resets can explain a
sign change without any new trading.

**Absent book evidence:** footprints report executed flow. They do not
measure orders still resting, queue priority, cancelled quotes or future
liquidity. They cannot identify a liquidation without a suitable separate
source. Aggregate data do not establish whether a participant borrowed,
hedged, opened or closed exposure. A large print is not evidence of a
retail trap.

**Uncalibrated inference:** the three already-inspected minutes are teaching
examples, not a random or untouched validation sample. Costs, spread,
latency, entry/stop ordering and account constraints remain outside these
calculations. No trading pattern works 100%, and historical signed flow
does not establish a calibrated chance that the next trade will win.

## Three real historical examples with dates

These are the same fixed index-sixty minutes used for independent
indicator/profile comparisons, rather than newly selected successful
footprints. Source archives were captured around 05:17 UTC on 28 October
2026 and their ZIP digests matched the actual companion CHECKSUM responses.
Every event timestamp below is historical UTC, distinct from retrieval.
Complete-minute availability begins at the stated interval's end, plus
unknown provider/client delay.

### Example 1 — 15 May 2023, 07:30–07:31 UTC: positive minute flow inside a negative longer sum

This minute is 03:30–03:31 New York EDT. Buyer-taker quantity totals
14.35224000 BTC and seller-taker quantity 11.26691000 BTC. Their difference
is positive 3.08533000 BTC, approximately 12.0431% of the minute's total
25.61915000 BTC. The price rises from 27,447.48 to 27,453.59 during the minute.
Assigning all green-candle volume positive would instead report
25.61915000 BTC, concealing the actual seller-taker executions.

The minute-reset CVD first reaches its observed minimum of negative
1.06018000 BTC at 07:30:09.607, then its maximum of positive 6.05122000 BTC
at 07:30:22.185, before ending at positive 3.08533000 BTC. Those extrema
describe the completed path, without explaining why later executions changed
the sum. The one-USDT footprint contains seven buy-side and three sell-side
research flags under the declared ratio/minimum-size rules.

The longer captured-window sum from 06:30 is negative 262.58633000 BTC;
the sum from 07:00 is negative 170.24222000 BTC. A positive current-minute
delta therefore coexists with negative longer cumulative states. The
07:35 candle later closes 27,436.04, just before 07:36. Positive minute flow
did not guarantee immediate price continuation, and no executed long is
implied.

### Example 2 — 5 January 2024, 15:30–15:31 UTC: negative flow precedes a rebound

This minute is 10:30–10:31 New York EST. Buyer-taker quantity is
15.29645000 BTC; seller-taker quantity is 31.06900000 BTC. Net delta is
negative 15.77255000 BTC, approximately negative 34.0179% of total quantity.
The candle declines from 43,690.64 to 43,638.05. The whole red-candle
surrogate would be negative 46.36545000 BTC, a different measurement.

Minute CVD reaches a positive 3.25350000 BTC at 15:30:01.509 and a negative
16.94118000 BTC minimum at 15:30:56.726. The late net state does not erase
that early buying. Fifteen buy-diagonal and thirteen sell-diagonal research
flags occur across different one-USDT rows; counts on both sides cannot
be turned into mutually exclusive forecasts.

The sum anchored at 14:30 is negative 107.58993000 BTC, while restarting at
15:00 yields positive 72.74424000 BTC. Both include the same latest negative
minute. The 15:35 candle subsequently closes 43,731.11 just before 15:36,
above the observation close. This is a genuine counterexample to treating
negative completed-minute delta as guaranteed immediate continuation. It
does not prove a profitable contrarian rule either.

### Example 3 — 8 August 2024, 18:30–18:31 UTC: a declining positive CVD peak with rising price

This minute is 14:30–14:31 New York EDT. Buyer-taker quantity is
5.99175000 BTC and seller-taker quantity 4.86321000 BTC. The positive
1.12854000 BTC delta is approximately 10.3965% of total volume, while the
price rises from 59,561.26 to 59,607.46. The candle-color surrogate instead
assigns all 10.85496000 BTC positive.

Minute-reset CVD has a minimum of negative 0.14133000 BTC at 18:30:01.392
and a maximum of positive 3.89405000 BTC at 18:30:15.918. Its final positive
value is lower than that earlier peak. Three buy-diagonal and three
sell-diagonal flags remain in the footprint. A smaller final CVD than an
earlier peak does not, by itself, identify absorption or a bearish reversal.

The captured-window sum from 17:30 is negative 117.64815000 BTC and the
18:00 sum negative 59.29137000 BTC, despite the positive latest minute.
The 18:35 candle later closes 59,650.78 just before 18:36. This continued
rise coexists with a negative longer CVD level. The reset, change over time
and actual price response all matter; the absolute sign alone is insufficient.

## How to use it to HUNT a trade

Start with a supported feed whose side semantics and sequence behavior are
known. Store venue, instrument, units, reset, row width and the latest source
time. Validate continuity and reconcile independent totals before trusting a
divergence or an imbalance flag. If the data do not support the required
classification, return `WAIT` rather than promote a price-color approximation
to exact order flow.

Frame a paper hypothesis in observable terms: a previously known price
reference, a defined flow change, a later confirmation condition and an
explicit cancellation boundary. Historical “absorption” language needs a
testable definition and counterexamples; it cannot supply missing resting
depth. Require realistic observed quotes, bounded risk and costs before
constructing a paper entry. The present dataset supplies no live levels.

Evaluate frozen versions on untouched chronological periods. Keep failed
continuations, rebounding negative flow, different resets, zero denominators,
missing classifications and no-trade outcomes. Prevent future full-minute
footprints or later-confirmed pivots entering earlier decisions. Export the
actual features and rejection reasons alongside cost and ambiguity checks.
Until independently calibrated, Hoshi's result is evidence coverage with
`win_probability=null`; source completion is neither model training nor a
completed runtime strategy release.

## Sources

Primary references actually checked on 28 October 2026; only brief
methodological paraphrases are used:

1. Binance's [aggregate-trade schema](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market),
   including quantity, underlying trade IDs and buyer-maker semantics.
2. [Official archive schema/checksum instructions](https://github.com/binance/binance-public-data)
   and [dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md).
   Binance Vision data and derived observations: CC BY-NC-SA 4.0,
   noncommercial research/education; attribution is not sponsorship.
3. Sierra Chart's official [Cumulative Delta Bars — Volume](https://www.sierrachart.com/index.php?ID=292&page=doc/StudiesReference.php)
   and [Numbers Bars](https://www.sierrachart.com/index.php?page=doc/NumbersBars.php)
   documentation. Definitions and comparison choices, not validation of
   Hoshi's original thresholds or vendor parity.
4. TradingView's official [Cumulative Volume Delta](https://www.tradingview.com/support/solutions/43000725058-cumulative-volume-delta/)
   explanation. Its intrabar estimate is distinguished from maker-flag data.
5. [Retained raw aggregate subsets, paths and footprints](indicator_observations_20261028.json),
   [original offline replay](../../scripts/v3_indicator_evidence.py)
   and [native minute source receipt](../05_ICT_COMPLETE/ict_intraday_observations_20261028.json).
   Exact archive URLs, capture times, ZIP/subset hashes and neighboring
   records are retained in the receipt; complete archives are not bundled.

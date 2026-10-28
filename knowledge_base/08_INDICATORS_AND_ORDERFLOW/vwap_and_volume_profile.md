# VWAP and volume profile: anchors, executed quantities and resolution

Reviewed on 28 October 2026. Data-derived examples are noncommercial
educational research using Binance Vision data under the recorded
CC BY-NC-SA 4.0 conditions. They concern Binance Spot BTCUSDT, not a
consolidated global BTC market, futures, NAS100 or a broker's CFD feed.
All prices are historical USDT per BTC. No chart-platform parity or
executable trading edge is claimed.

## What is it?

Volume-weighted average price measures an average of observed transaction
prices, weighted by executed quantity, over a specified interval. For trades
with price `p` and base quantity `q`, it is `sum(p*q)/sum(q)`. The numerator
has quote-currency units and the denominator base-asset units. The ratio is
a price. Zero total quantity has no defined VWAP and should not become zero
price or a trading signal.

A volume profile preserves the distribution that a single average discards.
It groups executed quantities into declared price rows. The largest row is
the point of control, or POC. A high-volume node is a relatively large region
in that particular histogram; a low-volume node is relatively sparse.
Neither the average nor the largest row reveals who currently holds an
inventory, whether those traders remain positioned, or their net cost after
fees, transfers and hedges.

A value area is a selected contiguous part of the profile built according to
a specified volume-fraction algorithm. Its upper and lower boundaries are
VAH and VAL. A nominal seventy-percent target is not a seventy-percent
probability of a future bounce, nor is it guaranteed to contain exactly
seventy percent when entire price rows must be included. A time-at-price
profile instead counts time opportunities; it is not interchangeable with
executed volume at price.

## Why does it form?

Executed quantity accumulates when compatible orders match. Prices where
many such executions occur receive more weight in a VWAP and larger rows
in a volume profile. This can reflect repeated two-sided exchange, large
orders, a prolonged pause, or rapidly changing participants. A large row
alone cannot distinguish those explanations. Every matched execution has
both a buyer and a seller; adding the same quantity once as “buy volume”
and again as “sell volume” doubles total activity incorrectly.

The arithmetic also explains seemingly contradictory chart readings. An
earlier heavy-volume episode can keep a long anchored VWAP far from the
current price even after a substantial recovery. Restarting the anchor
removes that earlier weight. Rebinning a histogram can merge several nearby
rows into a new peak, moving the POC without any new transaction. A changed
indicator label therefore need not mean market participants changed their
behavior at that instant.

These distinctions are useful because the language of acceptance, rejection
and fair value can otherwise become circular. A profile describes where
activity occurred within the selected interval. Whether a return to that
region attracts new trading, passes through it or never happens is another
empirical question. The histogram does not establish an institution's intent
or the cause of a subsequent price move.

## Application zone

### Specify the anchor and price input

An anchored VWAP begins at a fixed event or timestamp. A session VWAP resets
at a defined session boundary. A rolling VWAP continually removes older
observations. An event anchor selected only after seeing the eventual bottom
contains hindsight. In causal research, record when the anchor could first
have been chosen, including any later pivot-confirmation delay.

Sierra Chart's own VWAP documentation makes session configuration and
underlying-data selection explicit. TradingView's documented bar formula
uses a typical-price source, commonly `(high+low+close)/3`, weighted by bar
volume. Such a bar proxy need not equal the transaction-weighted average.
This chapter calculates both and names the difference rather than describing
one as the other's exact platform output.

The existing Binance minute receipt includes base quantity and quote value.
Summing reported quote value and dividing by summed base quantity gives a
transaction-value-weighted price for that captured interval, at the provider's
recorded precision. No interpolation inside the candle is needed for that
mean. It still does not reveal how the volume was distributed across prices;
different trade sequences can share the same OHLC and total quantity.

### Specify profile rows and value-area rules

For the actual price distribution, this chapter adds three fixed complete
minutes of primary aggregate-trade records. It groups each trade price into
half-open rows anchored at absolute zero: `[k*w, (k+1)*w)`, for width `w`.
Widths of one and five USDT are explicit research choices, not assertions
about the historical exchange tick size. Base BTC quantity weights the rows.
The receipt retains every occupied row, its boundaries and quantity.

Hoshi's original value-area rule starts at the largest row, choosing the
lower row when multiple POCs tie. It adds the larger adjacent row until the
included volume reaches at least seventy percent; adjacent ties choose the
lower side. Missing rows inside the observed range have zero captured
quantity. Whole-row additions may overshoot. This rule is versioned and
deliberately explicit; it is not claimed to match TradingView's published
stop-before-overshoot convention or every Sierra configuration.

TradingView documents lower-timeframe bar analysis and up/down-bar volume
classification for its profiles. That classification is distinct from
exchange-reported aggressor side. Sierra Chart documents why underlying
tick records matter for accurate volume-at-price construction. Hoshi's
examples use actual archived price/quantity aggregates; it does not spread
a candle's volume uniformly across its high-low range and call that observed
trade distribution.

### Verify the source before interpreting the shape

On 28 October 2026, a historical aggregate REST query for the first ten
seconds of the May case returned HTTP 200 with an empty array. That reply
does not establish that no trading occurred. The official daily archives
were available. Their downloaded ZIP SHA-256 values matched the actual
companion CHECKSUM responses, and the extraction retained all records whose
timestamps fell within each fixed minute, plus neighboring boundary records.

The three subsets contain 465, 1,653 and 575 aggregate rows respectively.
Their underlying trade-ID ranges represent 635, 1,984 and 807 executions.
Aggregate IDs and underlying trade IDs remain contiguous across the retained
records and boundary neighbors. Every subset exactly reconciles its open,
high, low, close, base quantity, quote value and execution count with the
independently captured minute kline. Aggregation therefore preserves the
price/quantity evidence needed here without pretending each row is exactly
one individual execution.

## Failure zones

**Changing the question:** moving the anchor, viewport or price-row width
changes the measured interval or grouping. A visible-range profile depends
on which history is displayed. A later full-session POC cannot be supplied
to a decision early in that session. A developing profile needs its own
as-of timestamp and must retain the state actually observable then.

**Small samples:** these are three one-minute profiles and two bounded VWAP
anchors per case. They are not full-session profiles, representative market
distributions or independent validation samples. A few large executions can
dominate a tiny profile. Adding more bins does not create more independent
information; it can expose increasingly noisy distinctions.

**Data substitutions:** tick-count volume is not executed BTC quantity.
Quote-weighting and base-weighting are different. Venue-specific spot volume
cannot establish a futures contract's inventory or another venue's stop
distribution. Synthetic candle types can transform the displayed prices;
their values should not be mistaken for executable trade prices.

**Execution:** trading below a VWAP does not guarantee a future return to it.
VWAP can be an execution benchmark only with a compatible interval, side,
quantity and cost convention. Comparing a morning purchase against the
future full-day VWAP uses information unavailable at that purchase time.
Slippage, spread, fees and market impact belong in a paper execution model;
this chapter has none of those historical order-book inputs and computes no
strategy PnL.

**Integrity and rights:** offline checks validate the selected CSV bytes,
ID continuity and reconciliation with recorded candles. Whole ZIP archives
are not bundled and are not re-downloaded by CI. The capture-time ZIP digest
match is a recorded verification step, not an offline proof against every
later archive revision. Binance's checked dataset terms provide these data
for specified noncommercial research/educational uses; this receipt does not
license a commercial data feed, train a model or supply a production-order
source. No trading pattern works 100%.

## Three real historical examples with dates

Each profile uses the fixed candle at index sixty of an existing 120-minute
capture, selected without future outcome conditions. Bar labels are opening
timestamps. The one-minute intervals below are start-inclusive and
end-exclusive; their complete profiles are possible only at the end,
before any unknown publication/arrival delay.

### Example 1 — 15 May 2023, 07:30–07:31 UTC: a mean differs from a modal row

This minute is 03:30–03:31 New York EDT. Its 465 aggregate records represent
635 executions and 25.61915000 BTC. The reconstructed transaction VWAP is
27,457.0954. The close is 27,453.59, below that mean. With one-USDT rows,
the largest bin is `[27459,27460)`, which is above both the close and the
mean. An average and a modal row need not coincide.

The one-USDT value area is `[27453,27464)` and includes approximately
83.7614% of this minute's quantity under the declared overshoot rule.
Five-USDT rows instead produce a POC of `[27455,27460)` and a value area
`[27450,27465)` containing approximately 89.5120%. These actual overshoots
show why a label of “70% value area” does not establish exactly seventy
percent containment or future reliability.

The longer VWAP from 06:30 through the completed 07:30 candle is
27,464.0032. Restarting at 07:00 gives 27,458.0521. Both differ from the
single-minute mean and from each other. None is a full-day session VWAP.
The later 07:35 candle closes lower at 27,436.04, just before 07:36;
reversion to a chosen mean is not demonstrated by this bounded path.

### Example 2 — 5 January 2024, 15:30–15:31 UTC: anchor choice reverses the label

This minute is 10:30–10:31 New York EST. Its 1,653 aggregates reconcile to
1,984 executions and 46.36545000 BTC. The transaction VWAP is 43,666.0066,
while the close is 43,638.05. The one-USDT POC is `[43629,43630)` and its
value area `[43628,43686)` contains approximately 73.7656% of minute volume.
Five-USDT grouping moves the POC to `[43625,43630)` and changes the area to
`[43625,43690)`, approximately 75.4406%.

More consequentially, the VWAP anchored at 14:30 is 43,620.0206, below the
same close. The anchor at 15:00 produces 43,695.5778, above that close.
Thus the statements “price is above VWAP” and “price is below VWAP” are both
arithmetically true with different declared anchors at the same instant.
Silently choosing whichever label supports a desired trade is hindsight,
not additional confluence.

For the 15:00 anchor, the HLC3-weighted bar proxy is 43,697.5934, approximately
0.4613 basis points above the quote/base result. This is a small observed
difference, not zero and not evidence that the proxy is always sufficiently
accurate for an execution decision. The 15:35 candle later closes 43,731.11;
the final profile alone does not identify an executable entry or stop.

### Example 3 — 8 August 2024, 18:30–18:31 UTC: aggregation moves the peak

This minute is 14:30–14:31 New York EDT. Its 575 aggregates represent
807 executions and 10.85496000 BTC. Transaction VWAP is 59,583.3789; the
minute closes 59,607.46. One-USDT grouping places the POC at `[59582,59583)`.
Five-USDT grouping places it at `[59575,59580)`, an interval that does not
contain the earlier one-USDT POC. Combining nearby quantities changed the
mode without changing the underlying executions.

The one-USDT value area `[59558,59592)` contains approximately 70.0612%.
The five-USDT area `[59575,59620)` contains approximately 70.9584%. Those
different contiguous areas describe the same 10.85496000 BTC. A reader must
know the bin width and algorithm before comparing screenshots or interpreting
a supposed level of rejection.

The earlier 17:30 VWAP anchor is 59,522.8130; restarting at 18:00 gives
59,466.9166. The observed close exceeds both. The later 18:35 candle closes
59,650.78 just before 18:36. That continuation is a historical observation,
not proof that price above every possible VWAP predicts a profitable long.

The ZIP subsets were captured around 05:17 UTC on 28 October 2026.
Kline source captures occurred earlier that day around 01:59 UTC. Both
retrieval clocks are distinct from the 2023/2024 trade timestamps. These
later archive observations do not establish historical feed latency or
point-in-time availability of subsequently corrected data.

## How to use it to HUNT a trade

Freeze the anchor, row width, quantity unit, value-area algorithm, data venue
and as-of boundary before looking for a setup. Ask what role each quantity
serves: execution benchmark, descriptive context, or a predeclared entry
hypothesis. Do not turn a distribution into a directional forecast merely
because a price is near its largest row.

Require a supported current source and a complete developing snapshot before
paper use. Distinguish a trade-price mean from a bar proxy and a historical
profile from resting order-book depth. A trade at a price proves execution
occurred there in the past; it does not prove orders remain there now.
Data gaps, stale quotes or an unsupported profile source require `WAIT`.

A later evaluation should reserve untouched chronological periods, test
anchor and binning sensitivity, retain no-return and continuation cases,
and model realistic costs and ambiguous paths. Report missing observations
and zero-trade results. The present receipt supplies original reproducible
historical analysis; `win_probability` remains null and real orders remain
disabled. Runtime retrieval and the final integrated V3 release are separate
unfinished gates.

## Sources

Primary materials checked on 28 October 2026; no proprietary course or chart
text reproduced:

1. Binance, [public-data schema and checksum instructions](https://github.com/binance/binance-public-data)
   and [dataset terms, version 1.0 dated 26 August 2026](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md).
   Data attribution: Binance Vision; CC BY-NC-SA 4.0 applies to retained
   data and data-derived case observations.
2. Actual downloaded archives and checked companion checksums:
   [15 May 2023](https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2023-05-15.zip),
   [checksum](https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2023-05-15.zip.CHECKSUM);
   [5 January 2024](https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2024-01-05.zip),
   [checksum](https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2024-01-05.zip.CHECKSUM);
   [8 August 2024](https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2024-08-08.zip),
   [checksum](https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-2024-08-08.zip.CHECKSUM).
3. Sierra Chart's official [Volume by Price](https://www.sierrachart.com/index.php?ID=141&page=doc/StudiesReference.php)
   and [VWAP](https://www.sierrachart.com/index.php?ID=108&page=doc/StudiesReference.php)
   documentation. Data resolution and calculation configuration, not evidence
   that the original Hoshi rules match that platform.
4. TradingView's official [volume-profile concepts](https://www.tradingview.com/support/solutions/43000502040-volume-profile-indicators-basic-concepts/)
   and [VWAP](https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/)
   documentation. Provider-specific bar approximations and conventions are
   distinguished from the raw-trade arithmetic above.
5. [Exact extracted records and calculation receipts](indicator_observations_20261028.json),
   [original offline arithmetic](../../scripts/v3_indicator_evidence.py)
   and [independent native-minute capture receipt](../05_ICT_COMPLETE/ict_intraday_observations_20261028.json).
   The full ZIPs are not bundled; exact archive/subset digests and boundary
   records support later re-extraction and audit.

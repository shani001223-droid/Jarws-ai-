# Supply and demand zones: observable references and falsifiable hypotheses

Reviewed: 28 October 2026, Asia/Karachi. Scope: price-derived zones, their
identification clock and historical observation. This source chapter does not
identify bank inventories, reconstruct hidden orders or change Hoshi's runtime.
The three cases use actual captured prices and an original offline protocol.

## What is it?

A supply or demand zone is a bounded price interval selected as a reference
for a possible later response. A demand hypothesis anticipates support when
price returns from above; a supply hypothesis anticipates resistance when
price returns from below. The interval is a feature created by a specified
method. It is not itself a count of orders, a guarantee of future response or
proof that a named participant is waiting to transact there.

Keep three concepts separate. Economic supply and demand concern willingness
to transact under changing conditions. An exchange's visible order book
contains current displayed bids and asks on that venue. A rectangle drawn
around an old candle is historical geometry. Its relationship to current
interest must be investigated; it cannot be assumed from the rectangle alone.
Binance's primary documentation distinguishes its price/quantity depth endpoint
from its timestamped candlestick endpoint. Our captures contain the latter,
not contemporaneous depth messages or historical queues.

Practitioner drawings use several different origin conventions. Some include
an entire candle or consolidation, some only the body, some the wick, and some
require a departure impulse. A narrow interval makes a chart look precise
but changes both contact frequency and failure frequency. A broad interval
can hide large adverse movement inside a supposedly successful zone. Neither
choice is automatically better. Define width, origin selection, activation,
future observation and invalidation together before comparing results.

CME's checked educational material treats support and resistance as areas
rather than perfectly reliable single prices, and describes previous extremes
among possible references. It does not certify this chapter's custom detector.
The following original definition exists to make the historical claims
reproducible, not to rename it as an exchange-endorsed trading method.

### Original confirmed-pivot wick protocol

`hoshi-confirmed-pivot-wick-zone-1` first requires a strict pivot using two
bars to the left and two to the right. A low must be below all four comparison
lows; a high must be above all four comparison highs. Ties do not qualify.
The candidate origin is visible on its own day, but the feature is unavailable
until the second right-hand candle closes. That lag is part of the method.

For a demand candidate, use the origin's low as the lower boundary and the
lesser of its open and close as the upper boundary. For supply, use the greater
of open and close as the lower boundary and the high as the upper boundary.
These are wick intervals. A zero-width wick is ineligible rather than replaced
with an invented minimum width. A candle can theoretically qualify as both
a strict high and strict low; those are separate features, not proof of two
independent institutional positions.

Activation occurs at the pivot confirmation close. The protocol deliberately
excludes contacts on the origin, the two confirmation bars and all earlier
bars from its subsequent contact ledger. It then observes exactly twenty
later completed candles. Inclusive high-low intersection counts as contact.
A demand candidate has an invalidating close strictly below its lower bound;
a supply candidate has one strictly above its upper bound. Equality is not
a breach under this particular rule.

A closing rejection requires contact followed by that same candle closing
strictly beyond the favourable side: above the upper demand boundary or below
the lower supply boundary. A wick crossing the wrong outer boundary is stored
separately. The active lifecycle stops at the first invalidating close. Contact
on that candle cannot override invalidation. These are diagnostic categories,
not simulated orders. If twenty future bars are unavailable, the final
observation is null rather than silently shortened to a favourable horizon.

## Why does it form?

A confirmed extremum is a local relationship among completed prices. A later
reaction near it can have several mechanisms: some participants may remember
an earlier price, new information may change valuations, or liquidity may
arrive or disappear as the market revisits the area. Those are plausible
hypotheses. Daily candles do not distinguish them or reveal who held which
position. A bounce alone cannot establish that old unfilled orders survived
unchanged until the retest.

The original research by Cont, Kukanov and Stoikov studies quote and order-book
events in fifty US stocks and relates short-horizon price changes to imbalance
at the best quotes and market depth. That is evidence about their measured
market microstructure, not validation of old daily Bitcoin rectangles. Their
preprint's first submission was 29 November 2010, its checked revision was
13 April 2011, and its journal reference is Winter 2014. Those are publication
dates, not dates of the three price cases below.

This distinction prevents a common reasoning error: moving from the correct
observation that orders and depth matter to the unsupported conclusion that
a particular wick reveals all of them. An identical wick can result from very
different intrabar paths. A candle with high turnover can contain repeated
transactions at the same prices; turnover is not a remaining inventory map.
The analyst needs actual order-level evidence to make stronger claims.

Zone width also expresses sampling choices. On a daily chart one long wick
may cover many smaller consolidations. At a different venue or daily boundary,
the extrema and open can differ. The causal method should survive as a clearly
defined measurement even when its economic hypothesis fails. Altering the
zone after each later price movement destroys that test.

## Application zone

Apply a zone as a predeclared observation area inside a larger research
question. Record the source, symbol, quote currency, timeframe and completion
cutoff. Determine whether the question is first return, closing rejection,
continued support over a fixed horizon, or an executable trade. These are
different outcomes. A candidate with no return supplies no evidence about
the profitability of a limit entry at its boundary.

These examples use **Binance Spot BTCUSDT**, USDT per BTC, with daily bars
running 00:00:00–23:59:59.999 UTC. They reuse three hash-checked response
captures containing 611 bars across bounded 2020, 2021 and 2022 windows.
The retained raw bytes were captured during the 28 October 2026 review, not
downloaded contemporaneously on the historical dates. There is no independent
historical-vintage guarantee. The companion `zone_observations_20261028.json`
records feature availability separately from twenty-bar outcome availability.

For an eventually executable paper model, a zone's width must be compared
with observed spread, feasible invalidation and risk budget. A small distance
to a theoretical stop can create a very large notional position if sizing
ignores slippage. Overlapping daily and hourly zones often derive from the
same transactions; counting them as independent confirmation inflates
evidence. A macro conflict or unsupported data source can still require WAIT
even when local geometry is present.

Separate a screening universe from illustrative case selection. The three
examples below were selected after inspecting the existing windows to teach
contact, absence and failure. They are not an exhaustive sample, an untouched
holdout or evidence for a success percentage. The offline implementation
can reproduce their prices and clocks; that mechanical property does not
establish that the method has an economic edge.

## Failure zones

No zone works 100%. A genuine confirmed pivot can be followed by a decisive
break. A twenty-bar period without a closing breach may contain a large wick
through the boundary, which matters to any stop-based strategy. A daily
close-based invalidation waits for information that arrives much later than
an intraday risk threshold. The choice must be stated rather than rewritten
after a loss.

A return into an interval is not a fill. It contains no queue priority,
spread, available size, order acknowledgement or cancellation history. The
SEC's stock-order explanation distinguishes price constraints on limit orders
from market-order execution-price uncertainty, and explains that a triggered
stock stop becomes a market order. These are useful execution distinctions;
crypto-specific order rules still require that venue's documentation. The
source is not evidence that a Binance historical low filled a hypothetical
Hoshi order or that a stop would execute exactly at a chosen line.

Confirmation introduces unavoidable delay. Buying at the origin's low after
requiring two right-hand bars uses a price unavailable at the stated decision
time unless a later, independently observed return exists. Marking that origin
as an entry on a retrospective screenshot hides the lag. Contacts before
activation should not become later retests. Likewise, a zone breached on its
first eligible contact is a failure under the closing rule, even if price
subsequently recovers or the origin looks attractive on another timeframe.

Sparse samples create another trap. With no return, an analyst may describe
the zone as extremely strong because price moved away. But the waiting-entry
model had no observed opportunity. With repeated contacts, the analyst may
claim demand increased, or alternatively that demand was consumed. Both
stories require evidence beyond contact count. Store the count and current
status; leave institutional inventory and intent unknown.

## Three real historical examples with dates

### Example 1 — 13 March–4 April 2020: delayed activation, then a closing rejection

On 13 March the source candle opened 4,800.01, traded low 3,782.13 and closed
5,578.60. The original demand interval is therefore **3,782.13–4,800.01**.
The low satisfies the strict two-left/two-right pivot relation, but the zone
is known only at the **15 March** completed close, when price closed 5,361.30.
No 13 March low entry is implied by that later confirmation.

On 16 March the daily range was 4,442.12–5,365.42 and the close was 5,028.97.
It intersects the interval and closes above its upper boundary, so the
protocol records both first eligible contact and closing rejection that day.
Across the twenty subsequent bars, ending **4 April**, neither a lower-bound
wick breach nor an invalidating close occurs. This is an observed favourable
geometric path, not a guaranteed purchase at 4,800.01 or a measured account
return. The interval's width itself makes risk and entry choices material.

### Example 2 — 20 July–11 August 2021: no later contact is not a filled winner

The 20 July candle had low 29,278 and closed 29,790.35, below its open
30,839.65. Its demand interval is **29,278–29,790.35**. Confirmation arrives
at the **22 July** close of 32,287.83. The first eligible later bar is
23 July, whose low is 31,924.32, already above the interval.

None of the twenty observed daily bars through **11 August** intersects the
frozen interval. First contact, closing rejection, wick breach and close
breach therefore remain null. The absence of a breach is real, but so is the
absence of an eligible return. A screenshot may make the origin look like
an excellent bottom; a waiting zone-entry rule cannot claim the subsequent
move as its trade. The receipt preserves `fill_known: false` and null PnL.

### Example 3 — 3–25 November 2022: the first contact also invalidates demand

The 3 November origin opened 20,151.84, traded low 20,031.24 and closed
20,207.82. Its interval is **20,031.24–20,151.84**. Confirmation arrives at
the **5 November** close of 21,299.37. The later observation window runs
6–25 November, independent of when the first failure occurs.

On **8 November** the candle opened 20,590.67, traded high 20,700.88 and low
17,166.83, then closed 18,547.23. It both intersects the interval and closes
below the lower boundary. The method records first contact, first wrong-side
wick and first invalidating close on the same bar, with no closing rejection.
The active lifecycle ends there. This is direct counterevidence to treating
every freshly confirmed low as safe demand. The prices alone neither identify
the cause of the selloff nor show the fill sequence of any hypothetical stop.

## How to use it to HUNT a trade

Begin with a valid supported feed and closed bars. Freeze a zone at its actual
activation time with a method identifier, boundaries and expiry. If it is
only a developing pivot, label it developing rather than presenting it as
confirmed. Displaying a historical origin can be useful for explanation, but
the decision record must retain the later confirmation clock.

Then monitor future observations without moving the rectangle to rescue it.
Distinguish waiting, contact, closing rejection, wick breach, invalidation,
expiry without contact and unavailable future data. If a single bar intersects
the zone and violates invalidation, preserve both facts and resolve the
eligibility conservatively. Do not label an order filled merely because the
bar traded somewhere through the interval.

If the larger evidence requirements and data quality permit research, define
a bounded paper plan using observed post-signal prices, realistic costs,
maximum aggregate exposure and an explicit ambiguity policy. Correlated zone,
candlestick and structure labels should share evidence lineage. Future V3
coverage scores must not turn these selected examples into win probability.
Independent chronological evaluation needs many more appropriately sampled
events, rejected cases and adverse outcomes.

Hoshi should normally express only the supported symbol, observation time,
candidate status and material missing requirements in concise Roman Urdu.
Teach the mechanisms when asked. This chapter and its replayable receipt are
source material, not model training, runtime retrieval or authorization to
send orders. Missing current data means WAIT rather than recycling historical
prices into a live entry, stop or target.

## Sources

Checked 28 October 2026. Institutional documentation supports the stated
concepts; the pivot-wick protocol and historical arithmetic are original.

- CME Group, [Support and Resistance](https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance): educational treatment of chart references and zones, without validation of this custom detector.
- Cont, Kukanov and Stoikov, [The Price Impact of Order Book Events, arXiv v3](https://arxiv.org/abs/1011.6402v3): checked abstract and version history; evidence concerns their quote-event sample, not historical zone accuracy.
- SEC Investor.gov, [Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders): stock-order price/execution distinctions; no claim of venue-identical crypto rules.
- Binance, [Spot market-data API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): separate depth and kline definitions. Exact underlying captures and request bounds are in `../01_MARKET_STRUCTURE/structure_observations_20261028.json`, referenced by hash in `zone_observations_20261028.json`.
- Binance [public-data project](https://github.com/binance/binance-public-data) and [market-data terms](https://data.binance.vision/?prefix=); source data and derived data analysis are attributed under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), for non-commercial educational research. Unrelated code and cited publications retain their own terms; no endorsement is claimed.

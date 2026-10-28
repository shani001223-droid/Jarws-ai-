# DOM, order books and execution: usable liquidity at a known instant

Reviewed on 28 October 2026. This chapter combines primary feed
specifications with three documented historical investigations. The historical
cases are report observations, not downloaded event-book replays. The current
curriculum has actual trades and candles but lacks synchronized historical
depth and client-arrival messages for those cases. No current quote, filled
order, measured strategy return or runtime depth engine is claimed.

## What is it?

Depth of market, or DOM, displays available buying and selling interest at
different prices on a specified venue. A central limit order book changes
through submissions, executions, cancellations and modifications. Its
displayed quantities are conditional on the observed instant; they do not
promise that the same quantity will remain available when another order
arrives.

The best bid is the highest displayed buy price and the best ask the lowest
displayed sell price in a valid two-sided book. Their difference is the
quoted spread. Their arithmetic mean is the midpoint, a descriptive reference
that may have no executable quantity. The last trade describes an earlier
execution and can differ from both current quotes. A footprint records
executions at prices; it cannot recover the unexecuted and cancelled interest
that a historical book would require.

| Common data level | Observable content | Important limit |
| --- | --- | --- |
| Top of book / L1 | Best quotes and associated sizes, depending on feed | Deeper execution capacity remains unknown |
| Price-level / L2 | Aggregated displayed quantity at several prices | Individual queue position and hidden quantity remain unknown |
| Order-level / L3 | Individual displayed orders and changes where supplied | Participant intent, reserve quantity and another venue's book still need separate evidence |

These labels are conventions, so the actual vendor schema controls. Hoshi
must store the supported instrument, venue, feed type, precision and depth
limit instead of assuming every service supplies equivalent market access.

## Why does it form?

A participant can offer liquidity by leaving an order available for execution
under a venue's rules, or demand immediate execution by submitting marketable
interest. The observable book is the changing intersection of those choices.
Repricing information, inventory limits, competing orders and risk controls
can change the book before a phone receives its next update. A large resting
quantity may therefore disappear through legitimate execution or cancellation.
Its disappearance alone does not establish spoofing.

Available liquidity also depends on size and time. A small hypothetical order
might fit at the best quote while a larger one would consume several levels.
A thin snapshot can replenish rapidly, whereas a deep snapshot can disappear
when conditions change. Static depth and resilience describe different
properties. Neither a large traded-volume bar nor an imbalance in displayed
quantity is a universal measure of the ability to execute at low cost.

This matters during stress because the measurement system itself can fail.
An interrupted connection can leave apparently attractive stale levels on
screen. A missing update can preserve orders that already executed, while a
misapplied quantity update can accumulate fictitious depth. Feed integrity is
part of the hypothesis, not a cosmetic detail to be checked after a signal.

## Application zone

### Describe the book with explicit algebra

Let `b` and `a` be the best bid and ask, with positive displayed quantities
`qB` and `qA`. The midpoint is `m=(a+b)/2`; the relative spread in basis
points is `10000*(a-b)/m`. A simple displayed-size imbalance is
`(qB-qA)/(qB+qA)`. These describe the selected book instant; they do not
estimate a trader's inventory or calibrated probability of the next price.

One possible weighted reference is
`(a*qB+b*qA)/(qB+qA)`, often called a simple microprice proxy. Larger bid
quantity moves this proxy toward the ask. This weighting is a mathematical
description, not proof that the ask will trade next. A feed with empty,
crossed, stale or otherwise invalid sides cannot receive a valid two-sided
metric merely by filling missing values with zeros.

For a hypothetical buy of quantity Q, walk ascending asks and assign each
level at most its visible quantity until Q is covered. The static average
is `sum(price_i*assigned_quantity_i)/Q` only if the full quantity is covered.
For a sell, walk descending bids. If the observed levels cannot cover Q,
the full-size estimate is unavailable. Do not price the remainder at the
last level, at the midpoint or at zero. Contract multipliers, base units and
venue quantity increments must be accounted for before comparing costs.

This is a static counterfactual, not a fill simulator. Orders can move during
latency; other orders can execute first; unseen interest can matter. A later
paper model needs observed source and arrival clocks, matching rules,
partial fills, fees, spread, market impact, rejection conditions and bounded
funds/risk. None is established by a DOM screenshot.

### Synchronize before calculating

Binance's checked primary Spot WebSocket instructions describe buffering
depth events, obtaining a snapshot, discarding obsolete buffered events,
and verifying the initial overlap with the snapshot's update ID. Subsequent
events carry first/final update IDs. A forward sequence gap requires
discarding the local book and resynchronizing. Listed level quantities
replace previous quantities; zero removes a level. Snapshot depth is bounded,
so unchanged levels outside it can remain unknown.

These are provider-specific reviewed instructions, not an implemented or
universally portable book builder. Exact bootstrap boundaries, duplicate
events, reconnects and snapshot races require pinned-spec integration tests
before runtime use. A timestamp alone cannot repair a broken sequence.
Current documentation does not establish the historical feed behavior during
an older event.

### Separate order eligibility from queue execution

A limit price constrains acceptable execution but does not ensure a fill.
Touching a price in a candle does not prove an order ahead in the queue was
fully executed. A market order or activated market-style stop can face a
worse price than a reference quote. The checked SEC investor material
explains stock-order distinctions; another venue's trigger and matching
policies still need their own specification.

A paper queue model must declare what it knows. L2 reductions cannot always
distinguish cancellations from executions or locate a hypothetical order
inside an aggregated queue. Matching may involve priority rules beyond a
simple first-in-first-out assumption. Where exact queue evidence is missing,
use a declared conservative bound or mark the fill unknown. Never backfill
an attractive realized execution because a later chart touched the limit.

## Failure zones

**Displayed-size storytelling:** a large wall is observable interest at one
instant, not a guaranteed barrier or proof of an intended trap. A heatmap
can preserve historical displayed states but still omit hidden orders,
cross-venue interest and another participant's queue position. A subsequent
move through a wall does not identify which mechanism removed it.

**Incomplete coverage:** a top-five-level snapshot does not describe an
entire market. A bounded feed can become insufficient for a larger order
even while small trades remain possible. Sparse data must not be treated
as an empty global book. Execution estimates need both the requested size
and the actually observed coverage.

**Clock confusion:** exchange event time, trade time, collector receipt,
device receipt and a report's publication time answer different questions.
An old snapshot reused after a disconnect can look orderly while the market
has already moved. A cleaned historical archive can omit the revision state
that an actual participant initially saw. Those limitations belong in the
evidence export and causal replay.

**Cross-market substitutions:** an equity index is not directly executable
like its futures contract; a Treasury yield is not a cash price; a spot
FX venue does not cover every dealer. A pause on one futures venue does not
mean another spot venue paused. Prices from one source cannot complete a
missing entry or stop model for another instrument.

**Source-case overreach:** official investigators can use supervisory records
or participant classifications unavailable to a retail system. Their later
explanations must not become features dated before publication. The cases
below explain failure modes; three famous disruptions do not calibrate their
frequency, a trading alarm, an entry rule or a win probability. No pattern
works 100%.

## Three real historical examples with dates

These cases reuse three relevant official investigations for a different
question: which execution assumption failed or remained unverified? They
are not additional independent strategy trials. Raw historical depth,
complete queue records and synchronized retail arrival logs remain missing.

### Example 1 — 6 May 2010: large turnover alongside very limited buy-side depth

The CFTC/SEC staff report dated 30 September 2010 examines the U.S. equity
and E-mini S&P 500 disruption. It reports an interval with over 27,000 HFT
contracts traded but only about 200 additional contracts bought net. At that
stage it estimates E-mini buy-side depth around $58 million, less than one
percent of that morning's level. These are reported findings, not Hoshi's
own reconstruction or a measurement of present-day capacity.

The relevant operational distinction is between repeated executed turnover
and remaining interest available to an incoming seller. A rule treating high
volume as a guarantee of low slippage would miss that difference. A rule
using reconstructed participant net positions also requires the information
those investigators actually had; an ordinary volume candle does not
provide it.

The source prints intraday times, but this chapter does not certify their
machine timezone mapping or reconstruct an event stream from them. The event
date and publication date are separate. Without the book and arrival records,
Hoshi cannot quote a hypothetical exact sweep price, queue fill or recovery
trade. A suitable paper response is to reject an uncostable size or broken
feed rather than assume that the last trade was an executable exit.

### Example 2 — 15 October 2014: linked securities retain different observation types

A Federal Reserve staff retrospective published 24 September 2020 describes
the benchmark ten-year Treasury yield falling sixteen basis points during
09:33–09:45 ET on 15 October 2014 before rebounding. That ET interval is
13:33–13:45 UTC under New York's historical daylight-saving convention. The
staff note compares Treasury activity observed through BrokerTec with agency
MBS transactions observed through TRACE and distinguishes their pricing and
trading patterns.

The original implication for Hoshi is that synchronized sources must still
be comparable. A midpoint-based Treasury observation is not an executable
offer in a selected MBS coupon. A sixteen-basis-point yield change is not a
sixteen-percent price return. A relative-value rule needs the actual
instrument terms, sides, sizes and timestamps on both legs; correlation
does not supply a missing quote.

The study's twelve-minute event window is an observation choice, not an
invented duration for all market dysfunction. It was analyzed years later.
No underlying BrokerTec/TRACE book or synchronized hypothetical hedge orders
were downloaded here, so a tradeable spread and its execution costs remain
unknown. The chapter teaches source alignment rather than claiming a
profitable arbitrage from the reported yield movement.

### Example 3 — 7 October 2016: insufficient depth differs from expensive depth

The BIS Markets Committee's January 2017 sterling report analyzes the
7 October 2016 event using Reuters Matching and other evidence. Its
five-million-pound sweep-to-fill measure contains gaps where displayed
depth could not complete that quantity. Those gaps mean unavailable
full-size capacity, not zero cost. The report also distinguishes CME
futures pauses and price limits from spot-market behavior.

For clock context, the initial Reuters midpoint decline is reported over
00:07:03–00:07:11 BST, from 1.2600 to 1.2494. BST is UTC+01:00, so the same
interval is 23:07:03–23:07:11 UTC on 6 October. Both calendar labels refer
to one event. Those midpoint observations do not identify the price at
which a full five-million-pound order could execute.

This case motivates a strict missing-capacity state. A smaller order may
still have been possible, while a larger one required unavailable depth.
The report cautions about interacting mechanisms, platform differences and
later trade revisions; the chapter does not select a single cause. Raw
Reuters book messages and individual hypothetical queue positions are not
available here. Hoshi therefore cannot turn the reported rebound into an
exact stop/target fill or a guaranteed recovery trade.

## How to use it to HUNT a trade

Begin with an observable supported instrument and a valid, sufficiently
fresh book. Store the sequence anchor and source/arrival times alongside
the intended paper quantity. If the book is invalid, coverage insufficient,
quotes stale or the requested instrument unsupported, output `WAIT`.
A chart shape or historical analogy cannot repair missing execution data.

Freeze the proposal before evaluating it: which liquidity change matters,
how many valid observations confirm it, what cancels the idea, which price
could actually serve as a paper reference, and how costs/risk are bounded.
Keep chart geometry, executed flow and resting depth as distinct evidence
families with their source dependencies. Avoid double-counting several
views of the same update.

An eventual causal replay needs genuine ordered messages, deterministic
reconnect handling, point-in-time rules, conservative queue assumptions,
partial fills, fees and ambiguous-path outcomes. Evaluate untouched
chronological periods including ordinary markets, false alarms, rejected
sizes and zero trades. Export the missing-data and cost bounds instead of
inventing precise PnL or drawdown. Until independent calibration exists,
`win_probability` stays null. This source chapter completes neither that
replay nor the separate brain/strategy/API/UI integration and release gates.

## Sources

Primary materials actually checked on 28 October 2026; brief paraphrases
support the stated observations, with original execution analysis above:

1. Binance's official [Spot WebSocket specification and local-book procedure](https://raw.githubusercontent.com/binance/binance-spot-api-docs/master/web-socket-streams.md)
   and [current stream schema](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/ws-streams/~).
   Reviewed documentation, not a delivered or historically certified feed adapter.
2. [SEC Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders).
   Stock-order distinctions; other venues' rules require separate verification.
3. [CFTC/SEC staff findings, 30 September 2010](https://www.sec.gov/news/studies/2010/marketevents-report.pdf),
   executive summary and printed pages 14–15. Findings are attributed to
   staff; the Commissions did not adopt every conclusion in this document.
4. [Federal Reserve staff retrospective, 24 September 2020](https://www.federalreserve.gov/econres/notes/feds-notes/retrospective-the-agency-mbs-market-on-october-15-2014-20200924.html).
   Historical event window and source/price-type distinctions; no present quote.
5. [BIS Markets Committee sterling report, January 2017](https://www.bis.org/publications/sterling-flash-event-7-october-2016.pdf),
   especially printed pages 5–9. Reported midpoint, venue and fixed-size
   depth-shortfall evidence; underlying order-book messages are not bundled.

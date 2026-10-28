# COT positioning, report families and information arrival

Status: bounded source research checked on **28 October 2026, Asia/Karachi**.
This is an expandable curriculum chapter, not a live position feed, trained
model, completed runtime loader or profitable strategy. Three historical Gold
position comparisons below are reproduced from the CFTC's public reporting
API. A position-date label, a publication date and a system receipt timestamp
are different facts. Missing original publication times remain missing.

## What is it?

The Commitments of Traders reports describe aggregate open positions in
specified derivatives markets. They do not identify individual customers or
show where today's resting stops sit. The CFTC explains that reports generally
cover Tuesday open interest in markets with at least twenty traders meeting
reporting thresholds. Legacy reports distinguish commercial, noncommercial
and nonreportable positions, with additional spreading fields. This is a
classification of reported holdings, not a league table ranking intelligent
and unintelligent traders. Nonreportable does not establish that every holder
is a small retail speculator. [1]

Choose a report family before interpreting a number. The physical-commodity
Disaggregated report separates producer/merchant/processor/user, swap dealer,
managed money and other reportable categories. A swap dealer can offset risk
created elsewhere; its futures position alone does not describe the final
customer's economic exposure. Legacy noncommercial is therefore not an alias
for Disaggregated managed money. Classification can change and concerns the
trader, rather than proving the purpose of each trade. [2]

Financial-futures TFF categories are dealer/intermediary, asset
manager/institutional, leveraged funds and other reportables. A dealer's
sell-side business role does not mean its reported futures position must be
short. TFF is not simply the Legacy financial report split into smaller
subcategories: a TFF category can draw traders from either Legacy group.
Spreading, cross-market hedging and changing classifications complicate any
story that treats one group's net short as a standalone directional bet. [3]

This chapter deliberately uses **Legacy, futures only, Gold, market code
088691, Commodity Exchange Inc.** All-maturity aggregate positions are not a
single expiring GC contract, an XAUUSD broker feed, a gold ETF or worldwide
bullion inventories. Futures-and-options-combined records require their own
option-equivalent interpretation; the calculations here never substitute
those records for futures only. Counts are contracts, not dollars invested.

## Why does it form?

An open futures contract connects a long and a short. Positions can persist
while prices move and can disappear when offset. Transactions during a week
are not identical to the difference between two weekly position snapshots.
A participant can open and close substantial exposure between Tuesdays
without leaving a large endpoint change. That makes a weekly difference an
inventory comparison, not a direct measurement of buying pressure, executed
volume, leverage or bank transfers.

For the specific Legacy fields retained here, let L and S be noncommercial
outright long and short counts, P their spreading count, C the corresponding
commercial fields and N the nonreportable fields. The retained records
reconcile both sides independently:

- Long-side open interest = L + P + C_long + N_long.
- Short-side open interest = S + P + C_short + N_short.
- Noncommercial net = L minus S; net share = 100 times net divided by open
  interest, with the share undefined when the denominator is zero.

Spreading contributes to both sides of this accounting and cancels from the
net. Adding category nets produces zero across the complete retained market;
that identity is not evidence that every participant has equal risk or that
price cannot trend. One holder may hedge an unobserved cash asset, another
may maintain an outright position, and their collateral constraints can be
very different. Those exposures are not recoverable from these columns.

The weekly delta also has two components. Net can rise because long exposure
increased, because shorts fell, or because both changed at different speeds.
A positive net change cannot be labelled new long buying without inspecting
both gross columns. Similarly, a rising net/open-interest share can occur
while the actual net contract count falls, if total open interest contracts
faster. The actual 2020 and 2024 cases below demonstrate that denominator
problem; it is not a hypothetical warning detached from the records.

Publication creates a second mechanism: an information set becomes available
after its measurement date. The normal CFTC schedule is 15:30 Eastern on
Friday for the prior Tuesday, subject to exceptions. Eastern is a civil time
zone with daylight-saving changes, not a permanent UTC offset. A schedule is
not proof that a particular historical file arrived exactly on time. [4]
A causal model must distinguish measurement, publication, correction,
retrieval and its own ingestion. Downloading a past row today supplies none
of those missing original receipt timestamps by itself.

## Application zone

COT is useful as a slow context variable when market identity, family,
measurement date and availability are all explicit. It can help ask whether
a proposed paper setup agrees with a recent exposure change or depends on a
crowding hypothesis that the available sample cannot support. It is poorly
suited to locating an intraminute entry on its own. Weekly inventory supplies
neither a fresh tradable quote nor a stop distance.

Build the smallest defensible research record before creating a feature.
Keep contract-market code as a string, the publisher's exact field names,
futures-only versus combined, long/short/spreading counts and open interest.
Store the original response body and digest. Reconcile the two open-interest
identities; reject duplicate dates and negative or fractional contract
counts in this selected dataset. Do not turn a missing field into zero.
Names can change, so identity should not depend solely on display text.

Define any normalization before looking at an outcome. Raw net, net divided
by open interest, a rolling rank and a rolling z-score answer different
questions. A rank needs a stated past-only window, minimum sample size,
handling of ties and missing weeks, and a consistent classification history.
Two selected weekly observations cannot establish an all-time extreme.
A zero standard deviation makes a z-score undefined, not infinitely strong.
These requirements are proposed research controls; no rolling-position
signal or performance estimate is delivered by this chapter.

Availability should be conservative and separately versioned. A documented
publication date without a verified time can support a date-level audit, but
cannot safely authorize a same-day intraday trade. Keep original and corrected
vintages distinct. For a future backtest, decide whether features use the
first accessible vintage or a later revision, and justify the choice. The
CFTC's explanatory material discusses historical classification backcasting;
retrieved classifications should not be assumed to reproduce every original
contemporaneous belief. [2][3]

## Failure zones

The commonest serious failure is attaching Tuesday positions to Tuesday price
bars as if the public already knew them. A second failure is mechanically
adding three calendar days to every report date. Holidays and exceptional
outages make that rule unreliable. During the 2023 ION disruption the CFTC
published delayed reports in sequence; the actual notice below is stronger
evidence than an earlier intention to resume publication. [5]

Another failure is inferring a trap from a category name. Reportable shorts
can hedge different assets or exposures. There is no customer-intent label,
order-book queue, stop map or evidence of deliberate retail targeting in the
selected records. A contrarian theory needs an observable definition and
counterexamples. "Commercials short, therefore price must fall" is not such
a definition and cannot establish causation.

Family switching is especially damaging. Combining Legacy noncommercial
history with a recent managed-money observation changes the measured
population. Mixing futures-only open interest with combined category counts
breaks the denominator. Combining gold contract counts with currency or oil
contract counts ignores different units and exposure. A change in dollar
notional would require verified contract specifications, compatible prices
and valuation times; those are absent here. Net counts also hide substantial
gross exposures and the distribution across individual holders.

Finally, a selected event sample cannot calibrate accuracy. None of the three
cases measures gold-price reactions, entry fills, slippage, fees, drawdown or
account returns. There is no independent evaluation set. A story connecting
a weekly change to a crisis headline remains a hypothesis until supported by
appropriately timed and independently tested evidence. No trading pattern
works 100%, and this chapter assigns no win probability.

## Three real historical examples with dates

### Example 1 — 3–10 March 2020: net contracts fall while normalized share rises

The first exact query returns Gold Legacy futures-only positions for the two
Tuesday labels **3 March and 10 March 2020**. Open interest declines from
**691,985 to 633,470 contracts**, a reduction of **58,515**. Noncommercial
longs decline from **366,173 to 336,290**, while shorts decline from **46,440
to 36,759**. Calculated net therefore declines from **319,733 to 299,531**,
a change of **minus 20,202 contracts**. Both gross sides contract; describing
the entire change as newly opened short positions would contradict the
retained endpoint columns. [6]

Yet net share of open interest rises from approximately **46.2052% to
47.2842%**. The denominator contracts proportionally faster than the net.
A feature using raw net change and one using normalized share could disagree
without either arithmetic calculation being wrong. Their economic meanings
must be specified before a rule scores confluence. Noncommercial spreading
also declines by **31,295**, illustrating another substantial change that a
net-only narrative would omit.

The normal-calendar expected publication date for the later row is **13 March
2020**. An actual historical release timestamp and first-arrival record were
not obtained, so the receipt leaves actual publication date and time unknown
rather than certifying that schedule. The API's midnight-formatted report
field is a position-date label, not a gold-price timestamp. This example
measures inventory accounting only: it establishes no contemporaneous gold
return, liquidation cause, executable short or profit.

### Example 2 — 31 January 2023 report, published 24 February: stale information is a real constraint

The second query compares **24 and 31 January 2023**. Open interest falls from
**499,927 to 471,642**. Noncommercial longs rise from **253,311 to 256,417**;
shorts also rise, from **95,638 to 96,136**. Net increases from **157,673 to
160,281**, or **2,608 contracts**. The increase is the difference between
**3,106 additional longs and 498 additional shorts**, not a uniform movement
by every trader. Net/open-interest share rises from approximately **31.5392%
to 33.9836%**. [6]

The CFTC's **24 February 2023** historical announcement explicitly says it is
issuing the report originally scheduled for **3 February**, after the ION
incident prevented timely and accurate submissions. That establishes a
**24-calendar-day** gap from 31 January's position date to publication and a
**21-calendar-day** delay from the originally scheduled release. The notice
also identifies adjustments in certain other markets. It does not establish
that today's retrieved Gold rows are identical to their first published
vintage, and this chapter makes no such claim. [5]

Those dates create an auditable information barrier. A replay must not use
this report on 3 February simply because it normally would have been a
Friday release. Exact intraday publication and ingestion times remain
unknown even on 24 February. No price reaction around either date was
retrieved for this case. The result is **WAIT**, not a backfilled confidence
score attached to an earlier chart. The useful historical lesson is the
failure of an assumed availability calendar, not a claim that the positioning
change predicted a particular subsequent gold move.

### Example 3 — 30 July–6 August 2024: simultaneous long and short reductions

The third Gold query compares **30 July and 6 August 2024**. Open interest
falls from **510,914 to 480,645**, a change of **minus 30,269**. Noncommercial
longs fall from **313,364 to 298,119** and shorts fall from **66,763 to
59,370**. Net falls from **246,601 to 238,749**, or **minus 7,852 contracts**.
The component changes are **minus 15,245 longs** and **minus 7,393 shorts**;
short reduction partially offsets the larger long reduction. Spreading falls
by another **5,725 contracts**. [6]

Normalized net nevertheless rises from approximately **48.2666% to
49.6726%**. As in the first example, shrinking open interest can make a
normalized measure rise while net contracts decline. A rule describing both
as simply "bullish COT inflow" would erase useful disagreement and invent a
cash-flow measurement. All category nets still sum to zero in both retained
rows, and both long- and short-side totals reconcile to published open
interest.

The normal expected release is **9 August 2024**, which is not independently
verified as an actual publication timestamp here. Neither the Tuesday label
nor a Friday schedule identifies the intraday point when HOSHI could have
acted. This comparison does not measure the **5 August** session separately:
it spans an entire weekly position interval. It cannot attribute changes to
that day's news, infer which traders closed risk first, or establish a
Gold/BTC/NAS100 correlation. Those would need additional synchronized and
permitted price and event data, plus a separate observation design.

## How to use it to HUNT a trade

Treat positioning as a question for a later validated strategy, not as a
standalone order. First resolve the exact instrument and report family.
Second, establish when the available vintage entered the information set.
If publication or arrival is unverified for the intended decision time,
return **WAIT** with the missing clock recorded. Do not manufacture a fresh
quote from a weekly report.

Next inspect gross components, net, spreading and open interest together.
Preserve disagreements between raw and normalized measures. If a crowding
feature is proposed, freeze its past-only window and evaluate it separately
from the price pattern; do not let a handpicked extreme define both the
feature and its success story. Price structure, liquidity and global-flow
features need their own genuine dated inputs. A later evidence-coverage
weight is not a calibrated chance of winning.

Only a supported observed price, spread, venue, timestamp, executable
instrument and bounded paper-risk calculation could supply a candidate
entry, stop or target. Actual fill assumptions, costs and adverse paths must
then be evaluated chronologically. None are present in these COT diagnostics,
so every receipt records **WAIT**, **win_probability=null**, and disabled
orders. Concise Roman Urdu when explanation is not requested: **"COT weekly
aur delayed data hai; verified publication aur current execution inputs ke
baghair WAIT."** Source prose is not model training or runtime knowledge.

Reproduction uses `scripts/v3_macro_evidence.py` and
`macro_observations_20261028.json`: exact selected-column API responses,
SHA-256 hashes, request/capture metadata, report identity checks, both
open-interest identities, gross/net deltas and the documented delay. A
zero denominator stays undefined; a wrong report family or malformed count
fails validation. These are original bounded accounting diagnostics, not a
complete COT trading system, causal market-impact study or licensed-price
history bundle.

## Sources

Links and the actual selected API responses were checked on **28 October
2026**. Wording is original; tables of contract counts are attributed to the
U.S. Commodity Futures Trading Commission. The CFTC web policy identifies
government information as public domain and asks for acknowledgement, while
excluding protected privately contributed material. The dataset metadata
returned no standalone license identifier; this receipt retains government
aggregate positions, not private market-price feeds. No CFTC endorsement is
implied. [7]

1. CFTC, [About the COT Reports](https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/cot_about.html): report population and Legacy fields.
2. CFTC, [Disaggregated Explanatory Notes](https://www.cftc.gov/MarketReports/CommitmentsofTraders/DisaggregatedExplanatoryNotes/index.htm): physical-market classifications, spreading, classification limits and historical backcasting.
3. CFTC, [Traders in Financial Futures Explanatory Notes](https://www.cftc.gov/sites/default/files/idc/groups/public/%40commitmentsoftraders/documents/file/tfmexplanatorynotes.pdf): financial categories and comparison with Legacy. The PDF's prospective 2010 wording is historical, not a new 2026 announcement.
4. CFTC, [Release Schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm): normal 15:30 Eastern rule and exceptions; not an actual arrival log for the selected historical rows.
5. CFTC, [Historical Special Announcements](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm), entry **24 February 2023**: actual delayed report issuance. Separate earlier intentions do not establish actual publication.
6. CFTC, [Legacy Futures Only dataset 6dca-aqww](https://publicreporting.cftc.gov/Commitments-of-Traders/Legacy-Futures-Only/6dca-aqww) and [API schema](https://publicreporting.cftc.gov/api/views/6dca-aqww.json). Full encoded three query URLs, raw responses and derived arithmetic are retained in the adjacent JSON receipt's `cot_cases`, captured on the review date.
7. CFTC, [Web Policy, Copyright](https://www.cftc.gov/WebPolicy/index.htm): source acknowledgement and scope limits.

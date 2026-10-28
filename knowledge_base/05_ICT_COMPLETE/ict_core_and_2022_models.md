# ICT core vocabulary and the 2022 model: attribution, chronology and evidence

## What is it?

ICT is a named teaching framework associated with Michael J. Huddleston's
Inner Circle Trader channel. Its vocabulary connects reference highs and lows,
directional movement, imbalances, retracements and selected trading hours.
Naming a framework identifies a source; it does not establish an exchange
mechanism or a measured trading advantage. This chapter introduces a bounded
2022 lesson and explains how Hoshi can turn an interpretation into an auditable
research question. It does not reproduce a mentorship, certify every ICT
concept, or imply the creator endorses Hoshi.

The original English captions of **2022 ICT Mentorship Episode 3** were retrieved
and checked against the creator channel. Public metadata dates its upload to
**26 January 2022, 03:00:03 UTC**; the opening narration refers to Tuesday,
25 January. At approximately 1:07 the speaker identifies a fifteen-minute
March 2022 E-mini Nasdaq-100 chart. These are different clocks: lecture context,
upload time, instrument contract and chart timeframe. Hoshi has not inspected
the chart images or obtained that contract's historical execution feed here.
The cases below therefore use independently captured Binance Spot BTCUSDT
minute bars, not alleged reproductions of the speaker's trades.

Two source distinctions matter. Around 13:50–14:23, the lesson allows the
reference high to be exceeded without requiring a closing break, while the
subsequent imbalance needs its forming candle completed. Around 14:53–15:29,
it discusses consecutive down candles together as an order-block reference.
Hoshi's earlier first-close-cross and latest-single-opposite-candle rules are
stricter original adaptations, not verified equivalents. Around 35:33–36:20,
the lesson recommends inspecting intraday examples. These limited attributions
must not be expanded into an unsupported claim of exact creator-method parity.

## Why does it form?

A useful model separates a visible observation from the explanation attached
to it. A previous high is an observable statistic. Conditional orders might
exist around it, but candles do not disclose the owners, quantities, cancellations
or intent of those orders. An upward excursion can reflect aggressive buying,
thin offers, news, hedging, inventory adjustment or several causes together.
Calling that excursion a liquidity raid is a hypothesis requiring a defined
price path; calling it deliberate institutional trapping needs evidence that
this dataset does not contain.

An imbalance also has a precise visual and a much broader colloquial meaning.
For three completed candles A, B and C, Hoshi's diagnostic bullish gap requires
A's high to be strictly below C's low. Its bearish counterpart requires C's high
strictly below A's low. The middle candle can have traded throughout the region.
Thus the geometry does not prove an exchange-wide interval contained no trades,
nor that participants must return there. It records nonoverlap between the outer
candles. The distinction prevents a chart label from inventing order-book facts.

The middle candle's size may suggest a fast repricing relative to the chosen
sampling interval. That suggestion depends on the benchmark: a ten-dollar move
in quiet conditions and the same move during an announcement need not mean the
same thing. A displacement threshold must specify the prior completed sample,
normalization and comparison. Selecting the strongest-looking candle after
observing the reversal introduces hindsight even when the drawing is accurate.
This chapter's minute diagnostic deliberately tests only gap geometry and
clock eligibility; it does not quietly claim displacement, sweep or higher-frame
bias was also established.

## Application zone

Use the vocabulary as a sequence of falsifiable conditions. First identify the
instrument, venue, price type, interval and information cutoff. Next freeze a
directional hypothesis and reference levels from observations available by that
cutoff. Then define the excursion or structure change, the required imbalance,
an eligible future contact and invalidation. State whether a wick or a close
activates each condition. Changing from close confirmation to wick confirmation
changes both information time and the eligible population. They need different
rule versions and separate evaluation.

The offline evidence uses `hoshi-minute-gap-clock-1`. Each two-hour capture has
120 consecutive native one-minute bars, fixed UTC request boundaries and an
exact response-body digest. The feature becomes logically available only after
C closes: the receipt records the first millisecond after that close. It does
not assume the provider delivered it immediately. Actual publication and device
arrival times are unknown. A live implementation would need measured latency
and a freshness limit before authorizing even a paper entry.

For a clock-controlled teaching comparison, all three forming bars and the
earliest possible decision must fall within one selected New York hour. Those
hours are introduced from the separately attributed Silver Bullet material in
the following chapters; they are an explicit diagnostic filter here, not a claim
that every 2022 model uses them. The first eligible gap is selected in chronological
order, without looking at subsequent returns. The next five bars are an outcome
window. They cannot help select or modify the already frozen feature.

Within that future window, interval overlap is a contact. A full crossing of
the far gap boundary cancels eligibility before any same-bar closing rejection
can be counted. A partial contact that holds the midpoint can qualify as a
geometric retest only if its completed-bar decision remains inside the same
hour. This is a conservative original research convention. It is not an order,
an entry price, a fill or a complete ICT setup. Missing directional context,
liquidity targets, realistic costs and macro evidence keep every diagnostic
decision at **WAIT**, with `win_probability=null`.

## Failure zones

The first failure is a false equivalence between terminology and implementation.
Two tools can both display an order block while selecting different candles,
bodies or wicks, and can both label a structure shift with different confirmation
rules. A documentation comparison must expose those differences. A source hash
proves the local file has not changed; it does not prove a drawing matches the
creator's chart or that a rule predicts prices.

The second failure is time leakage. An unfinished C candle can erase its apparent
gap before closing. A pivot requiring future right-hand bars is unavailable at
the pivot itself. A retest that closes after the eligibility hour cannot be
silently assigned to the hour when it opened. The source capture, event time,
feature availability and evaluation horizon all need separate fields. Prefix
tests verify that appending later candles leaves the earlier feature unchanged.

The third failure is execution inference. A one-minute high and low reveal a
range, not the precise order of every trade. A limit-price touch may not fill
an order behind other participants. A stop may execute worse during a gap or
fast move. A short hypothesis on spot data also needs an actually supported
instrument and permitted exposure; it is not permission to create leverage or
borrow assets. Hoshi enables no real orders in this curriculum work.

The fourth failure is sample selection. Three illustrative windows and the first
gap in each cannot estimate the probability of a complete model. Multiple gaps
inside an hour share price history and are not independent trials. These dates
were chosen for teaching and have now been examined. They cannot later be
presented as untouched validation. A future chronological study must retain
absent formations, missing feeds, invalidations, costs and zero-trade periods.

## Three real historical examples with dates

All prices below are USDT per BTC on **Binance Spot BTCUSDT**, not NQ futures,
NAS100 CFDs or an executable cross-market quote. Raw bars and replayable
calculations are in `ict_intraday_observations_20261028.json`. The three captures
were retrieved on 28 October 2026 at approximately 01:59 UTC. Their event dates
are 2023 and 2024; retrieval in 2026 does not create point-in-time arrival logs.

### Example 1 — 15 May 2023: first bearish gap crosses immediately

The observation covers 06:30–08:30 UTC. The first eligible bearish formation
uses A opening at 07:01 UTC, B at 07:02 and C at 07:03. A's low is **27,460.71**
and C's high **27,457.05**, defining a gap of **3.66**. At the earliest decision,
07:04 UTC, New York local time is **03:04 EDT**, not 02:04 on a fixed winter
offset. The following minute reaches **27,469.34**, beyond the bearish far
boundary. First contact therefore also invalidates the gap under the original
full-cross rule. No eligible rejection is credited.

The fifth following close is **27,474.10**, compared with C's **27,454.62**.
The raw close change is about **+0.07095%**, adverse to a simple short narrative.
It is not a realized loss: there was no authorized trade, observed execution,
position size or cost model. The important lesson is that an accurately timed,
correctly calculated formation can fail at its first subsequent contact.

### Example 2 — 5 January 2024: rising prices without a retest

This capture spans 14:30–16:30 UTC. A opens at 15:00 UTC, B at 15:01 and C at
15:02. A's high **43,581.39** is below C's low **43,610.00**. The bullish gap
is **28.61** wide and becomes logically available after C at **15:03 UTC /
10:03 EST**. None of the next five candles overlaps that gap. The lowest of
those five is **43,619.34**, still above its upper edge.

The fifth close **43,699.99** exceeds C's **43,659.80** by about **0.09205%**.
An entry based on a future gap contact did not occur within the declared horizon.
Counting this rising endpoint as a successful filled long would give credit
for a price never observed after eligibility. The result remains no contact,
unknown fill and null strategy PnL. A larger horizon would be a different
experiment and must not be chosen merely to improve this case.

### Example 3 — 8 August 2024: rejection-looking close after invalidation

The capture spans 17:30–19:30 UTC. A, B and C open at **18:05, 18:06 and
18:07 UTC**. Their bearish gap extends from **59,445.71** to **59,454.37**.
The earliest decision is **18:08 UTC / 14:08 EDT**. The 18:08 candle does not
contact the zone. The 18:09 candle reaches **59,455.00**, crossing its far
boundary, and then closes **59,429.82**, below the zone.

A screenshot emphasizing only that lower close could suggest a clean rejection.
The declared lifecycle instead records first-contact full crossing, so the
candidate cannot be revived by its later close. The five-bar endpoint is
**59,437.99**, versus C's **59,425.66**; the small positive raw change is not
strategy performance. No claim connects this BTC path causally to a lecture,
announcement or institutional plan. The case demonstrates why intrabar extremes
and explicit invalidation priority matter even when a closing candle looks neat.

## How to use it to HUNT a trade

Start with a paper research record, not a directional command. Save the supported
symbol and actual source times, then freeze the proposed bias, reference and
rule version. Require each subsequent condition to become known in order. If
an original lesson leaves a discretionary choice, record it as unresolved or
define an original convention before evaluation. Do not silently fill it using
the outcome. Keep an invalidation event irreversible for that candidate.

Only after context, chronology and an actual reachable entry are established
should sizing be considered. Use a bounded hypothetical loss budget, a valid
price increment, observed spread where available and conservative cost estimates.
If these cannot be established, report WAIT and the exact missing input. A
candidate's descriptive evidence coverage is distinct from the chance of winning.
No weighting of attractive labels turns an untested hypothesis into 92% accuracy.

For Jano, routine output should remain concise and in the existing Hoshi style:
supported pair, WAIT, source time and one short missing-evidence reason. Teach
this longer source comparison only when asked. That product behavior remains
an integration requirement; this chapter and its offline receipts are source
material, not model training or a delivered runtime trading engine.

## Sources

- [Original 2022 ICT Mentorship Episode 3](https://www.youtube.com/watch?v=nQfHZ2DEJ8c): original English captions and public creator-channel metadata checked 28 October 2026 via vidIQ. Selected times are described above; full captions and unviewed chart images are not republished.
- [Original Silver Bullet time-based lesson](https://www.youtube.com/watch?v=tRq1hyGGtl4): original captions and creator-channel publication metadata checked; source for the explicitly separate hour filter, detailed in its own chapter.
- [Binance Spot kline API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary schema checked, including open/close times, UTC request boundaries and twelve response fields.
- [Binance public-data repository and license](https://github.com/binance/binance-public-data): primary attribution/license checked during the preceding evidence work. Binance-derived observations remain CC BY-NC-SA 4.0 noncommercial research material; unrelated code is not relicensed.
- [Python IANA zoneinfo support](https://docs.python.org/3/library/zoneinfo.html): primary timezone conversion behavior checked; actual historical offsets are replayed using America/New_York.

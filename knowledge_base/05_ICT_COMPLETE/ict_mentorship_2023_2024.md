# Reading the 2023 and 2024 ICT material without rewriting history

## What is it?

An annual mentorship label is an edition identifier, not a standardized exchange
specification. The same speaker can explain related ideas with different chart
contexts, instruments, examples and discretionary choices. Hoshi needs a source
map that keeps those versions visible. This chapter examines two accessible
original publications: the 2023 Silver Bullet lesson and **2024 Mentorship,
Lecture 4, August 8**. It offers original analysis of how to preserve evidence
and test those ideas. It does not claim to transcribe or comprehensively cover
every lesson released in either year.

The original creator-channel metadata dates the Silver Bullet upload to
**14 May 2023, 21:00:19 UTC**. Its captions frame opportunities around specified
New York hours and distinguish a potential price objective from the distance
actually captured by a trade. The 2024 lecture was published **8 August 2024,
14:34:48 UTC**. In the selected 8:16–13:07 passage, the speaker discusses day
and week opening-gap references, their midpoint and an approaching 08:30 event.
These are brief source attributions, not proof of the proposed mechanism.
Captions were checked; chart visuals, exact historical quote feeds and the
speaker's actual execution records were not obtained.

A year stamp does not confer measured accuracy. A later video can illuminate an
older example, but a researcher cannot give a simulated historical decision
access to a rule published afterward while calling that decision prospective.
The publication time is one necessary boundary. It is not a precise archive of
when every viewer could access a caption, when a stream first aired, or when a
trader understood the method. Hoshi records these unknowns instead of assigning
a convenient availability timestamp.

## Why does it form?

Several distinct processes can make time and reference prices relevant. Trading
activity can vary around market openings, scheduled releases and handovers
between regions. A session boundary can change which participants are active.
Different venues can pause at different times, leaving a measurable difference
between the last price before a break and the first afterward. A trader may
also choose an intraday clock as a research convention. These observations do
not demonstrate that one algorithm predetermines every subsequent path.

An opening gap must therefore name its construction. Which contract and venue
closed? Which price type was last observed? When did trading resume? Are there
roll adjustments, settlement-versus-trade differences or missing prints? Its
midpoint is arithmetic once both endpoints are known; neither endpoint can be
borrowed from another feed without creating a new variable. A twenty-four-hour
spot market's arbitrary clock boundary is not automatically equivalent to a
futures trading break.

The same discipline applies to narrative updates. If an early model emphasizes
a structure shift and a later lecture emphasizes opening references, the
researcher needs to decide whether the latter is an additional required gate,
an optional descriptive feature, or an alternative strategy. Quietly treating
it as whichever interpretation would have worked on a historical chart creates
a moving target. A rule that changes after every losing example has no stable
population over which performance can be measured.

## Application zone

Create a versioned source record before creating a signal. Save the original
URL, title, creator channel identifier, publication timestamp, caption language
and digest of the retrieved track. Specify the passages actually examined.
Full captions need not be redistributed to provide that audit trail. Automatic
caption errors and references to unseen drawings must remain explicit. If a
number, line or symbol depends on a chart that was not inspected, do not infer
it from surrounding speech.

Keep three layers separate. The source layer records what an original lesson
said. The hypothesis layer chooses an original operational rule and its permitted
inputs. The evidence layer records the actual observations and later outcomes.
None of these alone is a trained model. A chapter hash cannot stand in for a
runtime loader, a source publication cannot stand in for a valid price feed,
and an attractive price path cannot stand in for an executable trade.

For the three examples here, Hoshi freezes an intentionally simple **prior
thirty-minute envelope** immediately before a selected hour. Its low and high
come only from those thirty completed native minute candles. Their average is
the midpoint. This is `hoshi-prior-thirty-minute-envelope-1`, an original
diagnostic reference, explicitly **not** a day/week opening gap, official opening
range, complete mentorship model or inferred institutional inventory.

The following sixty bars are an observation window. Record its open, extrema,
last close and the first bar exceeding each frozen boundary. An excursion's
bar interval is known; its precise intrabar trade time is not. Do not use the
hour's eventual low or high to choose an earlier directional bias. In these
receipts the bias remains null. A complete research hypothesis would need a
separately frozen reason to favor one side and a counterfactual that can fail.

Source-date control also matters when comparing editions. A January 2024 example
may test a rule available in May 2023. It cannot honestly be called a prospective
test of an August 2024 lecture. A replay can apply that later rule retrospectively,
but it must identify the change and use a later untouched period for validation.
Historical terminology and model development dates are features of the experiment,
not decorative footnotes.

## Failure zones

**False completeness:** two lessons do not contain all content of two years.
The chapter's release scope is the source comparison and evidence discipline
described here. Remaining lectures, visual chart details and any original
licensed study materials are not claimed obtained. Future additions must name
their sources and expand the manifest when they add a genuinely missing topic;
they cannot silently redefine an edition as fully ingested. Detailed day/week
session-opening-gap rules and actual session endpoints are a separate pending
chapter explicitly added in manifest scope revision 3.

**False cross-market equivalence:** BTCUSDT spot, an E-mini contract, an equity
index and a broker's NAS100 CFD have different sessions, units, financing and
execution conditions. The raw observations here support only their actual
venue. They cannot prove an index-point objective, a forex pip target or the
availability of a short position. No synthetic quote is manufactured for an
unsupported symbol.

**False calendar context:** a caption's reference to an employment release is
not the original release, its revision history or a point-in-time surprise
series. A future news feature requires the issuing institution, scheduled and
actual release timestamps, actual versus contemporaneously expected values,
revisions and a measured reaction window. None of those values is reconstructed
from a retrospective trading story in this chapter.

**False causal certainty:** an envelope excursion proves a level was exceeded
on this feed. It does not prove that stop orders were targeted, that banks
coordinated a trap, or that a later reversal was caused by that excursion.
Confounding events and ordinary price variation remain possible. Distinct
wording in two editions may reflect teaching style rather than a new mechanism.

**False evaluation independence:** the three windows below reuse the 360 bars
introduced in the preceding chapter. Different features do not create 360 new
observations, three new independent trials or an untouched holdout. This
explicit reuse supports an audit of alternative interpretations. It cannot
increase statistical confidence merely by increasing the number of descriptions.

## Three real historical examples with dates

All observations are **Binance Spot BTCUSDT**, native one-minute bars, UTC source
boundaries converted to **America/New_York**. They were fetched on 28 October
2026 and retained with raw response hashes. Prices are USDT per BTC; the
sixty-minute outcomes are retrospective descriptions, not order fills or returns
from a funded account. The script replays both frozen features and outcomes.

### Example 1 — 15 May 2023: a source available before an adverse first gap

The 06:30–07:00 UTC pre-hour corresponds to **02:30–03:00 EDT**. Its frozen low
is **27,405.00**, high **27,544.10**, midpoint **27,474.55** and last close
**27,475.63**. During the following 03:00–04:00 New York hour, the low is
**27,387.53**, high **27,498.02**, and final close **27,407.48**. A first
below-envelope excursion appears in the minute opening **03:24 EDT**; that
bar is complete at the boundary before 03:25. No above-envelope excursion occurs.

The 2023 lesson's recorded upload precedes this event. That permits a source-date
comparison, but it does not prove this exact dataset and rule were used live.
The preceding chapter's first bearish gap invalidates at 03:04 despite the
hour later ending lower. Selecting the entire hour's endpoint to erase that
early invalidation would reverse the declared lifecycle. A correct broad
direction does not retrospectively create a valid entry or fill.

### Example 2 — 5 January 2024: a small excursion is not a quantified stop raid

The **09:30–10:00 EST** pre-hour has low **43,100.00**, high **43,800.00**,
midpoint **43,450.00** and last close **43,486.04**. The next hour opens at
**43,488.21**, ranges from **43,355.54** to **43,801.10**, and closes
**43,500.01**. Its first above-boundary bar opens **10:11 EST** and is known
completed just before 10:12. There is no below-envelope excursion in that hour.

The high exceeds the frozen reference by only **1.10 USDT**. Whether any stops
were triggered, and in what quantity, is unknown. The data contain no participant
identifiers or stop-order registry. The first eligible bullish gap also has no
five-minute retest. Neither a tiny boundary excess nor an upward endpoint
supplies that missing contact. This event predates the August 2024 lecture;
applying that lecture's ideas here would be explicitly retrospective.

### Example 3 — 8 August 2024: publication chronology does not fill feed gaps

The **13:30–14:00 EDT** pre-hour gives low **59,437.77**, high **59,821.12**,
midpoint **59,629.445**, last close **59,469.88**. The 14:00–15:00 hour opens
**59,469.89**, reaches low **59,317.89**, high **59,696.44**, and closes
**59,328.09**. The first minute already moves below the frozen low; its completed
bar is available no earlier than 14:01. The upper envelope is never exceeded.

The lecture's recorded upload at 14:34:48 UTC precedes this 18:00 UTC observation
hour. That does not identify an exact historical caption-access time or prove
the lecture's futures references apply to BTC. This capture has no original
day/week futures opening endpoints and no official release-surprise series.
The missing inputs stay missing. The first bearish gap's later full crossing
also remains invalidated even though the hour ultimately closes lower.

## How to use it to HUNT a trade

Choose an edition and a finite rule before scanning. Enumerate required inputs,
their timestamps and supported instruments. Distinguish a frozen reference from
an interpretation and an entry condition from a later favorable excursion. For
an opening-gap strategy, obtain the actual specified contract's close/reopen
observations; if unavailable, WAIT rather than replacing them with spot-bar
boundaries. For a time model, use historical timezone conversion rather than
the device's current offset.

Write a counterexample alongside the hypothesis. A candidate may fail because
the reference is absent, direction was never justified, price never retraces,
an invalidation comes first, costs consume the possible move, or source data
arrive too late. Those failures belong in the denominator. Freeze parameters
before a chronological evaluation, separate overlapping events and preserve
negative as well as zero-trade periods. Any subsequent rule revision restarts
the validation question rather than repairing the earlier result.

Hoshi's eventual concise response can state the pair, WAIT and the exact absent
feature without teaching an unsolicited history lesson. It must not conceal
uncertainty behind a percentage. The requested weighted score will describe
evidence coverage; a win probability remains null until independently calibrated.
This source comparison is a curriculum delivery, while retrieval, strategy,
paper replay and final release integration remain separate pending work.

## Sources

- [Original 2023 Silver Bullet lesson](https://www.youtube.com/watch?v=tRq1hyGGtl4): original English captions and creator-channel public metadata checked 28 October 2026; upload timestamp, not an inferred event date, recorded in the manifest.
- [Original 2024 Mentorship Lecture 4, August 8](https://www.youtube.com/watch?v=hdSscxZgE58): original English captions and creator-channel metadata checked; selected opening-gap/calendar passages only, without chart-view or complete-edition claims.
- [Binance Spot kline schema](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary twelve-field schema and UTC request-time semantics checked; exact request URLs and response bodies are in the adjacent JSON evidence.
- [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html): primary timezone support checked; frozen UTC observations are converted with America/New_York, including historical daylight-saving offsets.

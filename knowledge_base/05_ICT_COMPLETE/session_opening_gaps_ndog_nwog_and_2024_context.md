# Day and week opening gaps: historical clocks, endpoint identity and evidence

> **INCOMPLETE DRAFT — 28 October 2026, Asia/Karachi.** This file is excluded
> from source-checked completion and runtime use. The three dated cases below
> document schedule changes and an actual sample audit. They are **not** the
> three verified, priced NDOG/NWOG chart cases still required for completion.
> Historical calendars, complete adjacent-session endpoints, point-in-time
> availability and applicable data permissions remain outstanding.

## What is it?

A new day opening gap, abbreviated NDOG in this curriculum, compares a
specified price before a trading-day closure with a specified price after
the next session begins. A new week opening gap, NWOG, compares the final
session of a defined exchange week with the first session of the next.
The definition needs a venue, exact instrument, price type, calendar version
and endpoint selection rule. A label on a chart does not supply those inputs.

For a proposed Hoshi research convention, let the two eligible executed-trade
prices be `p_before` and `p_after`. The signed difference is
`p_after - p_before`, the width is its absolute value, and the midpoint is
`(p_before + p_after) / 2`. These are original arithmetic definitions for
a future diagnostic, not proof of the creator's complete discretionary
model. The midpoint might fall between valid ticks. Any later executable
price would need an explicit rounding rule and actual venue observations.

Equal endpoints describe a zero price difference despite an interruption in
trading. They do not establish a zero spread, risk-free entry or absence
of news. A missing endpoint instead makes the gap and midpoint unknown;
it must not become zero. A negative futures price is not automatically an
invalid number merely because a particular historical equity-index sample
contains positive prices. Validation must use the identified instrument's
rules and distinguish finite numerical values from usable observations.

An opening gap differs from a three-candle fair-value-gap construction.
The former depends on a session interruption and the endpoint convention;
the latter compares chosen candle ranges. A daily candle's open and close
may represent a vendor convention, a settlement field or an adjusted
continuous series. None is automatically the last or first executed trade
required by this chapter. A twenty-four-hour spot-market clock split is
also a separate variable, not a substitute for a verified exchange break.

The existing annual-source chapter records a bounded review of the original
**2024 Mentorship Lecture 4, 8 August**, including selected opening-gap and
midpoint discussion. Its caption digest and creator metadata remain in the
manifest. That earlier check is reused explicitly; a fresh direct YouTube
page attempt in this review failed. No new chart inspection, full-edition
coverage or speaker-execution verification is claimed. [4]

## Why does it form?

A closure prevents continuous execution on the named venue during the
defined interval. Participants can receive information, change desired
positions or observe other markets while that venue is unavailable. When
trading resumes, the first eligible transaction can differ from the earlier
one. This is a possible economic explanation, not an identified cause of
any particular gap. A schedule change can also change the measured gap
without changing the trader's conceptual vocabulary.

Data construction creates additional explanations. Switching delivery
months can introduce a calendar-spread component. Selecting a settlement
instead of a last trade changes the reference price. A missing packet or
an incomplete sample can leave an apparent interruption that the exchange
never scheduled. Each mechanism produces different evidence requirements.
Calling all of them a liquidity hunt would replace measurement with an
unverified story about institutional intent.

The claimed tendency to revisit a gap or its midpoint must remain a
hypothesis. The market might return immediately, continue away, cross the
entire interval, or fail to trade at the proposed entry. A later touch
does not establish a fill or show that holding an earlier losing position
was acceptable. No pattern works 100 percent, and the presence of a
midpoint cannot calibrate a winning probability.

Weekly comparisons need particular care. A holiday can change the last or
first scheduled session, and an exchange trade date can differ from the
civil date printed in a UTC timestamp. A weekly boundary should come from
the relevant historical calendar rather than a permanent assumption that
Monday midnight UTC begins every instrument's trading week. Expiration
and delivery identity must remain fixed across the comparison.

## Application zone

Begin with a source map. Separate the exchange calendar, the creator's
chosen analytical convention and the market-data provider's actual fields.
Record which version applies and the date when the information became
available. An exchange announcement can establish a planned change without
establishing every later exceptional session. A current trading-hours page
cannot silently supply an old calendar.

For a daily candidate, retain the expected closure and reopening as
timezone-aware boundaries. Identify the last eligible executed-trade record
before the closure and the first eligible executed-trade record after
reopening in the same exact contract. Preserve exchange security identity,
delivery month, source precision and record sequence semantics. Complete
coverage, corrections and any missing segments must be assessed before
those observations can be called the actual session endpoints.

An opening marker without a trade quantity is not enough to infer an
executed fill. A volume-only message cannot provide a traded price. Nor
does receiving an entire HTTP response demonstrate that a published
part-file includes every adjacent session or correction. The retained
offline ES sample audit illustrates these distinctions; it is not a live
adapter or a completed opening-gap detector. [3]

If valid endpoints eventually exist, freeze the chosen reference after
the reopening observation is received and validated. A historical decision
cannot know the opening endpoint before it arrives. Keep the observation
timestamp, later capture timestamp and original delivery evidence separate.
A dataset downloaded today can support descriptive historical research
while still lacking the point-in-time arrivals needed for causal replay.

Specify outcomes before viewing later prices. Distinguish first boundary
contact, midpoint contact, full interval crossing and no contact within
the declared horizon. A final observation beyond the gap does not establish
the path through it. Missing bars, ambiguous ordering and censoring should
remain explicit. Use a fixed retirement rule so a researcher cannot choose
whichever revisit makes a historical example look successful.

The appropriate first application is therefore bounded paper research.
Each candidate needs an auditable endpoint pair and a subsequent observation
window, with costs and executable-price assumptions handled separately.
The new chapter must not count three expiry groups, three clock labels
or three documents as three completed priced gap examples.

## Failure zones

Clock substitution is an immediate failure. A modern close applied to an
older schedule can select the wrong final observation. A maintenance end
can be mistaken for the start of trading, while a pre-open phase may permit
different activities from an executable market. Changing the timezone
label without converting the instant creates another error. Historical
daylight offsets must be evaluated for the particular date.

Instrument substitution is equally serious. An ES calendar spread is not
an outright ES contract, and a March-to-June roll is not automatically
an overnight gap in one contract. Cash indices, index futures and a broker's
similarly named contract do not become interchangeable because they
share an underlying index. A source should retain unsupported symbols
as unsupported rather than invent a NAS100 entry from a different feed.

Endpoint substitution can hide missing evidence. Settlement, last quoted
bid, last traded price and vendor daily close answer different questions.
An incomplete snippet might contain plausible records on both sides of a
break without certifying that they were the true final and first prints.
The absence of a record is not proof of a scheduled closure, and a digest
only preserves the bytes actually captured.

Later revisions also matter. Sorting a final corrected tape into event
time can introduce information unavailable to the original decision.
Conversely, a sequence counter spanning interleaved contracts may appear
to regress even though that observation alone establishes no feed fault.
The researcher must document the counter's scope instead of treating a
single numerical order as a universal causal timeline.

Finally, retrospective selection can manufacture an attractive story.
Searching many gaps and highlighting only midpoint revisits ignores
unfilled entries, continued departures and losing paths. Similarity with
an old chart does not identify the cause of a new move or establish a
calibrated probability. The present draft supplies no new strategy returns,
independent holdout sample, account drawdown or simulated execution result.

## Three real historical examples with dates

These are **documented historical context and source-quality cases**.
They do not satisfy the outstanding requirement for three priced opening-gap
cases. No price endpoints or market returns are invented for them.

### Example 1 — the 18 November 2012 schedule change, trade date 19 November

CME's **S-6465, dated 14 November 2012**, announces the new schedule beginning
Sunday **18 November** for Monday's **19 November** trade date. It separates
the **15:15–15:30 CT** pause from the **16:15–17:00 CT** closure and retains
the **15:15 CT** daily settlement determination. The notice therefore does
not make settlement and the later trading close equivalent. [1]

As an original timezone calculation, **19 November 2012, 16:15 CT** maps
to **22:15 UTC**, and **17:00 CT** maps to **23:00 UTC** using
`America/Chicago` on that date. These are schedule-boundary conversions,
not observed transaction times. Notice date, effective civil date and
exchange trade date are separate fields. No claim is made that the current
researcher possessed the notice in 2012, or that every intervening schedule
exception has been reconstructed. Actual endpoint prices and later reaction
data for the new regime are missing here; the research decision stays WAIT.

### Example 2 — the 21 September 2015 earlier close

The CME Globex notice dated **14 September 2015** states that, effective
**21 September**, maintenance would begin at **16:00 CT**, earlier than
**16:15**, and run until **16:45** Monday through Thursday. It also advances
the listed markets' weekday closes to **16:00 CT** and says normal product
opening times remain unchanged. [2]

For **21 September 2015**, **16:00 CT** converts to **21:00 UTC** under that
date's daylight offset. The maintenance end converts to **21:45 UTC**.
Neither conversion proves a first executable transaction at maintenance
end. The announcement needs to be combined with the applicable product
schedule and actual records before constructing an endpoint pair. Applying
the later close to older data would change the selected reference by
fifteen minutes. This is a demonstrated calendar-definition risk, not
a measured gap size or profitable trade. No full historical session or
holiday calendar is certified from these two notices alone.

### Example 3 — the 11–12 March 2025 ES sample, captured 28 October 2026

The retained metadata receipt describes one primary ES v2 part-file:
**839,644 rows**, including **825,930 TRD** and **13,714 VOL** records.
The audited usable outright groups are **ESH5, ESM5 and ESU5**, with their
security IDs and delivery months retained separately. Six TRD/O records
without quantity are quarantined; no quantity or fill is imputed. The
underlying file's captured SHA-256 is recorded in the manifest. [3]

The parsed usable observations extend within the UTC interval beginning
**11 March 2025, 22:00** and ending **12 March, 20:59:59.445923749**.
This is a source-file observation bound, not a certified close/reopen pair.
The full HTTP body was captured **28 October 2026**, and its retained
digest was rechecked during this review. Original 2025 availability,
adjacent-session coverage and applicable publishing rights remain unverified.
Raw prices and the CSV are excluded from the repository. Three maturities
in this one part-file produce **zero certified gap cases**, not three
independent historical examples of the pattern or zero-trade performance.

## How to use it to HUNT a trade

The first hunt is for a qualifying observation, not a direction chosen from
a story. Select a supported exact instrument, verify its dated calendar
and obtain permitted source records. Resolve contract identity, endpoint
type, coverage and availability before calculating a gap. If any required
piece is missing, preserve the reason and return WAIT with null entry,
stop, targets and `win_probability=null`.

For a later eligible paper candidate, freeze the reference and specify its
expiry before considering a liquidity target or market-structure condition.
An isolated midpoint cannot replace the history, liquidity, structure and
global-flow requirements of the proposed V3 evidence score. Those future
40/20/20/20 weights will describe rule coverage, not a winning probability.
Historical resemblance cannot supply a missing current price or justify
an invented confidence value.

Record adverse and absent outcomes alongside contacts. If a window ends
before evaluation is possible, keep it censored. If a paper entry cannot
be resolved because of spread, gaps or within-bar ordering, preserve that
ambiguity rather than selecting a favorable fill. Export the endpoint
identities, calendar/source versions, decision clock, rejection reasons
and later observations needed to audit the result.

Default Hoshi output should remain concise in Roman Urdu and teach only
when asked. The present draft does not change that runtime behavior,
install retrieval, enable orders or alter privacy, voice and Stop controls.
Real orders, leverage, purchases and new paid infrastructure remain disabled.
Full source completion, bounded runtime integration and independent evaluation
are separate gates; writing this draft crosses none of them.

## Exact completion blockers

The manifest keeps this chapter in draft, outside the 49 source-checked
documents. Three genuinely dated **priced** NDOG/NWOG cases still need
verified same-contract pre-break last and post-break first trades, applicable
historical calendars and complete adjacent-session/correction coverage.
Original availability evidence and applicable data-use/redistribution rights
also remain unresolved. The three context cases above cannot be relabelled
as those missing observations to manufacture completion.

## Sources

Original prose and arithmetic. Primary exchange notices and data-layout
pages were actually opened on **28 October 2026**. The retained sample body
was fetched earlier that day and its digest rechecked; no raw market series
is redistributed. Current retrieval is not proof of original historical
receipt. Earlier creator-caption review is explicitly distinguished from
this review's unsuccessful direct YouTube fetch.

1. [CME Special Executive Report S-6465, 14 November 2012 — primary PDF](https://www.cmegroup.com/rulebook/files/ser-6465_Equity_Index_Futures_Options_on_Equity_Index_Futures_20121114.pdf), with [notice/effective-date index](https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-6465.html).
2. [CME Globex Notices, 14 September 2015 — Changes to Daily Maintenance Period](https://www.cmegroup.com/tools-information/lookups/advisories/electronic-trading/20150914.html).
3. [CME Time and Sales layout and sample table](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457223239/Time%2Band%2BSales), [the actual ES v2 part-file URL](https://www.cmegroup.com/files/download/xcme-tick-es-fut-20250312-part-00039-c000.csv) and the adjacent metadata-only `session_source_audit_20261028.json` receipt.
4. [Original 2024 Mentorship Lecture 4, 8 August](https://www.youtube.com/watch?v=hdSscxZgE58): reused earlier bounded caption/creator-metadata check, digest `08f9a65787563119b3ee69ed772a22c6ddb85ebe834b7862bd6b0bad4ff3045f`; no new transcript, chart inspection or full-edition claim.

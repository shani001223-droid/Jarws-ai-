# Killzones, Silver Bullet and Power of Three: clocks are conditions

## What is it?

A killzone is a named observation period in a trading framework. It limits when
a researcher looks for a setup; it does not create a setup by itself. Silver
Bullet is a more specific time-based ICT teaching model. Power of Three is a
separate narrative framework describing accumulation, manipulation and
distribution. Time eligibility, a price-path interpretation and an executable
entry are different variables. Hoshi must preserve that distinction instead of
giving a direction whenever the clock enters a familiar hour.

The original **London Killzone** captions identify **02:00–05:00 New York
time** around 1:36–2:39. The original **New York Killzone** lesson names
**07:00–09:00 New York time** around 1:00. Both public creator-channel uploads
are dated **9 December 2017**. These are source-specific classic Forex
definitions. Hoshi must not replace them with a wider interval remembered from
another course, or automatically extend their scope to every instrument.

The original 2023 Silver Bullet lesson identifies three New York hours:
**03:00–04:00**, **10:00–11:00**, and **14:00–15:00**. Around 11:14–11:45 it
distinguishes entry eligibility from a position's later exit. Its discussion of
possible objectives does not require that every trade capture the entire
framework range. Statements implying universal daily opportunity or high
probability are not adopted as measured facts. Those claims need a defined
sample, realistic execution and independent evaluation.

The original **2022 Mentorship Episode 9**, uploaded **16 February 2022,
01:30:28 UTC**, introduces Power of Three. Around 2:57 and 6:00–6:34, the
speaker describes a bullish opening reference, an initial lower excursion and
a later upward expansion; the example uses an 08:30 reference. That is brief
attribution. This chapter does not identify hidden accumulation or deliberate
manipulation from candles, nor treat every opening price as interchangeable.

## Why does it form?

Market activity need not be uniform through a day. Different participants have
different working hours, and scheduled events can concentrate attention around
a clock boundary. A time window can be a useful explanatory feature even if
its mechanism is uncertain. Testing that feature requires comparison with
neighboring hours, equivalent weekdays and different volatility conditions.
The existence of an active session does not prove that one particular gap or
retracement has positive expectancy after costs.

The Power of Three narrative is attractive because many completed candles have
an open, excursions on both sides and a close displaced from the open. After
the close, it is easy to label an early excursion as the false move and a later
one as the real move. Before the close, either can continue or reverse again.
An honest operational version must specify the anchor, permitted initial
range, excursion size, reclaim rule, confirmation and cancellation in advance.
Otherwise the phases are descriptions assigned using the answer.

Words such as accumulation and manipulation also carry stronger implications
than a price series alone supports. A narrow range can result from balanced
trading or low activity; it does not identify who is building inventory. A
boundary crossing can arise from ordinary buying, selling or repricing. To
allege coordinated trapping requires evidence outside OHLC bars. Hoshi may
record a failed excursion or an observed reclaim without inventing an owner,
intent or universal cause.

Time conventions themselves can generate misleading patterns. A chart whose
broker midnight differs from New York midnight constructs a different daily
candle and opening reference. A futures trading break differs from an arbitrary
spot-market midnight. A continuous contract can differ from the individual
expiring contract traded on that date. Replaying the wrong boundary can create
an apparently precise framework that was never available on the intended feed.

## Application zone

Store the clock as a named timezone, not a fixed offset or the phone's current
local hour. The offline diagnostic uses **America/New_York**, converting UTC
source timestamps through historical IANA timezone rules. January 2024 in these
cases uses UTC−05:00; May 2023 and August 2024 use UTC−04:00. The date and offset
remain visible in the evidence. Missing timezone data should fail explicitly,
not silently fall back to an hour that changes the selected population.

| Source-specific period | New York wall-clock interval | What it establishes |
| --- | --- | --- |
| Classic London Forex lesson | 02:00–05:00 | A source-defined study interval |
| Classic New York Forex lesson | 07:00–09:00 | A different source-defined study interval |
| Silver Bullet London hour | 03:00–04:00 | Time eligibility within the model |
| Silver Bullet morning hour | 10:00–11:00 | A separate hour, not the classic New York interval |
| Silver Bullet afternoon hour | 14:00–15:00 | Afternoon eligibility, not an automatic direction |

Hoshi's original minute-gap diagnostic treats these Silver Bullet hours as
half-open intervals: the start is included and the end excluded. All three
forming candles must start inside the same hour, and the earliest possible
post-C-close decision must still be inside it. Thus a C candle closing just
before 11:00 cannot authorize an entry at 11:00. Its formation may exist, but
this specified entry window has ended. The difference between a bar's opening
label and its decision time matters.

The diagnostic excludes weekends as an explicit original research convention.
That does not claim BTC spot is closed on weekends or reproduce every creator
rule. Holidays, early closes, exchange maintenance and contract-specific breaks
need their own verified calendar. A future futures implementation cannot assume
a weekday is automatically a normal trading session. Conversely, a crypto
experiment can deliberately include weekends, but that is a versioned change.

A candidate still needs direction, target, structure and a reachable risk plan.
After the gap forms, Hoshi observes the next five bars separately. Full crossing
of the far boundary takes priority over a same-bar closing rejection. A partial
contact must complete within the same eligible hour to count as the original
geometric retest. This is a narrow diagnostic convention, not a certified
Silver Bullet recognizer. All current receipts stay WAIT because complete
context and execution conditions are not supplied.

For a Power of Three experiment, freeze the chosen opening reference before
classifying the first excursion. Define how long the supposed initial phase
may last, what constitutes a material move, and when the hypothesis expires.
Keep a two-sided-expansion outcome instead of renaming the final favorable leg
as the only distribution phase. Do not derive a daily model from a two-hour
capture that lacks the required daily opening and later close.

## Failure zones

**The timing-only shortcut:** an eligible hour plus a three-candle gap does not
establish higher-frame bias, available liquidity targets, displacement, an
acceptable stop distance or favorable global-flow evidence. A timer must not
supply the other components of the requested weighted score. Missing components
remain absent even if a chart is visually persuasive.

**The timezone shortcut:** adding a constant five hours to UTC works for some
New York dates and fails for others. Local dates can also differ across regions.
Cross-region daylight-saving transitions do not necessarily occur together.
The label London describes the source's model; its stated New York clock should
not be replaced by an assumed fixed London opening hour.

**The boundary shortcut:** an apparent gap before C completes can disappear.
A touch inside a window can have its confirmation close outside it. An exit
may occur later if a separately defined trade was validly entered, but that
does not extend the permitted entry time. These distinctions should be unit
tested with synthetic clock boundaries and checked against real timestamped bars.

**The objective shortcut:** points, ticks, pips and account currency are not
synonyms. Captions can contain transcription errors. The checked CME contract
webpage did not expose its dynamic tick table in the retrieved text during this
run, so this chapter does not manufacture a universal point-to-tick conversion.
Any executable sizing later needs the actual supported instrument specification.
A narrative target range is neither an observed fill nor a guaranteed profit.

**The denominator shortcut:** many overlapping gaps in one hour are not many
independent strategies. Selecting a later successful gap after the first fails
adds a retry policy, costs and dependence. Such a policy must be declared before
evaluation. The first-chronological rule below preserves the adverse first
candidate rather than replacing it with a prettier example.

## Three real historical examples with dates

These are genuine **Binance Spot BTCUSDT one-minute observations**, reused from
the fixed 360-bar receipt. They are not original creator charts or additional
independent samples. Source requests and hashes are retained. Prices are USDT
per BTC, and the capture retrieval date is 28 October 2026. No futures or Forex
price is inferred from these spot observations.

### Example 1 — 15 May 2023: London hour contains failures, not certainty

The captured 06:30–08:30 UTC period includes **03:00–04:00 EDT**, corresponding
to 07:00–08:00 UTC. The diagnostic finds **22** strict in-window gaps whose
earliest completed decisions remain eligible. These are formation counts, not
22 trades or a win rate. Several use overlapping candles and share the same
hour's market conditions.

The first chronological candidate is bearish, available no earlier than
**03:04 EDT**, with gap **27,457.05–27,460.71**. Its next minute reaches
**27,469.34**, a full crossing. The original lifecycle cancels it before
crediting a rejection. The hour later ends below its opening price, but that
does not repair the first candidate. No entire-day Power of Three sequence is
certified: the capture is only two hours and does not supply a complete daily
opening-to-close experiment or a prior directional hypothesis.

### Example 2 — 5 January 2024: winter conversion and an unfilled opportunity

The 14:30–16:30 UTC capture contains **10:00–11:00 EST**, which is
**15:00–16:00 UTC**, not the summer 14:00–15:00 UTC equivalent. There are
**15** eligible gap formations. The first bullish gap is available no earlier
than **10:03 EST**, bounded by **43,581.39–43,610.00**.

None of the following five minutes contacts the gap. Rising prices above it do
not create a retrospective limit fill. The classic 07:00–09:00 New York Forex
killzone is a different source definition and is not present in this two-hour
capture. Calling the 10:03 event a classic New York killzone trade would merge
distinct rules. For Hoshi the result is time-qualified geometry with an absent
retest and missing full strategy gates, therefore WAIT.

### Example 3 — 8 August 2024: afternoon eligibility cannot override invalidation

The 17:30–19:30 UTC capture contains **14:00–15:00 EDT**, or
**18:00–19:00 UTC**. It has **12** eligible gap formations under the same
clock/geometry rule. The first bearish formation becomes available no earlier
than **14:08 EDT**, with bounds **59,445.71–59,454.37**.

The 14:09 candle reaches **59,455.00**, just beyond the far boundary, before
closing below the gap. Even though that close looks like rejection, the
full-cross priority invalidates the candidate. Exact tick sequencing and fills
are unknown. A later favorable hour does not justify silently searching for a
replacement after seeing the failure. A retriable model would require a fresh
version, a bounded attempt count and an evaluation that charges every attempt.

## How to use it to HUNT a trade

First decide which named source interval is relevant to the supported instrument.
Convert the actual source timestamp, verify the session calendar and reject
stale or incomplete data. Record the earliest possible feature availability,
then require actual provider arrival and acceptable latency in any eventual live
paper implementation. Keep the time gate a Boolean piece of evidence rather
than a confidence percentage.

Freeze price references and a falsifiable direction before waiting for a trigger.
Require the defined sequence, an unexpired entry condition, an observed reachable
price and bounded paper loss. If the setup never appears, export no setup. If
it invalidates, retain that outcome. If a required opening reference or calendar
is missing, state the exact gap and WAIT. Do not use a historical story to invent
entry, stop or target levels for an unsupported instrument.

Evaluate time filters against chronological comparison windows and realistic
costs, including no-trade periods, late data and same-bar ambiguity. Keep the
Power of Three label descriptive unless its phases have operational definitions
and independent evidence. Hoshi's usual response should stay short; detailed
teaching is available when requested. These source chapters and diagnostics do
not yet constitute runtime integration, a trained predictor or a calibrated
probability of success.

## Sources

- [Original ICT London Killzone](https://www.youtube.com/watch?v=G8OEsUAoIWE): original English captions and creator-channel metadata checked 28 October 2026; 02:00–05:00 New York definition, without adopting stated pip or probability claims.
- [Original ICT New York Killzone](https://www.youtube.com/watch?v=plNN9n7nrxc): original captions and creator-channel metadata checked; source-specific 07:00–09:00 definition.
- [Original Silver Bullet lesson](https://www.youtube.com/watch?v=tRq1hyGGtl4): original captions checked; three hours and entry-versus-exit distinction briefly attributed, not a guarantee or certified recognizer.
- [Original 2022 Mentorship Episode 9](https://www.youtube.com/watch?v=iZLXnNiZm_s): original captions/metadata checked; limited Power of Three attribution, not inferred participant intent.
- [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html): primary historical timezone conversion behavior checked; actual summer/winter cases replayed offline.
- [Binance kline API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary source field/time semantics checked; adjacent JSON retains actual raw requests and responses under the stated noncommercial data license.
- [CME E-mini S&P contract page](https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.contractSpecs.html): primary page checked, but dynamic tick table absent from retrieved text; no numeric tick-conversion claim derived from that missing table.

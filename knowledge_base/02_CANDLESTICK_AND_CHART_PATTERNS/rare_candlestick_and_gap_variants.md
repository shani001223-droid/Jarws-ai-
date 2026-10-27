# Rare candlestick and gap variants: definitions, absence and delayed confirmation

Reviewed: 28 October 2026, Asia/Karachi. This source chapter extends the core
candle catalogue with compound families and explicit gap distinctions. It does
not claim an exhaustive list of every named variant, executable recognition
of every library function, or knowledge already loaded into Hoshi's runtime.
The historical measurements below are original, offline educational analysis.

## What is it?

A compound candlestick pattern is a predicate across several completed bars.
Its name compresses choices about candle bodies, shadows, relative prices,
gaps, preceding context and sometimes subsequent confirmation. Similar names
can encode materially different comparisons. A useful catalogue must preserve
those differences rather than attaching the same reversal story to all of them.
TA-Lib's own function documentation is the primary reference for the library
variants described here. Hoshi has not executed those native functions or
verified parity with their configurable average-length settings.

Define a body's lower endpoint as the lesser of open and close, and its upper
endpoint as the greater. An upward **body gap** requires the new body's lower
endpoint to exceed the preceding body's upper endpoint. The bearish condition
reverses that inequality. A **full-range gap** instead requires the new low to
exceed the preceding high, or the new high to fall below the preceding low.
Bodies can be disjoint while shadows overlap. A session's open differing from
its previous close is yet another measurement: it does not establish either
of those whole-candle conditions. An absent timestamp is a data gap and must
never be relabelled as a price gap.

This distinction matters in continuously traded spot crypto. These captures
use artificial UTC daily boundaries, not an equity exchange's overnight
closure. Very small open/close differences can satisfy an unfiltered body-gap
inequality without showing an economically large jump. The three-bar FVG
convention used elsewhere also compares different bars and is not synonymous
with a strict gap between adjacent complete ranges. Record the exact relation,
price precision, threshold and bar alignment before comparing instruments.

### Discontinuous reversal and continuation families

An **abandoned baby** combines a substantial initial body, an isolated middle
doji and an opposing final body. The middle candle's separation and the final
return distinguish it from merely spotting a doji near a reversal. A **kicking**
sequence uses opposing marubozu-like bodies separated by a gap; the ordinary
library variant takes its sign from the second candle. **Kicking by length**
instead uses the colour of the larger body, with its documented tie rule.
Consequently, even the same apparent two-candle shock can receive different
direction labels under two deliberately different definitions.

**Two crows** and **upside-gap two crows** both begin with a rising body followed
by a dark body above it, but their third-candle requirements differ. In the
former the third dark close returns into the first light body. In the latter
the third body engulfs the second while its close remains above the first
close. Calling both simply a bearish gap would erase the tested boundary.
**Breakaway** extends over five candles: an early body gap and continuation
are followed by an opposing return into that gap. This is a sequence definition,
not evidence that a particular group intentionally abandoned positions.

**Tasuki gap** describes a directional body gap followed by an opposite-colour
candle that enters but does not fully close the relevant gap. **Upside/downside
gap three methods** involves an opposing third candle that fills back into the
gap between the first two same-colour bodies. **Side-by-side white lines** uses
two similar light bodies with nearby opens after a common upward or downward
separation from the first body. These are different partial-fill, fill and
parallel-body tests; none establishes a universal gap-fill probability.

**Mat hold** is a five-candle continuation construction with an initial strong
light body, a gap and contained reaction, then a renewed upward close. The
native definition does not impose every colour detail sometimes shown in
illustrations. **Three-line strike** has three same-colour progressing closes
and a fourth opposite body spanning back past the first open. TA-Lib keys its
direction convention to the initial three, so copying the final candle's colour
as the signal would misread this function. Context remains a separate test.

### Matching levels, contraction and exhaustion families

**Counterattack** compares the nearly matching closes of two long, opposite
bodies. **Separating lines** instead compares opens and adds a directional
belt-hold requirement to the second candle. A **matching low** concerns two
dark closes at approximately the same level, not two equal wick lows. A
**stick sandwich** inserts a light candle between two dark candles with nearby
closes. These equality conditions need an explicit tolerance; chart pixels are
not a numerical tolerance and equality in another quote precision may disappear.

The **on-neck**, **in-neck** and **thrusting** variants begin with a dark body
and a subsequent light candle opening below the earlier low. They distinguish
where the recovery closes: near that low, just into the body near its close,
or farther into the body while still below its midpoint. A body midpoint is
not the high-low midpoint. Changing one to the other can change classification.
Their continuation interpretation is a hypothesis requiring its own forward
test, rather than a reason to disregard an actual later upside break.

**Homing pigeon** places a smaller dark body inside a larger dark body. **Three
stars in the south** compresses three dark candles with specific shrinking
body and shadow relations. **Concealing baby swallow** uses four dark candles,
including early marubozu conditions and a final engulfing relation. The
traditional bullish labels attached to these constructions illustrate why
counting red candles alone cannot determine the intended pattern direction.
**Ladder bottom** adds a final light recovery after a declining dark-candle
sequence and a late upper shadow. **Unique three river** combines a large dark
body, a smaller dark body with a lower probe, and a small light third candle.

**Advance block** and **stalled pattern** describe progressive light closes
with weakening internal geometry, such as smaller bodies or conspicuous upper
shadows. They distinguish price progress from the strength of each individual
bar. **Identical three crows** adds later opens near previous closes to three
declining dark bodies. **Tri-star** uses three dojis with the middle body's
separation contributing direction. **Takuri** requires a doji near the high
with an exceptionally long lower shadow. A **rickshaw man** puts its doji body
near the middle between long shadows and is neutral in the checked definition.
Its positive integer presence code must not be translated into a bullish
probability or even a mandatory bullish direction.

### Inside-bar extensions and the original research rule

The checked **Hikkake** family starts from inside-bar geometry, a subsequent
extension and possible later reversal confirmation. The modified variant has
additional containment and close-location requirements; it must not be silently
substituted for the simpler pattern. For reproducible historical examples this
chapter uses a separate, deliberately narrow original rule,
`hoshi-inside-extension-1`, implemented in `scripts/v3_pattern_evidence.py`.
It is Hikkake-like geometry, not certification by either TA-Lib recognizer.

Call the mother candle M and the next strictly contained candle I. Both I's
high and low must be inside M's extremes; equal endpoints do not qualify. The
following candle T must shift both extremes lower than I, creating an upward
reclaim candidate above I's high, or shift both extremes higher, creating a
downward candidate below I's low. T need not close outside the inside range.
The setup is first known at T's completed close. Only the following three
completed bars are searched for a strict close beyond the opposite I boundary.
An intrabar wick crossing is insufficient. A complete three-bar window without
such a close has no confirmation; an unavailable three-bar horizon is missing,
not a failure or a zero return.

## Why does it form?

A narrow inside range records less high-low exploration within that sampling
interval. A later extension records different traded extremes. A subsequent
opposite close can support a description of failed immediate continuation,
but candles cannot reveal whether breakout traders were trapped, stops were
triggered or a bank arranged the sequence. Similar geometry can arise from
ordinary order arrivals, cancellations, inventory adjustment, announcement
responses, changing participation or simple aggregation boundaries. The data
here contain no trader identities or order-level intent.

Gapped patterns also mix two mechanisms. Closed-session instruments can
reprice when trading resumes after information accumulated outside the session.
Within continuous trading, a disjoint body can merely reflect the relationship
between four endpoints even though trades connected the ranges. A sparse print
series, a broken feed or adjusted historical prices can create additional
apparent discontinuities. Before giving a gap economic meaning, inspect the
venue's trading hours, timestamp continuity and adjustment methodology.

Several rare labels share much of the same input geometry. A large body with
limited shadows can participate in multiple compound predicates. These are
correlated descriptions of a path, not independent votes from unrelated
evidence sources. More elaborate naming increases degrees of freedom if the
analyst chooses a favourable variant after seeing the outcome. Keeping
definitions and absences is therefore as useful as accumulating recognitions.

## Application zone

Use a rare pattern as a precise question at a previously specified market
location. Freeze the instrument, venue, timeframe and reference level before
looking forward. Select whether the research question concerns immediate
continuation, a closing reclaim, a retest or a longer endpoint; do not switch
questions when one fails. Adaptive library body/shadow baselines need warmup
and versioned settings. This chapter's original rule needs no adaptive candle
baseline, but that convenience does not make it equivalent to native functions.

Daily source bars here are **Binance Spot BTCUSDT**, quoted in USDT per BTC,
from 00:00:00 through 23:59:59.999 UTC. The three captures span January–June
2020, March–August 2021 and May–December 2022. They contain 182, 184 and 245
bars respectively. All 611 were already inspected for earlier curriculum
chapters. They are examples and descriptive checks, not unseen validation
windows. `pattern_observations_20261028.json` identifies each underlying raw
response hash and preserves every input to the three cases below.

An exhaustive adjacent-pair gap check across these bounded captures finds:

| Observation window, UTC | Adjacent comparisons | Strict body gaps | Strict full-range gaps |
| --- | ---: | ---: | ---: |
| 1 January–30 June 2020 | 181 | 28 | 0 |
| 1 March–31 August 2021 | 183 | 24 | 0 |
| 1 May–31 December 2022 | 244 | 36 | 0 |

There is no tick-size or minimum-magnitude filter in this diagnostic. It
therefore should not be interpreted as 88 economically meaningful jumps or
88 tradable opportunities. Zero adjacent full-range gaps means there is no
positive example of that necessary condition in these captures. It does not
prove that every gap family is absent, that another session alignment behaves
the same, or that gaps always close. No success rate is computed from absence.

For future research, record the underlying source, completed-bar cutoff,
detector version and rejected candidates alongside positive ones. If a rule
needs a real overnight gap, choose an appropriate instrument and checked
session data rather than relaxing definitions until the existing crypto bars
fit. A missing relevant dataset is a valid research gap.

## Failure zones

No named construction works 100%. Narrow price equality can be sensitive to
precision, tick size and tolerant comparisons. A whole-range gap can disappear
when switching from regular-session to extended-session data. A doji threshold
can label the same candle differently under another historical baseline. These
are specification changes, not proof that a market respected or violated a
universal law. Keep the specification with the observation.

False confirmation is another separate risk. Closing through an inside-bar
boundary says nothing by itself about how long price remains beyond it. It
may return on the next bar. Waiting for that close also means the earlier
boundary price may no longer be executable. Placing a hypothetical entry at
the old boundary after observing the close would introduce look-ahead. Daily
OHLC cannot resolve intrabar order, queue position, spread or stop execution.
No receipt below contains fills, trade PnL or a calibrated win probability.

Library presence codes such as 100 and confirmation codes such as 200 are
categorical outputs. They are not percentages. Some checked reference pages
also discuss third-party pattern statistics; those results were not reproduced
here and must not be imported as Hoshi's accuracy. Different instrument sets,
holding periods, costs and definitions can invalidate such a transfer.

Finally, news, thin depth and gaps can bypass a theoretical invalidation price.
An ordinary completed-bar detector cannot guarantee loss containment. Multiple
pattern names on one candle should not multiply a score, and a failed setup
must remain in the ledger instead of acquiring a new name after the outcome.

## Three real historical examples with dates

### Example 1 — 13–18 February 2020: lower extension without a closing reclaim

The 13 February mother candle traded high 10,500 and low 10,080. On 14 February,
high 10,381.56 and low 10,111.37 were strictly inside it. The 15 February candle
shifted both extremes lower, to high 10,375 and low 9,801, and closed 9,904.72.
Only at the 15 February UTC close was the original bullish reclaim candidate
known. Its frozen confirmation boundary was the inside high, **10,381.56**.

The next three closes were 9,917.27 on 16 February, 9,706 on 17 February and
10,164.71 on 18 February. None closed above the boundary. This is a complete
negative confirmation window, retained in the receipt with
`first_confirmation: null`. It is not a historical long entry, a winning
Hikkake or proof of a trapped seller. Selecting the extension low as a purchase
after observing the subsequent bars would misstate both timing and evidence.

### Example 2 — 31 March–5 April 2021: confirmation followed by a return

The 31 March mother range was 56,769–59,800. The 1 April candle, with high
59,490 and low 57,935.45, was strictly inside it. The 2 April range moved up
to high 60,200 and low 58,428.57. At that day's close of 58,950.01, the original
rule created a downward reclaim candidate below **57,935.45**, without knowing
what the following day would do.

On 3 April price closed 57,051.94, the first strict closing confirmation.
However, closes on 4 and 5 April were 58,202.01 and 59,129.99, both back above
the frozen boundary. The sequence documents an eligible event and subsequent
reversal of its boundary relation. It does not establish a profitable short:
an executable entry, stop, target, holding rule, spread and costs are absent.
The confirmation should be stored as a dated observation, not a promise of
continuing downside or a reason to conceal the later adverse path.

### Example 3 — 23–28 September 2022: wick crossings precede a late close

The 23 September mother range was 18,531.42–19,500. The 24 September inside
range was 18,805.34–19,316.14. On 25 September both extremes shifted down to
18,629.20–19,180.21, creating an upward reclaim candidate at the completed
close. The frozen boundary was **19,316.14** and the horizon was exactly three
later daily bars.

On 26 September the high reached 19,318.96, marginally over that boundary,
but the close was 19,227.82. On 27 September the high reached 20,385.86 while
the close was only 19,079.13. Neither wick excursion confirmed this close-based
rule. The 28 September close of 19,412.82 finally qualified on the third
eligible bar. Using the first wick would have advanced the signal by two
days and changed the detector. No subsequent profit or causal stop-hunt story
is inferred from the delayed confirmation.

## How to use it to HUNT a trade

First select a supported instrument and actual observation time. Validate
timestamp continuity, OHLC relationships, closed-bar status and whether the
requested gap definition fits that venue's session. State the pattern variant
and level before future observations arrive. If necessary historical warmup,
licensing or session information is unavailable, retain the exact gap and WAIT.
Do not generate a different instrument's price levels from these old examples.

Next separate geometry from qualification. A candidate near an independently
specified reference may justify monitoring, but repeated descriptions of the
same candles do not supply independent liquidity or macro evidence. Require
the chosen confirmation at its actual close. Keep failed, expired and
incomplete candidates with different statuses. This prevents a polished chart
annotation from hiding the events that did not confirm.

Only then evaluate a bounded paper hypothesis using subsequent observed
prices and a defined execution model. Specify entry availability after the
signal, invalidation, exit horizon, costs and ambiguous same-bar outcomes.
Record that a discontinuity may produce a worse fill than the invalidation
level. Validate chronologically on genuinely independent data before promoting
any rule, and retain null probability until calibration is independently
supported. The three educational cases are not that calibration.

Hoshi's eventual concise output can report the candidate status, supported
symbol, source time and missing requirements without teaching this catalogue
unless asked. At this curriculum stage the original detectors run only in
offline source verification; they do not place orders or change V2 signals.

## Sources

Primary documentation checked 28 October 2026. These links support definitions,
not transferable accuracy claims. Prose is original; no proprietary course or
native source implementation has been reproduced.

- TA-Lib discontinuity families: [Abandoned Baby](https://ta-lib.org/functions/cdlabandonedbaby.html), [Kicking](https://ta-lib.org/functions/cdlkicking.html), [Kicking by Length](https://ta-lib.org/functions/cdlkickingbylength.html), [Two Crows](https://ta-lib.org/functions/cdl2crows.html), [Upside Gap Two Crows](https://ta-lib.org/functions/cdlupsidegap2crows.html), [Breakaway](https://ta-lib.org/functions/cdlbreakaway.html).
- TA-Lib gap continuation families: [Tasuki Gap](https://ta-lib.org/functions/cdltasukigap.html), [Gap Three Methods](https://ta-lib.org/functions/cdlxsidegap3methods.html), [Side-by-Side White Lines](https://ta-lib.org/functions/cdlgapsidesidewhite.html), [Mat Hold](https://ta-lib.org/functions/cdlmathold.html), [Three-Line Strike](https://ta-lib.org/functions/cdl3linestrike.html).
- TA-Lib matching/neck families: [Counterattack](https://ta-lib.org/functions/cdlcounterattack.html), [Separating Lines](https://ta-lib.org/functions/cdlseparatinglines.html), [Matching Low](https://ta-lib.org/functions/cdlmatchinglow.html), [Stick Sandwich](https://ta-lib.org/functions/cdlsticksandwich.html), [On-Neck](https://ta-lib.org/functions/cdlonneck.html), [In-Neck](https://ta-lib.org/functions/cdlinneck.html), [Thrusting](https://ta-lib.org/functions/cdlthrusting.html), [Belt Hold](https://ta-lib.org/functions/cdlbelthold.html).
- TA-Lib remaining compound families: [Homing Pigeon](https://ta-lib.org/functions/cdlhomingpigeon.html), [Three Stars in the South](https://ta-lib.org/functions/cdl3starsinsouth.html), [Concealing Baby Swallow](https://ta-lib.org/functions/cdlconcealbabyswall.html), [Ladder Bottom](https://ta-lib.org/functions/cdlladderbottom.html), [Unique Three River](https://ta-lib.org/functions/cdlunique3river.html), [Advance Block](https://ta-lib.org/functions/cdladvanceblock.html), [Stalled Pattern](https://ta-lib.org/functions/cdlstalledpattern.html), [Identical Three Crows](https://ta-lib.org/functions/cdlidentical3crows.html), [Tri-Star](https://ta-lib.org/functions/cdltristar.html), [Takuri](https://ta-lib.org/functions/cdltakuri.html), [Rickshaw Man](https://ta-lib.org/functions/cdlrickshawman.html).
- TA-Lib [Hikkake](https://ta-lib.org/functions/cdlhikkake.html) and [Modified Hikkake](https://ta-lib.org/functions/cdlhikkakemod.html); the original receipt rule is explicitly separate from these native recognizers.
- Binance [Spot kline specification](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints#klinecandlestick-data) and [public-data repository](https://github.com/binance/binance-public-data). Exact captured response bodies, request bounds and hashes are retained in `../01_MARKET_STRUCTURE/structure_observations_20261028.json`; derived cases and gap counts are in `pattern_observations_20261028.json` and checked offline.
- Binance Vision [market-data terms](https://data.binance.vision/?prefix=), with the [CC BY-NC-SA 4.0 licence](https://creativecommons.org/licenses/by-nc-sa/4.0/) applying to the attributed source data and these derived data analyses. Non-commercial educational use; no endorsement or commercial-data entitlement is claimed. This attribution does not relicense unrelated repository code or TA-Lib documentation.

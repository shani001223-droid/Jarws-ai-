# Candlestick pattern catalogue: geometry, context and the limits of a name

Reviewed **28 October 2026, Asia/Karachi**. Original educational curriculum,
not model training, a runtime recognizer catalogue or calibrated signals.
Historical examples are **Binance Spot BTCUSDT, USDT per BTC, daily UTC bars**.
Rare gap/compound variants require the separately declared expansion chapter;
this document does not claim that one vocabulary exhausts every pattern.

## What is it?

A candle encodes an interval's open, high, low and close, optionally accompanied
by a particular venue's volume. A pattern is a predicate applied to one or more
such observations, sometimes combined with prior context. Its name is a human
label for that predicate. A bullish-looking label does not identify who traded,
whether an order was executable, or a probability that the next price will rise.

Write the geometry before interpreting it. For a valid candle define range
`R=H-L`, real body `B=abs(C-O)`, upper shadow `U=H-max(O,C)` and lower shadow
`D=min(O,C)-L`. When `R>0`, body fraction is `B/R` and close location is
`(C-L)/R`. When the range is zero, those ratios are undefined and remain null;
a frozen or illiquid interval must not automatically become a powerful doji.
Candle color records the sign of `C-O`, not the quantity of buying versus
selling volume. Every executed trade has both a buyer and a seller.

The worked examples use version **hoshi-candle-geometry-1**, an original narrow
research convention. Doji geometry requires `B/R<=0.10`. Lower-wick geometry
requires `0<B/R<=0.35`, `D>=2B` and `U/R<=0.15`; upper-wick geometry reverses
the shadows. Body engulfing requires opposite candle colors, containment of the
preceding real body and at least one strictly extended endpoint. Inside and
outside bars compare wick extrema strictly. These are not claimed to match
TA-Lib's adaptive candle settings or every textbook definition.

TA-Lib's official documentation is useful precisely because it exposes
implementation distinctions. Its doji uses a candle-average threshold, and its
engulfing documentation distinguishes strict containment from a shared endpoint.
Some functions do not verify the preceding trend their conventional
interpretation assumes. Integer outputs such as 80 or 100 are classifier
codes, not 80% or 100% winning probabilities. This chapter does not adopt the
third-party performance percentages appearing in some source notes.

### Small-body and decisive-body families

**Doji and spinning top:** a doji concerns closeness of open and close under a
declared scale; a spinning top combines a small body with meaningful shadows
on both sides. A tiny body can occur in a large volatile interval or in a nearly
inactive one. Report range and baseline activity separately. Their overlap is
possible, so several labels on one candle are not several independent witnesses.

**Long-legged, dragonfly and gravestone doji:** these distinguish the distribution
of shadows around a near-zero body. A lower-shadow-dominant doji differs from
an upper-shadow-dominant one, and a long-legged form explores both directions.
The interpretation requires exact definitions of short body, long shadow and
allowable residual shadow. None establishes that a particular participant
defended the candle's low or high.

**Long line, short line and marubozu:** a body can be long relative to its own
range, relative to preceding bodies, or both. A marubozu convention combines a
substantial body with very short shadows. Opening and closing variants relax
different ends. An almost full-body candle may follow a gap, finish an extended
move or begin a new one; its visual decisiveness does not settle which. The
baseline and the side with residual shadow must be recorded.

### Shadow and context families

**Hammer and hanging man:** both commonly involve a body near the upper part
of the range and a longer lower shadow. Their conventional names depend on
preceding context: a decline for a possible bottoming interpretation, an advance
for a possible warning at the top. A geometry-only detector should say
lower-wick shape until context is explicitly checked. A pattern does not become
a confirmed reversal merely because its final color is positive.

**Inverted hammer and shooting star:** both place a relatively small body near
the lower part of a long-upper-shadow range. Again, context distinguishes a
possible bottoming attempt from a possible rejection after an advance. Define
shadow/body ratios and preceding trend separately. Later confirmation consumes
later information and must move the decision time forward accordingly.

**High-wave forms and pin-bar language:** broad two-sided shadows are often
described as uncertainty; pin-bar terminology emphasizes an asymmetric shadow.
Neither term has one universally binding numerical threshold. HOSHI must
preserve the actual rule version rather than silently equate a platform's pin
bar with a library hammer. Such variants can be compared empirically without
pretending their names refer to identical events.

### Two-candle relationships

**Bullish and bearish engulfing bodies:** compare real bodies, not automatically
entire high/low ranges. A bullish body can contain a prior bearish body while
its wicks remain inside the previous range. Conversely, a large outside bar
may fail the body-containment test. State how exact shared endpoints and
same-colored bars are handled. Engulfing without a prior-context check is a
geometric observation, not a verified trend reversal.

**Harami and harami cross:** a smaller real body sits within an earlier larger
body; the cross variant uses a doji-like second body. Wick containment is a
different condition. Define long and short relative to a frozen baseline,
endpoint tolerance and the direction/context assumption. The smaller second
body may describe slowing movement without proving that the next move reverses.

**Inside and outside bars:** these compare complete candle ranges. A strict
inside bar has a lower high and higher low than its mother bar. A strict
outside bar has a higher high and lower low. Equality handling is a separate
variant. An outside bar does not reveal whether its high occurred before its
low; assigning that path can manufacture an entry or a target-first outcome.

**Piercing and dark-cloud forms:** these involve penetration into an earlier
opposite-colored body, with specific opening-gap and close-depth conditions.
The checked TA-Lib piercing description uses an opening below the preceding
low and a recovery beyond the earlier body's midpoint; dark-cloud cover uses
an opening above the earlier high and a deep retreat into its body. Relaxing
gaps for continuous crypto creates a different rule, not an unchanged classic.

**Tweezer and matching-extreme language:** two similar highs or lows require a
tolerance in ticks, percentage or past volatility units. Exact float equality
and a wide visual resemblance select different samples. Repeated prices are
not evidence that all stops lie there. Confirmation, invalidation and how
closely spaced observations must be are separate experimental choices.

### Three-candle and continuation families

**Morning/evening stars:** these combine a directional first body, a smaller
middle body separated under a specified gap rule, and an opposite-direction
third body that penetrates the first. Morning and evening interpretations
reverse the arrangement. Doji-star variants alter the middle-body condition.
The third close is part of recognition; the pattern cannot be used two bars
earlier when only its first candle existed.

**Three advancing soldiers and three black crows:** these describe sequences
of directionally progressing bodies and closes, with constraints on opening
location and residual shadows. A run of three green or red candles alone is
not necessarily the specified pattern. Implementations differ in whether they
require an earlier opposite candle or prior mature trend. Recognize the run
only after the last required candle closes, when its earlier low/high may be
far from any feasible paper entry.

**Three inside/outside confirmation families:** these extend a two-candle
relationship with a further directional confirmation. The extra bar changes
both availability and price. A study using the two-candle entry cannot borrow
the three-candle form's later confirmation without delaying its entry. Maintain
separate identifiers for the precursor and the completed compound.

**Rising/falling three methods:** a directional impulse is followed by smaller
counter-direction candles and a later resumption. The checked library's
five-candle implementation uses three middle candles with particular overlap
conditions; it is not a detector of every visually similar pause. Declare
whether a study permits a variable number of middle bars or requires full
containment. Variable-duration relaxation is another model to count and test.

**Gap and rare compounds:** abandoned-baby, kicking, tasuki, side-by-side lines,
breakaway, hikkake, neck, river and ladder families add distinct sequence,
gap or confirmation requirements. Their names are not substitutes for those
requirements. Detailed rule variants and gap-preserving negative examples are
explicitly retained in the manifest's pending rare-variant chapter, rather than
claiming they were all implemented by the seven measured predicates above.

## Why does it form?

A candle is a lossy aggregation of a trading path. A long lower shadow means
the interval included prices below both the open and close; it does not tell
us all intervening transactions, quotes or motives. A large body means the
chosen endpoints differ considerably. Different paths can yield identical
OHLC. Explanations about trapped traders, inventories or news require evidence
beyond the shape itself.

Recognition rules turn continuous measurements into categories. A body
fraction just below a threshold and one just above it can be almost identical
economically but receive different labels. This discontinuity is a reason to
inspect sensitivity and uncertainty, not to keep changing thresholds until a
preferred historical screenshot qualifies. Price precision, missing bars and
candle alignment affect the classification too.

Prior context, subsequent confirmation and execution are separate stages.
Calling a lower shadow a hammer may embed a preceding-decline assumption;
requiring a later close above its high adds another event. Neither assumption
is automatically verified by a geometry classifier. The later outcome must be
stored outside the earlier feature record, with its own availability time.

## Application zone

Use the catalogue as a controlled vocabulary for research questions. Freeze
venue, instrument, candle interval, timezone, required history and measurement
rules. Validate completed bars and retain original source hashes. A synthetic
Heikin-Ashi body, an adjusted equity bar and an exchange trade candle are
different objects; do not silently interchange their opens and closes.

Define context with past-only data and a named method. If a hypothesis needs
a declining trend or a premarked support level, show the actual observation
and its knowledge time. If context is unavailable, report shape-only evidence.
Volume can describe activity at the venue but candle color cannot replace
aggressor-classified order flow. Three labels from one OHLC record must not be
counted as three independent confirmations.

Specify an execution trigger and expiry independently from recognition. A
next-close break, an intrabar stop-style trigger and a limit retest are different
studies. Choose a conservative ambiguity policy when available bars cannot
establish sequence. Entry, stop and target require supported actual prices and
bounded paper risk; the pattern's name cannot supply missing numbers.

Keep descriptive and evaluation outputs separate. A recognition hit can be
correct even when later prices move against a directional interpretation. A
classifier code, feature-coverage score and independently calibrated outcome
probability are three different objects. HOSHI must not turn the first two
into an invented confidence percentage.

## Failure zones

An unfinished candle can lose its shadow, expand its body or engulf another
body before closing. Backtests cannot recognize its final shape early. Missing
intervals, incorrect timezones and venue-specific extreme prints can also
manufacture patterns. Historical captures remain historical, not current-feed
certification or proof of a contemporaneous source vintage.

Context can overwhelm a shape. A lower wick during a decline can be followed
by another substantial fall; a near-zero body during an advance can precede
continuation or reversal. A tiny pattern may be economically smaller than
spread and fees. A huge pattern may require a stop distance incompatible with
bounded cash risk. No pattern has a 100% working zone.

Overlapping predicates and many tried variants create selection problems.
Choosing the most flattering name after seeing the future, excluding failures,
or citing a percentage from another asset sample does not validate HOSHI's
implementation. Preserve rejected observations, no-entry cases and negative
outcomes. Chronological evaluation and realistic execution remain pending even
when a source example has been measured correctly.

## Three real historical examples with dates

The companion `pattern_observations_20261028.json` references the existing
hash-checked source windows and records exact measurements. Candle dates are
UTC opening dates, ending **23:59:59.999 UTC** that day. Five-bar endpoint
changes are raw price observations, not realized or simulated strategy PnL.
The cases were selected retrospectively for teaching, not independent testing.

### Example 1 — 11–16 March 2020: lower-wick geometry before a further collapse

March 11 opened at **7,894.57**, reached **7,980.00**, traded as low as
**7,590.00**, and closed at **7,934.52**. Its range was **390.00**, body
**39.95**, lower shadow **304.57** and upper shadow **45.48**. Body/range was
approximately **0.10244**; lower- and upper-shadow fractions were approximately
**0.78095** and **0.11662**. It met the declared lower-wick geometry rule.

The next daily close, March 12, was **4,800.00**, below the pattern low. The
fifth subsequent close on March 16 was **5,028.97**, approximately **−36.6191%**
from the March 11 close. A long lower shadow did not guarantee a bottom. No
exact stop fill or trading loss is asserted; the observed adverse path is
enough to reject a universal reversal claim.

### Example 2 — 9–14 June 2021: body engulfing with a different confirmation clock

June 8 opened at **33,556.96** and closed at **33,380.81**, a bearish real
body. June 9 opened at **33,380.80** and closed at **37,388.05**, with a high
of **37,534.79** and low of **32,396.82**. Its opposite-colored real body
contained and extended the prior body, meeting the declared bullish engulfing
rule. That label alone does not establish a preceding trend reversal.

June 10 closed at **36,675.72**, below the event high, so a required immediate
next-close-above-high confirmation did not occur. The fifth subsequent close
on June 14 was **40,516.29**, approximately **+8.3670%** from the event close.
The later positive endpoint cannot be borrowed to invent an earlier confirmed
entry or to change the study's trigger after the outcome.

### Example 3 — 1–6 November 2022: a small-body observation without directional certainty

November 1 opened at **20,490.74**, reached **20,700.00**, traded down to
**20,330.74**, and closed at **20,483.62**. The body was **7.12** against a
**369.26** range, giving a body fraction of approximately **0.01928**. It met
the declared doji geometry rule. Its bearish color reflected the small
open-to-close decline, not observed net selling volume.

The next close was **20,151.84**; the fifth subsequent close on November 6 was
**20,905.58**, approximately **+2.0600%** from the event close. Opposite signs
at different endpoints illustrate why horizon and decision rules matter. This
case establishes a measured shape and path, not a bullish or bearish doji
win rate or an analogy-based forecast.

## How to use it to HUNT a trade

HUNT means searching for a bounded **paper research candidate**. Validate the
supported symbol, source times and closed history, then compute the chosen
predicate exactly. Expose missing context rather than filling it with an
institutional story. Freeze the invalidating reference and the later trigger
required by the study; unsupported or stale inputs produce WAIT.

Advance through observations causally. Recognize a multi-candle pattern only
when all required bars exist. Record subsequent confirmation, hypothetical
fill and exit separately, with realistic costs and unresolved path ambiguity.
If the permitted cash risk or minimum quantity makes the trade infeasible,
retain the rejection instead of increasing leverage or moving the stop.

Evaluate later untouched periods with failure and zero-entry records included.
Preserve source hashes, method versions and exact cutoff times in exports.
Default output can be `WAIT — candle ki shape mili hai, magar required
confirmation abhi nahi mili.` Provide the detailed lesson only when asked;
concise output still needs its evidence time and important limitations.

## Sources

The following primary documentation was checked; descriptions are paraphrased
briefly, while the protocol, examples and analysis are original. No source's
unverified third-party reversal percentage is adopted as HOSHI accuracy.

- [CME Group: Chart Types](https://www.cmegroup.com/education/courses/technical-analysis/chart-types-candlestick-line-bar) — OHLC representation and aggregation.
- TA-Lib's own definitions: [Doji](https://ta-lib.org/functions/cdldoji.html), [Spinning Top](https://ta-lib.org/functions/cdlspinningtop.html), [Marubozu](https://ta-lib.org/functions/cdlmarubozu.html), [Hammer](https://ta-lib.org/functions/cdlhammer.html), [Engulfing](https://ta-lib.org/functions/cdlengulfing.html), [Harami](https://ta-lib.org/functions/cdlharami.html), [Harami Cross](https://ta-lib.org/functions/cdlharamicross.html).
- Further primary implementation descriptions: [Piercing](https://ta-lib.org/functions/cdlpiercing.html), [Dark Cloud Cover](https://ta-lib.org/functions/cdldarkcloudcover.html), [Morning Star](https://ta-lib.org/functions/cdlmorningstar.html), [Evening Star](https://ta-lib.org/functions/cdleveningstar.html), [Three Advancing Soldiers](https://ta-lib.org/functions/cdl3whitesoldiers.html), [Three Black Crows](https://ta-lib.org/functions/cdl3blackcrows.html), [Rising/Falling Three Methods](https://ta-lib.org/functions/cdlrisefall3methods.html). HOSHI does not claim library parity or that all functions were installed or executed.
- [Binance Vision dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) and [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — Binance attribution and non-commercial educational/personal non-production use. This chapter and its Binance-derived evidence use share-alike terms; unrelated repository source is not relicensed and no provider endorsement is implied.

# Classical chart patterns: candidate geometry, activation and cancellation

Reviewed **28 October 2026, Asia/Karachi**. Original source curriculum and
offline observations, not runtime pattern recognition or a trading service.
Worked data are **Binance Spot BTCUSDT, USDT per BTC, daily UTC candles**.
No chart-pattern name supplies a win probability or guarantees a target.

## What is it?

A classical chart pattern is a rule-defined arrangement of observations across
multiple bars, usually expressed through extrema, boundaries, compression or
changes in direction. A candidate formation, an activated formation and a
completed trading position are different states. A recognizable shape can
exist without its activation event, and an activated shape can fail. A pattern
also depends on sampling, endpoint selection and the method used to identify
turns; a smooth retrospective line is not automatically a causal detector.

The major families organize different geometric questions. **Double and triple
tops/bottoms** compare repeated extremes and intervening counter-moves.
**Head-and-shoulders**, including its inverse, introduces a central extreme
beyond two surrounding shoulders and a neckline from intervening turns.
**Triangles** describe relationships between converging boundaries;
**rectangles** use approximately horizontal boundaries. **Flags and pennants**
describe bounded pauses relative to an earlier impulse. **Wedges** have
converging boundaries sloping in the same general direction. **Rounded/cup and
handle forms** require a curved transition and a separately defined smaller
pullback, rather than merely relabeling any V-shaped rebound.

CME's lessons provide conventional reversal and continuation vocabulary;
Fidelity's own webinar discusses additional constructions. HOSHI treats those
descriptions as hypotheses to formalize, not as externally certified
probabilities. The exact point-selection, tolerance, activation and expiry
rules below are original project research conventions. No library of every
classical pattern has been implemented by adding this chapter.

### Translate a drawing into a specification

For repeated extrema, define how similar prices must be and how much time or
counter-move must separate them. Three nearby prints from one noisy interval
are not necessarily three distinct attempts. For head-and-shoulders, define
the order of extrema, required head prominence, shoulder tolerance and neckline
construction. A sloping neckline needs a time-dependent equation fixed from
eligible points; moving it after price approaches changes the question.

For boundary patterns, define whether points are wick highs/lows or closes,
how many contacts are required, acceptable deviations, slope limits and
minimum width. An ascending triangle has an approximately horizontal upper
boundary and rising lower boundary; descending reverses those roles, while a
symmetrical triangle contracts on both sides. These shapes do not establish
which side will break next. A rectangle's finite high and low are insufficient
without a declared boundary-behavior rule.

For an impulse-and-pause family, quantify the impulse's size and duration and
the pause's depth and duration separately. A flag uses a roughly parallel
pause, while a pennant contracts. A wedge's two same-direction slopes differ
from a parallel channel. For a cup-like family, numerical curvature, rim
similarity, duration and handle-depth criteria are needed before any scan is
reproducible. Choosing whichever anchors flatter the future is not detection.

## Why does it form?

Observed paths can revisit a price region, compress, expand or migrate as
transactions and quotes change. Shared public reference levels may be relevant,
but OHLC cannot prove that the same institution defended both peaks, that all
retail traders placed stops together, or that a later move was planned. A
candidate's geometric description and a causal explanation need different
evidence.

Pattern vocabulary reduces a continuous path to a manageable set of features.
That compression can help organize research, but it throws away information.
Two paths can produce similar turning points while differing in intrabar
sequence, spread, volume and time at risk. Conversely, tiny changes in anchor
selection can move a candidate across a hard tolerance boundary. Record the
measurements instead of trusting the drawing's visual persuasiveness.

Confirmation introduces delay. A two-right-bar pivot is unavailable at its
turning candle. An activation at a neckline needs a later completed close if
that is the declared trigger. Waiting for a retest adds another event and
possibly no entry at all. These delays change price, risk distance and
opportunity; their effects cannot be erased by annotating an earlier low as
the entry after the complete pattern is visible.

Several pattern names can describe overlapping parts of one move. A double
bottom can lie inside a rectangle; an inverse head-and-shoulders can overlap
an expanding range. Those are correlated descriptions from the same data.
Counting them as independent confirmations exaggerates evidence without adding
new observations. Their incremental predictive value would need independent
chronological testing.

## Application zone

Begin with a candidate contract that specifies instrument, venue, interval,
timezone, price field and source availability. Use completed, validated history
and preserve gaps or revisions. Distinguish a charting platform's adjusted
series from actual instrument prices. These examples concern one crypto spot
venue; they cannot substitute for Nasdaq futures, a cash index or a CFD feed.

For the three examples here, **hoshi-two-turn-1** defines a narrow two-turn
research candidate. Select two **consecutive same-kind** strict two-left/two-right
wick pivots, at least three daily bars apart. Their absolute price difference
divided by their mean price must not exceed **0.03**. This tolerance was chosen
for an explicit exploratory teaching protocol, not established as optimal or
statistically validated. Highs and lows use the same tolerance convention.

The second pivot becomes usable only at its second following daily close.
Freeze a horizontal neckline from the most extreme intervening wick: maximum
high between two lows, minimum low between two highs. The outer invalidation
reference is the lower of the two lows or higher of the two highs. This
particular construction does not require an alternating ZigZag or a separate
confirmed neckline pivot; it uses only an already completed intervening window.

At formation availability, record whether the close has already crossed the
neckline. If it has, this protocol does not invent an earlier fresh activation.
Otherwise inspect exactly the next **ten** daily bars. A bottom-like candidate
activates on a close strictly above its frozen neckline; a top-like candidate
uses a close strictly below. A close beyond the outer reference in the
opposite direction cancels the candidate. A later neckline cross after that
cancellation cannot resurrect the original candidate.

The evidence stores both the first beyond-neckline close and the first
invalidation close so their order remains reviewable. An eligible break requires
similarity to pass, no already-completed break at formation, and a neckline
event before cancellation. Equality is not a strict crossing. If fewer than
ten future bars exist, outcome remains incomplete and null, rather than an
apparent zero-risk expiry.

Activation is still not an executed position. A paper engine would need a
separate entry mechanism, costs, sizing, invalidation policy and exit rules.
An outer geometric reference may imply a risk distance too large for the
allowed cash risk or minimum quantity. Correct handling can be no position.
A traditional measured-height projection is an arithmetic hypothesis, not a
guaranteed target, and is not automatically a defensible take-profit level.

Use context only when it has a point-in-time definition. A prior trend,
volatility bucket or session flag must be available before activation. Do not
call favorable cases trend continuation and adverse cases exceptional traps
after observing the outcome. Run separately defined context variants on new
evaluation data and retain all tested variants in the research record.

## Failure zones

**Anchor hindsight:** choosing turning points after a full chart is visible can
skip inconvenient intermediate pivots or move shoulders until a pattern fits.
The worked rule uses consecutive same-kind pivots precisely to expose that
selection constraint. It is one convention, not a claim that other conventions
are invalid; they require different identifiers and separate tests.

**Pre-confirmation action:** the second low or high is drawn on its own date
but becomes a confirmed pivot later. A strategy cannot consume that later
knowledge early. Candidate geometry, activation and any executable observation
must have distinct timestamps in a causal replay.

**Forgotten cancellation:** a candidate may be invalidated before an eventual
move through its neckline. A persuasive retrospective drawing can hide that
ordering. The November 2022 example below is an actual negative case: the later
downward crossing must not be counted as activation of the cancelled top.

**Tolerance fragility:** a pair at 2.94% difference passes a 3% rule but fails
a 2% rule. That is a measurement fact, not a natural dividing line between
good and bad trades. Sensitivity analysis must include adverse effects on
frequency, risk and outcomes, without selecting the best threshold on the
same evaluation period.

**False targets and fills:** touching a neckline, briefly crossing it, closing
beyond it and filling an order are different events. OHLC cannot establish
every intrabar path or queue position. If a hypothetical stop and target lie
inside the same candle, the missing sequence cannot be guessed in favor of
the model. Spread, latency, gaps and fees can overwhelm a visually attractive
formation.

**Sample and taxonomy overreach:** three selected examples cannot estimate
success rates for double turns, much less for wedges, flags or all classical
patterns. A correctly reconstructed formation does not prove net profit. No
pattern has a 100% working zone, and no all-pattern recognition capability is
claimed in HOSHI's current runtime.

## Three real historical examples with dates

The companion pattern evidence JSON records the exact rule outputs and links
them to captured source-response hashes. Dates below refer to daily UTC
candles, ending **23:59:59.999 UTC**. The ten-bar forward observations are
outcomes available later, not features known at the second pivot's date.
These are retrospective teaching cases, not independent strategy evaluation.

### Example 1 — 23 March–6 April 2020: two lows and a later eligible neckline close

The March 23 and March 30 confirmed wick lows were **5,688.00** and
**5,857.76**. Their difference divided by their mean was approximately
**2.94065%**, within this protocol's 3% limit. The first low was confirmed on
March 25; the second became available at the **April 1** close. The frozen
intervening-high neckline was **6,957.96**.

The first subsequent close strictly above that neckline was **7,329.90 on
April 6**. No close below the outer **5,688.00** reference occurred in the
declared ten-bar observation horizon. The candidate therefore had an eligible
activation under this narrow rule. That result establishes event chronology,
not an entry at either low or a profitable position. A 2% similarity rule
would reject this same geometry, illustrating threshold dependence.

### Example 2 — 29 April–12 May 2021: similar lows without activation before failure

April 29 and May 5 lows were **52,330.94** and **52,900.00**, a relative
difference of approximately **1.08155%**. The second pivot was confirmed at
the **May 7** close. The intervening-high neckline was **58,981.44** and the
outer invalidation reference **52,330.94**. The similar lows made a candidate,
not a confirmed bullish reversal.

Within the next ten bars there was no close above the frozen neckline.
Instead, **May 12 closed at 49,631.32**, below the outer reference, cancelling
the candidate. The evidence retains the missing activation and the observed
failure. An entry supposedly justified by a completed neckline break would
be invented in this example; no such trigger occurred during the horizon.

### Example 3 — 26 October–8 November 2022: cancellation preceded the later downward crossing

October 26 and October 29 highs were **21,020.00** and **21,085.00**, a relative
difference of approximately **0.30875%**. Both were eligible by the
**October 31** close. The intervening-low neckline was **20,000.09**; the outer
invalidation reference was **21,085.00**. The formation close was not already
below the neckline.

**November 4 closed at 21,148.52**, cancelling the top-like candidate before
any qualifying downward close. **November 8 later closed at 18,547.23**, below
the neckline. That later event is recorded but is **not** eligible activation
of the cancelled candidate. A screenshot that keeps the attractive later break
while omitting the prior cancellation would misrepresent the declared method.
No separate November 8 strategy or realized short profit is asserted here.

## How to use it to HUNT a trade

Start with one paper-only hypothesis and freeze the geometry, context,
confirmation rule, cancellation rule and expiry. Verify actual supported
source data and align timestamps. Preserve any insufficient history or
unsupported market as WAIT rather than substituting a familiar chart.

Build candidate features from the available prefix, then progress through new
observations causally. Record whether the candidate is waiting, activated,
cancelled, expired or unresolved. A new hypothesis after cancellation needs
a new candidate record; it must not silently inherit the cancelled candidate's
best prices or earlier knowledge time.

Only an actual tested paper execution model may turn an eligible event into
hypothetical position accounting. Use realistic observation delays and costs,
bounded cash risk, actual price distances and conservative ambiguity handling.
Log no-position outcomes along with losses and gains. A projected height or a
descriptive pattern cannot provide missing entry/SL/TP data.

Evaluate untouched chronological windows, retain all threshold variants and
export source hashes, anchor dates, confirmation times and rejection reasons.
Default output may be `WAIT — shape bani thi, lekin neckline se pehle
invalidation aa gayi.` The full lesson remains available when asked; the
concise answer must preserve the crucial event ordering.

## Sources

- [CME Group: Technical Patterns—Reversals](https://www.cmegroup.com/education/courses/technical-analysis/technical-patterns-reversals) — conventional repeated-extreme, neckline and shoulder vocabulary; the exact worked predicate is original HOSHI research.
- [CME Group: Trend and Continuation Patterns](https://www.cmegroup.com/education/courses/technical-analysis/trend-and-continuation-patterns) — triangle/rectangle/flag/pennant descriptions, without adopting a universal directional claim.
- [Fidelity's own Identifying Chart Patterns webinar](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/learning-center/Idenitfying-Chart-Patterns.pdf) — additional wedge and cup/handle construction context; no slides, charts, third-party statistics or proprietary course text are reproduced.
- [Binance Vision dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) and [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — Binance attribution and non-commercial educational/personal non-production use for this chapter and derived historical facts; unrelated code is not relicensed. Exact source responses and selected event receipts are preserved locally in the declared knowledge files.

# Breakouts, retests and regimes: freeze the reference and keep the failed event

Reviewed **28 October 2026, Asia/Karachi**. Educational source curriculum and
offline historical evidence only. Worked observations use **Binance Spot
BTCUSDT, USDT per BTC, daily UTC bars**. They are not current orders, fills,
calibrated probabilities or a claim that the V3 runtime is integrated.

## What is it?

A breakout is a specified crossing of a reference that was defined before the
crossing observation. A retest is a subsequent, separately specified return to
that reference or a predefined neighborhood. Without the price field, boundary
rule, comparison tolerance, event timing and expiry, both words are too vague
to reproduce. A wick briefly passing a previous high and a close finishing
above it describe different events. Neither automatically implies acceptance,
liquidity consumption, a favorable entry or a future trend.

This chapter uses one deliberately simple teaching protocol. At the close of
daily candle `t`, compute the highest wick high and lowest wick low of the
**preceding 20 complete daily candles**, excluding `t`. A close strictly above
the upper boundary is an above-boundary event; a close strictly below the lower
boundary is a below-boundary event. Equality is not a break. Every eligible
day can generate an event, so adjacent candidates can overlap. This is not
automatically a statistically independent event sample.

Freeze the broken boundary at the event. For exactly the next five daily bars,
a geometric contact occurs if `low <= frozen_level <= high`. An above-boundary
event has a close-back-across observation when a subsequent close is at or
below that level; a below-boundary event uses at or above. Record every such
date, the fifth subsequent close and its raw percentage change from the event
close. These are retrospective path measurements, not an order simulation.

In particular, a wick contact is not proof that a limit order at the boundary
would have filled. An actual strategy needs order placement time, side, size,
queue behavior, spread, fees and the path after any fill. The five-bar close
change is not strategy PnL, even when its sign agrees with the candidate's
direction. A no-contact case can produce no retest entry despite a favorable
subsequent price move.

A regime is a rule-defined description of conditions under which an experiment
is evaluated. Here it can mean rising/falling/mixed/insufficient confirmed
structure, a past-only volatility bucket, or a predefined event period. Those
descriptors must be defined before seeing the outcome. Calling a loss the
wrong regime afterward is an explanation to investigate, not a valid filter
that existed at the entry.

## Why does it form?

A reference crossing can occur because incoming trades and changing quotes
move the observed price beyond a previously recorded extreme. It can also
reflect information arrival, changing inventory willingness, forced activity,
an isolated print or a different mix of venues. A candle alone does not reveal
which explanation dominated. A useful research process keeps the observable
crossing separate from a proposed mechanism.

Carol Osler's original New York Fed research examines stop-loss and take-profit
orders at a large foreign-exchange dealing bank and relates their clustering
to different price dynamics near reference levels. That is direct evidence
about a particular order dataset, not a license to infer every BTC trader's
stops or to declare that a specific crypto wick was deliberately engineered.
The mechanism motivates a hypothesis; its transfer to another venue requires
new evidence.

Retests may occur when price revisits an earlier reference after the initial
crossing, but there is no conservation law requiring a return. Some paths move
away immediately; others cross repeatedly; still others fail before a usable
confirmation. A limit-entry model and a close-confirmed continuation model can
therefore select quite different observations. Mixing their best outcomes
creates a fictional strategy with hindsight entry flexibility.

Regime differences matter because an identical fixed distance can represent a
small fluctuation in one period and an unusually large move in another. This
does not justify assuming a particular volatility bucket is profitable. Record
the normalization, its past-only estimate and its missing-data behavior. A
threshold fitted after viewing these three examples would be a new, selected
experiment rather than an independently demonstrated improvement.

## Application zone

Use this vocabulary to design falsifiable paper studies. First specify the
reference family: a confirmed swing, prior session extreme, rolling envelope
or another point-in-time level. These references have different knowledge
times. A rolling 20-bar high can be known immediately after the twentieth
preceding bar closes; a two-right-bar swing cannot be confirmed at its own
turning candle. The current event bar must not enter its own prior envelope.

Next specify the crossing. For completed-close events, no decision is permitted
before that close exists. A historical order cannot claim the event's exact
closing price unless the execution model supplies a valid mechanism and costs.
An implementation can use the first subsequent eligible observation under a
declared model; it must preserve unavailable or delayed observations. Opening
the position at an earlier intraday extreme would consume future knowledge.

Then specify the retest while leaving the level frozen. For example, an exact
touch rule can miss a move that returns near the level but never reaches it.
A tolerance rule would define a zone, perhaps using a past-only scale, and
must record its width before evaluating outcomes. A body-overlap rule differs
from a wick-overlap rule. A close-reclaim trigger differs from both. Name the
actual predicate rather than calling all three a confirmed retest.

Choose an expiry. The next five daily bars in this teaching protocol are an
arbitrary declared observation horizon, not a universally optimal waiting
period. A study that waits until a retest eventually happens can hold an order
through unbounded changes in conditions. Decide whether the pending candidate
expires, cancels on a close back across, or requires another confirmation.
Those policies produce different samples and must not be swapped afterward.

Measure the event and its outcome on separate clocks. The historical evidence
stores `known_at` for the close-break and `available_at` for the fifth-bar
outcome. The latter must never become a feature at `known_at`. If the dataset
ends early, outcome status is incomplete and its value is null. Treating it
as zero would distort the distribution and might turn missing observations
into apparent low-risk results.

Use a regime descriptor only if it is available at the decision cutoff. A
volatility bucket needs a previously fixed calculation and history. A structural
label needs its confirmed pivots and current-price contradiction flags. A
news-event flag needs a genuinely dated announcement or scheduled calendar,
not an article published after the move. If the necessary data are absent,
record the unmeasured condition rather than assign the most convenient regime.

For execution analysis, distinguish a market-order experiment from a
limit-order experiment. Investor.gov's order guidance distinguishes execution
price uncertainty from limit-price constraints and nonexecution risk. A chart
touch is not sufficient evidence to resolve these issues. A protective stop
also does not establish that a historical exit would occur at its trigger
price when markets move abruptly. Gap and ambiguity policies belong in the
paper model before results are computed.

## Failure zones

**Moving the goalposts:** recomputing a rolling boundary after the event and
using the new value to grade its retest changes the original question. Keep
the event's boundary immutable. A later breakout can create another candidate,
but it does not rewrite the earlier one.

**Using the event bar as its own confirmation:** a large breakout candle may
trade through the boundary before closing above it. A retest rule activated
only after the close cannot claim that earlier intrabar touch. This subtle
error often makes a screenshot appear to provide an entry that the stated
method could not have taken.

**False certainty from a touch:** a contact followed by a favorable close can
still contain an adverse intrabar path or no executable fill. OHLC does not
identify the order of high and low, order queue, latency or all bid/ask quotes.
If stop and target both lie inside the same bar, the path is ambiguous without
finer trusted data. Do not award a target-first outcome by assumption.

**Ignoring the absent retest:** entering at the boundary after seeing a rally
that never returned fabricates opportunity. A strict retest model may produce
zero entries. That is a valid result to retain, especially when comparing a
patient entry policy with an immediate continuation policy.

**Outcome-based regime labels:** tagging the best examples as clean expansion
and the worst as news traps after observing their paths cannot demonstrate a
live filter. Separate an explanatory annotation from a pre-entry feature.
Historical resemblance also cannot establish that a future announcement will
produce the same sign or magnitude of response.

**Selection and dependence:** these teaching examples were intentionally chosen
to contrast contact, absence and failure. Three cases cannot estimate the
frequency of each outcome. Overlapping five-bar windows and repeated signals
during one move can inflate apparent sample size. Define deduplication or
dependence-aware evaluation before claiming statistical precision.

**Cost and risk blindness:** a move in the expected direction can be too small
after realistic costs, while a large favorable endpoint can conceal a severe
intervening drawdown. Report feasible size, losses, gaps, exposure and rejected
candidates. No pattern or regime in this chapter has a 100% success zone.

## Three real historical examples with dates

The following cases use the fixed rule above and exact source responses in
`structure_observations_20261028.json`. The offline evidence script verifies
their frozen boundaries, contact dates, close-back dates and arithmetic.
Subsequent bars are explicitly outcomes available later, never input features
at the event close. No intraday path or real order is invented.

### Example 1 — 23–28 April 2020: a contact followed by a positive fifth-close change

The preceding 20 daily bars ran from **April 3 through April 22**. Their highest
wick high was **7,459.69**. April 23 closed at **7,482.39**, strictly above that
boundary, so the event qualified only at that day's UTC close. Its own high of
**7,738.00** did not replace the frozen boundary used to evaluate the event.

The next five bars were April 24–28. The frozen **7,459.69** level lay inside
the daily high/low intervals on **April 24 and April 25**. None of those five
daily closes returned to or below the level. April 28 closed at **7,738.98**,
a raw close-to-close change of approximately **+3.4293%** from the event close.

This is a positive observed path under a fixed endpoint, not a profitable
limit-entry proof. Exact fills, stops, intraday drawdown and transaction costs
were not established. The research exercise is to reconstruct what was known
at the event and distinguish the later contact from an earlier hypothetical
entry inside the April 23 candle.

### Example 2 — 26–31 July 2021: price rose without a later boundary contact

The July 6–25 preceding window had a highest high of **35,398.00**. July 26
closed at **37,237.60**, qualifying above that frozen boundary. Its daily low
of **35,205.78** occurred inside the event bar, before a close-confirmed
candidate could be activated. That intrabar observation is not an eligible
post-event retest in this protocol.

During the next five bars, **July 27–31**, no daily high/low interval included
the frozen **35,398.00** level. July 31 closed at **41,461.83**, approximately
**+11.3440%** from the event close. The endpoint moved favorably for an
above-boundary narrative, but a strict exact-boundary retest study had no
eligible contact within its five-bar expiry.

Do not show an invented boundary fill and count that endpoint as realized
profit. A continuation model could be researched separately with its own
entry and cost assumptions. The difference between missed opportunity and a
loss is an important part of comparing models honestly.

### Example 3 — 4–9 November 2022: a retest was followed by close-back and a large negative endpoint

The October 15–November 3 preceding window's highest high was **21,085.00**.
November 4 closed at **21,148.52**, qualifying above the boundary. In the next
five daily bars, the level was contacted on **November 5 and November 6**.
The November 6 close was back at or below the frozen level, as were the closes
on November 7, 8 and 9.

November 9 closed at **15,922.81**, approximately **−24.7096%** from the event
close. A contact therefore did not guarantee continuation. A policy cancelling
on the first close-back would have a different path from one continuing to
wait; neither policy's actual fills or PnL are asserted here. The endpoint is
a raw market observation, not the loss of an implemented HOSHI position.

The case also shows why a small nominal percentage-risk setting is not an
execution guarantee. Abrupt paths require explicit gap and latency treatment.
No participant's intent, complete causal explanation or future analogous crash
probability is inferred from these candles.

## How to use it to HUNT a trade

HUNT begins with a paper-only event definition and an available supported
instrument feed. Freeze the source, timezone, prior-level rule, crossing field,
event cutoff, permitted entry policy and expiry. Reject missing or stale
inputs. These historical captures cannot justify today's NAS100, BTC or other
entry/SL/TP levels.

At the event cutoff, store only known features: the prior boundary, observed
close, structural context and any independently observed permitted filters.
Record contradictions and require WAIT when the chosen policy cannot resolve
them. Future retests and fifth-close outcomes belong in separate fields and
must remain inaccessible to the feature calculation.

During replay, advance one observed bar at a time. Distinguish contact,
confirmation, candidate cancellation, hypothetical fill and exit as separate
events. Apply a declared conservative ambiguity policy when the available bar
cannot establish sequence. Bound paper risk with actual price distances,
minimum quantities and realistic costs; infeasible candidates stay rejected.

Evaluate untouched chronological periods, preserve no-contact and negative
results, and export exact inputs and rule versions. Report performance only
when an actual position-accounting model has been tested. Default output can
be `WAIT — breakout mila tha, magar declared retest abhi nahi aaya.` A coverage
score may summarize available evidence later; it must not be relabeled as a
calibrated winning probability.

## Sources

- [CME Group: Support and Resistance](https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance) — conventional prior-level and role-change vocabulary; the exact event protocol is original project analysis.
- [Carol Osler, New York Fed Staff Report 125, April 2001](https://www.newyorkfed.org/research/staff_reports/sr125.html) — original order-clustering research in a particular FX-bank dataset, not proof of intent on Binance.
- [Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders) — order-price and execution distinctions; no order route is added to HOSHI.
- [Binance Spot kline documentation](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market) — source OHLC fields and request boundaries; exact captured responses and derived cases remain in the companion evidence JSON.
- [Binance Vision dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) and [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — attribution to Binance Vision, non-commercial education/personal non-production research and share-alike distribution for this chapter and derived evidence. Unrelated repository code is not relicensed; no sponsorship is claimed.

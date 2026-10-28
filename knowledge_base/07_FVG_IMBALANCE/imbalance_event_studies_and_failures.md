# Imbalance event studies, selection bias and failed execution assumptions

Status: original educational research, source-checked on 28 October 2026.
Historical prices are Binance Spot BTCUSDT in USDT per BTC, using native
one-minute candles. This is a bounded diagnostic study, not a trading system
backtest, creator-method certification, independent holdout or calibrated
probability estimate. All recorded decisions remain `WAIT`.

## What is it?

An imbalance event study freezes a definition, identifies every qualifying
event inside a declared sample, and records what can be observed afterward.
The purpose is to expose the distance between an attractive chart shape and
an executable trade. A candle gap can exist without a later retest. A retest
can breach the cancellation boundary. A favorable endpoint can occur after
both failures. Each observation answers a different question.

This chapter audits the original strict outer-wick gap adaptation defined in
the preceding lessons. With three completed candles A, B and C, a bullish
gap requires A's high strictly below C's low; a bearish gap requires C's
high strictly below A's low. Equality is not a positive-width gap. These
rules do not establish that every intermediate price went untraded, identify
unseen institutional orders, or reproduce all original ICT body-boundary
variants. The existing original-source attribution remains in the earlier
chapters; this study tests Hoshi's explicitly versioned arithmetic.

The population is three existing captures of 120 consecutive one-minute
candles each. Each capture supplies 118 possible three-bar decisions, giving
354 decisions altogether. Every strict gap is retained, including formations
outside the selected clock windows, those lacking warmup, and late events
without a complete future horizon. The resulting ledger contains 107 gaps
and 247 non-gap decisions. These are candle decisions, not 354 independent
trades or a random sample of global markets.

## Why does it form?

Separated outer-candle ranges describe a local price path. They can arise
during rapid continuation, a narrow preceding candle, a change in available
liquidity, or ordinary fluctuations in a continuously traded instrument.
OHLC data alone cannot separate those mechanisms. An event study is useful
because competing explanations can produce the same picture while implying
different future behavior and execution costs.

Apparent reliability can also form through the research process. If the
researcher picks an unusually large gap, extends the horizon until a return,
or ignores every gap that never receives an entry, the chart collection
changes its denominator. Selecting the first chronological qualifying event
avoids choosing its outcome afterward, but does not make the original dates
random or independent. These captures were already examined for teaching
other concepts. They remain development evidence even when every event
inside them is enumerated honestly.

Bailey, Borwein, López de Prado and Zhu's primary paper, revised
27 February 2015, explains why searching many strategy configurations can
select historical noise and produce misleading apparent performance. That
methodological warning applies here; the paper does not validate FVGs or
these particular windows. Hoshi has not calculated the paper's probability
of backtest overfitting or implemented its cross-validation procedure. A
three-window descriptive ledger cannot substitute for that analysis.

## Application zone

Use this study to inspect definitions, clocks, missingness and counterexamples
before proposing any strategy. `scripts/v3_fvg_evidence.py` reconstructs each
gap from immutable source candles. Features become possible only after C's
recorded close: `earliest_after_close = close_time + 1 millisecond`. Actual
historical provider publication and client arrival times are unknown. That
timestamp is an earliest bound, not proof that a trader could have acted
immediately at C's close price.

For each event, the outcome horizon is exactly the following five candles.
It is complete only when all five exist inside the capture. The gap's near
edge is the first edge approached from C's side; the far edge is its opposite
boundary. The ledger records first range overlap, midpoint contact, far-edge
touch or breach, and a partial contact whose close holds the midpoint in the
formation direction. Far-edge retirement takes priority over a closing hold
on the same candle. These are deliberately conservative diagnostic rules,
not assertions about the exact intrabar order of trades.

Two additional feature groups are reported separately. Clock eligibility
requires the forming bars and earliest post-close instant to remain inside
the same declared New York Silver Bullet window, with historical daylight
saving rules. Formation quality uses twenty preceding absolute candle bodies
before B, a directional B body at least 1.5 times that mean, a B close beyond
the prior five-bar extreme, and an opposite-colored origin candle in that
prior five-bar group. Missing warmup remains unknown rather than failing an
otherwise observed test. These minute-scale diagnostics do not establish
the full V2 timeframe, higher-frame trend, risk or live-input requirements.

The signed endpoint change is the percentage close change from C to the
fifth future close, multiplied by positive one for bullish geometry or
negative one for bearish geometry. It measures subsequent direction only.
It excludes entry qualification, fills, stops, position size and costs.
Never rename its positive count a win rate.

| Bounded capture, UTC | All gaps | Complete / incomplete five-bar outcomes | Contact / no contact among complete | Positive / negative signed endpoints | Clock-eligible gaps |
| --- | ---: | ---: | ---: | ---: | ---: |
| 15 May 2023, 06:30–08:30 exclusive | 46 | 44 / 2 | 38 / 6 | 14 / 30 | 22 |
| 5 January 2024, 14:30–16:30 exclusive | 37 | 36 / 1 | 24 / 12 | 15 / 21 | 15 |
| 8 August 2024, 17:30–19:30 exclusive | 24 | 22 / 2 | 13 / 9 | 15 / 7 | 12 |

The five censored tails are excluded from every complete-horizon statistic.
Their unavailable outcomes remain null, not losses, flat returns or evidence
that the market never returned after capture ended. The underlying JSON
exports every gap and its exact price path so these counts can be audited.

## Failure zones

**Endpoint substitution:** of 44 positive signed endpoints across the complete
events, 23 had no recorded contact with their gap before retirement or horizon
end. Another seven first contacted and retired on the same candle. A
directional prediction made from C and a resting gap-entry hypothesis are
different experiments. Subtracting a fee from C-to-future-close change does
not fix the missing-entry problem.

**Dependence:** five-bar observation paths overlap. The ledger identifies
59, 43 and 20 pairs of complete outcomes sharing future candles in the three
captures respectively. Each capture also contains a group of two qualified
formations reusing the same origin candle. These are not independent
confirmations merely because the gap timestamps differ. A later evaluation
needs event clustering, position-overlap rules and chronological separation;
it must not use an ordinary binomial confidence calculation on all 107 gaps.

**Confluence without execution:** quality gates qualify nine, seven and eight
formations respectively. None produces the separately defined same-bar
gap-and-origin range overlap plus midpoint hold before gap far-edge or
origin-close cancellation within a complete five-bar horizon. This is a
zero-count diagnostic under that specific rule. It is not a measured
zero-percent strategy win probability. Real trades, strategy PnL and account
drawdown remain null because no complete execution simulator exists here.

**Costs and resolution:** the receipt includes a hypothetical 30-basis-point
round-trip friction stress, not a claim about a historical Binance fee tier,
spread or realized slippage. Every observed gap width is smaller than that
assumed friction when scaled by C's close. Gap width is neither a stop
distance nor potential reward, so this comparison does not independently
prove every strategy unprofitable. It shows why small chart distances require
an explicit execution model. Tick size, quantity filters, available balance,
order priority, spread and latency still need genuine dated inputs.

**Transport and causality:** source checksums protect the captured bytes;
they do not certify complete exchange history or recreate a live feed.
Missing order-book snapshots prevent historical queue or spread reconstruction.
There is no basis for inferring manipulation, a bank's motive, an exogenous
news cause, or transferability from spot BTCUSDT to NAS100 futures or a
broker's CFD feed. No pattern works 100%.

## Three real historical examples with dates

### Example 1 — 15 May 2023: favorable endpoints after invalid entry geometry

The first fixed window is 06:30–08:30 UTC, equivalent to 02:30–04:30 New York
EDT. Its 46 gaps include six without the twenty prior pre-B candles needed
for quality assessment; forty have sufficient warmup. Of 44 complete future
paths, 38 contact their gap, sixteen show a partial closing hold before
retirement, and 28 reach the far edge. Eighteen first contact and retire on
the same candle. The latter categories can overlap over the full horizon;
they are not mutually exclusive trade outcomes.

The earliest gap, confirmed by the 06:32 candle, is bearish between 27,488.58
and 27,495.50. The 06:33 candle reaches 27,498.48 and retires it immediately
under the far-wick rule. The fifth future close, 27,470.01 at 06:37, is lower
than C's 27,482.98 close. A favorable bearish endpoint therefore coexists
with a failed gap-entry lifecycle. Across this window, five positive endpoints
have no contact and four follow same-bar first-contact retirement. These
observations explain why a screenshot of the final downward move cannot
establish an executable winning short.

### Example 2 — 5 January 2024: a closing hold before a later invalidation

The second capture is 14:30–16:30 UTC, or 09:30–11:30 New York EST. It has
37 gaps, 31 with quality warmup, and seven qualified formations. Thirty-six
complete outcomes include 24 contacts and twelve no-contact paths. There are
fifteen positive and 21 negative signed endpoints, with no exactly zero
endpoint. Those are descriptive counts, without a net-return calculation.

The first qualified bullish formation has C at 15:25 UTC and a gap from
43,730.16 to 43,750.00. Its 15:26 candle touches the near edge and closes
43,769.94, initially holding above the midpoint. At 15:27 the low reaches
43,725.61 and the close is 43,726.01, invalidating the gap under both far-wick
retirement and strict closing-breach diagnostics. The first candle whose
range also overlaps the separate origin zone appears only at 15:29, after
retirement. The fifth future close at 15:30 is 43,638.05. Contact, an initial
hold, eventual overlap and endpoint direction tell four distinct stories;
none establishes a fill at an unseen bid or ask.

### Example 3 — 8 August 2024: stronger direction counts with missing entries

The final window is 17:30–19:30 UTC, or 13:30–15:30 New York EDT. It produces
24 gaps, twenty with warmup and eight qualified formations. Twenty-two have
complete outcomes; thirteen contact and nine do not. Fifteen complete
endpoints favor the gap direction and seven oppose it. Eight of those
fifteen positive endpoints have no recorded gap contact. Therefore, even
this window's more favorable directional split does not establish the
success of a gap-retest trading rule.

The earliest bearish gap follows the 17:32 candle, with boundaries 59,681.63
and 59,708.25. Its next five candles never contact the interval; the fifth
close, at 17:37, is 59,533.59. A later first-qualified bearish formation at
17:59 does receive partial gap contact at 18:00, but its five-bar path never
also reaches the separate origin zone. The three observations—directional
continuation, gap contact and combined origin qualification—must remain
separate. The ledger records zero joint qualifying holds in this bounded
window, without manufacturing trades to make the study more impressive.

All three market dates are historical. The raw captures were retrieved on
28 October 2026 around 01:59 UTC; retrieval is not event time. Binance's
documented kline field mapping was checked on that review date. The JSON
preserves exact request URLs, raw response digests, capture bounds and
derived paths through its referenced source receipt. The study is a later
retrospective interpretation, not a forecast recorded in 2023 or 2024.

## How to use it to HUNT a trade

First freeze the instrument, venue, timezone, detector version, complete
feature availability time and cancellation convention. Keep unqualified
formations, missing-data decisions and unavailable horizons visible in the
research export. A system that records only filled winners cannot explain
its false starts or whether it waited correctly.

Next distinguish research stages. These already-inspected windows can test
arithmetic and reveal counterexamples. They cannot validate a rule selected
after reading them. A later causal replay must reserve untouched chronological
periods, prevent future candles and revised economic releases entering the
features, freeze parameters before evaluation, and account for overlapping
signals and cancelled orders. Report the number of configurations tried.
Changing the horizon or midpoint threshold after a disappointing result
requires a new version and another independent evaluation.

For paper execution, require actual supported quotes and source clocks,
available funds, realistic fees and slippage, tick and quantity constraints,
bounded risk and a documented stop/target ordering rule. If minute candles
cannot resolve whether both levels were touched in a tradable sequence,
record ambiguity or apply a declared conservative bound. Do not invent
intrabar price paths. Export decisions, rejections, costs, missing inputs,
equity and drawdown only to the extent genuinely computed.

The present conclusion is operationally simple: the evidence can teach
Hoshi when an appealing imbalance fails the data or entry gates. It supplies
no current trading levels, independently calibrated accuracy or authorization
for real orders. Missing or stale input requires `WAIT`, with
`win_probability=null`; source chapter completion does not load this study
into the runtime brain.

## Sources

Primary materials checked on 28 October 2026; paraphrased briefly, with
original study rules and calculations supplied above:

1. [Binance Spot REST API: market-data klines and field schema](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market).
   Native minute OHLC and timestamp semantics; not an execution feed.
2. [Primary native-minute capture receipt](../05_ICT_COMPLETE/ict_intraday_observations_20261028.json).
   Three exact dated requests, raw response bodies and digests; inherited
   CC BY-NC-SA 4.0 data conditions remain recorded.
3. [Complete bounded FVG event ledger](fvg_observations_20261028.json)
   and [original offline replay arithmetic](../../scripts/v3_fvg_evidence.py).
   These reproduce descriptive observations; they are not independent
   publications supporting a causal trading edge.
4. David H. Bailey, Jonathan M. Borwein, Marcos López de Prado and Qiji Jim Zhu,
   [The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf),
   version dated 27 February 2015. Methodological context only.
5. [SEC Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders).
   Stock-order price/execution distinctions illustrate a general modeling
   issue; this page is not a specification for Binance orders or fills.

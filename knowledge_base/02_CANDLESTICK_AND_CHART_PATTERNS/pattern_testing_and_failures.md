# Pattern testing and failures: separate detection, price observations and performance

Reviewed **28 October 2026, Asia/Karachi**. Original educational research, not
an integrated V3 trading engine. The measurements below use three previously
captured **Binance Spot BTCUSDT daily UTC** windows, with prices in **USDT per
BTC**. They are exploratory descriptions of already inspected data, not an
independent holdout, account backtest or proof of profitable trading.

## What is it?

Pattern testing asks a sequence of different questions. Does code recognize
the declared geometric predicate correctly? Was every input available at the
claimed decision time? What subsequently happened to observed prices? Could a
specified hypothetical order have executed? What would a bounded account have
earned or lost after costs? Does any result survive evaluation on genuinely
new data? Answering an earlier question does not automatically answer a later
one.

A unit test can verify containment, confirmation delay or missing-data handling
without demonstrating a predictive edge. An event study can describe later
prices without a fill model. A position backtest requires entry and exit
accounting, exposure, costs and ambiguity policies. A prospective paper trial
adds genuinely subsequent observations but still is not real-money execution.
Use the correct label for the evidence actually produced.

This chapter's executable illustration is deliberately an **event study**.
Version **hoshi-engulfing-endpoints-1** scans every pairwise comparison in each
source window for the original bullish-body-engulfing predicate defined in the
catalogue. There is no trend, indicator, macro or session filter. For each hit,
record its completed candle close and the close exactly five daily bars later.
Compute `100*(later_close/event_close-1)` when the later bar exists. Missing
endpoints remain null and are counted separately.

The event close is an observed price, not an assumed executable entry. These
changes are not strategy PnL or stop/target outcomes. All hits remain in the
receipt, including adverse endpoints and overlapping observation windows. A
positive endpoint count is not a winning-trade count, because no position,
quantity, fill, stop or exit policy has been simulated.

For descriptive context, the same window also reports five-bar close changes
for every eligible comparison bar with a complete endpoint. This baseline
shares observations with the pattern sample and is not an independent control
experiment. Its purpose is to show why a positive pattern-sample mean alone
does not demonstrate an advantage over the surrounding price behavior.

## Why does it form?

Apparent pattern performance can arise from actual conditional relationships,
general market direction, random variation, data problems or researcher
selection. A chart chosen because it looks impressive conditions on the outcome
before the reader sees it. An exhaustive scan within a declared window improves
transparency, but cannot make the window selection itself independent.

Bailey, Borwein, López de Prado and Zhu's original backtest-overfitting paper
examines the problem of selecting investment strategies through historical
tests and proposes a framework for estimating overfitting probability. Its
existence does not certify HOSHI's tests or make a reused holdout reliable.
This chapter does not calculate their PBO statistic or claim that one simple
split solves the selection problem.

Bailey and López de Prado's original Deflated Sharpe Ratio paper addresses
performance inflation related to selection and non-normal returns. It is
relevant when interpreting a selected performance statistic, not permission
to calculate Sharpe from unrelated, overlapping five-bar endpoints and call
it account performance. No DSR, annualized Sharpe or p-value is reported for
the small teaching samples below.

Implementation details can also manufacture results. A current bar entering
its own historical average, a future-confirmed pivot used early, a missing
observation replaced by zero or a favorable intrabar path invented from OHLC
can alter an apparent edge. These are testable software errors before they
are economic conclusions. The offline fixtures therefore preserve timestamps,
source hashes, negative results and nulls rather than only attractive charts.

## Application zone

Start with a written hypothesis and a versioned research ledger. Record the
universe, source, periods, predicate, context, decision time, observation horizon,
entry/exit assumptions if any, metrics and all variants tried. When the study
is exploratory, say so. A rule frozen after inspecting a dataset cannot be
retroactively described as preregistered on that same dataset.

Use chronological partitions for development, validation and final evaluation,
while considering event-label overlap and repeated experimentation. Training
examples whose outcomes extend into a later partition can leak information
across the boundary. Define how such observations are excluded or separated.
Any normalization, anchor selection or feature ranking must use only the
permitted earlier data. Reopening the final set to choose thresholds changes
its role; a new untouched evaluation period is then needed.

Keep timestamps explicit. A pattern can be known at a completed candle close,
while its five-bar label is known only later. Publication latency or delayed
vendor delivery can restrict availability further. Source captures downloaded
in October 2026 are not proof of exact historical feed arrival times. A
prospective trial needs actual logged observation/receipt times rather than
assuming that a historical timestamp equals instant availability.

Count the denominator honestly. Report bars inspected, recognized events,
complete outcomes, incomplete outcomes, rejected candidates and overlap.
Changing a denominator from all detections to only successful completed trades
can hide the very failures being tested. An empty sample is not zero return
with zero risk; its mean outcome is undefined. A model that never reaches
an executable trigger may produce zero positions, which must remain visible.

For this study, comparison begins at the second source bar because engulfing
needs a preceding candle. Complete five-bar baseline endpoints require five
later bars. Every detected event is retained even if it occurs near the source
end and lacks that endpoint. Forward windows overlap when their starting
event indices are fewer than five bars apart; the receipt counts all such
pairs. Counting those events as independent trades would be unjustified.

Use mean, median and the full outcome list together. A few large moves can
pull the mean away from a typical endpoint. Do not trim inconvenient extremes
after inspecting the sign. If a correction is justified by a verified data
error, preserve the original capture and document the corrected analysis as
a separate version. A genuine adverse market observation is not a data error
merely because it hurts a hypothesis.

For cost sensitivity, this illustration subtracts fixed **0.20** and **0.50
percentage points** from the raw mean, alongside a zero-deduction column.
These are deliberately hypothetical arithmetic deductions, not measured
exchange fees, spreads or realistic fills. They show sensitivity to an assumed
drag but are not net strategy returns. Actual costs require an instrument,
order mechanism, size, observation delay and appropriate source evidence.

A real paper-account simulation needs more: cash and quantity constraints,
one-position or overlapping-position rules, entry/exit prices, fees, spread,
slippage, gaps, partial fills and conservative treatment of unresolved bar
sequence. Drawdown requires a chronological equity path. Average event
endpoints cannot establish portfolio drawdown, risk of ruin or feasible cash
exposure. These runtime/evaluation gates remain pending in HOSHI V3.

## Failure zones

**Prediction inferred from recognition:** code can match its geometry exactly
while the subsequent direction is unfavorable. Recognition accuracy answers
whether the predicate was implemented, not whether its trading interpretation
works. Classifier values and evidence coverage remain distinct from calibrated
winning probability.

**Exploration mislabeled as independent validation:** these source windows and
several individual examples have already been inspected during curriculum
research. Their chronological order does not make them unseen. They can
support reproducibility and reveal failures, but cannot be promoted to a clean
final holdout. A genuinely new evaluation dataset remains necessary.

**Overlapping outcomes:** nearby events can share most of the same subsequent
bars. A common large move can affect several endpoint measurements. Reporting
many overlapping observations as a large independent sample can overstate
precision. A future strategy must additionally define whether concurrent
signals create one position, multiple bounded positions or no new entry.

**Endpoint success mistaken for tradability:** a favorable five-bar close can
follow a severe adverse path or no eligible entry. A stop might have been
crossed earlier, and a limit order might never have filled. Investor.gov's
order descriptions distinguish price constraints from execution-price
uncertainty; a candle endpoint does not resolve those mechanics.

**Missing outcomes hidden as zero:** an event near a dataset boundary can lack
its required future observations. Dropping it without disclosure changes the
denominator; filling its return with zero fabricates evidence. The receipt
stores the incomplete event explicitly and excludes it only from statistics
that require its unavailable endpoint.

**Universal thresholds and probabilities:** a positive mean in one selected
window can coexist with a negative median or a negative mean elsewhere. Cost
assumptions can alter the arithmetic sign. None of these small samples
establishes a universal win rate, a safe leverage level or a 100% working zone.
`win_probability` and `strategy_pnl` remain null in the study receipt.

## Three real historical examples with dates

Each case is an exhaustive scan **within its stated captured window**, not all
BTC history. The deterministic output and every event are preserved in
`pattern_observations_20261028.json`, referencing exact original response
hashes. All bar dates use UTC; outcomes are raw five-bar closing-price changes.
The values are calculated observations, not copied performance claims.

### Example 1 — 1 January–30 June 2020: a positive mean with a negative median

The window contains **182 daily bars**, yielding **181** adjacent comparisons.
The predicate detected **23 events**, all with complete five-bar endpoints:
**11 positive** and **12 nonpositive** endpoint changes. Their mean was
approximately **+0.06358%**, while their median was **−1.22940%**. There were
**10 overlapping forward-window pairs**.

The all-eligible-bar descriptive baseline contained **176** complete endpoints
with a mean of approximately **+1.12849%**. Neither that baseline nor the
pattern mean is a simulated account return. Subtracting the hypothetical
0.20-percentage-point deduction from the pattern mean gives approximately
**−0.13642 percentage points**. The tiny positive raw mean therefore cannot
support a robust profitability claim, especially with no execution model or
independent evaluation.

### Example 2 — 1 March–31 August 2021: a missing tail remains missing

The window contains **184 daily bars** and **183** adjacent comparisons. There
were **15 detections**, but only **14 complete endpoints**: **8 positive** and
**6 nonpositive**. **One event** lacked its required five subsequent bars and
remains explicitly incomplete. Its outcome is null, not a zero return or a
failed trade. The receipt counts **one overlapping forward-window pair**.

The observed-event mean was approximately **+2.51535%** and median **+2.89288%**.
The all-eligible-bar baseline had **178** endpoints with a mean near
**+0.36181%**. This difference is descriptive; it does not establish statistical
significance, executable returns or a calibrated signal. The window was already
viewed during research, so calling it an untouched validation set would be
incorrect regardless of the attractive raw mean.

### Example 3 — 1 May–31 December 2022: negative endpoints stay in the result

The window contains **245 daily bars**, **244** adjacent comparisons and
**19 detected events**, all with complete endpoints. There were **9 positive**
and **10 nonpositive** endpoint changes and **four overlapping forward-window
pairs**. The mean was approximately **−1.15180%** and median **−0.37554%**.
The all-eligible-bar baseline had **239** complete endpoints and a mean near
**−1.41444%**.

The pattern sample's mean was less negative than that broad baseline, but
remained negative. That does not create a profitable long strategy or prove
an advantage after risk and costs. The hypothetical 0.20-percentage-point
deduction gives approximately **−1.35180 percentage points**. Adverse results
are retained rather than relabeled as exceptional conditions or omitted from
the narrative. No account drawdown or realized loss is inferred from the
endpoint averages.

## How to use it to HUNT a trade

First ask which evidence stage has actually been reached. A pattern
recognition result or descriptive event study permits further research, not
an automatic trade. Freeze the candidate's data contract, entry/exit rules,
cost assumptions, rejection conditions and bounded paper-risk policy. Missing
current evidence or unsupported symbols produce WAIT.

Replay causally and export the full ledger: source identifiers, event and
availability times, features, candidate states, hypothetical fills if modeled,
costs, cancellations, ambiguity and outcomes. Confirm that future labels cannot
enter earlier feature calculation. Test no-event, incomplete-tail, adverse-path
and corrupted-evidence cases, not only expected successes.

Reserve genuinely new chronological observations for evaluation after the
exploratory decisions are fixed. Report sample limits, dependence, exposure,
drawdown and zero-position results honestly. A quiet candidate response can be
`WAIT — pattern study mein evidence mila hai, lekin independent validation aur
execution checks abhi complete nahi.` The knowledge may guide research
silently, but it must not hide the absence of validated performance.

## Sources

- [Bailey, Borwein, López de Prado and Zhu: The Probability of Backtest Overfitting, author-hosted version dated 27 February 2015](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) — original research on strategy selection and overfitting; its statistic is not claimed calculated here.
- [Bailey and López de Prado: The Deflated Sharpe Ratio, author-hosted version dated 31 July 2014](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) — original selection/non-normality research, not evidence that these endpoint samples constitute strategy returns.
- [Investor.gov: Types of Orders](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders) — execution-price and price-constraint distinctions; no order capability is added.
- [Binance Vision dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) and [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — Binance source attribution and original HOSHI calculations for non-commercial education/personal non-production research. This chapter and derived evidence use share-alike terms; unrelated code and cited papers are not relicensed.

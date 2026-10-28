# Backtest overfitting, chronological validation and honest negative results

Reviewed **28 October 2026, Asia/Karachi**. This chapter separates source
research, event diagnostics, executable strategy simulation and independent
evaluation. Its three historical examples reuse already inspected actual
BTCUSDT minute windows. They are explicitly **not new independent trials**.
No earlier unpushed replay prototype is assumed delivered, and no new market
replay, trained model or calibrated win rate is claimed here.

## What is it?

A backtest simulates a specified decision and execution policy on historical
inputs. A chart-pattern detector merely identifies geometry. An event study
measures paths around defined events. A strategy simulator additionally
needs information availability, entry eligibility, order assumptions,
position state, costs, cash/risk constraints and exits. Independent evaluation
then asks whether a rule frozen before inspecting the evaluation outcomes
performs adequately on a later or otherwise genuinely untouched sample.
Those are distinct evidential stages.

Overfitting occurs when choices adapt to accidental features of the research
sample rather than a relationship that transfers. Choices include thresholds,
symbols, time frames, sessions, stops, targets, exclusions and even which
performance measure gets reported. Selecting the best result from many
attempts can make a weak family look strong. Reporting only the final
configuration hides part of the selection process.

Bailey, Borwein, López de Prado and Zhu's primary **27 February 2015**
manuscript develops a probability-of-backtest-overfitting framework and
combinatorially symmetric cross-validation. That selection-risk diagnostic
is not a win probability and is not computed by HOSHI's curriculum counters.
A single holdout repeatedly inspected during development loses its intended
independence; statistical machinery also cannot repair incorrect historical
availability or fictional fills. [1]

A proposed HOSHI release therefore needs a frozen strategy version, source
and feature versions, explicit eligible population, chronological evaluation,
realistic cost assumptions and exportable evidence. A completed Markdown
curriculum or a high confluence coverage score is not that release evidence.
The requested weights describe rule coverage, with **win_probability=null**
until a separately justified calibration exists.

## Why does it form?

Every research choice offers an opportunity to adapt to noise. A rule may
look poor at one threshold and attractive after several nearby thresholds,
a new session filter and removal of an inconvenient event. Even when each
change sounds plausible, the final result incorporates information from
the failures that motivated those changes. The research log should retain
those attempts rather than treating the final rule as if it were the first.

Selection can also enter through data handling. Excluding a symbol after it
disappears, using revised macro values, ignoring missing bars, keeping only
completed winners or rolling futures with later-known information changes
the historical question. Data availability is a feature constraint, not
merely a technical detail. A Tuesday COT label does not make Friday's report
available on Tuesday; a later corrected release is not its first vintage.

Execution assumptions create another form of optimistic fit. A limit price
inside a candle's range does not prove that an order was active, had queue
priority or filled. A stop and target touched during one bar have unknown
sequence without suitable finer data. Selecting whichever order favors the
strategy is an implicit outcome-based rule. A model must predeclare a
conservative convention, mark ambiguity or exclude the candidate with the
exclusion counted; it cannot silently choose the favorable path.

Overlapping outcomes reduce independence. Adjacent five-bar event windows
can contain many of the same price changes and share an origin reference.
Treating them as unrelated Bernoulli trials understates uncertainty. A
random row split can also place future labels or closely related events
on both sides. A calendar split does not automatically solve this if labels
straddle the boundary or if the evaluation period was already used to tune
the rule.

There are economic reasons for transfer failure too. Costs, participant
behavior, constraints and competition can change. McLean and Pontiff's
primary article studies **97 published predictors** and distinguishes
out-of-sample from post-publication performance declines. Its reported
aggregate declines are research findings, not a universal discount factor
to apply to every new strategy, nor a causal estimate for HOSHI. The article
was first online **13 October 2015** and appeared in the **February 2016**
issue; those dates are distinct from its underlying predictor histories. [2]

## Application zone

Start with a research specification that can be executed without viewing
future data. Fix instrument/venue, calendar, source fields, observation and
arrival clocks, feature windows, signal timing, entry policy, invalidation,
costs and cash/risk constraints. Version the specification and hash the
source captures. Current downloaded history can reproduce arithmetic while
still failing point-in-time availability; record both facts.

Separate development, validation and final evaluation roles. Training or
research may choose parameters. Validation may compare a limited declared
family. Final evaluation is consumed when inspected; changing the strategy
after seeing it creates another development cycle. Walk-forward evaluation
must freeze each fit before its later evaluation segment. It cannot fit
normalization, thresholds or model parameters to the whole series first.

When event labels extend into the future, remove research labels that overlap
the evaluation interval and justify any separation buffer from feature/label
horizons and market dependence. These controls are not interchangeable with
ordinary random cross-validation. More sophisticated resampling must retain
relevant temporal dependence and the full configuration universe. Sullivan,
Timmermann and White's original research applies a Reality Check to an
expanded technical-rule universe; checking only the chosen winner would
answer a different selection question. [3]

Preserve a decision ledger before summarizing results. It should include
eligible decisions, insufficient warmup, stale/missing inputs, no signals,
rejected candidates, pending or unfilled orders if simulated, ambiguous
outcomes, exits and costs. Capture source time separately from decision time
and earliest possible execution time. A later bar close may confirm a
feature but cannot also supply an earlier fill at a price that preceded
confirmation.

Performance metrics require actual simulated account outcomes. Net profit
and drawdown need a marked-equity path including initial capital, open
exposure and costs. Profit factor requires a defined nonzero loss denominator;
no losing observations do not establish infinite reliable profitability.
Win rate needs a declared trade/partial-exit convention. Sharpe-style
annualization needs a return frequency, benchmark and dependence assumptions.
An event's favorable endpoint is none of these metrics by itself.

## Failure zones

The clearest failure is reporting selected source examples as a successful
backtest. A small set can teach detector timing and execution limits while
remaining useless for estimating long-run profitability. Repeating the
examples across several chapters does not increase the number of independent
observations. Neither does splitting the same explored windows after the
fact create untouched evidence.

A second failure is hiding a zero or unknown denominator. No complete trades
may result when a cautious rule is applied. Report an actual zero-trade
simulation as zero trades with undefined win rate and its sample limit.
If no execution simulation ran at all, trade count and strategy PnL are
**unknown/null**, not an observed zero-profit backtest. Hoshi's existing
minute-gap diagnostic is in this latter category.

A third failure is fitting costs to retain profitability. Fees, spread,
slippage, impact, funding, borrow, roll and settlement costs apply differently
across products. A hypothetical friction sensitivity is useful, but it is
not a measured historical fill cost. Unsupported derivatives cannot be
made executable by applying a spot fee percentage. Missing contemporary
specifications or data rights stay explicit gaps.

Mechanical unit tests cannot prove economic transfer. They can reject a
future-dependent feature, wrong units, corrupted capture or inconsistent
receipt. Successful browser/API/Docker tests can verify integration behavior.
Neither substitutes for independent chronological evaluation on a documented
population. All layers are required before the conditional final release;
content-count completion alone cannot authorize a merge.

## Three real historical examples with dates

### Example 1 — 15 May 2023, 06:30–08:29:59.999 UTC: selected winners versus a full bounded ledger

The already captured **Binance Spot BTCUSDT, one-minute** window contains
**120 bars** from **15 May 2023 06:30:00 UTC** through **08:29:59.999 UTC**.
The original strict three-candle diagnostic evaluates **118** possible
formations: **46 gaps** and **72 nongaps**. Of the gaps, **44** have complete
five-bar follow-up and **two** are censored at the window end. These counts
come from the retained source/digest-linked ledger, not an external
performance claim.

Among complete event outcomes, **14** have a positive directional endpoint
and **30** a negative one. However, **five positive endpoints had no gap
contact**, and **four** follow first-contact/retirement on the same bar.
There are **59 overlapping outcome pairs**. Selecting only favorable endpoints
would hide both missing entry geometry and dependence. These observations
do not establish filled trades or a win fraction.

The qualified joint-hold counter is zero under the declared diagnostic,
while simulated trade count, strategy PnL and account drawdown remain null
because a full execution policy was not run. Its **30-basis-point round-trip
friction** comparison is explicitly hypothetical, not a historical fee.
Original source-delivery clocks, queue priority and a genuinely independent
holdout were not obtained. A retrospective research/validation split of this
already inspected two-hour window would not change that status.

### Example 2 — 5 January 2024, 14:30–16:29:59.999 UTC: missing entries survive favorable endpoints

The second retained window covers **5 January 2024 14:30:00–16:29:59.999 UTC**
on the same venue, instrument and minute convention. It has **37 strict
gaps** among **118** possible formations, with **36** complete five-bar
outcomes and **one** censored gap. There are **43 overlapping outcome pairs**.
It is a source-captured historical window; this chapter does not claim a
fresh sample or intraday news attribution from its time label.

Of **15** positive directional endpoints, **ten** occur without a gap contact
and **two** occur after same-bar first contact/retirement. There are **21**
negative directional endpoints. The large difference between a favorable
later close and a usable entry illustrates why a price-only summary cannot
be converted into account PnL. A strategy that requires later contact could
miss the continuation entirely; inventing an earlier fill would change the
rule after seeing the result.

Again, the declared qualified joint-hold counter is zero and no independent
execution backtest has been delivered by these statistics. Historical
maker/taker costs, active order times, actual fills, market impact and a
complete strategy equity path remain unavailable. The later curriculum
capture on **28 October 2026** is not a source arrival timestamp in January
2024. All diagnostic decisions remain WAIT.

### Example 3 — 8 August 2024, 17:30–19:29:59.999 UTC: a different event mix is not a calibrated regime

The third **120-bar** BTCUSDT Spot window runs **8 August 2024
17:30:00–19:29:59.999 UTC**. It contains **24 gaps**, **94 nongaps**,
**22** complete five-bar outcomes and **two** censored gaps. Positive and
negative directional endpoint counts are **15 and seven**, with **20**
overlapping outcome pairs. The population is small, selected for teaching
and already inspected repeatedly.

Of the positive endpoints, **eight** have no gap contact and **one** follows
same-bar first contact/retirement. Only **20** of the 24 gaps have sufficient
pre-formation history for the quality features; missing warmup is not a
failed indicator with a zero value. All 24 gap widths are below the declared
hypothetical 30-basis-point friction comparison. That comparison is a scale
stress, not a forecast of net returns or proof that every possible execution
would lose.

Different endpoint counts across the three windows do not calibrate a regime
classifier or show a change in causal structure. Choosing this window because
its endpoints look better would be another selection choice. No simulated
strategy trade count, account drawdown or probability is inferred. These
three cases total **107 gaps and 102 complete event outcomes**; they remain
three bounded explored windows, not 102 independent executed trades.

## How to use it to HUNT a trade

Use a historical example to specify a hypothesis, then test its information
requirements before proposing an entry. A valid replay must know which
features existed before the decision, which source inputs were actually
available, and which later price could plausibly execute the declared paper
policy. Unsupported symbols, stale data, missing publication times or absent
execution evidence produce WAIT rather than invented entry/SL/TP levels.

Before evaluating a candidate family, freeze its definitions and preserve
all attempts. Reserve genuinely new chronological data, include realistic
cost sensitivity and adverse or ambiguous paths, and export both decisions
and outcomes. Report sample sizes, censored tails, overlap, coverage and
limits. If costs erase the apparent edge, or a complete valid simulation
produces no trades, preserve that result instead of weakening the rule until
it looks active.

Concise Roman Urdu default: **"Backtest ka selected chart proof nahi; causal
inputs, costs aur independent later evaluation ke baghair WAIT."** No pattern
works 100%, and historical resemblance is not causation. A 40/20/20/20
coverage score remains distinct from win probability; missing calibration
keeps **win_probability=null**.

The cases reproduce existing `scripts/v3_fvg_evidence.py` and
`fvg_observations_20261028.json`, linked to actual hashed minute captures.
Their existing tests check prefix timing, full-population reconciliation,
missing outcomes and corrupted/forged receipts. They do not implement a new
runtime replay or prove strategy profitability. Source chapters are not
model training or loaded knowledge; the independent evaluation and final
integration/release gates remain pending.

## Sources

Primary methodology sources and actual retained data receipts checked
**28 October 2026**. Prose and application analysis are original. Binance
Vision-derived observations/calculations retain their existing **CC BY-NC-SA
4.0**, noncommercial educational-research scope and attribution; no production
feed, commercial redistribution or model-training permission is implied.
Full papers and licensed benchmark histories are not republished.

1. Bailey, Borwein, López de Prado and Zhu, [The Probability of Backtest Overfitting, author manuscript](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf), revised **27 February 2015**: selection-risk framework. No PBO estimate or complete CSCV implementation is claimed here.
2. McLean and Pontiff, [Does Academic Research Destroy Stock Return Predictability?, primary publisher page](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365): abstract/methodological context, first online **13 October 2015**, journal issue **February 2016**. Full customer/security data and an independent replication were not obtained.
3. Sullivan, Timmermann and White, [original Financial Markets Group research page](https://www.fmg.ac.uk/publications/discussion-papers/data-snooping-technical-trading-rule-performance-and-bootstrap), dated **1 October 1998**, DP 303: expanded rule-universe/Reality Check context. This working-paper date is not the later 1999 journal date or a market event.
4. Binance, [public historical data documentation](https://github.com/binance/binance-public-data/blob/master/README.md) and [dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md). Exact historical requests, response hashes, capture clocks and source/license limits remain in `knowledge_base/05_ICT_COMPLETE/ict_intraday_observations_20261028.json`; all gap outcomes are retained in `knowledge_base/07_FVG_IMBALANCE/fvg_observations_20261028.json`. Reuse is disclosed rather than counted as new market trials.

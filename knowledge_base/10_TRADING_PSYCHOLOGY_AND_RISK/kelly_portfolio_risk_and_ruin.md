# Kelly growth, portfolio concentration and practical ruin

Reviewed **28 October 2026, Asia/Karachi**. This is bounded educational source
research with original synthetic mathematical checks. It supplies neither a
calibrated trading edge nor a recommendation to use Kelly stakes. The three
historical cases concern documented risk failures, not reconstructed Hoshi
positions. All missing original market inputs and execution paths remain
unavailable; the diagnostic decision is WAIT.

## What is it?

Kelly sizing optimizes expected logarithmic wealth growth within a specified
probability model and feasible set. Maximizing that objective is different
from maximizing the probability of a profitable next trade, minimizing every
drawdown or protecting a finite account against every possible loss. A
solution can be mathematically correct for the assumed distribution and
inappropriate when that distribution is wrong.

Nokia Bell Labs' primary publication catalogue identifies Kelly's *A New
Interpretation of Information Rate* as **July 1956**. The catalogue/excerpt
was checked; this chapter does not claim to reproduce the complete original
paper from that excerpt. For modern technical context, Busseti, Ryu and Boyd's
**19 March 2016** author manuscript explicitly separates growth optimization
from a drawdown-risk constraint. Their author's publication page records the
journal version in **Fall 2016**. Neither research guarantee transfers to an
unverified Hoshi market model. [1][2]

Portfolio risk concerns joint outcomes, not just isolated positions. Multiple
positive expected returns can share the same failure state. Diversification
therefore depends on exposures, dependence, tail behavior and ability to
rebalance, rather than counting ticker symbols. An unlevered cash position
has a different feasible set from a margined derivative or a portfolio with
shorts. This curriculum enables none of those real execution capabilities.

Ruin needs a definition. It might mean zero wealth, crossing a minimum
operating balance, a margin default, a drawdown ceiling or inability to fund
obligations when due. Those events are not interchangeable. A fractional
model can stay strictly above zero after any finite sequence of losses yet
cross a practical survival threshold long before mathematical zero. A
liquidity failure can arrive before a long-horizon valuation thesis resolves.

## Why does it form?

Consider an original two-outcome teaching model. A fraction f of equity is
lost on failure; success earns b times that amount, with probability p.
Assume p is known, outcomes follow the declared repeated model, costs are
already included in b and the loss convention, and no outcome destroys more
than the assumed fraction. Wealth multipliers are 1+b*f and 1-f.
Expected log growth is:

`g(f) = p*log(1+b*f) + (1-p)*log(1-f)`.

Differentiating and setting the derivative to zero gives
`f* = (b*p - (1-p))/b`. For a long-only no-borrowing mathematical exercise,
a negative result is replaced with zero. A boundary, drawdown constraint,
uncertain probabilities, multiple outcomes or different loss distribution
changes the problem. This derivation is not a general strategy recognizer.
A stop-defined chart reward multiple is not automatically a realized binary
payoff b because slippage, partial exits and missed fills change outcomes.

Take explicitly invented **p=0.55**, **b=1**. The binary optimum is **f=0.10**.
The original checker computes expected log growth near **0.00500837** per
trial at that fraction, but approximately **minus 0.00013774** at twice the
fraction. If the true hypothetical p were instead **0.51**, staking the same
0.10 would produce approximately **minus 0.00301846** expected log growth.
These are natural-log model values, not percentage returns, empirical
forecasts or an actual Hoshi win rate. The example demonstrates sensitivity
to overbetting and estimation error; it does not license a ten-percent risk
setting in Hoshi's bounded paper engine.

Fractional Kelly scales a model's allocation, often to reduce sensitivity or
risk. Scaling down does not make a false edge true, prove an acceptable
maximum drawdown or protect against outcomes excluded from the model.
Sun and Boyd's **December 2018** author note instead examines a distributional
uncertainty set and a worst-case log-growth objective. Its set must still be
justified; placing the true distribution outside the set can invalidate the
intended protection. No robust optimizer is implemented here. [3]

Dependence also changes portfolio arithmetic. In an original two-asset
example, each return variance is assumed **0.04**, and weights are **0.5/0.5**.
At zero covariance, portfolio variance is **0.02**. At perfect positive
correlation with those equal variances, it is **0.04**. Two holdings then
provide no variance reduction in this example. These assumed variances have
no estimated time horizon or market dataset attached; they are algebraic
fixtures. Correlation and covariance estimates from actual dated returns
would need their own sampling, synchronization and uncertainty analysis.

## Application zone

Use growth arithmetic to test whether a proposed sizing argument is internally
consistent. Ask where p and the payoff distribution came from, which costs
are included, how losses exceed the stop assumption, and whether independent
chronological evaluation supports the estimates. If p comes from a confluence
coverage score or a handful of selected textbook winners, Kelly cannot turn
that number into a calibrated probability. Hoshi's requested 40/20/20/20
weights are not p.

Stress lower success probabilities, worse payoff ratios, clustered losses,
spread expansion and inability to exit together. Record outcomes in the
account currency and preserve cash needed for obligations. A high expected
terminal wealth can coexist with unacceptable intermediate losses. Growth,
terminal-loss probability, maximum drawdown and cash shortfall should be
reported separately rather than compressed into one confidence label.

For an original repeated-loss illustration, ten losses of **10% of current
equity** leave about **34.8678%** of the initial balance. Ten losses of **5%**
leave about **59.8737%**. Neither calculation assumes a rebound. Reducing the
fraction reduces this particular damage, while the appropriate practical
ruin threshold remains a separate account constraint. A fixed money stake
would create a different sequence and can exhaust the account sooner.

Even streak probabilities require precise questions. With invented independent
win probability **0.55**, one specified block of ten losses has probability
approximately **0.0003405063**. The probability of **at least one run of ten
losses anywhere in 100 trials** is approximately **0.01708002**, from an exact
finite-state recurrence. Overlapping runs prevent simply multiplying the
first number by the number of possible starting positions. Real trading
losses need not be independent or identically distributed. These are
mathematical model probabilities, not forecasts of Hoshi's loss sequences.

A later portfolio workflow should retain a versioned joint scenario set,
concentration limits, cash reserves and suspension rules. Covariance matrices
must have coherent units and be positive semidefinite. Missing exposure or
unknown cross-market positions cannot be filled with zero. A proposed hedge
whose prices, contract multiplier or correlations are unsupported should
remain unsupported rather than being assigned a convenient negative
correlation.

## Failure zones

The binary Kelly formula fails as a description of a trade when outcomes
are not binary in the stated units. A win can have many magnitudes; a losing
exit can gap beyond one unit. A trade can remain open, partially fill or
be suspended. A model that omits those outcomes can overstate growth even
when its arithmetic has no error. Confidence in the formula is not evidence
that the market obeys the formula's assumptions.

Estimated probabilities are especially fragile after strategy selection.
Trying many patterns and choosing the best observed winner changes what a
reported win fraction means. The fraction can reflect selection noise,
overlap or a particular regime. Reducing an overfit allocation by half does
not create an independent test. Holding out later data and preserving the
full research search history remain necessary validation tasks.

Portfolio models can fail through concentration, changing dependence,
funding needs and price impact. A quoted mark is not a commitment by another
party to buy the entire position. A covariance estimate cannot reconstruct
missing counterparty exposures. A model that assumes all participants can
rebalance at historical midpoints may systematically understate the adverse
state where many participants want to sell together.

Drawdown is path dependent. In a synthetic account starting at 100, returns
**+50%, −20%, −20%** and **−20%, +50%, −20%** both finish at **96**. The first
path has a **36%** maximum drawdown from its running high, the second **20%**.
The checker includes initial wealth in the high-water mark, so a first-trade
loss is not omitted. These paths are not historical trades. They show why
final balance cannot substitute for a complete marked-equity path.

No growth or risk model works 100%. A claimed guarantee must be restricted
to the mathematical assumptions under which it was derived, and cannot be
advertised as guaranteed market profitability or a physical protection
against a gap. Missing calibration produces **win_probability=null**, not a
plug-in estimate chosen to support the preferred quantity.

## Three real historical examples with dates

### Example 1 — August–September 1998 LTCM stress, discussed on 1 October 1998

Alan Greenspan's **1 October 1998** testimony describes LTCM's use of repo
and derivatives leverage, substantial losses as conditions diverged from
historical patterns, and concern that disorderly liquidation could impair
market liquidity. It reports that about half its capital had been lost by
the end of August. It also states that the Federal Reserve put no funds at
risk in facilitating private discussions. The testimony date is not the
first date of the losses or an original trade timestamp. [4]

Original analysis: a convergence thesis can become impossible to carry when
funding, uncertainty and the joint behavior of others change. Low historical
spread volatility does not independently establish a small adverse cash
requirement. Growth optimization based on that historical sample can become
irrelevant if financing ends before the position can be maintained to its
assumed horizon. A portfolio can contain numerous trades yet depend on the
same funding and liquidity conditions.

The selected source does not provide a complete timestamped position book,
independent pricing history, realized execution costs or an implementable
point-in-time Kelly probability. No simulated LTCM trade ledger or claim
that a different sizing formula would certainly have prevented the crisis
is delivered. It is a documented stress case for the assumptions, not a
calibrated trading analogy.

### Example 2 — 26 March 2021 Archegos default, report published 29 July 2021

The externally investigated report commissioned by Credit Suisse's board,
published **29 July 2021** and filed with the SEC, describes its termination
notice effective **26 March 2021**, the ensuing unwind, and approximately
**5.5 billion USD** of Credit Suisse losses from the default/unwind. It
identifies concentration and failures to control and escalate risk. This is
a reported bank loss aggregate, not a direct calculation of every Archegos
customer's return or an exchange quote. [5]

Original analysis: one dealer's observed client positions may be an
incomplete view of the total exposure. Estimating independent position risk
from that partial book can understate joint liquidation needs. Repeated
limit exceptions change the effective feasible set: the formula written in
a risk policy no longer describes the positions actually permitted. A
constraint that is recorded but repeatedly bypassed is not an enforced cap.

The July investigation could not have been an available input to a March
trading decision. The chapter neither diagnoses an individual's psychology
nor reconstructs hidden intent, complete swaps, all broker books or exact
sale paths. It does not infer a win probability from the later failure.
Without actual dated inputs a purported historical match remains narrative
context and cannot generate a trade.

### Example 3 — 23 September–14 October 2022 UK LDI liquidity stress

The Bank of England's **13 December 2022** Financial Stability Report
reviews the gilt/LDI episode. For **23 September–14 October**, it estimates
sales of about **14 billion GBP by defined-benefit pension schemes** and
**23 billion GBP by LDI funds**, alongside combined margin/collateral calls
in excess of **70 billion GBP**. Those source categories and their common
observation window must remain distinct; the calls are not simply equal to
gilt-sale proceeds. They are later reported aggregate estimates, not one
fund's high-frequency account path. [6]

Original analysis: managing long-horizon liability exposure and funding
short-horizon collateral are different tasks. A portfolio may be intended
to hedge an economic sensitivity while still requiring cash rapidly after
adverse moves. Forced sales can then interact with price changes and other
participants' simultaneous needs. A model of final wealth that excludes
that intermediate cash constraint can miss the relevant survival event.

No individual pension fund's complete exposures, valuation times, collateral
agreement, financing cost or actual liquidation sequence was retrieved here.
The source's later estimates are not a contemporaneous signal. This case
therefore cannot certify a particular hedge ratio, acceptable leverage or
profitable advance short. Hoshi's paper spot scope remains unchanged; the
lesson is to keep funding and portfolio stress constraints explicit.

## How to use it to HUNT a trade

Before assigning size, require a supported candidate and genuine time-stamped
inputs. Ask whether the available sample independently estimates a payoff
distribution or merely contains selected demonstrations. If calibration is
absent, do not substitute the requested weighted confluence score for p.
Keep the output **WAIT** when required inputs are missing, stale or
unsupported. Historical resemblance does not establish causation.

For a later bounded paper experiment, evaluate conservative cost and adverse
path assumptions, aggregate existing exposures, and preserve suspension or
practical-ruin events. Test uncertainty in probabilities and correlations
rather than optimizing a large stake around one fitted estimate. Report
negative growth estimates and zero-trade results as results. An unknown
probability stays unknown even when the hypothetical calculator accepts a
number for a labelled classroom exercise.

Concise Roman Urdu: **"Kelly ke liye calibrated edge aur loss distribution
chahiye; confluence score win probability nahi. Missing evidence par WAIT."**
The original offline `scripts/v3_risk_evidence.py` and adjacent
`risk_arithmetic_20261028.json` reproduce the synthetic growth, finite-run,
portfolio-variance and drawdown counterexamples. Tests include independent
full enumeration of a small streak problem, input boundaries and forged
receipt rejection. They are not market replay, independent strategy
evaluation, model training or runtime integration. Real orders and leverage
remain disabled.

## Sources

Primary sources checked **28 October 2026**. Brief attributed research/event
facts are separated from original derivations and hypothetical examples.
No full copyrighted paper or report is republished in the repository.

1. Nokia Bell Labs, [A New Interpretation of Information Rate](https://www.nokia.com/bell-labs/publications-and-media/publications/a-new-interpretation-of-information-rate/): catalogue date **1 July 1956** and limited excerpt; full original-paper review is not claimed.
2. Busseti, Ryu and Boyd, [author manuscript, Risk-Constrained Kelly Gambling](https://stanford.edu/~boyd/papers/pdf/kelly.pdf), dated **19 March 2016**; [author publication page](https://web.stanford.edu/~boyd/papers/kelly.html) and [author-submitted version](https://arxiv.org/abs/1603.06183), submitted **20 March**. Mathematical risk constraints are conditional on the declared distribution and model.
3. Sun and Boyd, [Distributional Robust Kelly Gambling](https://web.stanford.edu/~boyd/papers/robust_kelly.html), author note **December 2018**: uncertainty-set context, not a delivered optimizer or promise of profitable robustness.
4. Federal Reserve, [Greenspan testimony on LTCM](https://www.federalreserve.gov/boarddocs/testimony/1998/19981001.htm), **1 October 1998**: retrospective account of earlier stress and private-sector refinancing.
5. Credit Suisse Special Committee, [Report on Archegos Capital Management](https://www.sec.gov/Archives/edgar/data/1053092/000137036821000064/a210729-ex992.htm), **29 July 2021**, executive summary and default/unwind sections. This is a commissioned investigation, not a judicial finding of every disputed matter.
6. Bank of England, [Financial Stability Report, December 2022](https://www.bankofengland.co.uk/financial-stability-report/2022/december-2022), published **13 December 2022**, LDI discussion and footnotes 13–14: defined windows and aggregate collateral/sale estimates.

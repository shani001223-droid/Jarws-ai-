# Position sizing, loss budgets and failure of a planned stop

Reviewed **28 October 2026, Asia/Karachi**. This chapter teaches bounded paper
risk arithmetic and three documented historical risk events. It is not an
order facility, account recommendation, live quote or performance forecast.
The historical events are not claimed as reconstructed customer trades;
missing quotes, fills, spreads and original arrival times stay missing.

## What is it?

Position sizing converts an explicitly limited loss budget into a quantity
under stated price, cost and execution assumptions. A position's notional,
its modeled stop loss, the cash needed to acquire it and its possible stressed
loss are different quantities. Confusing them is dangerous even in a paper
backtest. A small percentage stop does not automatically mean a small account
loss if the quantity is large or the exit cannot be obtained.

A fixed-fraction convention reserves a fraction of account equity for a
modeled adverse outcome. The often named **1% rule** is such a convention,
not a scientific optimum, a guaranteed maximum loss or permission to risk
that amount on every correlated idea. This curriculum does not set personal
financial suitability. The existing Hoshi paper-risk implementation accepts
hypothetical risk percentages from **0.1% through 1%**, uses bounded fee and
slippage assumptions, and remains long-only cash-capped BTC/ETH spot research.
Those source limits are implementation choices, not evidence that every
accepted setting is profitable.

A loss limit is a suspension rule as well as an arithmetic boundary. A
per-trade budget constrains a candidate; a portfolio budget constrains
simultaneous exposure; a daily budget constrains additions after losses.
A drawdown rule compares marked equity with its past high-water mark.
None can guarantee execution during a discontinuity. Their calculation must
include open exposure, not merely completed trades showing realized losses.

The SEC's stock-order bulletin distinguishes a stop trigger from the later
market execution. A stop-limit introduces a price condition but can remain
unexecuted. Broker trigger conventions can differ. Those stock-order
explanations do not certify the behavior of every crypto, OTC currency or
futures venue. An instrument-specific execution specification is still
required. [1]

## Why does it form?

A trading hypothesis can fail before or after its geometric invalidation.
A wrong directional view, wider spread, missing liquidity, data error,
contract event or delayed response can each increase the eventual loss.
Position sizing cannot repair the hypothesis; it determines how much the
paper account is exposed if the assumed path occurs. Using more size to
compensate for weak evidence reverses that purpose.

For a cash-funded long illustration, define equity E, a fractional budget r,
reference entry P, reference stop S below P, proportional fee f on each leg,
and assumed adverse slippage s on each leg. Estimated entry is P times
(1+s); estimated stop execution is S times (1-s). Modeled loss per base unit
is their difference plus f times their sum. Thus fees apply to both entry
and exit notionals. This linear model is an assumption, not a measured
market-impact function or an assertion that slippage is bounded by s.

The risk-limited quantity is E times r divided by modeled loss per unit.
The cash-limited quantity is available cash divided by estimated entry cost
including its fee. Take the smaller quantity and round down under a declared
precision convention. If a real venue's minimum size or minimum notional
cannot be met within both limits, reject the candidate rather than rounding
up. Hoshi's existing eight-decimal paper rounding is not an exchange-filter
certificate. A valid venue order and a mathematical quantity are separate.

A purely synthetic calculation makes the units visible. Assume **100 USDT**
equity, **0.5%** budget, reference entry **100**, stop **98**, **10 basis points**
fee and **5 basis points** adverse slippage on each side. The assumed entry
is **100.05**, the assumed stop fill **97.951**, and modeled loss per unit
**2.297001 USDT**. The risk budget is **0.50 USDT**. These invented teaching
inputs are not observed BTC prices or one of the historical cases below.
A different exit, fee tier or gap changes the loss; the budget calculation
cannot establish that such an exit was executable.

Losses also change the denominator. Repeatedly applying a fraction to current
equity reduces absolute stake after losses, whereas retaining a stake based
on the original equity increases its effective fraction as equity falls.
After a fractional drawdown d, the gain needed to recover is d divided by
(1-d), for d below one. A 20% decline therefore needs 25% recovery. This is
accounting, not a prediction that recovery will occur.

## Application zone

Begin sizing only after validating the instrument, observation times and
hypothesis. The existing `cloud_backend/paper_risk.py` requires compatible
closed-candle assessment, structure and indicator snapshots before a plan.
Missing support, unusable stop geometry, mismatched symbols or snapshots,
invalid settings and excessive modeled costs can produce WAIT or a bounded
input error. A positive watchlist status alone is not permission to trade.
The chapter does not bypass or enlarge those runtime gates.

For a later portfolio implementation, reserve budget for every open paper
position and pending candidate before accepting another. Use one account
currency and document conversion times. If reserves already consume the
portfolio or daily allowance, the new quantity is zero even when its
individual setup looks attractive. Reserves must not be released merely
because a planned stop moved on a chart; the position and actual cancellation
state would need to be known. This is a proposed accounting requirement,
not a delivered persistent account ledger.

Define daily loss from an explicit session boundary and equity convention.
UTC midnight, a New York session boundary and a broker statement day are not
interchangeable. Include costs and marked open losses; distinguish deposits
or withdrawals from trading performance. A daily suspension means no new
risk after the threshold, not a promise to liquidate everything exactly at
that threshold. A run that crosses the limit because of a gap should record
the breach, not rewrite the path to stop at the desired number.

Stress the quantity against adverse prices beyond the chosen stop and
against reduced ability to exit. For derivatives, contract multiplier,
settlement method, expiry, collateral and nonlinear exposure require a
different validated model. Hoshi's cash-funded spot arithmetic does not
cover them. Positive-price restrictions appropriate to spot must not erase
a genuinely negative futures observation in historical research. Unsupported
products remain unsupported rather than receiving a guessed conversion.

## Failure zones

A tight stop can inflate risk-based quantity precisely when bid/ask costs
are a large part of the intended distance. Ignoring those costs overstates
both size and reward-to-risk. Widening a stop after entry changes the original
loss budget; increasing quantity to recover recent losses changes it again.
Neither is justified by a confidence label. Reward multiples are geometric
reference distances, not probabilities of reaching a target.

A stop cannot protect against every gap, suspension, platform outage,
contract termination or impaired counterparty. Cash caps reduce one class
of overspending; they do not make every instrument's maximum loss equal to
cash spent. A physically delivered derivative and a cash purchase have
different obligations. Historical stress scenarios must preserve those
product differences rather than recycling a spot formula everywhere.

Portfolio limits fail when positions share a hidden driver or use stale
marks. Adding nominal individual budgets assumes more than the data show
if the same shock moves everything at once. Conversely, counting unrealized
profit at an unachievable quote as new available risk can expand exposure
on an accounting illusion. Correlation and liquidity uncertainty belong in
stress analysis; a single recent sample correlation is not an insurance
contract.

Implementation errors can be equally costly: confusing percent with a
fraction, using basis points as whole percentages, mixing base and quote
units, treating missing equity as zero or accepting nonfinite input. A validation
layer should reject those inputs before requesting market data. A missing
account balance is an unavailable risk input, not evidence that there is no
existing exposure. Likewise, stale or differently timed snapshots should
fail identity checks before their prices reach the sizing formula.

## Three real historical examples with dates

### Example 1 — 15 January 2015: a policy boundary is not a guaranteed stop

The Swiss National Bank's release dated **15 January 2015** announces the
end of the **CHF 1.20 per euro** minimum exchange rate and a sight-deposit
interest-rate reduction to **minus 0.75%**. The document concerns a monetary
policy decision, not a broker's guarantee to fill a customer's EURCHF exit.
The market is OTC foreign exchange rather than one consolidated exchange
with a universal event high and low. The selected release supplies a date;
this chapter does not invent an intraday publication timestamp. [2]

The risk lesson is a change in the conditions supporting an exposure. A
position model that treats the prior policy boundary as an immutable price
floor lacks a scenario for the boundary being withdrawn. A small apparent
stop distance under that model can encourage disproportionately large size.
That is an original risk inference from the policy change, not a reconstructed
customer liquidation or evidence of the central bank's intent toward retail.

Exact historical bid/ask paths, venue, customer positions, stop instructions,
broker execution rules, fills and account losses were not obtained here.
No percentage currency crash, guaranteed exit failure or profitable advance
signal is assigned. A paper replay with only this announcement and no
appropriate contemporaneous prices must remain WAIT. The case supports
stress-testing the assumptions behind the boundary rather than pretending
that an assumed fixed-fraction stop would have enforced the desired loss.

### Example 2 — 5–15 February 2018: XIV terms and changing operational dates

Credit Suisse's issuer release dated **6 February 2018**, filed as an SEC
exhibit, states that an acceleration event occurred after XIV's **5 February**
intraday indicative value reached no more than **20% of the prior closing
indicative value**. That statement concerns the issuer's indicative-value
condition, not a measured investor sale price or a Bitcoin/equity signal.
The release initially expected the last trading day to be **20 February**
and described expected valuation/payment dates. [3]

Nasdaq's **14 February 2018** trader alert subsequently states that trading
would halt after the market close on **15 February**. The publication dates
and differing operational information matter: a replay must not give the
later notice to an earlier decision. Nor may it silently treat the first
expected schedule as a verified final trading calendar. The alert concerns
Nasdaq-listed **XIV ETNs**, not direct ownership of the VIX or an ordinary
cash equity exposure. [4]

Original interpretation: a loss process can involve a contractual event and
loss of trading availability as well as a continuous chart move. Sizing
solely from a nearby candle low misses that dimension. No order-book history,
stop execution, investor cost basis or final payment calculation is supplied
in this case, so no account return is manufactured. Hoshi does not gain
permission or capability to trade this discontinued instrument by learning
its history. The defensible action is to require versioned contract and
trading-status information in any applicable research model.

### Example 3 — 20 April 2020: negative May WTI settlement breaks a zero-floor assumption

CFTC staff's interim report, **published 23 November 2020**, documents the
**NYMEX May 2020 WTI futures contract** settling at **minus 37.63 USD per
barrel on 20 April 2020**, before expiry on **21 April**. Its defined April
20 event session runs from **18:00 Eastern on 19 April to 14:30 Eastern on
20 April**. This is a dated futures-contract settlement observation, not a
negative retail pump price, a Cushing spot quote or an executable fill for
every participant. The report is interim staff analysis, not a finding that
one cause or manipulation explains every price movement. [5]

Original risk inference: a model that assumes this contract cannot pass
zero would censor a relevant adverse scenario. Risk calculated only as a
percentage of a positive price becomes especially misleading across zero;
contract price differences and a verified multiplier are needed instead.
Margin deposited is not a complete description of delivery and variation
exposure. The existing Hoshi spot model does not support this product, and
this chapter does not extend it to futures or enable leverage.

No historical Hoshi position, barrel exposure, broker margin schedule,
execution queue or customer liquidation was captured. The observed settlement
cannot be relabelled as an achievable stop exit or a trading return. The
November report also was unavailable on the April event date. A replay must
separate what later investigators documented from what the decision maker
could have known before the event. The proper response to missing contract
or execution inputs is WAIT, not a fabricated oil entry and stop.

## How to use it to HUNT a trade

A valid paper candidate begins with observable evidence and a defined
invalidation, then passes data, cost, cash and risk checks. Set the loss
budget before choosing quantity. Compute entry and adverse-exit assumptions
with consistent units, include both legs' fees and test a gap beyond the
reference stop. If required current observations, usable support or contract
specifications are missing, reject the candidate rather than making the
numbers look precise.

Next check aggregate reserves and the daily suspension state. A new setup
cannot replenish an exhausted budget just because its pattern resembles a
historical winner. Keep hypothetical prices and actual observations labelled
separately in exports. A replay must retain breaches, zero-trade periods,
ambiguous fills and drawdown rather than editing outcomes to meet a desired
risk limit. Independent chronological evaluation remains a later release
gate, not something established by these historical illustrations.

Default concise Roman Urdu: **"Stop guaranteed fill nahi; current data,
costs aur bounded paper budget verify na hon to WAIT."** Any later weighted
confluence output must preserve **win_probability=null** until independently
calibrated. No risk model works 100%, and no real orders, leverage, purchases
or paid data access are enabled. This source chapter is not model training
or loaded runtime knowledge.

## Sources

Primary documents actually checked **28 October 2026**; original prose and
risk inferences are separated from reported event facts. Historical notices
are not current trading-status feeds. Source code references above concern
the existing `cloud_backend/paper_risk.py`, its existing tests, and the
separate pending release gate; no runtime behavior was changed.

1. SEC Investor.gov, [Stop, Stop-Limit, and Trailing Stop Orders](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15), originally **13 July 2017**, page updated **18 August 2026**: stock-order trigger/execution and nonexecution distinctions.
2. SNB, [15 January 2015 release](https://www.snb.ch/en/publications/communication/press-releases/2015/pre_20150115), including its [original PDF](https://www.snb.ch/public/asset/en/www-snb-ch/publications/communication/press-releases/2015/pre_20150115/publications0_en/pre_20150115.en.pdf): withdrawal of the exchange-rate minimum.
3. Credit Suisse, [XIV acceleration release, SEC exhibit](https://www.sec.gov/Archives/edgar/data/1053092/000095010318001572/dp86358_ex9901.htm), **6 February 2018**: indicative-value condition and then-expected dates. A different same-date issuer coupon release is not this document.
4. Nasdaq, [Equity Trader Alert 2018-13](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2018-13), **14 February 2018**: later halt notice, not an execution-price history.
5. CFTC, [Interim Staff Report on NYMEX WTI](https://www.cftc.gov/media/5296/InterimStaffReportNYMEX_WTICrudeOil/download), published **23 November 2020**, introduction/footnote 2 and executive summary; [publication announcement](https://www.cftc.gov/PressRoom/PressReleases/8315-20). The report's later publication is distinct from the April event.

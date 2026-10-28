# Historical liquidity cases and execution: price observations are not fills

## What is it?

An execution study asks what could actually have been bought or sold, in what
quantity, at what cost and after which information became available. A chart
study asks what prices were recorded. Both can be useful, but they answer
different questions. A bar reaching a proposed target does not establish an
entry fill, and a final close cannot reveal which of two intraday barriers was
crossed first. Hoshi must retain those gaps rather than converting every
attractive price path into a trade result.

The checked SEC execution guidance explains that order handling takes time and
the displayed price applies to limited quantity; it is not an instant universal
fill promise. Its separate stock stop-order bulletin distinguishes activation
from execution price. Binance's checked primary filter documentation separately
defines symbol price increments, quantity increments and notional constraints.
These sources motivate the required checks. They do not supply the account's
historical fees, the selected dates' filter snapshots or a complete executable
book for the cases below.

This chapter adds **unfilled barrier and cost illustrations**, not a trading
engine or account backtest. A frozen event close is an observed analytical
reference. Hypothetical long-side price barriers sit one percent below and two
percent above it. The following five daily bars reveal which reference ranges
were reached, while the actual ability to enter at the old close remains
unknown. No real purchase, borrowed position or leveraged exposure is enabled.

## Why does it form?

The gap between an observed price and an executable trade starts with timing.
A completed candle becomes known only after its close, plus provider and device
delay. An instruction based on that close cannot simultaneously assume it was
already resting at that price beforehand. Subsequent transactions may revisit
the price, but an order's position in the queue and available opposing quantity
still matter. A bar's high-low interval does not resolve those conditions.

Execution costs also depend on the instrument, venue, order type, size and
market state. Fees can differ across accounts; spreads and slippage can change
within a session. Some costs are explicit, while others appear as a difference
between a decision reference and the obtained price. In a stress event, a fixed
small slippage allowance may understate the possible deviation. No historical
spread or fee is fabricated from daily OHLC observations here.

Stop and target ambiguity is a separate problem. If a later candle spans both
barriers, its open and close generally do not identify the full intrabar route.
Assuming the target happened first biases an evaluation upward; automatically
assuming the stop happened first is conservative but still a modeling convention.
Hoshi's illustration exports the ambiguity without assigning either payoff.
Higher-resolution data may reduce uncertainty, but even a trade tape does not
guarantee a particular resting order filled.

Risk sizing can conceal the same distinction. A planned loss amount assumes
some entry, exit and cost behavior. It is a budget under that model, not a
guaranteed maximum realized loss. A gap beyond a stop, delayed observation,
unavailable market or failed execution can invalidate the assumptions. The
first job of a robust study is to identify those failures, not to report a
precise percentage from a model whose entry never existed.

## Application zone

The original offline method is **hoshi-unfilled-barrier-cost-illustration-1**.
For each selected event, freeze the completed close E. Set the hypothetical
long-side stop reference to **0.99E** and target reference to **1.02E**. These
are deliberately simple comparison barriers, not optimized strategy parameters,
liquidity targets or prices offered to the user as an order ticket. The feature
is logically available after the event closes; actual provider arrival is null.

Only the next five completed daily bars form the outcome window. Check each
opening price first. An open at or beyond a barrier is recorded as an opening
gap/reference condition rather than a guaranteed fill at the barrier. Otherwise,
if the range reaches both barriers, retain an ambiguous same-bar result. If it
reaches just one, record that reference first. Stop the barrier classification
there instead of overwriting an earlier event with a more favorable later one.
If neither is reached, preserve no barrier event. Missing future bars produce
a null outcome.

For cost sensitivity, use hypothetical combined fee/slippage charges of **0,
5, 15 and 50 basis points per leg**. These are assumptions for comparison,
not current Binance rates or measured historical costs. For a long position
referenced to E and a common per-leg fraction c, modeled loss per unit at the
stop is **E − 0.99E + c(E + 0.99E)**. Modeled gain per unit at the target is
**1.02E − E − c(E + 1.02E)**. Costs are applied to both legs at their respective
reference prices, so the two cost amounts differ slightly.

The illustrative account has **10,000** quote-currency units, a **50-unit**
planned loss budget and a **10,000-unit** cash cap. The unrounded quantity is
the smaller of budget divided by modeled loss per unit, and cash divided by
entry cash required per unit including entry cost. Thus the model neither
borrows cash nor exceeds its planned stop-loss budget under its own assumptions.
It does not claim an exchange-valid quantity: actual historical filters and
minimum notional were not obtained.

The gross target-to-stop distance is 2:1. At fifteen basis points per leg,
the net modeled target-gain/stop-loss ratio falls to approximately **1.30689:1**.
This ratio is arithmetic, not an expectancy or a win probability. Expected
performance would also require reliable event frequency, entries, path outcomes
and costs. No combination of this sizing example and a target touch supplies
those missing observations.

## Failure zones

**Entry before information:** an event-close reference is not a fill available
after the event closes. The illustrations retain `entry_at_reference_proven=false`.
A future paper implementation needs actual post-decision prices and a causal
order policy. It must not assign the old close simply because that makes
the backtest convenient.

**Same-bar optimism:** a candle spanning both stop and target cannot be called
a win from daily data alone. Its close can be favorable after an unfavorable
earlier excursion. Hoshi keeps the ambiguous classification and null strategy
PnL. This is not a conservative zero loss or a profitable zero-trade result;
there is no reconstructed account path at all.

**Stop-price certainty:** an opening price beyond the stop changes the available
reference. Treating the stop level as an assured exit would cap an adverse
move using a price that may not have been executable. The same issue affects
gaps beyond a target or entry trigger. Preserve the gap condition and require
the appropriate execution model instead of silently filling at the old level.

**Fee substitution:** historical assumptions cannot become current venue fees,
and a current account fee cannot automatically describe an older period.
A fixed cost sensitivity is useful for identifying fragility, not proving
actual transaction costs. If the result depends on a small change in a guessed
cost, report that dependency and obtain better data before drawing conclusions.

**Quantity precision:** a long decimal quantity can satisfy an algebraic budget
while violating a lot-size step. Rounding up can exceed risk or cash caps;
rounding down may fall below minimum size. Real filters need timestamped
symbol-specific evidence. This chapter deliberately does not emit an executable
quantity or change any runtime order capability.

**Sample and portfolio leakage:** the examples are selected to explain contrasting
path classifications and reuse previously inspected captures. They are not a
random sample or independent holdout. Multiple candidates can overlap in time
and compete for the same cash. Adding their isolated favorable endpoints does
not produce a valid portfolio return or drawdown. A later replay needs a
chronological capital ledger, concurrency limits and explicit handling of gaps,
ambiguity and missing data.

## Three real historical examples with dates

The underlying prices are genuine **Binance Spot BTCUSDT daily bars**, opening
00:00 UTC and closing 23:59:59.999 UTC, measured in USDT per BTC. Exact raw
source hashes remain in the existing structure receipt. The derived execution
section of the liquidity receipt is reproducible offline. Each case observes
five subsequent daily bars, but no actual entry, fill, account PnL or drawdown
is reconstructed.

### Example 1 — 12 March 2020: both barriers in the next daily bar

The event close is **4,800.00**. The one-percent lower reference is **4,752.00**,
and the two-percent upper reference is **4,896.00**. The next day, **13 March**,
opens **4,800.01**, reaches high **5,955.00** and low **3,782.13**, and closes
**5,578.60**. Both barriers lie inside that recorded range. The opening price
lies between them, so the outcome is **ambiguous both barriers in one bar**,
not a target-first assumption based on the positive close.

At the hypothetical fifteen-basis-point per-leg cost, modeled loss per BTC
at the stop is **62.328** and modeled target gain per BTC is **81.456**.
The corresponding unrounded quantity is about **0.802208 BTC**, with modeled
entry cash including cost about **3,856.37**. These numbers demonstrate a
budget calculation only. The source does not prove that quantity could have
entered at 4,800 or exited at either reference in the required order.

### Example 2 — 10 April 2021: a target reference is reached, still no fill proof

The event close **59,769.13** gives lower reference **59,171.4387** and
upper reference **60,964.5126**. The following **11 April** range,
**59,232.52–60,699.00**, reaches neither. On **12 April**, the open is
**59,998.80**, high **61,300.00**, low **59,350.59**, and close **59,860.00**.
That bar reaches the upper reference while remaining above the lower one.
It is therefore the first target-reference-only observation in this illustration.

This does not establish that an entry at the old event close existed after
the source was delivered, nor that a limit or target order filled. It also
does not certify any liquidity pattern caused the movement. At the assumed
cost the unrounded budget quantity is about **0.0644245 BTC**. Strategy PnL
and account drawdown remain null. A favorable barrier event is a price-path
fact, not a completed profitable trade.

### Example 3 — 8 November 2022: the stop reference comes first

The event closes **18,547.23**, producing lower reference **18,361.7577**
and upper reference **18,918.1746**. On **9 November**, price opens
**18,545.38**, reaches high **18,587.76** and low **15,588.00**, and closes
**15,922.81**. The open is between the barriers, the high stays below the
upper one, and the low passes the lower one. The first barrier observation
is stop-reference-only, without claiming an actual stop execution price.

The large range demonstrates why a planned one-percent distance cannot be
described as a guaranteed one-percent realized loss. The dataset provides no
spread, depth or queue history at the crossing. At the assumed per-leg cost,
the illustrative quantity is approximately **0.207610 BTC** and the model's
planned stop loss is fifty units. A real gap or execution failure could violate
that modeled loss budget. No participant intent or complete crisis duration
is inferred from this daily bar.

## How to use it to HUNT a trade

Make the evidence chain explicit before sizing. Identify a supported symbol,
source event and actual arrival time. Freeze the candidate's prerequisites
and invalidation, then require a reachable post-decision entry under a defined
paper order policy. If only an old close exists, keep it as a reference and
WAIT rather than manufacturing a fill or current entry ticket.

Apply cost and cash/risk limits to a defensible entry, using actual filters
when available and bounded conservative assumptions where explicitly permitted.
Export ambiguous outcomes and adverse gaps. Evaluate the complete chronological
sample with independent periods and overlapping-capital checks; do not estimate
a win probability from these three teaching examples. Historical resemblance
and weighted rule coverage do not replace calibration.

For Jano, the default response remains concise and should identify the immediate
missing evidence. Longer execution teaching is available when requested. This
chapter's source material and offline illustrations do not deliver the pending
runtime replay, independent strategy evaluation or final V3 integration gate.
All actual order capability remains disabled.

## Sources

- [SEC Investor.gov: Executing an Order](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/executing-order): primary execution-delay/price/quantity discussion checked 28 October 2026; stock-market guidance, not a Binance fill record.
- [SEC stop-order bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15): primary activation-versus-execution distinctions checked; no assured stop fill adopted.
- [Binance symbol filters](https://developers.binance.com/docs/binance-spot-api-docs/filters): primary price, lot-size and notional concepts checked; historical symbol snapshots remain unavailable here.
- [Binance kline schema](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary UTC/OHLC field semantics checked; actual source bodies are pinned in the referenced daily capture receipt.

# Zone execution and failure cases: from a rectangle to an auditable paper hypothesis

Reviewed: 28 October 2026, Asia/Karachi. Scope: execution assumptions and failure
diagnosis using the actual zone receipts. This is source material for later
integration, not a new runtime backtest or trading service. No order, margin,
borrowing, leverage or paid data capability is enabled.

## What is it?

Zone execution is the process of turning an observed reference interval into
an explicitly timed, size-bounded and falsifiable paper hypothesis. A rectangle
alone does not specify when an order could have been sent, what price was
available, whether sufficient liquidity existed, or how a position would exit.
Those missing choices can dominate the result. A historical picture showing
contact and a later favourable close is not a completed trade record.

Separate six layers. A feature identifies geometry using information available
at its activation time. A qualification rule decides whether other evidence
permits monitoring. An order model specifies timing, side, size and price
constraints. An execution model resolves fills and costs only to the precision
supported by the data. A position model handles subsequent exposure and exits.
An evaluation ledger includes failures, missing observations and the effect
on equity. Success at one layer does not establish the next.

This distinction is particularly important for Hoshi's current source receipts.
They contain daily Binance Spot BTCUSDT bars, confirmed-pivot intervals and
audited V2-style formation features. They store later contact, rejection,
wick breach, close breach and gap crossing. They explicitly retain null
strategy PnL, unknown fills and null win probability. Those fields are evidence
boundaries. Adding a chapter does not silently convert them into a simulator.

### Execution vocabulary with venue limits

The SEC's checked stock-order bulletin distinguishes a limit's price condition
from a guarantee of execution, and a stop's activation price from its actual
market fill. It also discusses partial executions and broker-specific
differences. The bulletin is dated 12 July 2017 and reports an update on
18 August 2026. Neither date is one of the historical cases below, and the
stock examples do not establish Binance's exact order rules.

Binance's current filter documentation provides a separate venue-specific
constraint layer: price increments, quantity steps and minimum or bounded
notional can reject an otherwise attractive arithmetic plan. The examples
in that documentation are schema illustrations, not verified current or
historical BTCUSDT settings for these captures. A historical simulation would
need point-in-time settings; a current paper screen would need a fresh, checked
symbol specification. No historical filter snapshot or account fee tier was
captured with the daily data here.

## Why does it form?

Execution failure can arise even when the zone description is completely
accurate. Other participants can transact before a waiting limit order, an
order can arrive after the observed touch, an exchange can reject its size,
or the market can move through several prices before an exit executes.
A daily low records an extreme transaction in an interval; it does not
record the amount available to a specific hypothetical order at that time.

Aggregation removes ordering information. The same open, high, low and close
can be consistent with several intraday paths. If a candle touches a proposed
entry, stop and target, their numerical inclusion does not tell which event
occurred after entry. The high may precede the entry; the low may occur after
a favourable exit; or a sequence can revisit both levels several times.
Choosing the profitable path from daily data manufactures precision.

Signal delay adds another mechanism. A pivot needs right-hand candles and
an A/B/C formation needs C's completed extreme. The attractive origin price
often belongs to a period before the signal existed. A retrospective chart
can therefore combine a legitimate late feature with an impossible early
entry. An auditable ledger must carry the feature's knowledge time into
all subsequent execution decisions.

Zone failure itself is also a convention. A closing rule tolerates intrabar
excursions that a protective stop may not. An active-gap rule can reject a
candidate while the block's closing boundary still survives. An order model
can expire without contact while a chart continues moving favourably. These
different outcomes should explain differences between strategies rather than
being collapsed into one attractive success label.

## Application zone

Use explicit execution research when comparing ideas that otherwise look
similar on a chart. Freeze symbol, venue, quote currency, timeframe, source
cutoff, detector version and all eligibility rules. Separate a signal at a
completed close from an order that becomes eligible only afterward. If an
order requires a later rejection close, it cannot also claim a fill at the
earlier wick without an independently justified order placed before that wick.

Choose an execution resolution that matches the claim. Daily OHLC can support
bounded price-path diagnostics, absence of contact and some adverse extreme
observations. It cannot provide queue-level fills, precise arrival latency or
the intraday order of all touches. Lower-frequency insufficiency should become
an ambiguity or missing-data status. Obtain appropriate licensed finer data
before claiming exact stop-first or target-first results.

For future paper evaluation, a useful event record includes setup identifier,
information cutoff, proposed order activation, observed entry eligibility,
expiry, cancellation reason, cost assumptions and every unresolved ambiguity.
Store rejected candidates as well as accepted ones. Preserve the pre-specified
exit horizon and position rules through adverse outcomes. Costs must identify
their source and effective period, or be labelled hypothetical sensitivity
inputs rather than historical fees.

### Original sizing illustration, not a live recommendation

Suppose a hypothetical unleveraged paper account contains 1,000 quote units
and permits 5 units of intended scenario loss. A proposed entry is 100 and
invalidation is 98. Add an explicitly hypothetical 0.20 quote-unit per-unit
allowance for combined execution friction, so the assumed unit loss is 2.20.
Quantity cannot exceed 5 / 2.20, approximately 2.2727 units. Under an invented
illustrative step of 0.01, rounding down to 2.27 gives intended scenario loss
4.994 and entry notional 227. This is arithmetic using chosen assumptions,
not a current symbol lot size, measured fee or guaranteed maximum loss.

If actual slippage exceeds the allowance, realised loss can exceed the intended
budget. Cash affordability is a separate cap; a tiny stop distance must not
imply leverage. Minimum notional, open exposure, correlated positions and
available balance can require a smaller size or no paper opportunity. If
the legal minimum size exceeds the risk cap, the correct result is rejection,
not rounding upward to force a trade.

## Failure zones

No zone-based execution plan works 100%. An invalidation level is not insurance
against discontinuity or thin liquidity. A stop-limit can constrain its limit
price but may leave exposure open when price moves away. A market-style exit
prioritises executing under the relevant venue's rules while leaving the
actual price uncertain. An old candle cannot resolve that tradeoff for a
new live situation.

Ambiguity can bias both returns and drawdown. Reporting only closing PnL can
hide a severe intraday excursion. Reporting only the best possible touch can
ignore an earlier stop. A conservative ambiguity policy may assign an adverse
ordering or exclude the result, but the choice and count must remain visible.
Neither policy turns insufficient data into known historical fills. Report
bounds and unresolved cases when exact sequencing is unavailable.

Do not confuse zero opportunities with zero-risk profitability. A zone never
revisited under a limit-entry model produces no eligible touch. That model
cannot claim the subsequent directional move. A sample with no executable
trades should report its sample size and no performance estimate, rather
than a perfect win rate. Likewise, a missing tail window is not a zero return
and should not be silently dropped if its omission changes the conclusion.

Evaluation must eventually account for serial and portfolio dependence.
Several overlapping zones can trigger exposure to the same move. Treating
each as an independent full-risk bet can exceed an aggregate cap. A historical
pattern selected after inspection can also look better than its chronological
record. Keep selection rules and source lineage, evaluate with time-ordered
independent data, include costs and compare against appropriate simple
baselines. The current examples are already inspected educational cases.

## Three real historical examples with dates

All examples below use Binance Spot BTCUSDT daily UTC bars, 00:00:00 through
23:59:59.999, quoted in USDT per BTC. Exact captured bodies and hashes are
retained in the structure receipt and replayed by the zone receipt. They
document actual prices, not actual executions. Historical data were retrieved
during this 28 October 2026 source review; contemporaneous order books, fee
tiers, symbol filters and participant identities are missing.

### Example 1 — 8–13 May 2020: same-bar level coverage cannot establish a profitable fill

The bullish formation known at the **8 May** close references an origin block
**8,522–8,950** and a three-bar gap **9,395–9,705**. On **10 May** the actual
candle opened 9,539.10, traded high 9,574.83 and low 8,117, then closed
8,722.77. It contacts the block, crosses its lower boundary intrabar and
fully crosses the associated gap, while closing above the block low.

For illustration only, compare a hypothetical buy limit at 8,950, protective
threshold 8,500 and target 9,500, all chosen after formation for a paper
question. These are invented order instructions around genuine historical
prices, not submitted orders or detected Hoshi trade levels. The daily range
contains all three. Its high does not prove that a target filled after entry;
the candle opened above the target, so an early high could precede any entry.
Its low also shows why assuming safety from the closing hold is inappropriate.

The actual **13 May** close of 9,309.37 follows a later block contact and
qualifies as a closing rejection under the offline observation rule. That
later fact does not repair the earlier execution uncertainty or the already
crossed gap. The receipt therefore leaves fills and PnL unknown. No target-first
profit, stop-price guarantee or full V2 signal is claimed.

### Example 2 — 24 July–13 August 2021: a valid formation yields no origin-entry opportunity

The bullish formation becomes known at the **24 July** close. Its full origin
range is **29,278–31,063.07**, drawn from **20 July**. The three-bar gap is
**32,591.35–33,401.14**. Across exactly twenty subsequent daily bars,
**25 July–13 August**, the price ranges do not contact the block and do
not fully cross the gap's far boundary under the recorded rule.

A hypothetical passive purchase anywhere inside that block has no observed
eligible touch in this fixed window. Moving the entry upward after seeing
the rally would create a different strategy. Claiming a purchase at the
20 July low would also precede the formation's knowledge time by four days.
No-return is therefore a substantive result: the waiting model has no
demonstrated opportunity here, even though its historical origin looks
directionally appealing. This is not a zero-loss winning trade.

### Example 3 — 3–8 November 2022: a confirmed demand reference fails at first contact

The confirmed-pivot demand interval from **3 November** is
**20,031.24–20,151.84**, available only at the **5 November** close. Its first
eligible return occurs on **8 November**. That candle opens 20,590.67,
trades high 20,700.88 and low 17,166.83, and closes 18,547.23. First contact,
wrong-side wick and invalidating close all occur on that bar.

The rule cannot call this a favourable closing rejection. A paper model
with an intrabar protective threshold needs its own order and fill assumptions;
the source does not show that protection executed exactly at the zone low.
A day-end invalidation policy instead observes the close well below that
boundary. Either way, the attractive prior pivot is not a guarantee. No
institutional intent, headline cause, realised account loss or stop execution
is reconstructed from these aggregate prices.

## How to use it to HUNT a trade

Start by asking whether an executable paper question exists. The feature
must already be available, the symbol must be supported, the source current
enough for the intended horizon, and required evidence complete. Reject
stale bars and missing observations. Old examples may explain a method but
cannot supply today's entry, stop or target. A bearish spot study does not
create permission for borrowed or leveraged shorting.

Next freeze order timing, entry eligibility, cancellation, exit and aggregate
risk before looking forward. Explicitly identify hypothetical cost inputs
and unavailable depth or sequencing. For paper analysis, distinguish no
touch, possible touch without fill evidence, confirmed order-model fill,
ambiguous exit ordering and unavailable outcome. A historical close should
never be promoted to an execution price merely because it is convenient.

Then evaluate causally on a chronological ledger that retains every relevant
candidate and rejection. Export evidence times, feature versions, raw-source
hashes and assumptions with the result. Report costs, adverse movement,
drawdown and missing/ambiguous cases alongside any return estimate. A held-out
period must actually be independent of rule selection; these already reviewed
source windows do not qualify. Negative and zero-trade results must survive
the report.

Until that later implementation and independent evaluation exist, Hoshi should
return WAIT when essential execution inputs are absent and keep probability
null. A concise Roman Urdu response can state the evidence status and one
material missing requirement; the long explanation belongs only in requested
teaching. This chapter documents the execution standard without falsely
claiming that runtime replay, calibrated accuracy or final release has shipped.

## Sources

Checked 28 October 2026. Original analysis distinguishes hypothetical order
instructions from actual source observations.

- SEC Investor.gov, [Understanding Order Types — Investor Bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-14): stock-order execution and price limitations; publication and update dates are separate from event dates. These are not venue-specific Binance fill rules.
- Binance, [Spot filters](https://developers.binance.com/docs/binance-spot-api-docs/filters): current documented price/quantity/notional constraints. Illustrative schema values are not historical BTCUSDT filter observations; the checked page reports modification on 27 October 2026.
- Binance, [Spot market-data API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): kline versus depth inputs. Actual raw-response bodies, request bounds and hashes reside in `../01_MARKET_STRUCTURE/structure_observations_20261028.json`.
- Offline source evidence: `zone_observations_20261028.json`, verified by `scripts/v3_zone_evidence.py`, contains the genuine cases used above with separate knowledge and outcome times; it is not an order simulator.
- Binance [public-data project](https://github.com/binance/binance-public-data), [data terms](https://data.binance.vision/?prefix=) and [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/): attributed non-commercial data analysis, with unrelated code/publications retaining their own terms. No provider endorsement or paid entitlement is implied.

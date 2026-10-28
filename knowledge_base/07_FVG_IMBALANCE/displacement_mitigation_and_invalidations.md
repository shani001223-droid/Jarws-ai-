# Displacement, mitigation and invalidation: separate measurements, separate clocks

## What is it?

Displacement is a description of directional movement relative to an explicitly
chosen baseline and reference. Mitigation in chart vocabulary often refers to
a later revisit of a marked region. Invalidation is a condition that ends a
specific hypothesis. These are separate events. A large candle can leave a
gap that never receives an eligible return; a return can occur only after
the original candidate has already failed.

Hoshi's existing Confluence V2 source uses a concrete formation heuristic:
a three-bar gap, a directional middle-candle body at least 1.5 times the
mean absolute body of twenty prior candles, a close beyond five prior extrema,
and a recent opposite candle as a possible order-block origin. This chapter
audits that arithmetic on genuine minute data. It does not claim that a
one-minute example meets the runtime's fifteen-minute entry frame or its
one-hour/four-hour context checks.

The checked original Month 04 FVG captions provide neighboring-candle context;
selected 2024 captions qualify some gap boundaries using body information.
The original rule here remains the transparent **outer-wick** version, with
creator parity false. Neither those source descriptions nor V2's code proves
unfilled institutional orders exist inside a candle. A later overlap is price
geometry, not a report of a participant mitigating a known position.

There are at least three useful cancellation measurements: a wick reaches or
passes the far gap boundary; a close finishes strictly beyond that boundary;
or a close breaches the selected origin candle's full wick range. These need
not occur together. A method must specify which state controls eligibility,
rather than select the most forgiving definition after seeing a favorable move.

## Why does it form?

Relative-size thresholds try to distinguish ordinary bar variation from a
larger directional movement. Their result depends on the historical baseline.
A fifty-unit body can be exceptional in a quiet sample and ordinary in an
active one. A zero-body baseline cannot support a meaningful ratio. Hoshi
records that ratio as unavailable instead of treating it as infinite
confirmation.

The five-bar break asks a different question: did B's close exceed a nearby
completed reference in the proposed direction? A large body may stay inside
that range. A small body may break a narrow range. Combining the gates defines
a population; it does not prove either gate provides statistically independent
evidence. Both are derived from overlapping recent price history.

An opposite-candle origin is another operational choice. The most recent
opposite candle in the preceding five bars can be far from the resulting
gap, and several older candidates may exist. Choosing whichever origin best
fits a later retest would introduce hindsight. The version therefore selects
the latest qualifying one before B and freezes it when C confirms the formation.
It does not identify the actual location of an institution's inventory.

Later path behavior can differ across these regions. Price may enter the gap,
cross it, and only afterward reach the origin. A wide candle can overlap
both separate zones without offering the same entry price in both. This is
why bar-level overlap and a positive intersection of the actual price intervals
must be recorded as different facts.

## Application zone

The offline method is **hoshi-minute-gap-formation-quality-1**. Start with a
strict completed A/B/C outer-wick gap. Require twenty bars strictly before B
for its body baseline and five bars strictly before B for its break reference
and origin search. For a bullish candidate, use B.close − B.open and require
B.close above the preceding five-bar high. For a bearish candidate, reverse
the body sign and require its close below the preceding five-bar low.

Mean body is the arithmetic average of absolute close-minus-open across the
twenty earlier bars. It must be positive. The signed directional body must
be at least 1.5 times that mean. An opposite candle closes down for a proposed
bullish formation, or up for a bearish one; doji candles do not qualify.
All formation conditions become available only after C completes. The selected
origin existed earlier, but its role in this newly confirmed formation did not.

Search chronologically for the first formation satisfying those gates, without
filtering by its later outcome. Also preserve the first unfiltered gap with
enough prior history. That comparison shows why every geometric gap cannot
be called displacement. The data contain 40/31/20 such history-eligible gap
candidates across the three captures, of which 9/7/8 satisfy the formation
gates. These are correlated formation counts, not trades or performance ratios.

Observe five later minute bars and retain independent timestamps for first
gap contact, far-boundary wick, far-boundary close, origin closing breach
and a bar overlapping both regions. A partial gap contact holding the midpoint
is eligible only before the first far-boundary wick under the original
wick-retirement policy. A later favorable closing move cannot undo that
retirement. A separately versioned closing-only strategy would be a different
experiment with a different risk profile.

Calculate the positive price intersection of the gap and origin separately.
If it is empty, a wide bar can still overlap both, but that does not prove
one common price was inside both regions. The current V2 check uses same-bar
overlap; this chapter records its resolution limit rather than silently
claiming tick-level entry certainty or changing V2 runtime behavior.

Provider arrival, historical bid/ask, queue position and actual fills remain
unknown. These one-minute diagnostics do not supply the complete V2 or V3
strategy gates. Every decision stays WAIT, orders remain disabled and
win probability is null. Missing context cannot be supplied by the label
displacement or an impressive body multiple.

## Failure zones

**The event leaks into its baseline:** including B or C in the twenty-bar mean
changes the threshold using the movement being tested. Using a pivot or an
origin that requires later bars similarly changes the information cutoff.
Prefix tests verify the recorded features use only the required earlier bars
and completed C; future outcomes cannot change them.

**A large body replaces a break:** the body-size gate and reference-break
gate are distinct. If one fails, the formation does not qualify under this
version, even if its later direction looks right. Conversely, a qualified
formation can fail at first contact. Retaining rejected candidates is needed
to audit what the gates actually remove.

**Every return is mitigation:** a later touch does not identify a position
being reduced, an order being filled or an institution defending the origin.
The source contains only one venue's candles. A return after the gap has
retired is a later observation, not an eligible retest of the original active
candidate.

**One failure threshold masquerades as another:** a wick can cross the gap
while the origin remains intact. A closing breach can arrive minutes after
an earlier partial hold. Replacing the gap stop with the wider origin range
after seeing the breach increases assumed risk retrospectively. Freeze the
invalidation policy before entry and report each diagnostic without renaming it.

**Same bar means same fill:** a bar can span two nonoverlapping zones. Its
range does not establish the order of trades, a particular order's queue
position or a common executable price. The checked primary order guidance
does not turn an interval overlap into execution certainty. A future paper
entry policy needs actual post-decision prices and explicit ambiguity handling.

**Filtering manufactures validation:** all these captures were already examined.
The thresholds are inherited operational choices, not parameters optimized here,
but this is still an exploratory sample. A formation count, one attractive
retest or a raw five-minute change cannot calibrate accuracy. Independent
chronological evaluation with costs and missing/zero-trade results remains
separate pending work.

## Three real historical examples with dates

The following cases are the **first chronological qualified formation** in
each genuine Binance Spot BTCUSDT native-minute capture. All times are UTC
and prices USDT per BTC. The existing raw source bodies were fetched on
28 October 2026; these are retrospective diagnostics with theoretical
completed-bar availability, not proof of historic source arrival or trades.

### Example 1 — 15 May 2023: first contact fails before the origin breaches

The first history-eligible gap, with C at **06:52**, has directional B body
**5.03** versus prior mean **10.952**, a multiple of only **0.45928**.
It does not satisfy displacement. The first qualified bearish formation
instead has C at **06:54**, gap **27,439.75–27,445.90**, B close
**27,422.56**, directional body **23.34** and mean **9.88**, approximately
**2.36235** times the baseline. B also closes below the prior five-bar
low **27,445.90**.

Its origin is the up candle at **06:49**, range **27,455.50–27,470.09**.
Gap and origin have no positive price intersection. The **06:55** bar ranges
**27,432.28–27,457.15** and closes **27,450.81**: it overlaps both regions
but already crosses and closes beyond the bearish gap's far boundary.
Only at **06:57**, close **27,481.71**, does the origin's upper boundary
receive a closing breach. The two failure clocks are different; neither
proves an earlier order filled. No partial gap hold is credited before retirement.

### Example 2 — 5 January 2024: an initial hold precedes gap cancellation

The first eligible unfiltered gap at **14:52** has a body multiple of only
**0.43785**. The first qualified formation comes later: bullish C at
**15:25**, gap **43,730.16–43,750.00**, B close **43,780.13**, directional
body **49.98**, prior mean **31.1555**, multiple about **1.60421**.
B closes above the prior five-bar high **43,730.16**. The origin at
**15:20** has range **43,580.92–43,690.12**, separate from the gap.

At **15:26**, low **43,750.00** contacts the near gap boundary and close
**43,769.94** holds its midpoint. At **15:27**, low **43,725.61** and
close **43,726.01** breach the far gap boundary. A bar finally overlapping
both gap and origin appears at **15:29**, after the gap has retired.
The origin itself has no closing breach in the five-bar window. Counting
that later joint overlap as a fresh eligible gap retest would erase the
already observed cancellation.

### Example 3 — 8 August 2024: gap contact without order-block contact

The first prior-history gap at **17:57** has body multiple **1.09100**,
below the threshold. The first qualified bearish formation has C at
**17:59**, gap **59,480.04–59,538.00**. B's directional body is **57.97**,
prior mean **26.00**, multiple approximately **2.22962**, and its close
**59,480.04** is below the prior five-bar low **59,538.00**.

The origin at **17:54** ranges **59,543.25–59,617.88**, leaving a gap
between the two regions. At **18:00**, the following bar reaches
**59,488.89** and closes **59,414.08**, a partial gap contact holding
in the bearish direction. The next five bars contain no far gap wick,
gap closing breach, origin closing breach or bar overlapping both regions.
Thus gap retest geometry exists while the separate origin-overlap requirement
is absent. This is not a complete V2 signal, a source-certified short or
an executable spot short position.

## How to use it to HUNT a trade

Freeze the displacement baseline, break reference, origin policy, gap bounds
and controlling invalidation before observing a retest. Require completed
source bars and actual arrival/freshness. Then ask whether the required
subsequent event happened while the candidate remained active. A later
joint overlap cannot repair an earlier cancellation.

Keep formation quality, context, entry reachability and paper risk separate.
If the entry frame, historical filters, global-flow inputs or source quote
is missing, WAIT. Never convert a body multiple into confidence or replace
a missing level with an invented NAS100 ticket. An evidence-coverage score
is not a calibrated probability of profit.

Hoshi should apply these distinctions quietly and teach the full analysis
only when Jano asks. This chapter and its offline receipt do not alter the
V2 runtime, train a model, deliver the pending V3 loader or replace independent
replay/release verification. Real orders and leverage remain disabled.

## Sources

- [Original Month 04 FVG lesson](https://www.youtube.com/watch?v=FgacYSN9QEo): original English captions and creator metadata checked; limited neighboring-candle context, not proof of institutional positions.
- [Original September 2024 FVG lesson](https://www.youtube.com/watch?v=HhgWGduQZQY): selected boundary qualifications checked; full-track/chart parity not claimed.
- [Existing V2 strategy source](https://github.com/shani001223-droid/Jarws-ai-/blob/fb34e359c752380a4740fb972cfadfd8e8eabfb9/cloud_backend/strategy_engine.py): primary project implementation inspected; this chapter audits formation arithmetic offline without claiming complete fifteen-minute/HTF runtime qualification.
- [Binance kline API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary time/OHLC schema checked; actual raw responses remain pinned in the referenced capture receipt.
- [SEC order types](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders): primary price-condition/execution distinction checked; no fill inferred from a wide bar.

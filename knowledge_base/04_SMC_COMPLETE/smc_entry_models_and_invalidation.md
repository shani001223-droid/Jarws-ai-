# SMC entry models and invalidation: causal sequences rather than hindsight entries

Reviewed: 28 October 2026, Asia/Karachi. This chapter develops explicit research
templates and a reproducible, original price-sequence audit. It does not
implement a live entry service, complete V3 confluence, model training or
certified parity with an educator's proprietary model.

## What is it?

An entry model specifies the conditions, order and timing that must exist
before an executable paper hypothesis can be considered. It is more than
a collection of rectangles. A sweep on one date, a break on another and
a historical gap elsewhere cannot be combined merely because the completed
chart looks persuasive. Their references must be available in the required
order, on the specified instrument and at their actual decision times.

Two useful template families are continuation and reversal. A continuation
template starts with an independently defined larger trend, seeks a pullback
into a predeclared location and requires renewed evidence in the original
direction. A reversal template first requires a failure of the prior move
and a break against it, then investigates a later retracement. A local
countertrend signal alone does not establish a larger reversal. Neither
template is a complete strategy until data, execution, risk and exit rules
are specified.

A third distinction concerns entry timing. An anticipatory limit hypothesis
can be eligible before a rejection close, but it accepts that rejection
has not yet been observed. A confirmation hypothesis waits for the close
and then uses only subsequent available prices. Claiming the best early
wick entry while also requiring its later closing confirmation combines
incompatible information clocks. A method must choose and record its policy.

### Original sweep–break–gap audit

The offline method `hoshi-sweep-break-gap-audit-1` measures a limited price
chain, not all gates of either template. Choose a direction and a proposed
confirmation candle C. B is the immediately preceding candle and A the one
before B. Search the three candles strictly before B for a sweep-like reclaim.
For an upward chain, a candle must trade strictly below the most recent pivot
low known before its own open, then close strictly above that level. The
downward chain mirrors this at a previously known high. If several qualify,
retain the latest. Equality does not qualify.

That observation is only a price reclaim. The audit does not establish that
the level was untapped, that stop orders existed there or that participants
intentionally hunted them. Its reference remains frozen as of the sweep's
own clock, even if a new pivot confirms later. Replacing it with B's latest
pivot would rewrite the original observation.

B must then first close through the relevant opposing confirmed reference
under the preceding chapter's consumed-reference rule. It must also qualify
as displacement: directional body at least 1.5 times the positive mean of
twenty prior bodies, plus a strict close beyond the preceding five-bar
extreme. The break may remain unclassified when the prior swing-pair state
is mixed. That does not magically supply a trend for a continuation or
reversal template; it only records the measured cross.

Finally, C must complete the repository's audited three-bar gap and opposite
origin formation. An upward gap has A high below C low; a downward gap has
C high below A low. The origin is the most recent opposite-colour candle
among the five before B, using its full high-low range. The formation is
known at C close, and its origin cannot already be invalid by C's close.
The sweep, B and C therefore have strictly ordered knowledge times.

The price chain qualifies only when all of those conditions exist. Missing
sweep, fresh break, displacement or formation remains a specific rejection
reason. The next **five** completed bars are then observed for a later gap
retest. Inclusive intersection establishes geometric contact. To qualify
as a retained retest event, the close must hold the favourable side of the
gap midpoint while the gap remains unfilled under the chosen extremum rule.

A bullish low at or below the far lower gap edge, or a bearish high at or
above its upper edge, invalidates the active gap. A wrong-side close beyond
the origin block also invalidates the chain. Invalidation has priority over
an eligible retest on the same bar. The audit preserves an earlier eligible
event if later invalidation occurs; it never rewrites the earlier clock.
It records geometry, not fill price, position size, target or strategy PnL.

## Why does it form?

The sequence selects a local rejection of one reference, a subsequent
directional expansion and separated ranges around that expansion. It may
represent a change in participation or liquidity, but OHLC alone cannot
identify the cause. A reclaim can occur without actual stops being triggered,
and a later gap contact can occur without the original participants returning.
The words “sweep” and “order block” must not supply missing order evidence.

CME's primary MBO documentation describes anonymous order-level information
and its distinction from price-level aggregation. Even the richer feed
does not identify the customer. These daily captures contain neither feed,
so attributing a sequence to a named institution would be particularly
unsupported. The causal price audit requires less ambitious claims: which
reference existed, which candle crossed it and when that fact became known.

Requiring stages reduces the number of qualifying observations because the
conditions are conjunctive. It does not logically increase profitability.
Some rejected paths will subsequently move favourably; some complete chains
will fail. Adding more correlated conditions can also overfit a small sample.
A useful model must retain both kinds of counterexample and pay the cost
of waiting for its confirmations.

## Application zone

Use a sequence audit to test whether the events actually line up before
thinking about an entry. Determine the larger-frame role separately: a
continuation hypothesis needs support for its existing trend, whereas a
reversal hypothesis needs a specified opposing break and invalidation of
the earlier view. The same small pattern should not be retrospectively
called whichever template best explains the later move.

The original audit is deliberately narrower than V2 confluence. It does
not verify higher-timeframe alignment, an untested liquidity target, joint
order-block overlap, global money flow, session/news context, current
source quality or execution inputs. It does not independently calibrate
probability. Its default decision is therefore **WAIT**, even when its
price chain and geometric retest are present. These missing requirements
are explicit in the receipt.

The distinction between gap contact and joint block overlap is substantive.
A return can enter a gap while remaining far from the selected origin
block. The existing V2 location condition has a separate overlap requirement.
An educational gap event must not be advertised as a fully qualified V2
signal, much less the not-yet-integrated V3 engine.

All examples below use Binance Spot BTCUSDT, USDT per BTC, daily UTC bars
running 00:00:00–23:59:59.999. The bounded captures were retrieved during
this 28 October 2026 review and were already inspected for other chapters.
They are not unseen evaluation data, order records or historical-vintage
certification. The source receipt retains raw responses and hashes; the SMC
receipt stores each stage and its distinct knowledge time.

## Failure zones

No entry model works 100%. A price chain can complete and never retest within
its declared horizon. Extending the horizon only for favourable cases changes
the experiment. A first contact can fully cross the gap, meaning that
contact and invalidation occur together. Recording it as a clean held
retest would conceal the actual path and violate the model's own rule.

Feature invalidation, trade invalidation and operational cancellation are
different. A filled gap can retire a geometric candidate even while its
origin block survives by close. A hypothetical position may need to exit
earlier under a separately defined loss cap. A stale feed, unsupported
symbol or user Stop can cancel further activity without requiring a market
pattern failure. None of those states should be misreported as a completed
profitable trade.

The checked SEC stock-order bulletin distinguishes a limit's price condition
from guaranteed execution, and a stop trigger from its eventual market
fill. Those are execution principles with venue-specific details, not proof
of any Binance fill here. Daily OHLC cannot resolve queue, spread, order
arrival or all same-bar stop/target ordering. A close-confirmed retest also
arrives after the earlier touch; its old boundary is not automatically an
available entry price.

An apparently successful bearish example is particularly easy to misuse
on spot. A bearish research label is not permission for borrowing, short
orders or leverage. Hoshi's free-first, paper-only constraints remain in
force. Any future hypothesis needs cash/exposure limits and realistic costs;
the current chain has no position PnL and cannot establish a win rate.

## Three real historical examples with dates

### Example 1 — 26 January–2 February 2020: ordered reversal-like chain without a later retest

On **26 January**, the daily low **8,293.66** passes below the then-known
reference **8,466**, while the close **8,615** reclaims it. That reference
was confirmed on 21 January. A newer low is not substituted into this
earlier sweep observation. On **27 January**, price closes **8,907.57**
through the opposing known high **8,818**, producing an upward CHoCH label
and displacement body multiple approximately **1.6200**.

C on **28 January** completes a gap **8,618.13–8,862.40** and an origin
block **8,254.90–8,451.26** from 25 January. The joint price chain first
exists at C's close. Across the next five bars, **29 January–2 February**,
there is no gap contact or eligible retest. The proper status is no eligible
retest in the window, not a purchase at the earlier origin or a profitable
limit entry. The chain's temporal order does not eliminate entry absence.

### Example 2 — 10–18 May 2021: a real geometric retest still leaves full strategy inputs missing

On **10 May**, high **59,500** exceeds the known high **58,981.44**, while
the close **55,816.14** is below it. B on **12 May** closes **49,631.32**
below the known low **52,900**, with downward displacement multiple about
**4.1679**. Its prior swing-pair description is mixed, so the break is
explicitly unclassified rather than certified as a bearish trend template.

C on **13 May** completes the downward gap **51,367.19–54,370**. Its up
origin is 11 May, range **54,370–56,862.43**. On **14 May**, high **51,483**
enters the gap and close **49,841.45** holds below its midpoint without
fully crossing the upper gap edge. The audit records a first eligible
geometric retest. The five-bar observation ends **18 May**.

The 14 May high is nevertheless below the origin block's lower boundary.
It does not establish joint block overlap, and no higher-frame, macro,
live execution or calibrated probability evidence is present. The decision
stays WAIT. The later fall to a 18 May close of **42,849.78** is an observed
path, not proof of a hypothetical short fill or account profit.

### Example 3 — 28 May–5 June 2022: first contact invalidates the active gap

On **28 May**, low **28,450** trades below the then-known low **28,654.47**
and close **29,031.33** reclaims it. B on **30 May** closes **31,734.22**
above the known high **30,670.51**, with an upward CHoCH label and body
multiple about **2.7647**. C on **31 May** completes the gap
**29,587.78–31,200.01** and origin block **28,282.90–29,397.66**.

The first later contact, **1 June**, trades low **29,301** and closes
**29,805.83**. The low fully crosses the far gap edge, while the close
does not breach the origin block low. Those are distinct facts. Under
this model, full gap crossing has already invalidated the active candidate;
there is no eligible held retest on that candle. The fixed observation
ends **5 June**, preserving the invalidation instead of treating a visible
contact as an entry confirmation.

## How to use it to HUNT a trade

Start from validated closed bars and separately available context. Freeze
references when they become known and enforce event order. If a sweep
reference changes later, retain the original observation instead of editing
its past. A B-only impulse is not a C-confirmed formation; a formation is
not a later retest; a later retest is not a fill.

Then apply an explicit invalidation hierarchy. Reject missing source or
context before calculating confidence-like outputs. Retire filled gaps and
wrong-side closing breaches under the declared rule. Keep horizon expiry
and missing future observations distinct from invalidation. If a contact
and failure occur together, record both and reject the clean-retest claim.

Only a later, fully specified paper process can add observed executable
prices, costs, risk, exits and portfolio exposure. Evaluate that process
chronologically on genuinely independent data, retaining rejected chains,
zero-opportunity windows, adverse paths and ambiguous fills. Multiple features
from one impulse share data and must not masquerade as independent votes.
The requested eventual evidence weights will not calibrate a win probability
by themselves.

Hoshi's concise Roman Urdu default should convey the actual evidence status,
source time and important missing requirement. Teaching this sequence belongs
in requested explanations. This chapter and its offline audit neither load
V3 knowledge into the model nor enable trading, and missing essential inputs
continue to produce WAIT.

## Sources

Primary links checked 28 October 2026; templates and numerical audit are original.

- Existing repository source: `cloud_backend/strategy_engine.py` and `modules/04_smc.md`, inspected without runtime changes. The audit combines a limited original sequence, not all existing V2 gates or creator-certified models.
- CME Group, [Market by Order](https://www.cmegroup.com/articles/faqs/market-by-order-mbo.html): order-level versus price-level observations remain anonymous and are not supplied by these daily candles.
- SEC Investor.gov, [Understanding Order Types — Investor Bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-14): execution-price and order-type limitations for stocks, not Binance-specific historical fill proof.
- LuxAlgo, [SMC library description](https://www.luxalgo.com/library/indicator/smart-money-concepts-smc/): attributed public terminology; no transfer of its settings, source implementation or performance claims.
- Binance, [Spot market-data specification](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints). Exact source responses and hashes are retained in the structure receipt and linked in `smc_observations_20261028.json`.
- Binance [public-data project](https://github.com/binance/binance-public-data), [data terms](https://data.binance.vision/?prefix=) and [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/): attributed non-commercial derived analysis. Unrelated code/publications retain their terms; no provider endorsement is claimed.

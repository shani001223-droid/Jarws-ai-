# Premium, discount and dealing ranges: coordinates rather than fair value

Reviewed: 28 October 2026, Asia/Karachi. This chapter treats range location as
an explicitly anchored price measurement. It does not estimate intrinsic value,
calibrated reversal probability or a current executable trading level. The
offline examples remain separate from Hoshi's existing V2 runtime.

## What is it?

A dealing range is a specified lower and upper reference used to express
where price lies between them. In the convention used here, the lower half
is discount, the upper half premium, and the exact midpoint equilibrium.
These are relative coordinates. Discount does not mean that an asset is
fundamentally undervalued; premium does not mean it must fall. Their meaning
depends completely on which boundaries, timeframe and information cutoff
were selected.

Given lower boundary L and higher boundary H, with L strictly less than H,
the midpoint is (L + H) / 2. The normalized position of a price P is
(P − L) / (H − L). Inside the closed interval, positions below one half
are discount and positions above one half premium. Exact equality is
equilibrium under this narrow definition. Endpoints belong to the interval.
A price below L or above H is outside, not an extra-strong discount or premium
observation. The position can be negative or greater than one; it must not
be silently clamped to make an invalid location look eligible.

This fraction is not an empirical percentile or probability. A position of
0.8 means eighty percent of the price distance from L to H. It does not say
that eighty percent of trades occurred below P, or that a reversal has an
eighty percent chance. A midpoint can also lie between permissible price
increments. Mathematical coordinates need not be valid executable order
prices without checking the venue's rules.

First-party LuxAlgo documentation presents premium, central equilibrium and
discount as chart areas. Its text also makes a stronger directional-likelihood
claim that is not reproduced or calibrated here. This chapter adopts only
an attributed description of the vocabulary, then states its own exact
arithmetic. It does not claim parity with the provider's zone widths,
protected swings or re-anchoring implementation.

### Original anchor policy and disclosed alternatives

`hoshi-prior-confirmed-dealing-range-1` takes the most recent strict two-left,
two-right pivot high and low confirmed **before the event bar opens**. The
chosen anchors stay frozen while that candle forms. At its completed close,
the tool locates the observed price relative to those pre-existing bounds.
Both origin and confirmation times remain in the receipt. The high and low
are independent latest references; they are not certified as the endpoints
of one selected directional impulse.

If either reference is absent, or L is not strictly below H, the range is
unavailable or invalid. No midpoint or location is fabricated. If price
finishes outside a valid pair, the original pair is preserved and the outside
status is explicit. Updating boundaries only because the price left them
would change the question being tested.

The receipt also computes two clearly named comparisons. A prior-twenty-bar
range uses the greatest high and least low of the twenty candles before the
event, excluding the event. An as-of-close pivot comparison allows a pivot
whose second confirmation candle is the event itself. Both alternatives
are causal at their stated clocks. They answer different questions and are
not interchangeable with a range fixed before the open.

Hoshi's existing V2 location check operates on its own confirmed higher-frame
references and latest lower-frame price. It is not replaced by this single
daily-frame educational protocol. In particular, a snapshot allowing newly
confirmed anchors at the close cannot claim that those anchors were already
available earlier within the day. Cross-frame range and price cutoffs also
need separate recording in eventual integration.

## Why does it form?

The coordinate forms because an analyst chooses two boundaries and normalizes
price between them. That part is arithmetic, not a market mechanism. Prices
may respond near previously observed areas because participants notice them,
new orders arrive, liquidity changes or valuations shift. Daily candles do
not identify which explanation applies. The fact that a price lies below
a chosen midpoint does not reveal demand, hidden inventories or a compulsory
return to equilibrium.

Range selection changes the reference distribution. A recent local pair can
be much narrower than a twenty-bar envelope, especially after a large trend.
An old high may remain the latest confirmed high while price moves far above
it; the necessary right-hand bars for a newer pivot may not yet exist.
That lag is a property of the definition, not evidence that price is
mathematically impossible or that the data should be edited.

Re-anchoring can change the label without changing the evaluated price.
A newly confirmed higher high raises the midpoint while the low stays fixed.
The same close can consequently move from premium to discount under another
permitted anchor clock. This is not a newly observed purchase or a valuation
change. A reliable record must attribute the changed label to the changed
reference, rather than presenting it as fresh independent market evidence.

## Application zone

Use range location as a conditional screen after freezing a valid range
selection policy. Define whether it is a recent local range, a larger
directional leg, a session range or another predeclared object. Record its
instrument, venue, quote currency, timeframe and activation time. If the
range is part of a paper hypothesis, specify when it expires or resets
before observing the future path. Do not combine a wide range for eligibility
with a narrower range for a favourable retrospective exit.

Premium and discount are most useful when they expose disagreement. A lower
frame can be in local premium while a larger frame remains in discount.
Those descriptions can both be true because they use different bounds.
They are not independent probability estimates and need not be resolved by
silently choosing the preferred one. A missing required alignment should
remain missing or produce WAIT under the eventual strategy's rules.

The educational receipt evaluates a fixed five-later-bar horizon against
the original before-open pivot bounds. It retains the first later close
below the frozen low or above the frozen high, along with the full path
and raw close change. It does not retrospectively update the original
boundaries to the alternatives. If the horizon is incomplete or the initial
range invalid, its outcome is null rather than a shortened success.

All cases use Binance Spot BTCUSDT daily UTC bars, 00:00:00–23:59:59.999,
quoted in USDT per BTC. They come from the existing three bounded captures,
retrieved during this 28 October 2026 review. These windows were already
inspected in prior curriculum work and are not independent holdouts. The
source receipt preserves exact raw bytes and hashes, while the SMC receipt
separates anchor, event and later-outcome times.

## Failure zones

No range location works 100%. Price can spend a long time in premium during
an advance or remain in discount during a decline. Fading every upper-half
observation can repeatedly oppose a trend. Buying each lower-half observation
can accumulate exposure while the chosen low is being invalidated. A range
describes relative location; it does not supply the independent conditions,
risk budget or execution assumptions needed by a strategy.

Stale or incompatible anchors are especially dangerous. Independent latest
pivots can describe different episodes and sometimes produce invalid ordering.
That invalidity must be retained. A narrow reference can also become obsolete
after a breakout. Calling any price below the old low discount conceals the
fact that the initial range has already failed as a containment hypothesis.
This protocol keeps outside status visible even if the price later rebounds.

Post-selection creates another failure. Trying several swing lengths and
choosing whichever calls the winner discount is fitting a description to
an outcome. The same problem arises when an analyst anchors a range using
a final extreme that had not yet occurred at decision time. A completed
chart does not prove that its final high was knowable at the earlier entry.
Feature tests must therefore replay prefixes, not merely recompute final
chart coordinates.

Finally, a location fraction cannot be substituted for fundamental value,
liquidity, spread or probability. A midpoint has no built-in fill guarantee.
If the minimum feasible paper size exceeds a cash or risk cap, a cheap-looking
coordinate does not fix that conflict. The current chapter includes no
orders, leverage or account performance, and its illustrative comparisons
cannot supply calibrated confidence.

## Three real historical examples with dates

### Example 1 — 11–16 June 2020: outside a local pair, discount in a wider envelope

Before **11 June**, the latest eligible low is **9,372.46**, originating
7 June and confirmed 9 June; the eligible high is **10,380**, originating
1 June and confirmed 3 June. Their midpoint is **9,876.23**. The event close
is **9,280.40**, below the low, with normalized position approximately
**−0.09137**. The correct label under the fixed pivot policy is outside below.

The alternative prior-twenty-bar bounds are **8,642.72–10,380**, midpoint
**9,511.36**. The identical close is inside their lower half, at position
about **0.36706**. Neither calculation is an error: the methods selected
different reference objects. The fifth later close on **16 June** is
9,525.59, approximately **+2.6420%** above the event close. That rebound
does not justify relabelling the original outside status as a guaranteed
discount entry or claiming an executed purchase at its low.

### Example 2 — 10–15 August 2021: premium does not make a subsequent advance impossible

At the **10 August** close, price is **45,584.99**. The pre-existing pivot
pair is **37,332.70–42,599**, midpoint **39,965.85**. The price lies outside
above it, at position approximately **1.56700**, and is not clamped to one.
The high originates 1 August and confirms 3 August; the low originates
5 August and confirms 7 August. These are lagged available references.

The wider prior-twenty-bar envelope is **29,482.61–46,454.15**. Its midpoint
is approximately **37,968.38**, and the event close is premium at position
about **0.94879**. The fifth later close, **15 August**, is **46,973.82**,
approximately **+3.0467%** higher. Premium in that alternative range is
therefore not a sufficient bearish forecast. No sale, short, target or
account result is inferred from the label.

### Example 3 — 7–12 November 2022: the same close changes sides when a high confirms

The pre-open pair on **7 November** is **20,031.24–21,085**, midpoint
approximately **20,558.12**. The observed close **20,591.13** is premium,
at position about **0.53133**. The upper anchor originates 29 October and
is already confirmed on 31 October; the low originates 3 November and
confirms 5 November.

At the **7 November close**, a newer high from **5 November**, **21,480.65**,
finishes its two-right-bar confirmation. The disclosed as-of-close comparison
can now use it with the same low. The midpoint becomes **20,755.945**,
placing the identical close in discount at approximately **0.38629**.
This later anchor was not available at the day's open. The midpoint's
fractional precision is arithmetic, not an executable order instruction.

The fifth later close, **12 November**, is **16,812.08**, a raw change of
approximately **−18.3528%** from 7 November. Thus even a causal at-close
discount classification does not establish safety or future appreciation.
The first later close below the original frozen low occurs on **8 November**.
The receipt retains that failure rather than replacing the old range with
later lows to rescue a historical buy story.

## How to use it to HUNT a trade

Begin with an explicit range definition and an actual information cutoff.
Use only anchors available under that definition, verify L is below H,
and locate an observed current-enough price. Report missing, invalid and
outside states honestly. A request for premium/discount does not authorize
invented anchors or a guessed NAS100 quote from Bitcoin history.

Next preserve disagreements rather than resolving them after the outcome.
If a new pivot changes the label, record the replacement and its activation.
If the strategy requires a range fixed before a session, do not use an
end-of-session anchor for an earlier decision. Cross-frame prices and
references need their own source times. Multiple coordinate methods on one
price history remain correlated descriptions.

A paper opportunity then requires separately defined structure, liquidity,
global flow, observed execution inputs and bounded cash/risk. Define costs,
expiry, ambiguity and failure handling before replay. Evaluate chronologically
on independent data, retaining outside-range and zero-opportunity cases.
Keep evidence coverage separate from win probability, which remains null
until genuinely calibrated. Missing required information means WAIT.

Hoshi should normally return a concise Roman Urdu status and teach the range
algebra only when asked. This source chapter and its offline measurements
are not runtime retrieval, model training, a profitable strategy or permission
to place orders.

## Sources

Primary links checked 28 October 2026. Numerical rules and comparisons are
original; no provider source implementation or course is reproduced.

- LuxAlgo, [Premium & Discount Zones](https://docs.luxalgo.com/platform/algos/price-action-concepts/pdzones): first-party terminology only; its stronger likelihood statement is not adopted as Hoshi evidence.
- LuxAlgo, [Market Structure](https://docs.luxalgo.com/platform/algos/price-action-concepts/market-structures): confirms that swing-display timing needs care, without certifying this anchor policy or detector parity.
- CME Group, [Support and Resistance](https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance): educational price-area references, not a fair-value model.
- Binance, [Spot market-data specification](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints). Raw observations are preserved in `../01_MARKET_STRUCTURE/structure_observations_20261028.json`, linked by hash in `smc_observations_20261028.json` and checked offline.
- Binance [public-data project](https://github.com/binance/binance-public-data), [data terms](https://data.binance.vision/?prefix=) and [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/): attributed non-commercial derived data analysis. Unrelated code/publications retain their own terms; no endorsement is claimed.

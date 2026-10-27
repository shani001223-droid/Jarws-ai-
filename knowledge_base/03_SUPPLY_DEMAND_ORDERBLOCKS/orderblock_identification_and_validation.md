# Order-block identification: operational rules, formation clocks and validation

Reviewed: 28 October 2026, Asia/Karachi. This chapter documents Hoshi's existing
formation convention in depth and audits it against genuine historical prices.
It does not certify a universal ICT definition, identify institutional orders
or replace the V2 runtime. Daily educational examples are separate from the
existing engine's actual fifteen-minute entry-pattern checks.

## What is it?

Within this repository, an order block is a price-action feature: a selected
opposite-colour candle before a qualifying directional displacement. Its
high-low interval becomes a reference for future observation. The term does
not mean that the candle contains a visible block order, that a bank has an
unfinished position there, or that price is obliged to return. A detector can
identify its own price conditions while leaving all those stronger claims
unknown.

The primary specification for Hoshi is `cloud_backend/strategy_engine.py`,
especially `_active_patterns`, together with the existing V2 module. This
chapter preserves that implementation and explains its formation arithmetic.
Other educators can select bodies, opens, multiple candles or different
qualification conditions. Those are different methods. A full original
licensed, timestamped creator-course definition and exact recognizer parity
were not obtained here; canonical creator-method certification remains an
explicit gap, not something inferred from third-party summaries.

The offline audit is called `hoshi-v2-orderblock-formation-audit-1`. It checks
the formation component on a chosen historical daily candle. It deliberately
does not claim to satisfy the entire V2 multi-timeframe, liquidity, dealing
range, active-gap, latest-bar retest and time-filter pipeline. A qualified
formation is weaker than an active confluence candidate, which is itself
weaker than an independently evaluated paper strategy.

### Exact formation arithmetic

Let A, B and C be three consecutive completed candles, with B the possible
displacement and C the confirmation candle. For a bullish construction the
geometric gap requires A's high to be strictly below C's low. For a bearish
construction C's high must be strictly below A's low. The interval between
those endpoints is the three-bar gap. Equality is ineligible. This is not a
claim that no transaction occurred there during B, nor an adjacent overnight
gap between two sessions.

Compute the average absolute open-close body of the twenty candles strictly
before B. B's directional body must be at least 1.5 times that positive
baseline. For bullish displacement its close must also exceed the greatest
high of the five candles immediately before B. For bearish displacement it
must close below their least low. A large body without that strict five-bar
break is not qualified. Including B in its own baseline or extreme window
changes the method and risks accidental self-comparison.

Among those same five preceding candles, choose the most recent strictly
opposite-colour candle: a down body before bullish B or an up body before
bearish B. Equal open and close is neither for this selection. If there is no
qualifying origin, no block is created. Freeze its **full high-low range**;
this differs from the wick-only pivot zones in the preceding chapter.
The origin can precede A, and no local pivot is required for this rule.

The joint feature becomes available only at C's close. Knowing the old origin
after B's impulse is insufficient while C's eventual extreme is still unknown.
The audit records the actual origin, B, C, baseline, directional body, body
multiple, five-bar reference, gap bounds and knowledge time. These inputs
allow another reviewer to reproduce the decision instead of relying on a
retrospectively placed rectangle.

## Why does it form?

The rule selects a particular transition: a recent opposite body, then a
relatively large directional body closing beyond recent extremes, followed
by separated A/C ranges. It describes a concentrated price move compared
with the chosen baseline. That description does not identify the underlying
trader, the fraction of unfilled interest or the intention behind later
cancellations. A colour change on an OHLC chart is not a position ledger.

Several ordinary mechanisms could generate such a move. Aggressive arrivals
can consume available quotes; displayed liquidity can be cancelled; a new
valuation can move both sides of the book; or the same flow can have more
impact when depth is low. These are possible explanations, not conclusions
drawn from the three daily cases. Without quote-event messages the audit
cannot allocate the movement among those mechanisms.

Actual hidden-order research uses richer inputs. CME distinguishes anonymous
order-level MBO information from price-level aggregation, and explains that
native iceberg refreshes retain an order identifier while externally managed
refreshes can arrive with new identifiers. Even that public feed does not
identify the customer. Zotikov and Antonov's paper, submitted 20 September
2019, describes iceberg detection using trade-summary/order-change relations
and closely timed arrivals, with validation on full-depth data. A daily
opposite candle contains none of those required observations.

Thus a statement such as “a large participant could have contributed to this
impulse” is a hypothesis. “The banks have orders left in this block” would be
an unsupported factual assertion here. A later revisit also admits multiple
explanations. It can be observed without claiming that the same historical
orders caused the response or that a deliberate retail trap occurred.

## Application zone

Use the formation as one reproducible location feature after its actual
confirmation. Retain the same width convention across samples, freeze the
origin and state the later validity rule. Hoshi's V2 convention invalidates
a bullish block when a later close falls below the origin low, and a bearish
block when a later close rises above its high. Separately, V2 requires its
three-bar gap to remain unfilled under its own extremum rule. A block that
survives by closing prices may still lose eligibility because the gap was
fully crossed.

The daily audit observes exactly twenty bars after C and retains first
contact, first favourable closing rejection, first wrong-side wick, first
invalidating close and first full gap crossing. It uses no hypothetical
fills. An incomplete twenty-bar window produces null outcome. These horizons
and diagnostics are educational extensions; they are not a claim that V2
trades daily bars or waits twenty days to make its current decision.

Actual V2 additionally uses the newest later bar, a recent scanning window,
an unfilled gap and a closing hold relative to its midpoint, with order-block
overlap and the other confluence gates handled downstream. Some checks share
the same bars and therefore the same evidence lineage. A gap, displacement
and block around one impulse should not be counted as three statistically
independent forecasts. These daily examples test formation and later price
relations only.

The source captures are Binance Spot BTCUSDT, quoted in USDT per BTC, daily
UTC 00:00:00–23:59:59.999. Historical windows are bounded and were retrieved
during the 28 October 2026 review, not on their event dates. All were already
inspected for curriculum work, so this is not untouched holdout evidence.
The companion zone receipt references exact raw-response hashes; observation
time, review date, formation date and outcome availability remain separate.

## Failure zones

No block works 100%. A fresh formation can fail on its first revisit. A large
body can reflect volatility expansion rather than durable directional
information. An extreme historical shock can inflate a twenty-body baseline,
making later legitimate moves ineligible. A low-volatility baseline can make
a modest absolute move pass. The multiplier is a versioned design choice,
not a universal measure of institutional conviction.

A full-range origin can be wide enough to make a tight invalidation unrealistic.
Refining to its open or midpoint only after seeing a successful later contact
adds hindsight. Changing origin to an older, better-looking candle after a
failure is another form of rule selection. The latest-opposite policy must
retain its failures even when a neighbouring candle would have worked.

Distinguish a closing rule from a stop rule. A long candidate can survive all
daily closes while an intervening low falls far below the origin. Calling
that a safe winning block ignores the likely relevance of that path to a
position. Conversely, a close invalidation observed at day-end cannot be
used to assume a fill at the earlier boundary. Gap crossing and block
invalidation must also remain separate events.

No revisit means no zone-entry opportunity under a waiting model. Price can
move away for twenty bars without validating a fill. On spot, bearish geometry
does not authorize borrowing or leveraged short execution. These are bearish
studies, not a new order path. The repo's free-first and paper-only constraints
apply regardless of how attractive the annotated historical chart appears.

## Three real historical examples with dates

### Example 1 — 4–28 May 2020: an intact close boundary conceals a lower wick

The selected down origin is **4 May**, with high 8,950 and low 8,522. Bullish
B on **7 May** opened 9,143.40 and closed 9,986.40: body 843 versus a preceding
twenty-body mean approximately 181.0475, or **4.6562 times** the baseline.
Its close exceeds the five-bar reference 9,395. C on **8 May** has low 9,705,
leaving a gap **9,395–9,705**. The formation is known at that day's close,
not at the 4 May origin or 7 May impulse.

On **10 May**, low 8,117 passes beneath the origin's 8,522 boundary, while
close 8,722.77 remains inside the block. That candle also fully crosses the
gap. A later **13 May** contact closes 9,309.37, beyond the block's upper
edge. Through the twenty-bar window ending **28 May**, no close invalidates
the block. Nevertheless its wrong-side wick and filled gap are explicit.
This is not evidence of a successful V2 entry or a safely held stop: the
active-gap condition has already failed and execution is unmeasured.

### Example 2 — 20 July–13 August 2021: qualified formation without a return

The latest eligible down origin is **20 July**, range **29,278–31,063.07**.
B on **23 July** closes 33,634.09 with directional body approximately
1,346.51 against baseline 745.6395, a multiple about **1.8058**. The five-bar
high reference is 32,858. C on **24 July** leaves a gap from A's high
32,591.35 to C's low 33,401.14. Only its close activates the joint feature.

Across the twenty later bars, **25 July–13 August**, neither the block nor
the far gap boundary is reached under the audit's tests. No contact, closing
rejection, wick breach, close invalidation or full gap crossing is recorded.
The qualification arithmetic is genuine; a hypothetical purchase at the
origin is not. The separate pivot-wick chapter uses a narrower interval and
an earlier activation for this same origin, illustrating why method and
clock must accompany every rectangle.

### Example 3 — 4–27 September 2022: bearish formation fails on first contact

The up origin on **4 September** has range **19,583.10–20,029.23**. Bearish B
on **6 September** falls from 19,795.34 to 18,790.61. Its directional body
1,004.73 is approximately **2.3644 times** the prior mean 424.9425, and the
close is below the five-bar low reference 19,565.66. C on **7 September**
has high 19,464.06 beneath A's low 19,633.83, qualifying the bearish gap.

On **9 September**, the first eligible block contact trades as high as
21,597.22 and closes 21,360.11. It crosses the gap and closes above the
origin high, invalidating the bearish block on that same candle. There is
no favourable closing rejection before invalidation. The fixed outcome
window ends **27 September**, but the active block's lifecycle already
ended on the ninth. A strong-looking formation therefore supplies a real
counterexample, not a calibrated bearish probability or profitable short.

## How to use it to HUNT a trade

Start with validated, appropriately current bars and an explicitly supported
symbol. Establish whether the candidate is a developing origin, a B-only
impulse or a completed A/B/C formation. Freeze all preceding windows before
calculating the body multiplier and extreme break. If any requirement is
missing, retain a rejection reason instead of retrofitting the oldest
opposite candle into a block.

After C closes, monitor future data with separate gap and block states. A
full gap crossing does not have to invalidate the block by close, but it
does change eligibility for a method requiring an unfilled gap. Record
contacts before or at close invalidation without promoting them to entries.
Keep no-return and incomplete-horizon statuses distinct. Only actual
post-signal observations can support later executable prices.

For paper research, add independently defined structure, liquidity, macro
and risk requirements, accounting for shared evidence. Costs, spread,
latency, partial fills and ambiguous intrabar ordering need a separate
execution model. The three selected cases cannot supply that model's win
rate. Chronological evaluation must include all qualifying candidates,
counterexamples, expired opportunities and drawdown, with genuine unseen
data and null probability until calibration is independently supported.

Hoshi's concise default output should report the evidence state and source
time, with WAIT when essential data or gates are absent. Explain the full
mechanics only when asked. This source chapter and offline audit are neither
runtime V3 integration nor model training, and they enable no live orders.

## Sources

Checked 28 October 2026; no proprietary mentorship text or native hidden-order
detector is copied.

- Existing repository specification: `cloud_backend/strategy_engine.py`, `_active_patterns`, and `modules/03_order_blocks.md`, inspected at the parent lineage preserved by `backup-v2-to-v3`. Offline audit implements formation arithmetic only; runtime source is unchanged.
- CME Group, [Market by Order](https://www.cmegroup.com/articles/faqs/market-by-order-mbo.html): anonymous order-level versus price-level evidence and native/synthetic iceberg identifier distinctions. No historical MBO dataset was obtained for these cases.
- CME Group, [EBS Iceberg Orders](https://www.cmegroup.com/tools-information/webhelp/ebs-workstation-quick-guide/Content/IcebergOrders.html): actual displayed/hidden quantity functionality, distinct from candle-derived labels.
- Zotikov and Antonov, [CME Iceberg Order Detection and Prediction](https://arxiv.org/abs/1909.09495): checked original abstract and submission date, not a claim that its method or results were replicated by Hoshi.
- Binance, [Spot market-data specification](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints), [public-data project](https://github.com/binance/binance-public-data), and [data terms](https://data.binance.vision/?prefix=). Exact captured prices and response hashes are retained in the structure receipt and referenced by `zone_observations_20261028.json`.
- Binance-derived data analyses use [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) attribution for non-commercial educational research, without relicensing unrelated code or publications or claiming endorsement.

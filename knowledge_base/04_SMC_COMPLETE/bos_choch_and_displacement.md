# BOS, CHoCH and displacement: explicit references, clocks and counterexamples

Reviewed: 28 October 2026, Asia/Karachi. This chapter defines original Hoshi
research measurements within the SMC vocabulary. It does not port a commercial
indicator, certify a creator mentorship or identify institutional intent.
Offline source verification is separate from runtime retrieval and signals.

## What is it?

Break of Structure, or BOS, conventionally describes a price break in the
direction of an existing structural trend. Change of Character, or CHoCH,
describes an opposing break that raises a reversal question. Displacement
describes an unusually large directional price movement under a chosen size
and location test. They answer different questions: which reference was
crossed, how that crossing relates to prior structure, and how the event's
body compares with its recent baseline. None is a probability.

The checked first-party LuxAlgo library distinguishes trend-direction BOS
from countertrend CHoCH. Its separate market-structure documentation also
shows how changing swing sensitivity changes the internal versus larger
labels, and warns that displayed swing locations are retrospective. That
page's CHoCH paragraph uses directional parenthetical labels in a way that
does not match a simple break-direction convention. Hoshi therefore records
the actual crossed side and prior state explicitly, rather than treating a
provider's colour or directional adjective as a universal standard.

Market Structure Shift, or MSS, is sometimes used alongside CHoCH, but a
specific method may additionally require displacement, a sweep or another
condition. It is unsafe to declare every wick beyond a swing to be a completed
MSS. This chapter uses its own finite measurements and does not certify that
another named framework's complete setup is present. Teacher-specific
mitigation/breaker definitions remain separately pending in the manifest.

### Original prior-confirmed closing-break convention

The offline method is `hoshi-prior-confirmed-close-break-1`. It uses strict
two-left/two-right pivots, matching the repository's existing descriptive
structure vocabulary. A pivot high exceeds the four comparison highs; a
pivot low is below all four comparison lows. Equal extrema do not qualify.
The point becomes known only after the second right-hand bar closes. The
origin date and confirmation date must remain separate.

For an event candle, use only pivots confirmed **before its opening time**.
Select the most recent such high and low, without using the event itself
to create a new reference. The prior trend description compares the latest
two known highs and two known lows. Strict increases in both give rising
structure; strict decreases give falling structure. Other combinations are
mixed or insufficient. These are lagged descriptions, not forward truths.

A new up close-cross requires the preceding close to be at or below the
chosen high and the event close strictly above it. The down test mirrors
this at the selected low. In addition, the reference must not already have
been crossed by an earlier completed close after its confirmation. A later
return and recross of that same consumed level is stored as a recross,
not another fresh structural discovery. If the selected pivot changes,
its lifecycle and first-cross test change with it.

An up break with rising prior structure receives `bos_up`; an up break with
falling prior structure receives `choch_up`. Down breaks mirror these labels.
If the prior description is mixed or insufficient, a measured cross remains
an unclassified break rather than being assigned a convenient trend. Wick
excursions are recorded separately and do not satisfy the closing rule.
These labels belong to this versioned convention, not an exchange taxonomy.

### Separate displacement measurement

At the event's close, calculate the mean absolute open-close body of the
twenty bars strictly before it. A qualifying displacement must have a
directional body at least 1.5 times that positive mean and close beyond
the corresponding extreme of the immediately preceding five bars. The event
must close above its open for the upward test or below it for the downward
test. A large body alone is insufficient, and a swing cross can occur
without satisfying displacement.

Twenty prior bars are required. Missing warmup produces unavailable evidence;
a zero body baseline produces no ratio or qualified displacement. A small
baseline must not be divided into an invented infinity or perfect score.
This multiplier is Hoshi's operational research choice, consistent with the
body/break language already used in V2 formation analysis. It does not prove
that large orders, informed traders or a single controlling algorithm caused
the candle.

## Why does it form?

The observable event is that completed prices moved beyond a previously
available reference. Plausible mechanisms include aggressive transactions,
quote cancellation, changing valuations and variations in depth. The same
net flow can move price differently under different liquidity conditions.
Daily OHLC cannot separate those mechanisms or identify the parties involved.
A directional narrative must therefore remain a hypothesis rather than a
statement that institutions have disclosed their intentions.

BOS and CHoCH also arise partly from the observer's segmentation. A short
swing radius produces more local turning points than a longer one. A daily
countertrend break can coexist with a weekly uptrend. A detector that updates
the reference every time a small pivot confirms will generate a different
sequence from one protecting an older external extreme. Both can be clearly
specified; neither earns reliability merely by using the same acronym.

Displacement is relative to its baseline. After unusually quiet bars, a modest
absolute move may pass the multiplier. After a shock, an economically large
move may fail it. The five-bar extreme test adds location information, but
it still shares the event's prices with the body and structure tests.
Combining these checks does not create independent statistical confirmations.
The analyst should retain their common data lineage.

## Application zone

Use the labels to organize an observation sequence with an actual information
clock. First record the prior confirmed reference, its activation and whether
it has already been broken. Then observe the event close and compute its
separate body/break test. Only afterward investigate future retests, other
timeframes, macro evidence and feasible paper execution. A retest occurring
before the structural event cannot be relabelled as its later entry.

For reproducibility, distinguish reference availability from historical
outcome availability. The companion receipt records the feature at the event
close and then exactly five later completed bars. Their raw endpoint change
is a descriptive price comparison. It includes no hypothetical entry fill,
holding policy, transaction costs or account exposure, so it is not PnL.
When fewer than five later bars are available, the outcome remains null.

All examples use **Binance Spot BTCUSDT**, USDT per BTC, daily bars from
00:00:00 to 23:59:59.999 UTC. The bounded source windows contain 611 bars
across 2020, 2021 and 2022, already inspected in earlier chapters. They were
retrieved during the 28 October 2026 review, rather than on their event dates.
Exact raw-response hashes and request bounds are retained. No independent
historical-vintage guarantee, order book or cross-venue execution evidence
is supplied by these captures.

## Failure zones

No structural label works 100%. A correctly measured bullish BOS can be
followed by a lower five-bar endpoint. A bearish CHoCH can precede a rebound.
The labels describe how a bar relates to old prices, not which future path
must occur. They also do not specify a stop, target, size or holding period.
Selecting whichever exit later looks best would conceal that missing strategy.

Wicks and closes must remain distinct. A wick can cross a level while the
close stays on the original side. A closing confirmation arrives later than
that wick, and the old boundary may no longer be an executable price. The
method cannot demand close confirmation and simultaneously claim an earlier
entry at the extreme without a separately justified pre-existing order.

Repeated crossings are another failure in event accounting. Without a consumed
reference flag, a choppy market can manufacture several purported fresh BOS
events from one old line. This chapter preserves raw recrosses but excludes
them from fresh break classification. It does not erase their prices or
pretend the original break remained continuously valid.

Lagged swing-pair state can stay rising even after price violates its latest
low, until new pivots confirm. A live continuation gate must check that
contradiction and WAIT when required. The offline event label does not
automatically replace the full regime or authorize a reversal trade. These
measurement tools are not connected to V2 or V3 runtime decisions.

## Three real historical examples with dates

### Example 1 — 6–11 April 2020: bullish BOS and displacement, lower later endpoint

Before **6 April**, the most recent eligible high is **7,198**, originating
2 April and confirmed at the 4 April UTC close. The latest eligible low is
5,857.76, and the prior two-pair description is rising. The preceding close
is 6,772.78. On 6 April price opens 6,772.78 and closes **7,329.90**, its
first qualifying close beyond that high under the reference lifecycle.

The body is approximately 557.12 against a prior twenty-body mean 233.0805,
or **2.3902 times** the baseline, with a five-bar high break. Both `bos_up`
and upward displacement are therefore observed at the 6 April close.
However, the fifth later close, **11 April**, is **6,876.83**, a raw change
of approximately **−6.1811%** from the event close. This is counterevidence
to converting correct recognition into guaranteed continuation, not a
simulated account loss. The intervening 8 April recross of 7,198 is retained
as a previously broken reference recross, not a second fresh BOS.

### Example 2 — 21–26 June 2021: bearish CHoCH with a later rebound

Before **21 June**, the prior structure description is rising. The eligible
low **34,600.36** originates on 12 June and is confirmed at the 14 June close.
The preceding close is 35,600.16. The 21 June candle falls from 35,600.17
to **31,608.93**, first closing through that low. The method records
`choch_down`, with downward displacement: body approximately 3,991.24 versus
baseline 1,341.274, a multiple about **2.9757**.

The next day's low reaches 28,805, but the fixed fifth later close on
**26 June** is **32,283.65**, approximately **+2.1346%** above the event close.
An intraperiod lower low does not turn that positive endpoint into a negative
one. It also does not establish whether a hypothetical short target or stop
would have executed first. The receipt preserves both the path and endpoint,
with fills and strategy PnL unknown.

### Example 3 — 4–9 November 2022: strong bullish break before severe adverse movement

Before **4 November**, the latest eligible high is **21,085**, originating
29 October and confirmed on 31 October. The prior two-pair description is
rising, and the preceding close is 20,207.82. The event closes **21,148.52**,
first crossing that reference. Its body 941.40 is approximately **3.7579 times**
the preceding body mean 250.5135 and also breaks the five-bar high.

The measurement is a qualified `bos_up` with upward displacement. The later
path nevertheless closes 18,547.23 on **8 November** and **15,922.81** on
**9 November**, the fixed fifth bar. The endpoint change is approximately
**−24.7096%**. Those are actual venue prices, not proof of a particular news
cause or a realised trading loss. A larger displacement multiple clearly
does not protect against a subsequent adverse regime.

## How to use it to HUNT a trade

Start with a supported source and completed bars. Reject insufficient history,
future references and unconfirmed pivots. Keep the chosen swing method,
timeframe and direction convention fixed. If a source calls a label bullish
because of its prior trend while another uses the break direction, resolve
the actual high/low crossing instead of blindly translating the adjective.

Observe the close and record geometry before considering a paper opportunity.
Preserve the displacement result separately from BOS/CHoCH, and preserve
mixed-state breaks without inventing trend. Require genuinely later evidence
for any retest model. If the same reference has already broken, classify the
recross explicitly rather than increasing a fresh-event count.

A later executable hypothesis needs independently defined liquidity, global
flow, source times, risk, costs and an ambiguity policy. Multiple tests on one
impulse are correlated. These selected historical cases are not independent
calibration and cannot produce a 92% confidence figure. Future evidence
coverage must remain distinct from win probability, which stays null until
independently calibrated. Missing or stale required inputs mean WAIT.

Hoshi's normal response should remain concise Roman Urdu, teaching this
material only when asked. The chapter and receipt add source knowledge for
later integration, not model training, current trade prices or an order path.

## Sources

Primary links checked 28 October 2026; analysis and offline rules are original.

- LuxAlgo, [SMC library description](https://www.luxalgo.com/library/indicator/smart-money-concepts-smc/): first-party terminology, not evidence of predictive performance or Hoshi parity.
- LuxAlgo, [Market Structure documentation](https://docs.luxalgo.com/platform/algos/price-action-concepts/market-structures): checked sensitivity/retrospective-display discussion and directional wording. Hoshi uses explicit crossed-side fields rather than assuming identical labels.
- CME Group, [Support and Resistance](https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance): chart references as areas, not a guarantee or certification of this detector.
- Binance, [Spot market-data specification](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints). Exact captures and hashes are retained in `../01_MARKET_STRUCTURE/structure_observations_20261028.json`; `smc_observations_20261028.json` references them and is replayed by `scripts/v3_smc_evidence.py`.
- Binance [public-data project](https://github.com/binance/binance-public-data) and [market-data terms](https://data.binance.vision/?prefix=); attributed derived data analysis under [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) for non-commercial education. No endorsement, paid entitlement or relicensing of unrelated code/publications is claimed.

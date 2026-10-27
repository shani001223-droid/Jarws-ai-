# Market structure and swings: observable geometry, causal confirmation and invalidation

Reviewed **28 October 2026, Asia/Karachi**. Curriculum research; no runtime
integration, model training, live signal or order execution. Historical prices
below are **Binance Spot BTCUSDT, USDT per BTC, daily UTC candles**, not USD
bank quotes, Nasdaq futures or a consolidated cryptocurrency market.

## What is it?

Market structure is a description of the ordering and relationships of observed
price extremes, transitions and reference levels over a specified sampling
interval. A swing high is a local maximum under a declared rule; a swing low is
a local minimum. Neither term identifies the owner, intent or profitability of
an order. An observation must say whether it uses candle wicks, closes, a
threshold reversal, or another construction. These methods can disagree without
either dataset being corrupt.

For HOSHI's worked observations, a daily wick high at index `i` qualifies only
when its high is strictly greater than the highs of the two previous and two
subsequent completed candles. A low uses the reverse strict comparison. Equal
extremes produce no pivot under this particular rule. The rule is an explicit
project convention, not a universal definition certified by an exchange.
`pivot_at` records the candidate candle's close; `confirmed_at` records the close
of the second following candle. At a decision time, only confirmations already
available are eligible. Drawing a marker two days earlier does not make its
information available two days earlier.

Higher highs and higher lows describe two rising sequences of same-type
confirmed extremes. Lower highs and lower lows describe two falling sequences.
Mixed comparisons are a separate state. Insufficient observations are also a
separate state; they must not be silently mapped to neutral, bearish or zero
risk. This chapter compares the most recent two highs and most recent two lows
independently, as the existing research module does. It does not automatically
collapse consecutive highs into an alternating ZigZag. An alternating-swing
algorithm would require its own version and separate evidence.

Separate **stored swing state**, **latest price location** and **trade permission**.
A previous rising pair of lows can remain the last confirmed pair while the
current price has already broken below it. Calling that stored state bullish
without its breach flag would conceal important information. A future V3 entry
gate must resolve the contradiction or return WAIT. More precise vocabulary
improves honesty before it improves any prediction.

## Why does it form?

Price paths reflect transactions, quote changes, changing willingness to take
inventory, information arrivals and differences in trading horizons. A local
extreme is what a chosen sampling and comparison procedure retains from that
path. It does not by itself demonstrate that a bank defended a level or that a
retail stop was targeted. Identical candle geometry can arise from different
underlying sequences of orders.

Past highs and lows can become public reference points, so it is reasonable to
test whether behavior near them differs from behavior elsewhere. CME's support
and resistance lesson describes their use as chart references. That is a
description of a technical practice, not evidence that every retest succeeds.
The proposed mechanism and its empirical strength are distinct questions.

Lo, Mamaysky and Wang's original research illustrates how visually described
patterns can be translated into algorithms and conditional-distribution tests.
Its reported information content does not validate HOSHI's two-bar convention,
establish net returns for these examples, or eliminate the need for independent
testing. The useful lesson is methodological: specify the mapping from data to
labels before examining outcomes.

There is an unavoidable delay-versus-noise tradeoff. A smaller comparison radius
produces more candidates, more local reversals and less confirmation delay. A
larger radius can suppress small moves while requiring additional subsequent
bars. A percentage-reversal rule answers a different question from a fixed-bar
rule. Choosing whichever rule looks best after a crash is a new experiment and
must be counted in the research search, rather than presented as foreknowledge.

## Application zone

Use structural observations to answer bounded questions: which previously
confirmed extreme is nearest, whether successive comparable swings rise or
fall, whether current price has crossed a known reference, and whether enough
closed history exists. These are useful inputs to a paper research process.
They do not independently supply an entry, stop, target, position size or
calibrated probability of success.

Start with the instrument and data contract. BTCUSDT spot and a perpetual
contract can print different wicks. A four-hour UTC candle and a four-hour
candle aligned to another timezone can contain different observations. A daily
index close has no intraday high or low information. Missing bars must be
reported and handled according to a predefined policy; stitching a gap and
pretending the series remained continuous can manufacture a local extreme.

Then specify the event. A wick crossing is not a close crossing. A first close
beyond a level is not a retest. A sequence of two closes is not an independently
observed liquidity event. For a close-break experiment, freeze the level before
the decision candle and compare the completed close with that frozen level.
For a wick-break experiment, use an observed high or low. Include tick size,
comparison tolerance and equality handling in the versioned rule.

Use both the level's origin and its knowledge time. If a candidate high is on
Monday and needs Tuesday and Wednesday to confirm, the historical engine may
first use it after Wednesday's close. If the data vendor publishes later, that
publication or receipt delay is an additional restriction. These captures were
downloaded retrospectively in October 2026; they do not prove the exact vintage
or feed latency available to a trader in 2020, 2021 or 2022.

Record the state and the latest-price contradiction separately. A falling swing
sequence with a new close above its latest confirmed high is a transition
candidate, not permission to sell automatically. Likewise, a rising sequence
with a close below its last confirmed low deserves an invalidation flag before
any continuation model is considered. The correct response can be WAIT even
when the descriptive label has not yet changed.

For comparisons across markets, normalize distances deliberately. A fixed
100-unit difference means different things in a 5,000-price series and a
50,000-price series. Percentage distance and a past-only volatility estimate
answer different questions. Do not use the maximum future excursion to set a
threshold that supposedly existed at the entry. Spread and other execution
costs need separate observations; candle volume cannot substitute for them.

## Failure zones

**Confirmation leakage:** a hindsight chart shows a perfect turning point, but
the right-hand bars did not exist at the claimed entry. Backdating the decision
to the pivot creates a strategy that could not have acted on that information.
The evidence tooling tests that appending future candles cannot change a
snapshot explicitly requested for an earlier cutoff.

**Stale-state continuation:** the last two confirmed highs and lows may describe
an obsolete path. If price travels strongly in one direction without another
qualified pivot, that state can persist through a large move. Neither the
stored sequence nor its age is a substitute for current location. November
2022 below gives an actual contradiction rather than an invented success case.

**Multiple scales:** a two-day pullback can coexist with a larger rising trend.
Calling one timeframe correct and the other wrong hides the fact that their
questions differ. Changing timeframe after a loss can make almost any outcome
look consistent. Predeclare the context and decision frames and preserve
disagreement as data.

**Ambiguous bars:** a wide outside candle may be a local high and local low at
once. Daily OHLC does not reveal which extreme happened first, which orders
were active, or whether a limit order would have filled. An algorithm must
retain ambiguity instead of inventing an intraday path. The captured November
14, 2022 candle meets both local-extreme tests under this convention.

**Extreme prints and venue differences:** an isolated wick may be an actual
local trade, an error, or a price unavailable elsewhere. Inspect source
provenance, amendments and independent data where permitted. Do not delete the
observation merely because it damages a preferred narrative. Retain an original
capture and a documented correction separately when a provider revises data.

**Small and selected samples:** three historical windows are teaching material,
not an unbiased population. They contain different market conditions but were
chosen retrospectively. No win rate, statistical significance, strategy return
or benefit after fees has been estimated here. No market structure works 100%.

## Three real historical examples with dates

The companion `structure_observations_20261028.json` contains exact captured
responses, request bounds, retrieval times, provider attribution and hashes.
`scripts/v3_structure_evidence.py` reconstructs the observations without a
network connection. Candle dates below mean UTC opening dates; a daily bar ends
at **23:59:59.999 UTC on that date**. These are analytical reconstructions from
observations, not fabricated trades or proof of what the market intended.

### Example 1 — 13–15 March 2020: knowing a low only after its confirmation

In the January–June 2020 BTCUSDT capture, the March 13 daily wick low was
**3,782.13**. Under the strict two-left/two-right rule it became a confirmed low
only at the March 15 close. The March 13 close was **5,578.60**; the March 15
close was **5,361.30**. Neither closing value is the wick price or a guaranteed
buy fill at the low. The minimum could have been seen as an evolving price
before confirmation, but it was not yet a confirmed pivot under this rule.

At the March 13 cutoff the last confirmed lows were February 19 at **9,350.00**
and March 1 at **8,411.00**; the close was already below the latter. The stored
high sequence still used March 2 at **8,965.75** and March 7 at **9,188.00**, so
the pair-comparison state was mixed. At March 15 the new low entered the
confirmed set, yet the same two highs still made the combined state mixed.
This is why a crash narrative and a mechanical structural label can differ.

The exercise is to replay both cutoffs, expose the breach and confirmation
timestamps, and reject any entry supposedly based on a confirmed March 13 low
at that day's wick. It does not establish a profitable bottom-buying rule.

### Example 2 — 19–21 May 2021: a descriptive falling sequence after a large move

The March–August 2021 capture records a May 19 daily low of **30,000.00**,
confirmed at the May 21 close. At that cutoff the last two confirmed highs were
April 14 at **64,854.00** and May 3 at **58,981.44**. The last two confirmed lows
were May 13 at **46,000.00** and May 19 at **30,000.00**. Both comparisons were
lower, so the explicitly defined state was lower highs and lower lows.

That description was available only after the relevant confirmations. The
May 21 close was **37,252.01**, far above the May 19 wick low. The analysis does
not claim that someone could short the earlier high after learning the later
state, or that a fresh short at the observed close would have favorable net
expectancy. The distance between the low and the later decision price is part
of the problem, not a detail to erase from a persuasive screenshot.

The exercise is to distinguish historical path description from a forward
entry hypothesis. Require a separately observed, risk-bounded setup and retain
the possibility that nothing is executable after confirmation. There are no
position fills or strategy profits in this example.

### Example 3 — 10 November 2022: a rising stored label contradicted by price

At the November 10 close, the May–December 2022 capture still had confirmed
highs of **21,085.00** on October 29 and **21,480.65** on November 5. Its latest
confirmed lows were **20,000.09** on October 28 and **20,031.24** on November 3.
Those four earlier extremes produced a rising pair-comparison label. However,
the November 10 close was **17,601.15**, below the latest confirmed low. The
receipt therefore records `close_below_latest_confirmed_low=true` alongside the
rising stored label.

The November 9 wick low of **15,588.00** was not confirmed until the November 11
close. A chart rendered after November 11 can display that marker on November
9, but a November 10 decision cannot consume its later confirmation. On
November 11 the two-low comparison changed and the combined state became mixed.
This counterexample demonstrates a lag in a simple descriptive convention,
without assuming why particular market participants sold.

A future V3 continuation gate must handle the contradiction explicitly. It
must not treat the unqualified rising label as sufficient evidence for a long.
This chapter records the requirement; it does not claim that the existing
runtime has already been changed or that the counterexample calibrates an
alternative trading rule.

## How to use it to HUNT a trade

Here HUNT means a reproducible search for a **paper research candidate**. Begin
by freezing venue, symbol, interval, candle alignment, decision cutoff and the
exact pivot version. Verify continuous completed data and its provenance.
Unsupported markets, gaps, future bars or stale required inputs produce WAIT.
Do not substitute these old captures for a current price feed.

Next, reconstruct only the prefix available at the cutoff. Report the last two
eligible highs and lows with confirmation timestamps, current price relative to
them, the structural state, contradictory breaks and the age of each reference.
Write down which observation would invalidate the intended continuation or
reversal hypothesis. If there is no stable reference, record it as missing.

Then ask whether an independent, predeclared execution trigger exists. A
structural context can organize a search, but it cannot manufacture a liquidity
event, FVG retest, global-flow observation, cost estimate or supported market.
Correlated labels calculated from the same candles should not be counted as
independent confirmations merely because their names differ.

Finally, record the candidate before measuring its subsequent path. Evaluate
chronological holdouts with realistic delay, spread, fees, slippage and gap
assumptions. If both stop and target fall inside one historical bar and no
finer data exist, retain the ambiguity or use a declared conservative policy.
Export the inputs, rule version, cutoff and failed cases along with any
successful ones. Default output can be concise Roman Urdu, for example:
`WAIT — purana swing label hai; price ne confirmed low tor diya. Naya setup
abhi verify nahi hua.` Concision must preserve the evidence limit.

## Sources

All links below were checked during this chapter's review. The reasoning and
algorithms are original project analysis; external descriptions are attributed
and are not copied course material. Source pages can change after review.

- [CME Group: Support and Resistance](https://www.cmegroup.com/education/courses/technical-analysis/support-and-resistance) — prior extremes as conventional chart references; not a universal success claim.
- [Lo, Mamaysky and Wang, Journal of Finance, August 2000, author-hosted original paper](https://www.mit.edu/~wangj/pap/LoMamayskyWang00.pdf) — algorithmic pattern recognition and empirical inference; not validation of HOSHI's custom rule.
- [Binance Spot REST market-data documentation](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market) — kline fields, UTC default and bounded historical requests.
- [Binance market-data-only endpoint documentation](https://developers.binance.com/en/docs/products/spot/faqs/market_data_only) — keyless read-only host used for the captures.
- [Binance Vision dataset terms, reviewed version dated 26 August 2026](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md) — captured data and derived analytical facts are used for non-commercial education/personal non-production research with attribution.
- [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) — this chapter and the companion Binance-derived evidence are distributed under these terms; unrelated repository code is not relicensed. No commercial-data permission or provider endorsement is asserted.

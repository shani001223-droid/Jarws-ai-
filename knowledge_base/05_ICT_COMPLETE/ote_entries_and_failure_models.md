# Optimal Trade Entry: retracement arithmetic, anchor choices and failed entries

## What is it?

Optimal Trade Entry, usually abbreviated OTE in ICT material, is a named
retracement framework. The word optimal is part of the name, not a result
established by optimization or an assurance that its entry maximizes profit.
A retracement fraction tells us where a price lies relative to two selected
anchors. It cannot tell us by itself whether the selected move will resume,
whether an order can fill, or whether the expected gain exceeds realistic costs.

The original **OTE Primer — Intro To ICT Optimal Trade Entry** was uploaded to
the creator channel on **30 September 2017, 00:08:26 UTC**. Original English
captions were checked. Around 9:06–11:31, the speaker discusses retracement
after an impulse/structure change and identifies **62%, 70.5% and 79%** levels.
Around 14:15, the narration acknowledges that objectives are not always reached.
Around 35:36, it discusses body-based anchoring rather than simply taking wick
extremes. Chart visuals and a complete creator-method recognizer were not
obtained. Hoshi's fixed-wick diagnostic below is therefore explicitly an
original adaptation, not verified replication of the primer's drawings.

For an upward leg from low L to high H, with range R = H − L, the q retracement
price is **H − qR**. The 62–79% band is therefore **[H − 0.79R, H − 0.62R]**.
For a downward leg from H to L, the corresponding upward retracement is
**L + qR**, with band **[L + 0.62R, L + 0.79R]**. The 70.5% line lies halfway
between those band boundaries. Percentages are fractions of the selected leg,
not percentages of the account, absolute price or chance of a winning trade.

## Why does it form?

Prices can retrace after a move for many reasons: changed immediate demand,
profit taking, hedging, new information or ordinary variation around a range.
The OHLC data alone do not identify which mechanism caused a specific pullback.
A ratio overlays a consistent measurement on that pullback. Consistent geometry
is useful for describing and testing a hypothesis, but it is not evidence that
prices obey a ratio or that a participant must defend it.

Anchor selection accounts for much of the apparent precision. If a trader can
choose among many nested legs, several ratio bands may lie near almost any
interesting later turn. Selecting whichever leg best explains the outcome gives
the appearance of prediction while using hindsight. A testable approach must
say how anchors are selected, when they become known and whether later extremes
replace them. A range frozen before a decision is different from a range
continually redrawn to contain the entire later move.

Bodies and wicks answer different questions. Wicks retain the full recorded
trade range of each candle on that feed; bodies use its opening and closing
prices. Switching between them changes the endpoints, band width, distance to
invalidation and candidate contacts. Neither choice can be silently adjusted
because a later candle missed a boundary by a small amount. Feed differences,
price increments and sampling intervals make exact equality especially fragile.

A retracement also needs a directional premise. Choosing an ordered low followed
by a high describes an upward leg within that sample, not necessarily the
higher-frame trend. A larger decline can contain that leg. The same price may
be deep retracement of one move and shallow retracement of another. The correct
response to conflicting anchors is to expose the competing hypotheses and test
them separately, not average their labels into confidence.

## Application zone

The original offline convention is **hoshi-frozen-wick-ote-1**. It uses the
thirty completed one-minute bars immediately before one of the already specified
study hours. The first occurrence of the global low and first occurrence of
the global high within that fixed window are the anchors. If the low occurs
first, the descriptive leg is upward; if the high occurs first, it is downward.
If both extremes occupy the same candle, their intrabar ordering is unknown
and this convention rejects the case. A nonpositive range is also invalid.

All anchors are fixed before the study hour begins. The feature stores their
actual bar intervals, the source range, exact floating-point calculations and
earliest possible availability after the last pre-hour candle closes. Provider
arrival time remains unknown. The convention uses wick extremes throughout;
it does not call its bounded leg the original creator's optimal impulse,
assert a structure shift occurred, or invent a global directional thesis.

Observe the **next five completed minute bars** as a separate outcome horizon,
consistent with the bounded minute diagnostics in this family. A band contact
requires the bar range to overlap the band. A closing rejection requires a
contact followed by a close at or beyond the 70.5% line in the proposed direction.
Touching or crossing the original opposite anchor invalidates that candidate
before a same-bar rejection can be credited. These are declared research
conventions, not a guarantee that a resting order could fill or that a closing
confirmation could be traded at its earlier contact price.

The band itself spans **17% of R**. A very large anchor range creates a wide
band and potentially large distance to invalidation. A tiny range can create
distances dominated by spread and fees. Exact calculated prices may not be valid
exchange increments, so a future paper execution model needs the actual symbol's
filters and a deterministic rounding convention. These diagnostic receipts
retain the unrounded arithmetic for audit; they issue no executable price.

For illustration, suppose an entirely hypothetical paper account allows a
five-unit loss budget and an observed, permitted entry has ten units of
price risk per asset before costs. The cost-free upper quantity would be
0.5 asset units. Adding fees, slippage allowance, lot-size rounding and an
account exposure cap can only reduce the permitted quantity. This arithmetic
does not authorize a real purchase, short, leveraged position or paid service.
If a valid reachable entry is absent, sizing is premature.

## Failure zones

**No retracement:** the move continues without contacting the fixed band. The
directional story might look correct at the endpoint, but the proposed entry
did not happen. Replacing the absent entry with the earlier close creates an
entirely different strategy. The three actual examples below intentionally
retain this unfilled outcome instead of counting favorable moves as wins.

**Excess retracement:** price passes through the band and reaches the original
anchor. A visually attractive rejection close can occur after that invalidation.
Hoshi records the boundary event first. A longer-term interpretation may use
another invalidation rule, but it must be separately versioned and cannot erase
the original candidate's failure.

**Unconfirmed anchors:** a discretionary swing can look obvious only after
future candles. A pivot requiring right-hand confirmation is unavailable at
the pivot's own timestamp. This fixed-window diagnostic avoids that particular
lookahead by waiting for the entire pre-hour window. It still has sampling
and anchor-selection limitations, and is not automatically a better trading rule.

**Touch versus execution:** a contact is an interval relationship in a candle.
It does not prove queue priority, an executable bid/ask or an order fill.
Entering only after a rejection close means the earlier band price cannot be
claimed as the entry without a subsequent observation and explicit order policy.
If stop and target both lie within one candle, their order can remain unknown;
a future evaluation must preserve ambiguity or use conservative treatment.

**Post-selection repair:** changing anchors, moving from wicks to bodies,
extending five minutes to an hour, or adding a second attempt after seeing
the first result changes the experiment. Such ideas can be researched as new
versions, but their tuned examples are not independent validation. These
three windows were already inspected in adjacent chapters and remain an
exploratory teaching sample, not untouched evidence of an OTE advantage.

## Three real historical examples with dates

The following **Binance Spot BTCUSDT** one-minute cases reuse the same genuine
fixed captures as the preceding ICT chapters. They were fetched on 28 October
2026 with exact response hashes. Event timestamps below are **New York local
time**, with their historical EST/EDT offsets explicit. All prices are USDT per
BTC. No creator-chart reproduction, futures equivalence, actual fill, strategy
PnL or calibrated probability is claimed.

### Example 1 — 15 May 2023: bearish geometry, absent five-minute entry

The pre-hour window is **02:30–03:00 EDT**, or 06:30–07:00 UTC. Its high
**27,544.10** occurs in the 02:30 candle; its low **27,405.00** in the 02:53
candle. Their chronological order defines a descriptive downward leg with
R = **139.10**. The upward-retracement band is **27,491.242–27,514.889**,
and its 70.5% line is **27,503.0655**. Those many decimals describe arithmetic,
not an executable price-increment claim.

During 03:00–03:05, the highest observed price is **27,489.49**, below the
band's lower edge. No band contact or closing rejection occurs. The fifth close
is **27,469.34**, below the last pre-hour close **27,475.63** by approximately
**0.02289%**. That directional endpoint is not a filled short. There is no trade
under this declared contact requirement, and strategy PnL remains null.

### Example 2 — 5 January 2024: bullish leg does not promise a pullback

The **09:30–10:00 EST** window corresponds to 14:30–15:00 UTC. Its first low
**43,100.00** occurs at 09:42 and high **43,800.00** at 09:49. The ordered
upward range is **700.00**. The retracement band is **43,247.00–43,366.00**,
with 70.5% line **43,306.50**. All anchors are known only after the pre-hour
window completes; their earlier candle times do not imply an earlier active
entry instruction.

The following five minutes never fall into the band: their minimum is
**43,487.18**. The fifth close **43,680.52** is about **0.44722%** above the
last pre-hour close **43,486.04**. Crediting that move to a deep-retracement
entry would invent the missing execution. The narrow experiment observes no
contact. Whether a later hour contains a retracement is a separate horizon,
not permission to retrofit this result.

### Example 3 — 8 August 2024: almost flat endpoint, still no entry

The **13:30–14:00 EDT** window, 17:30–18:00 UTC, has high **59,821.12** at
13:30 and low **59,437.77** at 13:59. The descriptive downward range is
**383.35**. Its upward-retracement band is **59,675.447–59,740.6165**, with
70.5% line **59,708.03175**. The final low anchor is in the last pre-hour
candle, so it cannot be treated as confirmed before that candle has completed.

Across 14:00–14:05, the highest price is **59,498.34**, far below the band.
The fifth close **59,469.67** is only **0.21 USDT** below the last pre-hour
close **59,469.88**, approximately **−0.00035%**. That small raw change is
neither a profitable trade after costs nor measured zero risk. Contact is
absent, no order is enabled, and a probability remains null.

## How to use it to HUNT a trade

Specify the leg-selection rule, timeframe and information cutoff before drawing
ratios. Calculate the band from the frozen endpoints and preserve its version.
Then wait for the actual declared entry event inside its permitted horizon.
If the band is missed, export no entry. If the anchor invalidates first,
cancel the candidate. Never move a boundary to rescue a near miss or infer
a limit fill from a favorable later close.

Require independent evidence for direction, reference liquidity and global
context before considering even bounded paper risk. Confirm the symbol's
supported venue, actual price increments, source freshness and realistic
costs. An unsupported short or unavailable quote produces WAIT rather than
an invented NAS100 order ticket. A descriptive retracement percentage is not
a success percentage, and evidence coverage is not a calibrated win probability.

Maintain causal replay records with absent contacts, invalidations, ambiguous
bars and unknown fills. Future chronological evaluation must use an independent
period, charge plausible costs and report zero trades honestly. For Jano,
routine Hoshi output can remain concise and explain only the immediate missing
condition; this longer lesson is for requested teaching. The chapter and offline
diagnostic do not train a model or complete the pending runtime/release gates.

## Sources

- [Original OTE Primer](https://www.youtube.com/watch?v=Cg0-CFJOJvg): original English captions and creator-channel publication metadata checked 28 October 2026; selected ratio/anchoring/failure passages briefly attributed. Chart visuals and exact recognizer parity remain unclaimed.
- [Binance Spot kline schema](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary timestamp and OHLC schema checked; adjacent JSON retains actual source URLs, raw response bodies and digests.
- [Python zoneinfo documentation](https://docs.python.org/3/library/zoneinfo.html): primary IANA conversion behavior checked; winter and summer source times are replayed using America/New_York.

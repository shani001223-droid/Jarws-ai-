# Fair value gaps: definition, completed-bar detection and honest retests

## What is it?

A fair value gap, or FVG in ICT chart vocabulary, is a relationship among
price ranges, not an exchange valuation or a guarantee that price must return.
Hoshi's explicit geometric version uses three completed candles A, B and C.
A bullish gap exists when **A.high < C.low**, leaving the interval
**[A.high, C.low]**. A bearish gap exists when **C.high < A.low**, leaving
**[C.high, A.low]**. Equality has zero width and does not qualify. The middle
candle can have traded through the entire interval, so this definition does
not prove that the interval contained no transactions.

The original creator-channel **Month 04 Fair Value Gaps** lesson was publicly
uploaded **10 September 2022, 19:00:04 UTC**. Its original English captions
were checked. Around 1:52–4:21, the speaker frames a bearish example using
the neighboring candles and the middle downward movement. Its commentary
also discusses lower-timeframe voids. That does not supply an audited global
trade tape. The uploader's description refers to older course distribution;
the upload date is not a dated market-event observation.

A separately checked original lesson uploaded **16 September 2024,
15:48:45 UTC** discusses additional body-gap boundary considerations around
24:17–24:33. Consequently a simple outer-wick detector must not claim exact
parity with every later creator interpretation. This chapter's method is
**hoshi-strict-outer-wick-gap-1**, an original transparent convention. Original
chart images and a complete creator-method recognizer have not been obtained.

The arithmetic midpoint, sometimes called consequent encroachment in the
teaching vocabulary, is **(low + high) / 2**. Width is **high − low**. Width
in basis points of C's close is **10,000 × width / C.close**. These are
descriptive measurements. A fifty-percent location is not a fifty-percent
chance of a successful trade, and the word fair does not establish fundamental
value or institutional ownership.

## Why does it form?

Sampling divides a continuous sequence of market activity into artificial
intervals. If prices move sufficiently between those intervals, the outer
candles can have nonoverlapping ranges even though the middle candle contains
many trades. Changing the timeframe changes which transactions belong to
each candle and can change whether an FVG exists. A one-minute gap can
disappear inside a five-minute aggregate without any source error.

Directional movement can reflect aggressive orders, changing available quotes,
news, hedging or other activity. An outer-wick gap alone does not identify
which mechanism dominated. In particular, it cannot establish a queue of
unfilled institutional orders waiting in the shaded rectangle. That stronger
claim would need evidence unavailable in OHLC bars.

A later return can occur because the market revisits earlier prices, but it
is not compelled by a bookkeeping imbalance in the drawing. Price may continue
away, pass straight through the area, or react only after an earlier trade
would already have invalidated. The useful question is conditional: under a
frozen definition, what happens within a stated subsequent horizon? It is
not whether a visually chosen example can eventually be drawn to look balanced.

Tick size and feed construction also matter. A tiny apparent separation can
be sensitive to venue, sampling alignment or numeric rounding. The source
prices here are Binance Spot trades represented in native minute bars. They
do not stand in for a futures contract, a broker CFD or the best bid/offer.
The same symbol name on another platform can denote a different instrument.

## Application zone

Start by validating the feed. Native interval, timestamp units, consecutive
bars, finite positive OHLC and sensible high/low relationships are prerequisites.
Keep the original request boundaries and exact response-body hash. The existing
minute receipt contains three fixed two-hour BTCUSDT captures, each with 120
bars. The new FVG receipt references that file and its hash rather than
silently duplicating it as fresh independent data.

An FVG is unavailable while C is unfinished. Its low or high may change and
erase the apparent separation. The feature records the first possible instant
after C closes, plus `provider_arrival_time=null`. Logical availability is
not proof that a provider or Realme phone received the candle instantly.
Any future live use needs actual arrival/freshness evidence before acting.

The chapter's examples select the **first chronological strict gap** in each
capture, without filtering by a clock window or future outcome. This differs
from the ICT-family study that selected the first gap inside a specific New
York hour. Different selection rules have different denominators. A geometry
detector can find a gap outside a trading window without contradicting the
time-filtered diagnostic.

Observe exactly five subsequent completed minute bars. Range overlap with the
gap is contact. Containing its midpoint is a midpoint touch. For a bullish
candidate, a later low at or below the lower boundary retires the original
candidate; for a bearish candidate, a high at or above the upper boundary does
so. This far-boundary rule takes priority over a same-bar closing rejection.
A bar that opens beyond a zone can pass the reference without proving every
intermediate price traded; the field therefore says touch or breach rather
than claiming a literal complete fill of resting orders.

A partial contact with a close holding the midpoint in the proposed direction
can be recorded before retirement. It is still geometric evidence, not an
entry fill. After retirement, later favorable movement does not reactivate
the same original candidate. Any inversion or fresh formation requires its
own later information time and rule version, addressed separately.

Complete outcomes include the five-bar path and raw endpoint change from C's
close. Incomplete outcomes remain null. No-contact, adverse first contact and
later favorable movement all stay visible. The diagnostic records WAIT,
orders disabled, unknown fills and `win_probability=null`; higher-frame,
liquidity, global-flow, supported execution and risk gates are not supplied
by three candles alone.

## Failure zones

**A moving C candle:** trading an apparent gap before confirmation uses a
different intrabar model. A backtest using C's final low/high to place an
earlier order leaks future information. Prefix tests require the completed
feature to be identical whether or not later bars have been appended.

**A contact treated as a fill:** the SEC's checked order guidance distinguishes
price conditions from guaranteed execution. A quoted or traded touch may not
fill a resting order of the desired size. An entry requiring a rejection close
cannot also claim the earlier touched price without a separate subsequent
order policy. Historical spread, queue position and device delay remain unknown.

**A later endpoint repairing invalidation:** if first contact crosses the far
boundary, a lower close five minutes later does not make a bearish gap valid
again. Selecting only the later favorable part of the path suppresses the
event that would have canceled the original hypothesis. A fresh candidate
must be explicitly identified rather than relabeling the failed one.

**A narrow gap ignoring cost:** a few USDT of width on a high-priced asset
can be small in relative terms. Fees, spread and slippage may exceed that
width. Gap width is not automatically the stop distance or available target
distance, so a direct width-versus-fee comparison is only a fragility check,
not a profitability estimate. Actual costs and valid price increments are
required for an executable paper plan.

**A name substituted for context:** a gap does not reveal an appropriate
direction, news clearance, an untouched liquidity target or a favorable
historical regime. Nor does the title of an original lesson validate an
automated implementation. Source attribution, operational parity and predictive
evaluation are separate claims.

**An inspected sample sold as validation:** these 360 minute bars were examined
in earlier chapters. The examples below add new measurements and a distinct
selection rule, not new unseen samples. Many formations share bars and
outcome horizons. A later evaluation needs a fixed population, independent
chronological periods, overlap handling and costs before any win probability
could be estimated.

## Three real historical examples with dates

All cases are **Binance Spot BTCUSDT, native one-minute candles**, priced in
USDT per BTC. Source intervals and event times below are UTC. The raw captures
were retrieved **28 October 2026** at approximately 01:59 UTC; the events
occurred in 2023 or 2024. Retrieval time is not a historical provider-arrival
log, and these examples are not the original creator's charts or reported trades.

### Example 1 — 15 May 2023: first bearish contact retires the candidate

A opens **06:30 UTC**, B **06:31**, C **06:32**. C.high is **27,488.58**
and A.low **27,495.50**, leaving a bearish gap **6.92** wide with midpoint
**27,492.04**. C closes **27,482.98**. The feature is logically available
no earlier than **06:33 UTC**, which is 02:33 New York daylight time and
outside the later 03:00–04:00 Silver Bullet hour.

The next minute reaches **27,498.48**, beyond the gap's far boundary, and
closes **27,498.47**. It is first contact and retirement, not an eligible
partial rejection. The fifth following close is **27,470.01**, about
**−0.04719%** from C's close. That later lower endpoint cannot restore the
retired bearish candidate or prove that a short filled before invalidation.

### Example 2 — 5 January 2024: a wider gap has the same lifecycle problem

The first strict gap uses A at **14:34 UTC**, B at **14:35**, C at
**14:36**. Its bearish bounds are **43,683.73–43,736.01**, width **52.28**
and midpoint **43,709.87**. C closes **43,672.01**. The earliest decision is
**14:37 UTC / 09:37 EST**, also before the separate 10:00–11:00 study hour.

The **14:37** candle reaches **43,771.30** and closes **43,747.85**. It
contacts and passes the far boundary in the same bar, so no partial-contact
closing hold is counted. Five minutes after C, the close is **43,642.23**,
approximately **−0.06819%** from its close. The direction of that endpoint
does not reverse the earlier retirement. Width alone did not prevent first-contact
failure, and no strategy PnL is assigned.

### Example 3 — 8 August 2024: continuation without a retest

A, B and C open at **17:30, 17:31 and 17:32 UTC**. The bearish gap is
**59,681.63–59,708.25**, width **26.62**, midpoint **59,694.94**. C's close
is **59,660.67**. The earliest feature time is **17:33 UTC / 13:33 EDT**.
The following five bars remain below the gap; their highest recorded price
is **59,660.68**, below its near boundary.

No contact, midpoint touch or far-boundary retirement occurs within that
five-minute horizon. The fifth close, **59,533.59**, is about **−0.21300%**
from C's close. This favorable-looking bearish movement did not provide the
declared retest entry. A system that requires contact must preserve no entry
rather than award a profitable fill at a price never revisited in the window.

## How to use it to HUNT a trade

Freeze the supported feed, timeframe and gap definition before scanning. Wait
for C to complete and for actual source arrival, then apply the separate
context, target, cost and paper-risk checks. Require the declared subsequent
entry event while the candidate remains active. If it never contacts, export
no entry. If its far boundary retires it, cancel that original candidate.

Do not manufacture current NAS100, forex or other unsupported levels from
these historical BTC observations. A score can describe the coverage of
observed rules, but it cannot become a confidence percentage without independent
calibration. Keep missing or stale inputs as WAIT, and retain ambiguity rather
than choosing a favorable intrabar sequence.

For Jano, the normal response should stay short in the existing Hoshi style;
teach the detailed geometry only when asked. This chapter and its offline
receipt are source knowledge, not fine-tuning, a new runtime loader or a
delivered trading signal engine. The final integration and release gates
remain pending.

## Sources

- [Original Month 04 Fair Value Gaps lesson](https://www.youtube.com/watch?v=FgacYSN9QEo): original English captions and creator-channel public metadata checked 28 October 2026; selected boundary/timeframe passages briefly attributed, not full-track republication or chart parity.
- [Original 16 September 2024 FVG lesson](https://www.youtube.com/watch?v=HhgWGduQZQY): original captions/public metadata checked; selected body-gap boundary qualification, not a complete recognizer specification.
- [Binance Spot kline schema](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary timestamp/OHLC schema checked; adjacent receipt pins actual source bodies and derived observations.
- [SEC Investor.gov order types](https://www.investor.gov/introduction-investing/investing-basics/how-stock-markets-work/types-orders): primary execution-versus-price-condition distinction checked; no exchange-specific fill assumed.

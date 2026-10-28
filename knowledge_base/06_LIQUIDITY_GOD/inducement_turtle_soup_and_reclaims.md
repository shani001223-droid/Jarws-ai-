# Inducement, Turtle Soup and reclaims: source rules versus inferred intent

## What is it?

Inducement is often used in discretionary trading language for a visible move
or reference that supposedly encourages participants to enter before a reversal.
Its strongest interpretation alleges someone deliberately caused that response.
An OHLC chart cannot establish such intent. Hoshi uses observable descriptions:
which reference existed, when price exceeded it, whether price returned, and
when that return could be known. A failed breakout can be measured without
claiming a coordinated trap or identifying anyone's positions.

Turtle Soup and Turtle Soup Plus One are named strategies associated with Larry
Connors and Linda Bradford Raschke. A checked **TradingMarkets Editors lesson,
published 9 September 2004**, provides a public publisher-side explanation.
It describes a same-day new twenty-session extreme whose prior extreme is at
least four sessions old; the long example uses a buy stop five to ten contract
ticks above the earlier low, valid that day, with a protective stop below the
new low. The short side reverses the construction. Plus One instead requires
an earlier extreme at least three sessions old, a first-day close beyond that
reference, and a next-day trigger back at it that expires if unused. Its stop
and management rules also differ. This brief attribution does not reproduce
the book or certify every implementation carrying the name.

The publisher's book catalogue independently identifies both authors and lists
separate chapters for the two strategies. The accessible public lesson resolves
the earlier missing-definition source gap; no purchase, account or third-party
full-book mirror was needed. The catalogue is not evidence for the profitability
of either method, and its promotional claims are not adopted. Full book/chart
parity and any particular ICT reinterpretation remain unverified.

## Why does it form?

A level can be salient to both continuation and reversal traders. A breakout
participant may interpret a new extreme as continuation; a reversal participant
may wait for that interpretation to fail. If the market cannot sustain prices
beyond the reference, a later return can create a falsifiable failed-break
description. Whether the move arose from stops, discretionary trading, hedging,
news or ordinary variation requires additional evidence.

The key event is not merely a long wick. A reference must exist before the
excursion, and a reclaim must occur afterward. A low visited earlier in the
same session cannot be promoted to a pre-existing multi-session low just because
it makes a neat drawing. Likewise, a closing reclaim is known at the close;
it cannot establish the precise intraday moment an earlier conditional order
was placed or filled.

The different age requirements express different hypotheses about the reference.
A level established yesterday and one left unbroken for several sessions
describe different histories. Ties matter: if the same extreme printed on
multiple days, selecting its oldest occurrence can artificially make a recent
reference look mature. Hoshi's original diagnostic selects the most recent
tied occurrence. That conservative convention is explicit rather than silently
choosing the age that admits a desired example.

A failed break also need not initiate a lasting reversal. Price can return
inside the old range briefly and then resume the original direction. Some
reclaims are too small relative to costs; others require a stop distance that
exceeds a bounded paper risk budget. A descriptive reversal candle therefore
does not establish a favorable trade, and a favorable five-day endpoint does
not establish a reachable entry.

## Application zone

The offline rule **hoshi-prior20-reclaim-1** is an original closed-day diagnostic,
not a reproduction of the publisher's intraday orders. For an event day, freeze
the maximum high or minimum low of the preceding twenty completed daily bars.
Exclude the event itself. Record the latest date on which that prior extreme
occurred and its age in bars. The feature then observes whether the event
strictly exceeds the high or low and whether its completed close returns to
the other side of the reference.

For a high-side case, a new high with a close below the old high is a closing
reclaim; for a low-side case, a new low with a close above the old low is its
mirror. Equality is not a strict reclaim. The same-day age gate requires at
least four bars. The diagnostic Plus One setup requires at least three bars,
a strict new extreme and a close at or beyond the old reference. These Boolean
fields describe geometry and the published age/close distinctions. They do not
claim that historical tick offsets, order trigger conventions or fills have
been verified.

The data here are **Binance Spot BTCUSDT UTC daily bars**, including weekends.
Twenty of these bars are not automatically twenty exchange sessions in a
particular futures contract. No historical tick-size filter for the selected
dates is supplied. Consequently the original five-to-ten-tick entry cannot
be converted into a fabricated BTC amount, forex pip distance or NAS100 level.
A future market-specific experiment needs the actual contract/calendar, valid
increments and independently checked order rules.

Keep the following five bars in a separate outcome record. For a prospective
Plus One candidate, the first of those bars is the only next-day eligibility
window in this diagnostic. Record whether its high-low range contains the
reference and whether it opens beyond the proposed entry side. A gap beyond
a stop trigger can entail execution at a different price; an absent reference
inside the recorded range is not automatically proof that every order type
could never execute. The opening-side flag prevents that misleading inference.

The event feature is available no earlier than the first instant after the
event closes. Provider publication and phone arrival times remain unknown.
The five-bar outcome is known only after its final close. Prefix tests ensure
later candles cannot alter the original reference or age. Incomplete outcomes
stay null rather than being counted as losses, zero returns or completed trades.

## Failure zones

**Confusing order variants:** the same-day version and Plus One have different
timing, age and trigger rules. Replacing both with a close-back-inside rule
creates an adaptation. Using the label Turtle Soup without exposing that change
makes comparisons unreliable. This chapter deliberately separates the publisher
description from Hoshi's narrower observable diagnostic.

**Using the final session extreme as an earlier stop:** a day's eventual low
may occur after the proposed entry. It was not available at entry time. Daily
bars do not resolve that sequence, and a historically correct full-day low
does not justify a precisely priced protective order earlier in the day.
Higher-resolution observations and a declared order lifecycle are required.

**Ignoring continuation:** a new low that closes below the old low may keep
falling rather than recover the next day. A high-side reclaim can fail as the
uptrend resumes. The absence of the required return must remain in the sample.
There is no universal number of attempts after which a reversal becomes certain.
Retry rules need their own limits, costs and independent evaluation.

**Inventing participants:** the terms inducement and trap can hide an untested
causal story. An extreme, a reclaim and a subsequent loss do not identify whose
stop was triggered or whether anyone engineered the sequence. Hoshi records
`institutional_intent_known=false`. A regulatory finding about a particular
event would be separately attributed rather than generalized to every wick.

**Equating trigger with fill:** the checked SEC stock-order bulletin distinguishes
stop activation from the execution price and stop-limit price control from
execution certainty. Venue-specific trigger rules can differ. Those mechanics
motivate conservative treatment; they do not certify a Binance order or a
short position. No real orders, borrowing or leverage are enabled here.

**Tuning the story afterward:** these examples reuse already inspected source
windows. They are not an independent holdout or a calibrated strategy study.
Moving the lookback, choosing older tied anchors or extending expiry after
seeing a missed trigger changes the experiment. Preserve the first version
and evaluate any revision on later untouched observations.

## Three real historical examples with dates

The cases are the first chronological strict new twenty-bar extreme with the
four-bar age gate and five subsequent bars available in each of the three
existing daily captures. Selection does not require a favorable future outcome.
All prices are **USDT per BTC on Binance Spot BTCUSDT**. Days run from
00:00 through 23:59:59.999 UTC. Original raw responses and source hashes remain
in the existing structure receipt; this chapter adds replayable derived cases,
not three new independent datasets or creator-chart replicas.

### Example 1 — 28 January 2020: next-day short reference never reached

The prior twenty-bar high is **9,198.98**, last observed **19 January**, nine
daily bars earlier. On 28 January, the high reaches **9,400.00** and the close
is **9,374.21**, above the old reference. There is a qualifying age/excursion
but no same-day closing reclaim. The diagnostic Plus One condition is present
on the short side because the event closes beyond the reference.

On **29 January**, price opens **9,375.34** and ranges **9,216.00–9,449.24**,
closing **9,301.53**. It neither opens below the proposed short reference nor
trades down to **9,198.98** in that recorded daily range. No next-day reference
contact can be credited. The fifth following close, **2 February: 9,331.51**,
is about **−0.45551%** from the event close. That lower endpoint is not a
filled short and cannot repair an expired missing next-day trigger.

### Example 2 — 10 April 2021: closing reclaim followed by adverse expansion

The prior twenty-bar high is **60,200.00** from **2 April**, eight daily bars
old. On 10 April, price reaches **61,500.00** but closes **59,769.13**, below
the old high. The four-bar age condition and a same-day closing reclaim both
hold in the original diagnostic. Plus One does not: its first-day close
requirement is different.

This daily candle does not validate the publisher's intraday tick-offset order
or prove which side of the extreme an order would have filled first. Nor does
the reclaim promise a sustained decline. The fifth following close on
**15 April** is **63,159.98**, approximately **+5.67325%** from the event
close, adverse to a simple short-at-close narrative. That is a raw price
comparison, not a simulated trade loss; entry, risk, costs and fills remain
unknown. The case prevents a neat rejection candle from becoming a guaranteed
reversal example.

### Example 3 — 12 June 2022: a lower extreme keeps falling

The preceding twenty-bar low is **28,019.56**, most recently **26 May**,
seventeen bars earlier. On 12 June, the low is **26,560.00** and close
**26,574.53**, still below the reference. The diagnostic next-day long setup
exists, but a same-day closing reclaim does not.

On **13 June**, the open is **26,574.53**, high **26,895.84**, low
**21,925.77**, and close **22,487.41**. Neither the open nor any price in
that recorded range reaches the old **28,019.56** reference on the entry side.
The following fifth close, **17 June: 20,468.81**, is approximately
**−22.97583%** from the event close. A new low did not force a next-day
reversal. This does not establish a crash duration or identify an institutional
cause; it establishes the specific missing return and later observed path.

## How to use it to HUNT a trade

Choose the source-specific variant and supported market before scanning.
Freeze its calendar, prior reference, age/tie policy and expiry. Require the
excursion before a reclaim, and distinguish a live intraday trigger from a
completed close-based proxy. If the requested precision is unsupported by the
data, WAIT and name the missing input instead of inventing entry/SL/TP prices.

Use a bounded paper risk budget only after an actual reachable entry and
invalidation can be supported. Include source latency, valid price increments,
realistic spread/fees and conservative slippage. Retain gap-open ambiguity,
missing contacts and failed reclaims in chronological evaluation. A descriptive
rule-coverage score is separate from a win probability; all current evidence
records leave probability null and real orders disabled.

Hoshi should normally provide the concise supported result and immediate reason
in Roman Urdu, without an unsolicited lesson. Explain the longer source/history
comparison only when asked. These original source-attributed chapters and
offline checks are not model training, loaded runtime knowledge or completed
V3 strategy integration.

## Sources

- [TradingMarkets Editors: Today's Trading Lesson, 9 September 2004](https://tradingmarkets.com/recent/todays_trading_lesson_from_tradingmarkets-649736): public publisher lesson checked 28 October 2026, same-day versus Plus One rule passages. Brief attribution only; full book and charts not reproduced.
- [TradingMarkets Street Smarts catalogue](https://store.tradingmarkets.com/products/street-smarts-immediate-download-selected-by-technical-analysis-of-stocks-and-commodities-magazine-as-one-of-the-classics-for-trading-books-written-in-the-20th-century): checked author names and distinct chapter listings; no purchase or promotional performance claim adopted.
- [Binance Spot kline API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary field/time schema checked; source-specific raw responses and digests already retained.
- [SEC Investor.gov stop-order bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15): primary trigger-versus-execution distinctions checked; stock-market mechanics are not automatic venue parity.

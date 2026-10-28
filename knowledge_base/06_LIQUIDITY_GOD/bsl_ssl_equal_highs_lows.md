# Buy-side and sell-side liquidity: reference levels are not an order registry

## What is it?

In SMC/ICT chart vocabulary, buy-side liquidity, or BSL, often refers to a
hypothesized concentration of buy-triggered orders above reference highs.
Sell-side liquidity, or SSL, similarly refers to possible sell-triggered orders
below reference lows. Equal highs and equal lows describe nearby price extrema
that traders may choose as shared reference areas. These labels are useful
only if their observational limits remain explicit: a price chart does not
contain a complete inventory of resting, hidden, conditional or canceled orders.

Actual trading mechanics distinguish several order types. The SEC's Investor.gov
bulletin explains, for stocks, that a stop becomes a market order when its
trigger is reached, while a stop-limit becomes a limit order and can remain
unexecuted. Trigger conventions can vary by brokerage; the stop price is not
a guaranteed execution price. Those checked mechanics explain why a reference
area could matter. They do not establish where a specific Binance participant
placed a stop or prove that another venue uses identical triggers.

Buy-side in this chart vocabulary does not mean visible offers waiting to sell,
and sell-side does not mean visible bids waiting to buy. A triggered buy stop
may consume available offers; an untriggered conditional order is not necessarily
displayed in the public limit book. A candle alone cannot distinguish such
buying from discretionary purchases or another source of aggressive demand.
Keep directional conditional-order hypotheses separate from observed depth,
executed volume, price extremes and institutional ownership.

Exactly equal printed extrema are also different from a near-equal cluster.
The offline convention here uses a stated relative tolerance, not visual
judgment. A cluster can be measured even when the hypothesis of actual stops
remains unknown. Hoshi must not label the measured cluster's existence as
observed liquidity quantity or convert it into a calibrated trading probability.

## Why does it form?

Repeated reference prices can arise because participants reuse visible levels,
because prices have finite increments, because the chosen sampling interval
compresses many trades, or simply by chance. Traders with different strategies
may place protective or entry orders near salient extremes. Others may cancel,
move or execute them elsewhere. A pair of similar highs therefore motivates a
testable hypothesis about a later excursion; it does not reveal a universal
pool of orders that must be collected.

Price can accelerate through an extreme if aggressive demand meets limited
available offers, and it can reverse if subsequent demand is insufficient or
new selling appears. Both outcomes are possible. The mere crossing does not
tell us which will follow, whether stops were present, or whether someone
intended to trigger them. A news-driven repricing can continue far beyond a
reference that looked strong on an earlier chart.

Repeated highs and lows also depend on scale. Two daily highs near one another
can conceal very different intraday paths. A lower-timeframe excursion may
already have exceeded one member of a cluster before its second member is
confirmed. A market can revisit the same reference many times. Calling every
visit fresh liquidity without recording previous excursions creates a false
history of untouched orders.

Tolerance choices affect apparent abundance. A wider threshold labels more
pairs as equal, while a narrow threshold may label none. Absolute price
tolerances also change meaning as an instrument's price changes. A relative
threshold makes the units explicit but is not automatically optimal. Selection
must be frozen before evaluating outcomes; tuning it on the same attractive
cases can overstate evidence even if the arithmetic is correct.

## Application zone

The original offline rule is **hoshi-latest-two-confirmed-cluster-25bp-1**.
For a selected event day, consider only earlier completed daily bars. Use
strict two-left/two-right pivots from the existing structure evidence: a high
must exceed the four neighboring highs, or a low must be below the four
neighboring lows. A pivot becomes known only after the second right-hand bar
has completed. The latest two confirmed highs or latest two confirmed lows
form the candidate pair. Ties do not qualify as strict pivots.

For pair prices P1 and P2, calculate separation in basis points as
**10,000 × |P1 − P2| / ((P1 + P2) / 2)**. At most **25 basis points**, or
0.25% of their average, qualifies as a near-equal pair under this version.
This threshold is an original teaching convention, not a creator standard,
exchange rule or parameter shown to maximize returns. The receipt preserves
the exact separation so that another hypothesis can be evaluated separately.

Store both prices rather than drawing a deceptively exact single line. The
outer high reference is the larger pair price; the outer low reference is
the smaller. Record whether any bar after the second pivot's confirmation
already exceeded that outer reference before the event. This flag describes
observed price history. Even a false flag does not prove stop orders remained
untouched, because cancellations, other venues and unobserved instructions
remain outside the dataset.

The event day's high above the outer high, or low below the outer low, is a
strict excursion. A high-side excursion that closes below the entire pair,
or a low-side excursion closing above the entire pair, is a same-day geometric
reclaim. The event decision becomes logically available only after that daily
bar has closed. It is not a signal at the moment the intraday excursion began,
and source delivery time is unknown. A live device would need an actual arrival
timestamp and freshness gate.

Observe the next five daily bars separately. Retain the first future excursion
and the first reclaim **after an excursion has actually occurred**. A close
below a high pair before any high-side excursion is not a completed raid and
reclaim. This ordering prevents a normal below-reference close from being
retroactively relabeled when a later bar finally crosses the highs.

The receipts use descriptive outcomes only. They do not choose a tradable bias,
entry, stop distance or leverage. Even an observed reclaim lacks the complete
history, structure, global-flow, supported execution and risk inputs required
for the later V3 strategy. All diagnostic decisions therefore remain **WAIT**,
with `win_probability=null`, unknown fills and null strategy PnL.

## Failure zones

**Continuation through the reference:** an excursion is not a reversal promise.
A low cluster can be exceeded and remain far above all subsequent prices.
Buying merely because supposed SSL was taken can mean buying into a continuing
decline. Conversely, fading every high-side excursion can oppose a genuine
upward repricing. The reclaim condition is separate evidence, not an automatic
consequence of the crossing.

**Future confirmation hidden in a past label:** a high at time T is not known
to be a strict pivot until later bars exist. A backtest that places orders at
T using that later label leaks information. Prefix tests verify that only the
prior-confirmed pair is selected, and appending the five outcome bars cannot
alter the frozen event feature. Source and derived-result corruption also
must fail rather than quietly changing an example.

**Equal-looking but materially different levels:** a chart's zoom can make a
large price difference look small. The pair's separation, tolerance and units
must be visible. A single high/low candle with both relevant extremes may have
unknown intrabar ordering. A larger daily range can also cross both sides of
a setup before closing; OHLC data alone cannot supply the exact order of fills.

**Invented execution or inventory:** neither a large wick nor a low traded
volume proves institutional intent, a stop quantity or a coordinated trap.
Visible displayed depth can be canceled and omits undisplayed interest.
A protective stop's trigger can execute at a different price; a stop-limit
can miss execution. A fixed hypothetical loss budget cannot guarantee a
maximum realized loss through gaps or market disruption.

**Repeated or selected observations:** the three examples reuse already
examined daily captures. They are not independent holdout data. Clusters can
persist over many days, so counting every day as a new independent target
overstates the sample. A later study needs a declared retirement/expiry policy,
bounded attempts, costs, overlapping-event handling and untouched chronological
evaluation before it can estimate an advantage.

## Three real historical examples with dates

All cases use **Binance Spot BTCUSDT**, daily bars opening 00:00 UTC and closing
23:59:59.999 UTC. Prices are USDT per BTC. The existing raw-response receipts
contain 611 actual bars across bounded 2020, 2021 and 2022 windows. The new
liquidity receipt references those exact source-file and window hashes; it
does not duplicate them as new independent data or claim actual stop records.

### Example 1 — 1 June 2020: high-side crossing, delayed reclaim

The latest two prior-confirmed highs are **14 May: 9,939.00**, confirmed after
16 May, and **18 May: 9,950.00**, confirmed after 20 May. Their separation
is approximately **11.0614 basis points**, within the stated 25-basis-point
tolerance. No subsequent prior daily bar exceeds the outer **9,950.00**
reference after the second confirmation.

On 1 June, price reaches **10,380.00** and closes **10,200.77**. The high-side
excursion is real on this feed, but the close remains above the pair: no
same-day reclaim exists. On 2 June, the low is **9,266.00** and close
**9,518.04**, now below the entire pair. That is a later reclaim with later
information availability, not a fact known at the first crossing. The fifth
following close, 6 June, is **9,666.30**, about **−5.2395%** from the event
close. That raw change is not a filled short or proof of which orders caused it.

### Example 2 — 5 April 2021: visible high pair, target not yet reached

The pair is **18 March: 60,129.97**, confirmed after 20 March, and **2 April:
60,200.00**, confirmed after 4 April. Its separation is approximately
**11.6397 basis points**. At the start of 5 April both are known; the later
pivot's confirmation must not be assigned to its 2 April candle time.

The event day reaches only **59,272.00** and closes **59,129.99**. No high-side
excursion occurs. A 6 April close below the pair therefore cannot be called
a post-excursion reclaim. The first later high beyond the frozen outer
reference arrives on **10 April**, at **61,500.00**, with close **59,769.13**
below the entire pair. That same later day supplies the excursion/reclaim
geometry. The fifth-day raw close change from 5 April is approximately
**+1.0809%**, without establishing an earlier entry, an intrabar fill or a win.

### Example 3 — 8 November 2022: low-side crossing without recovery

The latest confirmed low pair is **28 October: 20,000.09**, confirmed after
30 October, and **3 November: 20,031.24**, confirmed after 5 November. Its
separation is approximately **15.5628 basis points**. The outer low is
**20,000.09**; no prior post-confirmation bar crosses below it before this event.

On 8 November, the low is **17,166.83** and close **18,547.23**, both well
below the pair. The event does not reclaim the lows. On 9 November price
reaches **15,588.00**; none of the following five daily closes regains the
entire pair. The 13 November close is **16,329.85**, approximately **−11.9553%**
from the event close. Supposed SSL being taken did not force a bounce back
to the reference in this observation window. No crash duration, causal
institutional motive or universal historical analogy is inferred.

## How to use it to HUNT a trade

Map candidate reference areas using only data available at the decision cutoff.
Keep the actual pair, confirmation times, tolerance and prior-excursion history.
Then wait for the declared event and confirmation sequence. A reference that
has not been reached remains a potential target, not an executed setup. A
crossing without reclaim remains a crossing, not a mandatory reversal.

Before any paper trade, require the supported symbol, observed prices, source
arrival/freshness, complete directional and global context, realistic costs
and bounded loss sizing. Record the invalidation that would falsify the
hypothesis. If missing data or same-bar ordering prevents a defensible entry,
WAIT. Never invent a stop registry, a cross-market NAS100 level or a confidence
percentage to make the output look decisive.

Evaluate a frozen version chronologically with counterexamples, no-event days,
repeated references, late inputs and negative outcomes retained. Distinguish
rule coverage from calibrated probability. Hoshi can use that discipline
silently and keep the ordinary response short in Roman Urdu, while explaining
the underlying concepts when Jano asks. This chapter adds checked source
material and offline evidence; runtime retrieval, paper replay and final release
remain separate pending gates.

## Sources

- [SEC Investor.gov: Stop, Stop-Limit and Trailing Stop Orders](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15): primary stock-order mechanics checked 28 October 2026; triggers, execution uncertainty and brokerage differences, not Binance stop inventory.
- [Binance Spot kline API](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints): primary schema and source-time semantics checked; exact raw bars are preserved in the referenced daily evidence file.
- [Binance public-data source and license](https://github.com/binance/binance-public-data): primary attribution checked in the existing capture work; derived observations remain CC BY-NC-SA 4.0 noncommercial research material, without relicensing unrelated code.

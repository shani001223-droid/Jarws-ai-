# Dollar, gold, oil and equities: conditional links rather than fixed signals

Reviewed on 28 October 2026. This is a bounded source chapter with original
retrospective calculations and three dated cases. Public-domain Fed and EIA
observations are retained with attribution. Licensed benchmark-series
permissions and original daily publication/arrival histories remain separate
unresolved requirements. No price below is a current quote or executable
trading level.

## What is it?

Intermarket analysis compares different markets to identify compatible or
conflicting evidence about financing conditions, expected growth, inflation,
liquidity and risk appetite. It does not mean that one asset mechanically
commands another. A dollar index, a gold benchmark, a physical oil assessment
and an equity index measure different objects, at different times and with
different exposure weights.

ICE's DXY is a geometrically calculated six-currency benchmark with fixed
composition weights; the euro exposure is 57.6%. The checked primary ICE
pages describe component bid/offer midpoints as calculation inputs. The
Federal Reserve's nominal broad dollar index instead uses a broad trading-
partner framework with weights that can be revised. The retained series
`DTWEXBGS`, indexed to January 2006, is that Fed broad measure. It is never
renamed DXY. A currency basket's composition affects what its movement means.

Gold observations also require a benchmark and unit. An ounce price in US
dollars, a local-currency bullion price, an ETF share and a futures contract
are different instruments. Cushing WTI spot assessment in dollars per barrel
is distinct from front-month WTI futures, Brent or an oil-producer stock.
An equity price index differs from a dividend-reinvested total-return index
and from a tradable ETF after costs.

Finally, prices are not measured capital flows. A rising index alone does
not reveal how much money entered a country or asset class. Holdings, ETF
flows, balance-of-payments accounts, trading volume and price changes answer
different questions. Hoshi must name which evidence it actually has before
describing a “global money flow” signal.

## Why does it form?

Several channels can connect these markets. Dollar financing demand can rise
when participants need cash, collateral or hedges. A more expensive dollar
can change non-US purchasing costs for dollar-priced commodities. Yet
different supply, demand and financing shocks can offset that effect. The
currency conversion identity does not require every dollar commodity to
fall whenever a selected dollar basket rises.

Gold can respond to opportunity costs, perceived risk, collateral demand and
investment positioning. An asset held as a hedge can still be sold when
cash is urgently needed elsewhere. Thus a longer-horizon diversification
argument does not guarantee an immediate intraday hedge. The World Gold
Council's 19 March 2020 note specifically discussed gold selling alongside
other assets during stressed liquidation, presenting cash-raising and
positioning explanations as interpretations rather than observed identities
of every seller.

Oil illustrates why the initiating shock matters. Stronger expected demand
can support both oil and some equity earnings. A disruption to oil supply
can instead raise input costs for consumers and importers while benefiting
some producers. Index sector weights, hedges and policy expectations affect
the net equity response. EIA's 4 March 2022 report discusses invasion-related
risk alongside stronger demand and slower production growth; it does not
assign every observed price change to a single cause.

Equity valuation adds another layer. Expected cash flows and required returns
can change together. A lower discount-rate expectation may help valuations,
while the reason for that expectation—a worsening growth outlook, for
example—may reduce expected earnings. Merely observing a yield decline does
not determine the net result. Historical resemblance should motivate competing
hypotheses, not an automatic NAS100 short or a fabricated confidence percentage.

## Application zone

### Define instruments, clocks and usable data

The reproducible receipt here retains only Fed broad-dollar and EIA Cushing
WTI spot observations obtained through FRED for three fixed windows.
Their series pages tag them public domain with citation requested. The
CSV response bodies, request bounds, capture timestamps and SHA-256 digests
are preserved in `macro_observations_20261028.json`.

The source dates are daily observation labels. A shared date does not prove
simultaneous fixing, publication or availability to a phone. H.10 is a
scheduled release, and the Fed explicitly warns that revised trade weights
can change past index values. These captures therefore represent a later
retrieved history, not verified original vintages available during the
events. Their original publication and client-arrival timestamps remain null.

DXY, gold and equity benchmark price arrays are explicitly null in these
new diagnostics. DXY methodology was checked without obtaining a permitted
price-series source. No raw gold benchmark was acquired. FRED's Nasdaq
Composite metadata flags copyrighted, pre-approval-required data, so new raw
Nasdaq CSVs are not redistributed in this receipt. Earlier limited curriculum
observations still require a rights review before any data/runtime bundling;
their presence does not establish a blanket license. This is an integration
gate, not a reason to replace the missing series with an attractive proxy.

### Compare the same intervals without filling missing observations

For positive starting values, the endpoint arithmetic change is
`100*(last/first-1)`. Missing exact endpoints remain unavailable instead of
silently moving to a more convenient nearby day. A zero or negative base
requires another declared convention; it cannot be treated as an ordinary
positive-price percentage baseline. Percentage changes in indexes or prices
are distinct from percentage-point changes in yields.

The optional two-series diagnostic intersects genuinely observed dates and
calculates both changes over each identical consecutive common-date interval.
It does not forward-fill a holiday, manufacture weekend observations or call
a Friday-to-Monday change a one-calendar-day move. Pearson correlation is
then calculated from those paired arithmetic changes, not from trending
price levels. Undefined variance or insufficient pairs produce null.

Even correctly aligned daily labels do not solve intraday timing differences.
The sample counts are only nine, nine and five paired intervals. They are
descriptive calculations in selected, already-examined windows, not independent
strategy trials or stable population estimates. No significance claim,
causal coefficient or conversion to win probability is supplied.

### Use context as a conditional gate

An eventual point-in-time research record should contain instrument identity,
source version, observation time, actual release/arrival where known, change
horizon, missing inputs and competing interpretations. Separate dollar
funding stress from commodity supply stress, and separate a monthly report
from the next minute's trigger. A proposed local setup still needs supported
fresh prices, genuine liquidity/structure evidence, costs and bounded paper
risk. Context cannot supply missing entry, stop or target levels.

## Failure zones

**Universal inverse rules:** a dollar basket and oil can both rise. A gold
hedge can decline during a cash scramble. Equities in different sectors can
react differently to an energy shock. A memorized sign rule discards the
conditional mechanism it was supposed to describe. No trading pattern works
100%.

**Mismatched windows:** a positive February gold return is not a return from
23 February to 8 March. A full-August gain is not the reaction over 1–8
August. The reported gold figures below are kept in their own explicitly
different observation windows and are excluded from the paired calculation.
Otherwise a comparison can manufacture correlation from incompatible dates.

**Causal storytelling:** a report may propose liquidation, safe-haven demand
or expected rate cuts as explanations. Those are not a decomposition measured
by Hoshi's two daily CSVs. Other information and position adjustments occur
over the same interval. A residual in an analyst's model is not proof of
one institution's hidden strategy.

**Data and revision leakage:** final revised values may differ from the
original release. A feature stamped with an observation date can still be
unavailable until a later publication. Using it before that publication is
look-ahead. A future runtime needs a versioned availability contract and must
wait when that contract cannot be met.

**Trading-product substitution:** a spot oil percentage is not a futures
roll-adjusted return; a price index excludes investor-specific execution,
funding, fees and dividends. A bearish macro view is not authorization or
capacity to short a spot asset. The current diagnostics issue `WAIT`, with
orders disabled and `win_probability=null`.

## Three real historical examples with dates

All numerical dollar/oil paths below come from exact source windows captured
on 28 October 2026. They are retrospective daily observations, not live
chart examples or proof of how a strategy would have filled. Gold and equity
context is briefly attributed to dated primary research, not independently
reconstructed from a licensed benchmark feed.

### Example 1 — 9–20 March 2020: opposite endpoints with near-zero interval correlation

The captured Fed broad-dollar index rises from 117.1871 on 9 March to
124.9362 on 20 March, approximately positive 6.6126%. Cushing WTI spot moves
from $31.05 to $19.48 per barrel, approximately negative 37.2625%. Those
endpoint directions might tempt an inverse-dollar rule, but the nine paired
common-date changes have a Pearson correlation around negative 0.0526,
close to zero within this very small selected sample.

For example, both series rise from 9 to 10 March: broad dollar by about
0.6106% and WTI spot by 11.0145%. Large reversals elsewhere in the window
change the relation between the endpoint narrative and interval-to-interval
co-movement. The 13–16 March observation spans three calendar days. None
of those labels supplies a synchronized intraday pair of executable quotes.

The World Gold Council note published on 19 March discusses gold falling
alongside stocks amid broad liquidation and possible cash raising. That
contemporaneous interpretation supplies a documented counterexample to
assuming an immediate safe-haven gain. It is not a gold-return array in
Hoshi's receipt, and it cannot be extended into a claim about every market's
recovery date or every investor's motive.

### Example 2 — 23 February–8 March 2022: dollar and oil rise together

Across this fixed window, the broad-dollar index rises from 114.6668 to
117.6176, approximately positive 2.5734%. Cushing WTI spot rises from
$92.14 to $123.64 per barrel, approximately positive 34.1871%. Their nine
paired common-date changes have a correlation around positive 0.2088.
Both the endpoint signs and this limited interval calculation contradict an
unconditional rule that a stronger dollar must accompany falling oil.

EIA's 4 March article discusses front-month Brent and WTI futures in the
invasion period. That supports the historical supply-risk context, but its
futures prices are not substituted for the Cushing spot observations above.
The World Gold Council's 7 March report says its LBMA Gold Price PM measure
gained about 6% over the whole of February, discussing safe-haven demand
despite higher nominal yields and a marginally stronger dollar.

That monthly gold observation includes many days before 23 February and
ends before 8 March. It cannot be joined to this window as though all four
markets had one simultaneous return. The invasion is a documented event;
the causal contribution of that event to each price is not isolated by
these comparisons. A later trading input needs contemporaneous sources and
counterexamples rather than a rule that war always produces the same signal.

### Example 3 — 1–8 August 2024: a narrow window differs from the monthly gold result

The broad-dollar index declines from 123.8693 to 123.4466, approximately
negative 0.3412%, while Cushing WTI spot declines from $77.74 to $77.64,
approximately negative 0.1286%. Both endpoint changes are negative. Across
only five paired intervals, the correlation is around positive 0.5020; that
small count cannot justify describing a durable regime.

Within the same window, the 2–5 August broad-dollar change is positive
0.0896% while WTI spot falls about 0.7068%. Thus even a positive sample
correlation leaves individual opposing moves. The three-calendar-day gap
between those observations is retained explicitly. Intraday response order
and original release availability are still missing.

The World Gold Council's commentary published 5 September reports a
3.6% gold gain over the whole of August, attributing support to a weaker
dollar and lower yields in its own model. That is a later monthly result,
not the 1–8 August gold return or information available during the early
August sell-off. The public report also notes the equity market's early
disruption and subsequent strength. No raw equity series or numerical
cross-asset equity correlation is fabricated here.

## How to use it to HUNT a trade

Start by stating the hypothesis and its alternatives. Is the relevant shock
primarily a funding scramble, growth repricing, commodity supply concern or
policy-expectations change? Which inputs support that interpretation, and
which disagree? Keep price evidence distinct from reported positions or
measured flows. A missing licensed series remains unsupported, not an
invented DXY, gold or NAS100 quote.

Freeze the observation and decision cutoffs before replay. Require the actual
version and publication time of slow macro inputs, and use supported fresh
venue prices for local structure and liquidity. Review benchmark-data rights
before redistributing or bundling a feed. A historical case can motivate a
versioned paper hypothesis; it cannot manufacture current trade levels.

Evaluate later on untouched chronological periods, with realistic costs,
revisions, unavailable inputs, missed opportunities and drawdown/ambiguity
checks. Keep zero-trade results. Hoshi's requested global-flow weight must
mean explicitly defined evidence coverage, not a probability inferred from
these three examples. This source chapter is neither model training nor
loaded runtime knowledge; the integrated V3 release remains a separate gate.

## Sources

Primary materials actually checked on 28 October 2026; limited report
observations are paraphrased in original analysis:

1. ICE, [USDX composition](https://www.ice.com/forex/usdx)
   and [currency-index data description](https://developer.ice.com/fixed-income-data-services/catalog/ice-data-indices-currency-indices).
   Methodology reviewed; no permitted historical DXY price feed obtained.
2. Federal Reserve, [H.10 nominal/real dollar-index summary](https://www.federalreserve.gov/releases/H10/summary/default.htm)
   and [2019 methodology revision](https://www.federalreserve.gov/econres/notes/feds-notes/revisions-to-the-federal-reserve-dollar-indexes-20190115.html).
   Current historical revisions are distinct from original vintages.
3. [DTWEXBGS series/attribution](https://fred.stlouisfed.org/series/DTWEXBGS)
   and [EIA Cushing WTI series/attribution](https://fred.stlouisfed.org/series/DCOILWTICO),
   both tagged public domain, citation requested. Exact raw requests are in
   the [macro receipt](macro_observations_20261028.json).
4. EIA, [4 March 2022 oil-market report](https://www.eia.gov/todayinenergy/detail.php?id=51498).
   Its front-month futures context is separate from retained spot prices.
5. World Gold Council, [19 March 2020 liquidation update](https://www.gold.org/goldhub/research/gold-prices-swing-as-markets-sell-off),
   [February 2022 commentary, published 7 March](https://www.gold.org/goldhub/research/gold-market-commentary-february-2022),
   and [August 2024 commentary, published 5 September](https://www.gold.org/goldhub/research/gold-market-commentary-august-2024).
   Brief published context, not a redistributed licensed gold history.
6. [Nasdaq Composite metadata and rights tag](https://fred.stlouisfed.org/series/NASDAQCOM).
   Pre-approval-required series; new raw observations excluded pending rights review.
7. [Original daily alignment/calculation code](../../scripts/v3_macro_evidence.py).
   Sample correlations are descriptive, uncalibrated and not causal effects.

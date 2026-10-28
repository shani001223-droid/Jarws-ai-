# Bitcoin correlations, changing regimes and incompatible clocks

Source review: **28 October 2026, Asia/Karachi**. This is noncommercial
historical educational research, not a current quote, trained predictor or
runtime price service. The three bounded comparisons use actual Binance Spot
BTCUSDT daily candles and public Federal Reserve/EIA observations already
captured for this curriculum. They do not reproduce a licensed equity-index
history or measure a permanent economic relationship.

## What is it?

Correlation describes a specified association between paired observations.
For trading research, the input should usually be defined price changes,
not two trending price levels. The horizon, return definition, observation
clock, quote currency and missing-date rule are part of the statistic. Saying
"Bitcoin follows stocks" without those choices does not identify a testable
rule. A positive sample correlation does not imply identical daily signs,
equal volatility, a particular lead-lag order or a profitable hedge.

A regime is a proposed state with explicitly defined boundaries or a
probabilistic state estimate. Volatility, trend, liquidity and correlation
regimes are distinct. A quiet rising market need not have the same
cross-asset dependence as a high-volatility rebound. Calling a historical
interval "risk off" after observing its losses is a retrospective label;
it does not establish when a live system could first have known that state.
The three selected windows below are examples, not fitted regime boundaries.

An IMF blog published **11 January 2022** reports Bitcoin/S&P 500 return
correlation of **0.01 for 2017–19** and **0.36 for 2020–21**. Those are the
source's historical estimates for its sample and method, not today's values,
HOSHI calculations or trading probabilities. They support investigating a
changing association rather than assuming perpetual independence. They do
not establish that a particular future Bitcoin trade will win 36% of the
time. [1]

An IMF working paper published **4 August 2023** studies a common crypto
factor and monetary-policy transmission through risk taking. Its empirical
association with institutional participation and model-based explanation
are research findings, not direct observations of every investor's motives.
The paper's aggregate-factor results are not equivalent to a Bitcoin-only
entry rule. Its publication date also cannot be used as if the completed
paper had been available during the earlier events it studies. [2]

## Why does it form?

Co-movement can arise without one asset mechanically causing another.
Participants may respond to common information, reduce exposure together,
rebalance collateral or change their willingness to bear risk. Different
investor populations and instruments may strengthen or weaken those links.
Those are plausible mechanisms to test, not quantities directly measured
by the retained daily candles. HOSHI must not translate a price coincidence
into a claim that named institutions moved money between assets.

Observed correlation can also change for statistical reasons. An unusually
large observation can dominate a tiny window. Altering the window length,
including weekends, changing close times or using log rather than arithmetic
changes can change the estimate. A pair's volatility can change substantially
even when correlation stays similar. Hedge sizing depends on covariance,
exposure units and uncertainty; correlation alone supplies no position size.

The original diagnostic here uses arithmetic percentage changes. For every
pair of adjacent dates with valid observations in both assets, calculate
100 times the later value divided by the earlier value minus one. Pearson
correlation then compares the two sequences after subtracting their sample
means. It is undefined if either sequence has no variation. The code requires
at least three complete intervals before reporting a coefficient; this is a
computational minimum, not a claim of statistical sufficiency.

Critically, dates are intersected before changes are computed. Bitcoin trades
on dates when a conventional series has no observation. If Friday and Monday
are adjacent common dates, both assets' changes cover that same three-calendar-
day label interval. The algorithm never compares Bitcoin's Sunday-to-Monday
change with another asset's Friday-to-Monday change while calling both
one-day returns. It also never forward-fills weekend macro observations into
artificial zero returns. These controls fix one alignment problem; they do
not make the underlying prices simultaneous.

## Application zone

Use a correlation estimate to challenge concentration and a proposed
explanation. If two paper positions depend on the same risk factor, treating
them as independent because their instrument names differ can understate
loss exposure. Conversely, an observed negative correlation from a handful
of dates cannot establish a reliable hedge. A future risk system needs
instrument-specific exposure conversion, loss scenarios and correlation
uncertainty rather than a single historical coefficient.

The instrument boundaries in this chapter are deliberately narrow:
**BTCUSDT on Binance Spot**, with native daily bars starting **00:00 UTC** and
ending **23:59:59.999 UTC**, is not BTCUSD cash on every exchange. USDT is the
quote asset; no conversion to USD cash or assumption of a permanent exact
peg is applied. The provider documents the twelve kline fields. Its public
archive documentation also flags microsecond timestamps for spot archives
from 2025 onward; these **2020/2022/2024 captures use verified millisecond
boundaries**, and the checker rejects a silent unit change. [3]

The macro comparisons use **DTWEXBGS**, the Federal Reserve's nominal broad
dollar index, and **DCOILWTICO**, EIA's Cushing WTI spot price through FRED.
The broad index is not ICE DXY, and spot oil is not a rolled WTI futures
strategy. These are currently retrieved historical series, potentially
revised, with missing original release and delivery clocks. Their daily
labels do not document the same instant as a UTC Bitcoin candle close.
Therefore, every comparison is marked nonsynchronous. [4][5]

A usable future regime feature would need a frozen past-only specification:
lookback, minimum paired observations, estimator, thresholds, refresh time,
staleness limit and behavior when estimates disagree. Evaluate that frozen
rule on later chronological data without tuning thresholds to those same
outcomes. Retain negative results and periods with no eligible decisions.
The present chapter provides diagnostic arithmetic and counterexamples;
it does not deliver that strategy, a structural-break test or independent
out-of-sample validation.

## Failure zones

One failure is substituting a correlation narrative for a complete decision.
Even an accurate contemporaneous coefficient does not supply market
structure, a liquidity reference, an observed entry or execution costs.
Direction, magnitude and arrival time are separate. A history-pattern match
could earn evidence coverage in a later engine while remaining incapable of
producing a calibrated win probability.

Another failure is claiming causation from date-aligned daily changes.
A UTC crypto close may include information arriving after another series'
observation time. A backtest that makes both available at the start of that
date leaks information. A one-day shift is not automatically the correct
repair: the actual sampling and publication clocks must be established for
the intended decision horizon. Revisions create another barrier between
current downloaded history and the information originally available.

Endpoint direction is not correlation. Two assets can both finish above
their initial values while their intervening changes have negative Pearson
correlation. They can also share one severe loss date without having a stable
relationship over longer samples. The actual 2022 comparison below retains
the former counterexample. It prevents the system from equating a shared
upward endpoint with positive return dependence.

Selection and licensing also matter. These windows were chosen for teaching,
not sampled as an independent test set. Five or nine paired intervals cannot
justify a persistent safe-haven label or a change-point declaration. No raw
S&P/Nasdaq/DXY/gold benchmark array is introduced to fill the gap. Public page
access is not blanket redistribution permission. Binance-derived captures
and calculations remain under their stated **CC BY-NC-SA 4.0** noncommercial
research scope; production, commercial signals and model training are not
authorized by this chapter's research receipt. [6]

## Three real historical examples with dates

### Example 1 — 9–20 March 2020: a severe BTC loss and limited paired evidence

For UTC bar labels **9 March through 20 March 2020**, Binance Spot BTCUSDT
closes move from **7,929.87000000 to 6,208.36000000 USDT per BTC**. The
calculated endpoint close change is **minus 21.7092%**. Over the same date
labels, the broad Fed dollar index rises approximately **6.6126%**, while
Cushing WTI spot falls approximately **37.2625%**. These are separate
instrument observations, not simultaneous execution prices. [3][4][5]

Intersecting valid macro dates produces **nine paired change intervals**.
The resulting BTC/broad-dollar arithmetic-change correlation is approximately
**minus 0.5909**; BTC/WTI spot is approximately **plus 0.2390**. Neither
coefficient is a probability. The BTC close change from **11 to 12 March**
is approximately **minus 39.5048%**, a large single observation within this
small selected sample. It is retained rather than removed to make the
relationship smoother. No estimate excluding it is silently substituted.

The **13–16 March** interval spans three calendar days. Bitcoin weekend
movement contributes to the common-endpoint change, while no invented
weekend dollar or oil values enter the sample. Original macro publication
and ingestion times remain unavailable, so this comparison cannot support
an intraday lead-lag or crisis-cause conclusion. The 2022 IMF publication
provides later research context; it was not a contemporaneously available
instruction for a March 2020 trade. No filled trade or account return is
claimed, and the diagnostic decision remains **WAIT**.

### Example 2 — 23 February–8 March 2022: both endpoints rise despite negative paired correlation

BTCUSDT UTC closes from **23 February to 8 March 2022** rise from
**37,250.01000000 to 38,730.63000000**, approximately **plus 3.9748%**.
Across those date labels the broad dollar rises approximately **2.5734%**
and WTI spot approximately **34.1871%**. Those positive endpoint changes do
not establish that all three moved together throughout the window. No claim
is made that a headline mechanically caused these complete paths. [3][4][5]

The same-endpoint algorithm yields **nine paired intervals**. BTC/broad-dollar
correlation is approximately **minus 0.2451**, despite both endpoints being
higher. BTC/WTI spot correlation is approximately **minus 0.0325**. For a
concrete local contrast, **3–4 March** BTC closes fall approximately **7.7857%**
while WTI spot rises approximately **7.5030%**. Elsewhere in the interval the
signs and magnitudes differ again. A statement based only on final levels
would discard precisely the path information needed to compute correlation.

The data therefore contradict a simple "both rose, so the correlation was
positive" inference. They do not prove a profitable inverse trading rule:
fees, latency, bid/ask spreads, exposure conversion and executable entries
were not measured. Nor does this selected window test a permanent war hedge,
a stable oil relationship or causality. Historical resemblance supplies a
research question. The evidence remains nonsynchronous, retrospectively
retrieved and insufficient for a calibrated probability or a live order.

### Example 3 — 1–8 August 2024: a large weekend-spanning move in a five-interval sample

BTCUSDT UTC closes from **1 August to 8 August 2024** move from
**65,354.02000000 to 61,685.99000000**, approximately **minus 5.6126%**.
The broad dollar endpoint change is approximately **minus 0.3412%** and
WTI spot approximately **minus 0.1286%**. These are not total returns after
costs, and a UTC close is not a verified fill available to a US-session
strategy at its earlier decision time. [3][4][5]

Only **five common-date intervals** remain after pairing. BTC/broad-dollar
correlation is approximately **minus 0.0514** and BTC/WTI spot approximately
**plus 0.4676**. The **2–5 August** common interval spans three calendar
days; BTC closes decline approximately **12.1622%** over those endpoints,
while the broad dollar rises approximately **0.0896%**. Treating the BTC
component as only Monday's close-to-close move would change the question.
The **7–8 August** BTC close change is approximately **plus 11.8834%**,
showing that the window also contains a substantial reversal.

A tiny coefficient near zero does not establish economic independence, and
a moderate coefficient from five intervals does not certify a new stable
regime. There is no independent structural-break test or contemporaneous
state transition estimate here. This example preserves the short sample,
weekend span and rebound instead of compressing the event into a single
safe-haven story. It supplies no S&P/Nasdaq correlation because the required
permitted, aligned benchmark history was not delivered in this receipt.

## How to use it to HUNT a trade

Start with the proposed economic exposure rather than a familiar slogan.
Resolve the pair, venue, spot versus derivative, quote asset and decision
clock. Then require evidence whose original publication and arrival precede
that clock. If a broad-dollar observation is stale, an equity history is
unsupported or the quote is only an old daily close, return **WAIT** and
record the missing input. A completed knowledge chapter does not refresh a
price feed.

For a later paper candidate, compare a frozen recent estimate with a
predeclared longer baseline, report sample sizes and preserve disagreement.
Define a deterioration or suspension rule before seeing the evaluation
outcome. Treat multiple correlated proposed positions as potentially
concentrated exposure; do not assume adding assets creates diversification.
Do not optimize a hedge ratio on the same selected crisis window used to
advertise its success.

Structure, liquidity and historical analogy must each retain genuine dated
inputs. The requested weighted evidence score will describe rule coverage,
not the chance that BTC or NAS100 will rise. Until there is independent
chronological calibration, **win_probability=null**. Without current observed
execution prices, realistic costs and bounded paper risk, no entry, stop or
target is produced. Roman Urdu default: **"Correlation window ke saath
badalti hai; synchronized aur fresh inputs missing hain, is liye WAIT."**

Reproduce these bounded facts with `scripts/v3_macro_evidence.py` and the
adjacent `macro_observations_20261028.json`. The receipt retains three exact
BTC API responses and hashes, references the already retained public macro
captures, computes identical common-date spans and rejects timestamp-unit,
venue, quote and OHLC corruption. Prefix tests ensure later BTC closes cannot
change earlier paired intervals. All three diagnostics disable orders and
remain historical research; they are not a causal replay of a deployed
strategy, model training or a loaded runtime knowledge bundle.

## Sources

Primary pages and actual API responses checked **28 October 2026**. Binance
Vision is acknowledged for the selected BTC observations. BTC-derived data
and calculations in this chapter/receipt are shared as noncommercial
educational research under **CC BY-NC-SA 4.0**, without endorsement; this does
not relicense unrelated repository code or government series. Benchmark
rights, original-vintage timing and production data support remain separate
release gates.

1. IMF, [Crypto Prices Move More in Sync With Stocks, Posing New Risks](https://www.imf.org/en/Blogs/Articles/2022/01/11/crypto-prices-move-more-in-sync-with-stocks-posing-new-risks), **11 January 2022**: attributed historical correlation estimates, not HOSHI's measured live relationship.
2. Che, Copestake, Furceri and Terracciano, IMF Working Paper, [The Crypto Cycle and US Monetary Policy](https://www.imf.org/en/publications/wp/issues/2023/08/04/the-crypto-cycle-and-us-monetary-policy-534834), **4 August 2023**: research context, not creator or runtime strategy parity.
3. Binance, [Public Data README](https://github.com/binance/binance-public-data/blob/master/README.md), kline fields and timestamp conventions; [public klines endpoint](https://data-api.binance.vision/api/v3/klines). Exact bounded BTCUSDT requests and raw responses are stored in `btc_cases` in the adjacent JSON receipt.
4. Federal Reserve/FRED, [DTWEXBGS](https://fred.stlouisfed.org/series/DTWEXBGS): nominal broad dollar, not ICE DXY. Exact requested windows, raw CSV bodies and hashes are retained in the receipt's `money_flow_cases`.
5. EIA/FRED, [DCOILWTICO](https://fred.stlouisfed.org/series/DCOILWTICO): Cushing WTI spot, not futures; same retained daily-window receipts.
6. Binance, [Vision Dataset Terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md), version 1.0 updated **26 August 2026**: noncommercial attribution/share-alike scope and production restrictions; [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

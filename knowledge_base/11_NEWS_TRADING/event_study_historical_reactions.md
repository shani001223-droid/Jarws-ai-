# Historical event studies: estimands, clocks and defensible comparisons

Reviewed **28 October 2026, Asia/Karachi**. This chapter adds original
reproducible daily-yield path diagnostics to the **six already retained news
cases**. Reuse is explicit: these are not six new independent events. The
three detailed examples below are genuine dated observations, not invented
announcement quotes, abnormal returns or filled trades. A descriptive path
is not a causal estimate.

## What is it?

An event study defines an event, an outcome, an observation window and a
comparison intended to answer a particular question. "How did the observed
yield change over these dates?" differs from "What change was caused by the
announcement?" and from "Could a strategy have earned that change after
learning the news?" Each question needs additional assumptions and data.
A study should state its estimand before presenting the result.

A raw price return compares compatible observed prices. A yield difference
compares interest-rate levels and is usually expressed in basis points.
A normal-return benchmark is a specified counterfactual model; an abnormal
return is the observed return minus that benchmark. A cumulative abnormal
return aggregates the defined abnormal returns over a window. None of these
becomes a causal effect merely because the calculation is labelled an event
study. No normal-return model or abnormal-return estimate is fitted here.

The primary Bernanke–Kuttner **March 2004** manuscript illustrates why
anticipated and unanticipated policy components must be distinguished,
using federal-funds futures to measure surprises in its own research.
The Fed archive page is dated **1 April 2004**. This chapter does not import
its historical coefficient as a forecast for a present Hoshi trade, and
contains no matching futures-expectation dataset or replication. [1]

The measured object here is deliberately narrower: **two- and ten-year
Treasury constant-maturity reference yields, DGS2/DGS10**, from already
captured H.15/FRED daily history. Daily labels, source release clocks and
pipeline arrival are separate. The diagnostic computes differences between
observations; it cannot create a synchronized intraday price or a return
on an actual bond portfolio. [2][3]

## Why does it form?

A useful comparison requires more than two numbers near a headline. The
pre-event observation may already contain anticipation. The event-date
observation may reflect many hours of other information. A later observation
may include additional policy statements or unrelated releases. Expanding
the window captures more adjustment while increasing the opportunity for
confounding. Narrowing it can miss the response or require finer data than
are available.

Event selection also matters. Choosing only large moves after a known
headline selects on the outcome. Choosing only widely discussed crises
may not represent ordinary announcements. If one seeks a history-matching
feature, define the eligible event population and matching fields before
seeing the future result. Include absent, adverse and untradable cases.
An interesting example is not a calibrated event probability.

An original arithmetic decomposition helps expose horizon sensitivity.
Let the requested starting yield be A, the observed yield with the event's
date label be E, and the ending yield be B, all in percent per annum.
The two changes in basis points are **100*(E−A)** and **100*(B−E)**. When
all three observations exist, their sum is **100*(B−A)**. This identity does
not identify the exact timing or economic cause of either component.
The E observation is not assumed to be the first post-announcement quote.

A missing E cannot be replaced by the nearest date without changing that
question. If E is absent, the decomposition stays unavailable even if A and
B exist. The original script preserves missingness and reports calendar
spans between available observations. A Friday-to-Monday span is three
calendar days; no weekend rate is manufactured to make it look like one.

Range and endpoint are different statistics too. The difference between the
highest and lowest observed daily yields can exceed the net endpoint change
when the path reverses. That daily observation range is not the intraday
high-low range, an executable stop distance or account drawdown. A simulator
would need its own position and execution state to calculate those outcomes.

## Application zone

First freeze the event identity and time convention. Distinguish scheduled
release time, first public appearance, document revision and local ingestion.
For international or political events, a date-only source remains date-only.
A later certified compilation or legal publication may verify history while
being unsuitable as an earlier decision input. Source authority and temporal
availability are independent requirements.

Next choose the instrument and units. Do not pair a cash-index close with a
CFD quote and call them the same asset. Do not call a yield change a bond-price
return or compare two dates with different contract definitions. A return
calculation needs compatible price conventions, adjustments and currencies.
The H.15 observations here avoid pretending to deliver a licensed equity,
gold or futures price feed.

Define any comparison model using information that precedes the event.
For example, an explicitly hypothetical benchmark might estimate an asset's
normal relation to a market return on a separate pre-event sample. Fitting
that relation after inspecting the event uses the result to construct its
counterfactual. Even a pre-event model can be wrong if its relation changes;
model residuals then mix event information and benchmark error. This chapter
implements no such fitted benchmark and reports abnormal return as null.

An inference layer also needs a defensible sampling design. Events can
cluster in time and share market shocks. Multiple assets around one event
are not automatically independent events. Overlapping windows and repeated
research choices affect uncertainty. A resampling scheme must preserve the
relevant dependence rather than shuffle away the feature under study.
Six selected educational cases are insufficient to claim universal causal
identification or a calibrated trading accuracy.

Finally, keep an execution study separate. A market response can occur before
the data were received or before the pattern confirmed. Net trading outcomes
require permitted actual prices, realistic costs, cash/risk limits, fill
assumptions, ambiguity handling and a marked-equity path. No raw daily
event difference can supply those missing fields by itself.

## Failure zones

The most serious error is interpreting a correctly computed descriptive
change as an identified causal response. Temporal association is evidence
of co-occurrence, not proof that the headline caused the entire move.
A daily observation can include anticipatory changes, multiple announcements
and ordinary market noise. The source receipt retains those limits instead
of making the causal field equal to the arithmetic delta.

A second error is treating the event-date observation as if it were sampled
exactly at release. The US jobs and CPI documents provide stated clocks;
the H.15 historical series provides daily rate labels. The latter cannot be
upgraded into first-tick execution data by adding the release time to the
row. Original sampling/publication/arrival histories remain unverified.

A third error is selecting the window after the outcome. A long window can
hide a sharp adverse interval; a short window can miss a reversal. Preserve
the declared start, event label and end even when a different choice would
support the desired story. Keep range and net movement separate, and avoid
annualizing a tiny selected sample into an impressive performance number.

Repeated data reuse creates another trap. These six cases were already
inspected in earlier chapters. Adding a new statistic to them does not make
a new independent evaluation sample. The original script's prefix tests
can verify arithmetic dependence on earlier observations; they do not prove
that a trading strategy transfers to later markets. Win probability,
strategy PnL and causal effects remain null.

## Three real historical examples with dates

### Example 1 — 5 January 2024 employment label: a positive first component and negative later component

The archived employment release is stated for **5 January 2024, 08:30 New
York/13:30 UTC**, for **December 2023**. In the fixed **4–8 January** rate
window, DGS2 is **4.38%, 4.40%, 4.36%** on **4, 5 and 8 January**. The
starting-to-event-date component is **plus two basis points** and the
event-date-to-end component **minus four**, giving the original **minus two**
endpoint change. The observed daily range is **four basis points**. [2][4]

DGS10 is **3.99%, 4.05%, 4.01%**. Its components are **plus six** and
**minus four basis points**, giving **plus two** overall. The observed daily
range is **six basis points**. The two maturities thus have different net
outcomes while sharing a negative later component. Those are reproducible
observations, not estimated surprise responses. [3]

Original analysis: choosing only one endpoint could support a misleadingly
simple direction label. The Friday-to-Monday component spans three calendar
days and includes whatever information arrived over that interval. The
actual first post-release Treasury bid/ask, original source delivery,
consensus and fills are absent. No abnormal return, causal coefficient or
executable NAS100/BTC plan is inferred. The study remains WAIT.

### Example 2 — 13 October 2022 CPI label: maturity and horizon change the magnitude

The archived CPI release is stated for **13 October 2022, 08:30 New York/
12:30 UTC**, for **September 2022**. In the **12–14 October** window, DGS2
moves **4.28% → 4.47% → 4.48%**. The components are **plus 19** and **plus
one basis point**, with an endpoint change and daily observation range of
**20 basis points**. These quantities refer to rate levels, not a twenty-
percent return. [2][5]

DGS10 moves **3.91% → 3.97% → 4.00%**. Its components are **plus six** and
**plus three basis points**, with an endpoint change and daily observation
range of **nine basis points**. The different maturity profiles do not
identify which part of the move came from inflation expectations, policy
expectations or other risk components. [3]

Original analysis: a descriptive study can retain a larger move around the
selected date while declining to attribute it all to the release. Without
contemporaneous consensus, surprise is unknown; without synchronized prices,
the first-minute path is unknown. A hypothetical normal-return benchmark
would add assumptions, not restore those missing observations. No bond
portfolio duration or return, equity-index reversal, order fill or calibrated
probability is delivered by this comparison.

### Example 3 — 2 April 2025 policy date: range exceeds the net change and the selected document arrives later

For the **2 April 2025** signing date of EO 14257 and the fixed **1–4 April**
window, DGS2 is **3.87%, 3.91%, 3.71%, 3.68%**. The starting-to-event-date
component is **plus four basis points** and the event-date-to-end component
**minus 23**, producing **minus 19** overall. The daily observation range
is **23 basis points**, larger than the absolute endpoint change. [2][6]

DGS10 is **4.17%, 4.20%, 4.06%, 4.01%**. Its corresponding components are
**plus three** and **minus 19 basis points**, net **minus 16**, with a daily
observation range of **19 basis points**. No claim is made about where a
particular announcement falls within the 2 April observation interval. [3]

The selected official Federal Register publication is **7 April**, after
the observation window. The document establishes historical policy identity
but cannot be retroactively used as a 3 April input. Earlier announcements
may have existed; their actual captures and first-arrival clocks were not
obtained here. Original analysis: both path reversal and source availability
must survive the study design. Treating the later publication as an earlier
feature would manufacture information, even if every daily yield number
were correct. No current tariff advice, causal return or trading action
follows from this historical comparison.

## How to use it to HUNT a trade

An event study should test a predeclared question, not decorate a chosen
trade with a past story. Freeze event population, matching features,
instrument, source clocks, observation windows and comparisons. Preserve
negative, missing and ambiguous results. A later history feature must use
versioned genuine dated inputs and retain counterexamples; it must not
backfill information from subsequent reports.

Before a bounded paper candidate, check whether market data exist at the
required execution resolution and whether the relevant information arrived
before the decision. Missing or stale data, unsupported markets, unknown
costs or absent risk inputs produce WAIT. Do not invent entry/SL/TP levels
from a daily yield range. A reasonable-looking estimated response is not
a guarantee of available liquidity or an acceptable account drawdown.

The requested weighted evidence score can report coverage of explicit rules.
It cannot be calibrated from these selected descriptive examples. Keep
**win_probability=null** until independent chronological evaluation supports
it. Concise Roman Urdu: **"Daily event-window move causal reaction ya trade
profit nahi; original clocks aur execution evidence missing ho to WAIT."**
No pattern works 100%, and historical resemblance is not causation.

Reproduction uses `scripts/v3_news_evidence.py` and the adjacent
`news_events_20261028.json`. Six reused cases carry complete daily paths,
calendar spans, decomposition and observed ranges. Tests verify decomposition,
missing event-day behavior, prefix stability and receipt completeness.
No normal-return model, abnormal-return estimator, live news adapter or
causal strategy replay is delivered. Source chapters are not model training
or loaded runtime knowledge; orders and leverage remain disabled.

## Sources

Primary method paper, official events and actual retained H.15 observations
checked **28 October 2026**. Original arithmetic/interpretation is separated
from reported facts. Daily source data are public-domain-tagged with citation
requested; no proprietary expectation or tradable benchmark history is
republished.

1. Bernanke and Kuttner, [What Explains the Stock Market's Reaction to Federal Reserve Policy?, primary Fed manuscript](https://www.federalreserve.gov/pubs/feds/2004/200416/200416pap.pdf), **March 2004**; [archive metadata](https://www.federalreserve.gov/pubs/feds/2004/200416/200416abs.html), updated **1 April 2004**. Its surprise-identification method and historical estimates are not implemented or transferred as Hoshi forecasts.
2. Board of Governors/FRED, [DGS2](https://fred.stlouisfed.org/series/DGS2): exact daily captures, dates and hashes in `news_events_20261028.json`.
3. Board of Governors/FRED, [DGS10](https://fred.stlouisfed.org/series/DGS10): corresponding ten-year reference-yield history; original vintage/delivery and tradable bond prices remain unavailable.
4. BLS, [5 January 2024 employment release](https://www.bls.gov/news.release/archives/empsit_01052024.htm): stated clock and economic reference period.
5. BLS, [13 October 2022 CPI release](https://www.bls.gov/news.release/archives/cpi_10132022.htm): stated clock and reference period.
6. Federal Register/GPO, [EO 14257 dated 2 April, published 7 April 2025](https://www.govinfo.gov/content/pkg/FR-2025-04-07/html/2025-06063.htm): historical document and publication distinction, not a contemporary live feed.

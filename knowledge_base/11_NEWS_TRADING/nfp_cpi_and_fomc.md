# NFP, CPI and FOMC: releases, expectations and conditional market response

Reviewed **28 October 2026, Asia/Karachi**. The examples preserve official
historical announcements and actual daily Treasury reference-yield
observations. They are not live quotes or measurements of instantaneous
announcement effects. Archived release numbers, later-retrieved rate history,
pre-release expectations and original network arrival are different inputs.
Unsupported or missing inputs produce WAIT.

## What is it?

The US Employment Situation combines two surveys. Establishment data report
payroll jobs; household data provide measures including unemployment. The
headline nonfarm-payroll change is not a count of all people newly employed
under every definition. Revisions, earnings, hours, participation and survey
differences can matter alongside the headline. The archived release should
be read in its own vintage rather than silently replaced by today's revised
series. [1]

The Consumer Price Index release reports price-index changes with specified
population, period and adjustment conventions. A seasonally adjusted monthly
change and an unadjusted twelve-month change are different statistics.
Headline and excluding-food-and-energy measures are also different fields.
They can move differently without a contradiction. Do not compare a monthly
core figure with an annual headline forecast and call the result a surprise.
The selected September 2022 release demonstrates those distinct units. [2]

An FOMC announcement is a policy communication, not a single macroeconomic
measurement. The target range, decision change, statement, implementation
information, projections when supplied and subsequent communications can
carry different information. The **18 September 2024** statement lowers the
target range by half a percentage point to **4.75–5.00%** and specifies its
release clock. Those facts do not determine the sign of every market's next
move. [3]

A news surprise requires a pre-release expectation for the **same field,
units, vintage and horizon**. A prior month's value is not a consensus
forecast. Neither is a forecast collected after publication. This receipt
contains no verified pre-release survey snapshot, so numeric surprises stay
null. Calling a report "strong" or "hot" relative to expectations would need
that missing comparison.

## Why does it form?

A public announcement changes the available information set. Participants
may revise their outlook for growth, inflation, policy, earnings or risk.
But the price before publication can already reflect expectations, hedges
and uncertainty. A known outcome can therefore coincide with a small move,
a reversal or disagreement across instruments. The absolute level of a
headline does not by itself specify the change in beliefs.

Several channels can act in opposite directions. Better growth information
might improve an earnings outlook while increasing expected discount rates.
A policy cut might reduce the overnight target while longer yields reflect
a different growth, inflation or term-risk assessment. These are hypotheses
to investigate, not causal decompositions estimated by this chapter. A
single daily rate change cannot identify how much of each channel occurred.

The measurement clock also matters. An economic reference month precedes
the release date; the public document's stated release or embargo time is
not the time HOSHI's data pipeline actually received it. A daily market
observation can include many other announcements before and after the
selected release. Its date label does not reconstruct the first tradable
bid/ask response.

Execution adds another layer. A correct directional interpretation can still
fail if the proposed price was unavailable, spread widened, the signal
arrived late or a stop/target sequence is ambiguous. A market-price path and
an executable trading policy must be evaluated separately. This curriculum
never fills missing arrival or execution data with a fabricated entry.

## Application zone

Before a scheduled release, verify the official calendar and document source.
Store the local civil time zone and the UTC conversion. New York winter and
summer clocks differ: **08:30 Eastern** is not always the same UTC hour.
A hardcoded fixed offset can put a strategy on the wrong bar. The selected
employment and CPI dates below are deliberately on different offsets.

Specify which fields the research hypothesis uses before viewing the
outcome. For payroll research, define whether the feature is the first
headline change, revisions, earnings or a combination, and how mixed evidence
is handled. For CPI, fix the series, adjustment and horizon. For FOMC,
distinguish the target decision from a measured change in expectations.
Versions must preserve both the reported value and its source release.

At publication, verify identity and provenance before acting on extracted
numbers. A headline with the wrong reference period or a reposted old
release can look relevant while being stale. Preserve source publication,
local ingestion and decision times separately. A scheduled time alone does
not verify receipt. If parsing, source identity or current execution inputs
are missing, the candidate remains WAIT.

After publication, any proposed paper setup still needs its own supported
instrument, observed price, structure, liquidity and risk evidence. A label
such as NFP day is context, not a substitute for these inputs. A post-release
retest hypothesis needs a predeclared rule for confirmation, expiry and
invalidation, and cannot use an earlier favorable tick as an assumed fill.
No number in this chapter authorizes leveraged or real-money execution.

The market context retained here uses **Board H.15 DGS2 and DGS10**, via FRED,
in **percent per annum**. A **0.01 percentage-point** change equals **one
basis point**. These are two- and ten-year constant-maturity reference yields,
not directly executable bond prices. A yield rise is not an observed bond
portfolio return. Source metadata and exact daily endpoints are retained;
original rate-vintage and delivery histories remain unverified. [4][5]

## Failure zones

The headline-to-direction shortcut fails when expectations, revisions,
other fields or prior positioning matter. The source may report a positive
jobs number while components disagree, or a policy change may already have
been anticipated. Without a pre-release consensus snapshot, the sign and
magnitude of the surprise cannot be recovered by looking at the subsequent
chart. Doing so uses the outcome to define the input.

Time substitution is another failure. Replacing a first-release value with
a revised historical series gives the model later information. Treating the
reference month as the announcement date gives it information too early.
Treating a later daily yield as an intraday execution quote also leaks
information. This chapter retains these gaps rather than claiming a causal
replay from current downloads.

A fixed waiting period does not guarantee safe liquidity or complete news
interpretation. Subsequent documents, corrections and other announcements
may arrive. A cautious research policy can suspend candidates around events,
but its specific interval and cost assumptions still need evaluation.
Normal schedules must not be assumed to cover every special policy release;
the actual official notice controls.

The three selected windows are too few to calibrate a news strategy. There
are no verified consensus estimates, intraday prices, fills, spreads or
historical execution costs. All observed yield changes are descriptive daily
context and may contain other information. No pattern works 100%, and no
historical comparison establishes institutional intent, a guaranteed NAS100
short or a profitable next trade.

## Three real historical examples with dates

### Example 1 — 5 January 2024 employment release: first-day and later yield paths differ

The archived BLS release for **December 2023** states **08:30 Eastern on
5 January 2024**, corresponding to **13:30 UTC** in New York winter time.
It reports a **216,000** seasonally adjusted nonfarm-payroll increase and
**3.7%** unemployment. Those are fields in the reviewed release, not today's
revised employment history. No verified pre-release consensus or original
network-arrival log was obtained. [1]

The bounded rate window is **4–8 January 2024**. Actual DGS2 observations
are **4.38%, 4.40%, 4.36%** on **4, 5 and 8 January**, respectively. DGS10
observations are **3.99%, 4.05%, 4.01%**. Thus the release-date daily labels
show increases of **two and six basis points** from the preceding observed
date, while the complete selected window ends at **minus two and plus two
basis points**, respectively. The weekend is not filled with invented
intermediate observations. [4][5]

Original analysis: the observation horizon changes the descriptive answer.
Neither the first-day increase nor the later partial reversal identifies
an instantaneous payroll effect. The daily data include other information,
and neither yield is an executable NAS100 or BTC entry. The historical
release clock is known from the document; actual ingestion, tradable prices
and costs are not. The diagnostic remains WAIT with null surprise and win
probability.

### Example 2 — 13 October 2022 CPI release: units and observation windows must match

The BLS release for **September 2022**, stated for **08:30 Eastern on
13 October 2022**, corresponds to **12:30 UTC** under that date's daylight
saving time. It reports **0.4% monthly seasonally adjusted** headline CPI-U
and **8.2% unadjusted twelve-month** growth. Excluding food and energy, the
corresponding fields are **0.6% monthly** and **6.6% twelve-month**. These
are separate release-vintage measures rather than interchangeable inflation
numbers. [2]

For **12–14 October**, DGS2 is **4.28%, 4.47%, 4.48%** on the three daily
labels; DGS10 is **3.91%, 3.97%, 4.00%**. Exact endpoint changes are therefore
**plus 20 basis points** and **plus nine basis points**. The release-date
label alone differs from the following day's endpoint. The receipt does
not infer a bond-price return from those yields. [4][5]

Original analysis: a large yield change can coexist with many possible
intraday price paths. It cannot prove that an assumed entry immediately
after 12:30 UTC was available or that a particular stop would have held.
No equity-index reversal, minute-by-minute high/low, consensus surprise or
customer trade is invented from these daily data. Original-vintage rates,
source arrival and executable bid/ask information are still missing.

### Example 3 — 18 September 2024 FOMC cut: different maturities need not move together

The official statement is dated **18 September 2024**, with release at
**14:00 EDT**, or **18:00 UTC**. It cuts the federal-funds target range by
**50 basis points to 4.75–5.00%**. This is a policy-target decision, not a
fifty-basis-point instruction for every bond maturity. The reviewed statement
contains the decision; no contemporaneous market-implied expectation
snapshot was captured for this receipt. [3]

The reused, already attributed **17–20 September** H.15 window has DGS2
moving **3.59% to 3.55%**, or **minus four basis points**, while DGS10 moves
**3.65% to 3.73%**, or **plus eight basis points**. These observations were
already retained in the bonds chapter; they are reused transparently, not
counted as a new independent event or a new price feed. [4][5]

Original analysis: policy level and market yields describe related but
different objects. A simple cut-means-all-yields-fall rule contradicts this
selected endpoint comparison. The comparison does not isolate the statement,
subsequent communications, expectations or other releases. No actual bond
holdings, duration, tradable prices, spreads or fills were obtained. The
result supports caution about deterministic mappings, not a calibrated
contrarian trade. The diagnostic remains WAIT.

## How to use it to HUNT a trade

Build a point-in-time event record first: official identity, reference period,
stated release clock, first accessible vintage, genuine ingestion time and
any pre-release expectation source. If a field is unavailable, record it as
missing rather than infer it from price. A historical pattern match must
include counterexamples and relevant differences; matching event labels
alone is not causation.

Then require supported actual market data and a frozen paper hypothesis.
Observed structure/liquidity, source freshness, an executable instrument,
cost assumptions and bounded paper risk must all be present. Reject a
candidate whose supposed entry precedes source receipt or confirmation.
Do not fabricate entries, stops or targets for NAS100, gold or any other
unsupported market. A daily Treasury context observation cannot supply
those missing execution inputs.

The requested 40 history/20 liquidity/20 structure/20 global-flow result
will describe evidence coverage, not calibrated confidence. Until independent
chronological evaluation supports probability estimation, keep
**win_probability=null**. Concise Roman Urdu: **"Release ka source aur waqt
verified hai; consensus aur fresh execution inputs missing hain, is liye
WAIT."** Explain economic details only when asked; do not hide material
missing evidence behind a confident direction label.

Reproduction uses `scripts/v3_news_evidence.py` and
`news_events_20261028.json`: exact selected release fields, date-specific
New York offsets, raw H.15 CSV bodies/hashes and endpoint basis-point
calculations. Tests reject wrong clocks, forged fields, source/series aliases,
corrupt hashes and invented zero surprises. Missing endpoints remain missing.
This is source research, not a live news adapter, model training or an
implemented causal trading evaluation. Real orders and leverage stay disabled.

## Sources

Primary archived documents and actual rate captures checked **28 October
2026**. Brief reported facts are paraphrased; analysis is original. BLS release
figures preserve the reviewed archive, while the market-rate series are
later-retrieved history. No pre-release forecast feed or licensed benchmark
history was purchased or republished.

1. BLS, [Employment Situation release, 5 January 2024](https://www.bls.gov/news.release/archives/empsit_01052024.htm): December 2023 reference period, release clock and reported survey fields.
2. BLS, [CPI release, 13 October 2022](https://www.bls.gov/news.release/archives/cpi_10132022.htm): September 2022 reference period, clock and adjustment/horizon distinctions.
3. Federal Reserve, [FOMC statement, 18 September 2024](https://www.federalreserve.gov/newsevents/pressreleases/monetary20240918a.htm): stated release time and target decision.
4. Federal Reserve/FRED, [DGS2](https://fred.stlouisfed.org/series/DGS2): daily two-year constant-maturity yield, percent per annum, public-domain-tagged with citation requested. Full bounded CSV requests/responses are retained in the adjacent receipt.
5. Federal Reserve/FRED, [DGS10](https://fred.stlouisfed.org/series/DGS10) and [H.15 release](https://www.federalreserve.gov/releases/h15/): ten-year reference-yield and publication context, not a trade-price or original-arrival history.

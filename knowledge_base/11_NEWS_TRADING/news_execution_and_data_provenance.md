# News execution and data provenance: knowing what was actually knowable

Reviewed **28 October 2026, Asia/Karachi**. The three cases below are
documented publication or authenticity incidents. They are not fabricated
price charts, reconstructed fills or causal estimates of market reaction.
The implementation requirements in this chapter are original design
analysis for Hoshi's later integration; writing them does not install a
live news adapter, train a model or demonstrate a profitable strategy.

## What is it?

News provenance is the evidence connecting a statement or number to its
origin, version, meaning and availability. An execution decision adds a
second chain: what the system received, when it accepted the input, which
rule it applied and what executable market information existed afterward.
A correct economic number can still be unusable for a historical trading
decision if it was published later, revised after the event or attached
to the wrong instrument. Provenance is therefore part of the decision
input, rather than an optional footnote added after a backtest succeeds.

Several clocks must remain distinct. The reference period says what an
economic statistic describes. An event date identifies the occurrence
under study. A stated release time describes the publisher's schedule.
Actual first publication, a provider's timestamp, local receipt, completed
validation, decision and possible execution are separate events. The
schedule is not proof of any particular receipt time. A later investigator's
account can document an earlier incident without having been available to
a trader during that incident.

For Hoshi, an acceptable future input record should identify the issuing
organization, exact source URL, document identity, referenced period,
reported units, revision or vintage, clock precision and explicit UTC
offset where known. Capture time and a digest of retained bytes make the
research reproducible. They do not authenticate every underlying claim,
prove first publication or grant redistribution rights. A hash can preserve
an incorrect payload perfectly. An HTTPS connection can reach an authentic
publisher while the payload is stale, incomplete or subsequently corrected.

Provenance also includes instrument identity. A macro release is not a
quote for an exchange-traded futures contract, a cash index or a broker's
NAS100 contract. Those instruments have different sessions and execution
conditions. A research record that names the news source but leaves the
traded instrument, venue and price observation unspecified cannot support
an entry, stop or target. No pattern or news filter works 100 percent.

## Why does it form?

Information passes through multiple systems before becoming a usable
feature. Each handoff can change formatting, timing or meaning. A table
may distinguish a month-on-month seasonally adjusted rate from an annual
unadjusted rate; a short headline may omit that distinction. A calendar
entry can survive unchanged while publication is delayed. A current
historical database may incorporate corrections that a contemporary
observer did not possess. These are different failure mechanisms and
require different checks.

The engineering consequence is that the system should preserve both
content and availability evidence. A raw response and parser version
explain how a normalized feature was obtained. A timestamp with stated
precision explains what timing claim is justified. Keeping successive
versions separately permits a revision to change later decisions without
rewriting what earlier decisions allegedly knew. Overwriting the original
record with the newest value would make an apparently precise replay
historically dishonest.

Authenticity is another layer. An account name can be familiar while a
particular message is unauthorized. Repetition through many aggregators
does not create independent confirmation when every copy derives from
one origin. Conversely, a discrepancy can reflect publication timing,
units or a correction rather than a malicious act. The appropriate
response is to preserve the conflict, check the issuing authority's
designated publication channel and withhold an unsupported decision.
Inferring secret institutional intent from the conflict adds no evidence.

Finally, the economic surprise and the executable trade are different
objects. A surprise requires a suitably timed expectation measure with
compatible definitions. A later market price requires a timestamped
observation from a supported venue. The first number does not supply the
second. A strong narrative cannot repair missing arrival logs, historical
quotes, transaction costs or contract specifications.

## Application zone

The following requirements describe a bounded, read-only integration
target. They are not a claim that the present runtime already satisfies
them. First, supported sources and data purposes should be explicit.
Network responses need bounded size, timeouts, schema validation and a
clear treatment of missing, non-finite or unexpected fields. Redirects,
arbitrary user-provided URLs and text embedded in articles must not expand
the system's permissions or become a route to private credentials.

Second, normalization should retain the original document identifier and
field names alongside the chosen units. The rule must distinguish a
release's stated time from a measured receipt. Timezone conversion should
use the correct local offset for that date. A date-only source must remain
date-only; assigning midnight invents precision. Hoshi's Asia/Karachi
display can help the user understand timing while the evidence preserves
the source clock and a defensible UTC conversion.

Third, features should become eligible only after the required evidence
has been received and validated. A historical replay must not backdate a
correction to the original observation period. When original arrival is
unknown, the record should identify that gap rather than silently treat
the event time as receipt time. A coarse daily series may support a daily
descriptive study while remaining unsuitable for a minute-level news entry.

Fourth, freshness must be defined for the feature's purpose. A weekly
position report and an execution quote cannot share an arbitrary common
expiry rule. Re-fetching an old report now does not make the underlying
positions current. Freshness checks should examine the represented period,
publication and capture independently, and preserve a visible reason for
rejection. Duplicate delivery should not count as another independent
piece of confluence evidence.

Fifth, accepted news still needs compatible market observations and bounded
paper risk. A paper scenario needs an identified instrument, observed
prices, market status, realistic costs and a rule for ambiguous fills.
An old daily close cannot substitute for a live bid or offer. If those
inputs are absent, the correct future output is WAIT with null price
levels and `win_probability=null`. A rule-coverage score describes checked
conditions; it does not measure the probability of winning.

## Failure zones

A calendar-only backtest fails when it assumes the scheduled release was
both published and received at that instant. A latest-vintage backtest
fails when later corrections become earlier features. A social-headline
strategy fails its evidence gate when source identity is mistaken for
authorization of the particular statement. A replay may even combine all
three errors while its timestamps look neatly aligned.

Execution creates further limits. Without contemporaneous quotes and
venue rules, a candle's range cannot establish a fill sequence, queue
position or achievable spread. A post-event chart selected because it
looks dramatic supplies neither a precommitted decision nor an independent
evaluation sample. A correctly reported release can coexist with a losing
trade, an unfilled order or no qualifying trade. Retaining those outcomes
is necessary to assess a rule rather than advertise its best examples.

External text is data, never an instruction to modify Hoshi's identity,
risk limits, system prompt, permissions or Stop controls. A document that
asks for secrets, arbitrary code execution or a new data purchase should
not gain authority through retrieval. Research logs should retain only
what is necessary for reproducibility, with credentials and private user
content excluded. Existing privacy and voice controls must remain usable
even when a source is unavailable or a parser rejects a response.

There is also a legal and operational boundary. Reading a public page does
not automatically permit copying a licensed benchmark into a production
bundle, redistributing raw market data or using a research dataset for a
different purpose. The exact missing permission should be recorded. A
source outage or unclear right should reduce available functionality to
an honest WAIT or research-only result, not trigger an unauthorized paid
subscription or a substitution disguised as the original source.

## Three real historical examples with dates

### Example 1 — delayed COT publication, 31 January–24 February 2023

The CFTC's **24 February 2023** announcement says it issued the COT report
originally scheduled for **3 February**, after the ION-related disruption
prevented timely, accurate submissions. The announcement identifies the
position week ending **31 January** and adjustments in specified markets.
That is a **21-calendar-day schedule delay** and a **24-calendar-day gap
from the position date to the stated publication date**, calculated from
those dates. Exact intraday publication and pipeline arrival are missing.
The identified adjustments do not prove that every other market's present
historical row equals its first published vintage. [1]

The relevant observations here are publication dates, not a Gold return
or a hypothetical trade. The existing COT chapter separately retains
historical position rows; this example adds no new price observations.
A replay that attaches the eventual report to 31 January would let a
decision use evidence unavailable on that date. Attaching it automatically
to the originally planned Friday also fails. A defensible replay needs
the actual availability bound and the version used. Even after publication,
the report describes earlier positions rather than present orders at a
particular exchange price.

### Example 2 — unauthorized SEC social-account message, 9 January 2024

The SEC's statement dated **12 January 2024** recounts an unauthorized
**9 January** post at **16:11 ET** purporting to announce spot bitcoin ETF
approval. It records a warning from the Chair's account at **16:26 ET**
and a new SEC-account warning at **16:42 ET**. The statement explains that
Commission actions are made public on the SEC website and amplified through
social media. These are retrospective documented timestamps; the later
statement was not itself a 9 January predictive input. [2]

No exchange-specific BTC price tape, original message capture or local
receipt log accompanies this case. Therefore it supplies no measured
reaction, fill, profit or loss. The appropriate analytical lesson is to
distinguish the platform account, the authority to publish the particular
action and the content's validation state. A digest of the unauthorized
post would preserve its bytes without validating the purported approval.
After discovering a conflict, a system should invalidate dependent pending
decisions while preserving an audit trail. It must not rewrite the earlier
input as though the correction had always been known.

### Example 3 — early subset of BLS files, 15 May 2024

BLS's notice, last modified **15 May 2024**, says a subset of CPI and Real
Earnings files was inadvertently placed online **approximately 30 minutes
before release**. The archived CPI release states **08:30 ET on 15 May
2024**, or **12:30 UTC** under that date's daylight offset. The notice does
not identify an exact first-upload timestamp for every file or establish
that every observer received the entire release early. An exact 08:00
receipt is therefore not asserted. [3][4]

This is an availability exception, not a reconstructed strategy. The
retained primary documents establish the reported incident and scheduled
clock, but original per-file uploads, user arrivals, contemporaneous quotes
and executable spreads are missing. No market reaction or profitable
head start is inferred. The research requirement is to keep stated embargo,
actual availability and local receipt as distinct fields. A later downloaded
archive and a release calendar alone cannot resolve those clocks. The
case is included to expose false timing precision, not to recommend seeking
restricted information or bypassing publication controls.

## How to use it to HUNT a trade

For this chapter, hunting begins by determining whether a trade can be
evaluated honestly. Identify a supported instrument and the permitted
source before interpreting the headline. Record the feature's referenced
period, units, version and defensible availability. Reject unresolved
source conflicts and avoid treating duplicated news as multiple votes.
Only then examine the requested historical, liquidity, structure and global
flow evidence using inputs genuinely available at the decision time.

If any required source or execution observation is missing, Hoshi should
eventually return a concise Roman Urdu WAIT with the material gap. Entry,
SL and TP remain null. Teaching the entire incident history is appropriate
when asked; it is unnecessary in every default trading response. A short
reason can still name the source age or validation issue, rather than
present an invented confidence percentage. No historical resemblance in
these three incidents calibrates a future win probability.

If a later paper-only evaluation has all required inputs, freeze its rules
and costs before replay. Export the raw-source identifiers, version hashes,
normalized fields, eligible-at times, decision reasons and rejected cases
alongside results. Keep evaluation dates chronological and separate from
development choices. A correct provenance chain is necessary evidence for
that evaluation; it is not sufficient evidence of an edge. Real orders,
leverage, new paid infrastructure and purchases remain disabled, and the
existing privacy, voice and Stop behavior remains part of the integration
acceptance gate.

## Sources

Primary pages actually checked on **28 October 2026**. Prose is original;
short factual paraphrases support the dated cases. Current retrieval of a
historical document does not establish original pipeline arrival or grant
market-data redistribution permission.

1. [CFTC, COT Historical Special Announcements — 24 February 2023 entry](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm).
2. [SEC, Statement on Unauthorized Access to the SEC's X.com Account, 12 January 2024](https://www.sec.gov/newsroom/speeches-statements/gensler-x-account).
3. [BLS, Early release of CPI and Real Earnings data on 15 May 2024](https://www.bls.gov/bls/early-data-release-05152024.htm).
4. [BLS, archived CPI release, 15 May 2024 — stated embargo header](https://www.bls.gov/news.release/archives/cpi_05152024.htm).

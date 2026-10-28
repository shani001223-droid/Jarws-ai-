# Liquidity voids and stop events: measurement before a trading story

## What is it?

Liquidity void is not a single universal exchange field. Chart users sometimes
use the term for a large directional candle, a multi-candle imbalance or an
area that price traversed quickly. Microstructure research instead asks how
much buying or selling could be executed, at which prices, with what spread,
depth, replenishment and delay. Hoshi must name the measurement it actually
has. A large candle can be observed without a historical order book; a claim
that executable liquidity disappeared needs much more evidence.

Distinguish three objects. A **chart gap** is a relationship between sampled
prices, such as nonoverlapping outer candles in the existing FVG diagnostic.
A **trade-price gap** is a discontinuity between observed transactions on a
specified feed. A **depth shortfall** means that a specified order size cannot
be completed within the displayed price range or cost limit at a particular
instant. These can coexist, but none is automatically equivalent to another.
A gap in a data feed can also be missing information rather than a market event.

A stop event requires similar care. A stop order is a conditional instruction,
not the same thing as a displayed resting limit order. The checked SEC stock
order bulletin distinguishes stop-trigger activation from the eventual market
execution price, and stop-limit price control from guaranteed execution. A
specific venue's trigger rules still need checking. Candles crossing yesterday's
low do not reveal how many stops activated or whether any belonged to a
particular institution.

This chapter uses three official historical investigations to examine market
functioning. It does not certify a proprietary ICT void recognizer, supply
live depth for an unsupported symbol, or reproduce the reports' full datasets.
The case facts are explicitly reported observations, followed by original
analysis of what Hoshi could and could not infer at a decision cutoff.

## Why does it form?

At any instant, an aggressive order can consume available opposing limit
interest. Further interest can appear, disappear or move before another order
arrives. If aggressive demand persists while usable opposing interest is
limited, execution may require progressively less favorable prices. That is
a conditional mechanism, not a claim that every rapid move has the same cause.
Changing information can also cause participants to reprice quotes together.

Displayed quantity is not a promise to a future trader. An order may execute
against someone else, be canceled or become inaccessible before the phone's
request reaches the venue. Market depth can be distributed across price levels
and venues, and some interest may not be displayed. A screenshot of a large
bid therefore differs from a verified ability to sell the intended quantity
at that price after realistic latency.

Feedback can intensify stress. A conditional order that activates into a market
order adds immediate demand for execution. Hedging can add demand as prices
change. Participants may reduce risk limits or withdraw quotes when their
information is stale. A pause or price limit on one venue changes the information
and execution available to others. The relative importance of each mechanism
requires event-specific evidence, not an assumption of deliberate trapping.

High turnover also does not guarantee low execution cost. Many transactions
can transfer positions rapidly among a small group while little new capacity
absorbs sustained one-sided demand. Conversely, a thin-looking market can
sometimes replenish quickly when orders arrive. The relevant question is
resilience for a stated size and horizon, not simply whether the volume bar
is large or the last candle is long.

## Application zone

For a microstructure hypothesis, freeze the instrument, venue, price type,
order size, time interval and cost limit. A possible diagnostic is the cost
of sweeping displayed opposing depth for a fixed hypothetical quantity, measured
relative to the simultaneous midpoint. If displayed depth is insufficient,
the result is **unavailable at that size**, not zero cost. A missing quote,
crossed book, sequence gap or stale timestamp must be a data-quality state.

Compare observations with a point-in-time baseline appropriate to the same
instrument and time of day. A relative spread change without its absolute
spread can be misleading. A percentage-price move without volume and depth
cannot distinguish ordinary repricing from an execution-capacity shortfall.
Specify whether the baseline uses prior days, the preceding minutes or a
different venue. Do not select whichever benchmark makes the event look most
exceptional after seeing the outcome.

Keep source clocks separate. Exchange event time describes when a message
was generated; capture time describes when it reached the collector; device
arrival time describes what Hoshi could know. A later regulatory report may
identify a mechanism using privileged transaction or supervisory data that a
retail strategy never had. That report is valuable for retrospective learning,
but its conclusions cannot become an intraday input years before publication.

When only OHLC data exist, export an explicitly named **price-range proxy**.
The existing daily and minute receipts can establish recorded highs, lows,
closes and some gap geometry. They cannot measure queue position, canceled
orders, sweep-to-fill costs or participant stop inventories. No threshold on
a candle's range silently upgrades that proxy into a depth detector. This
chapter adds no new purported book reconstruction or runtime data feed.

An eventual paper experiment should also state its operational response.
Possible conditions include pausing new candidates when quotes are stale,
rejecting unsupported markets, restricting hypothetical size and requiring a
stable observation period after a disruption. Each threshold needs a version
and a causal replay. A protective control can reduce exposure without implying
the remaining trades are safe or profitable.

## Failure zones

**Assuming the gap must fill:** a chart imbalance can persist while price
continues away. Even when a later return occurs, it may happen after a stop,
expiry, financing charge or unacceptable drawdown. A retrospective touch is
not proof that a trader could wait indefinitely. Define the observation and
entry horizons before studying whether price returned.

**Treating every decline as a stop hunt:** the fact that stops can amplify
movement does not prove they initiated a particular event or reveal malicious
intent. An official report can discuss several plausible contributors while
leaving causal uncertainty. Hoshi should preserve that uncertainty rather
than converting the report into a single institution-versus-retail narrative.

**Using volume as capacity:** a huge volume bar does not identify how much
new one-sided risk a market can absorb at the current price. A later analysis
that reconstructs participant positions has more information than the bar.
An intraday rule cannot assume those later reconstructed identities were
observable at the time.

**Mixing markets and price types:** a Treasury yield change is not an equity
return; a midpoint is not necessarily a transaction; a spot FX venue is not
the entire decentralized market. A futures trading pause does not imply every
related spot venue paused. Combining incompatible observations into a single
seamless chart can manufacture a trade that no participant could execute.

**Ignoring trade revisions and outages:** an extreme print may later be
canceled, corrected or disputed. A missing feed can look like an empty book.
Research should preserve both the originally observable record and subsequent
corrections with separate timestamps. Silently using cleaned hindsight data
to determine historical orders makes execution claims unreliable.

**Evaluating only spectacular events:** famous disruptions explain failure
mechanisms, not their frequency in ordinary trading. Three selected episodes
cannot calibrate an alarm or establish a win probability. A future study
needs normal periods, false alarms, missing data, opportunity costs and
zero-trade results as well as dramatic examples.

## Three real historical examples with dates

These are **officially documented market-functioning cases**, not three
downloaded live chart replays. Numerical statements below are attributed
report findings. Raw historical book messages, complete execution records
and point-in-time retail arrival logs were not obtained for these cases.
No entry/stop/target, strategy return, crash duration or exact fill is invented.

### Example 1 — 6 May 2010: turnover and usable absorption diverge

The CFTC/SEC staff report, dated **30 September 2010**, examines the U.S.
equity and E-mini S&P 500 disruption of **6 May**. Its executive summary and
futures discussion describe rapid repeated transfers among high-frequency
participants rather than equivalent net absorption. It reports over
**27,000 contracts** traded by HFTs in a fourteen-second interval while
their additional net purchases were only about **200 contracts**. It also
records a **five-second** E-mini Stop Logic pause, followed by stabilization
and recovery. These are report findings, not Hoshi's own trade-tape calculations.

The original lesson for Hoshi is about measurement: gross volume and incremental
risk absorption are different quantities. A chart volume spike alone would
not provide the participant-level net measure reconstructed in the report.
Nor would a candle identify whether an order rested behind available buyers
or would be exposed to a pause. This chapter does not convert the report's
market-clock timestamps into a machine UTC event stream; an exact replay
would require an explicitly verified clock convention and raw messages.

A paper control motivated by this case should ask whether its feed and
execution assumptions still hold during disruption. It should not infer that
every large volume spike forecasts a reversal or reuse a later official
explanation as information available before the event ended.

### Example 2 — 15 October 2014: related markets need separate measurements

A Federal Reserve staff retrospective published **24 September 2020** reports
that the benchmark ten-year Treasury yield fell **16 basis points** during
**09:33–09:45 ET** on **15 October 2014** and rebounded within that event
window. The entire day's reported yield range was **37 basis points**.
The note compares BrokerTec Treasury activity with agency MBS transactions
reported through TRACE. It distinguishes Treasury midpoint-based price
comparisons from MBS transaction-price observations and documents different
patterns of trading intensity across the related markets.

Those source distinctions prevent a misleading unified signal. A spread or
relative-value hypothesis needs synchronized observations of the actual
instruments and comparable price types, not a yield-change percentage copied
onto an unrelated instrument. The twelve-minute window is the study's event
definition, not an invented complete crash duration or a guarantee that a
retail stop could execute throughout it.

The study is a later staff analysis, not an information release available
during the 2014 morning. Hoshi has not downloaded the underlying BrokerTec
and TRACE messages. The original joint report's full large PDF was not used
as a substitute for those missing data; the checked 2020 note directly
supports the limited reported facts used here. No tradable spread, fill or
calibrated return is derived.

### Example 3 — 7 October 2016: actual depth shortfall and cross-venue limits

The BIS Markets Committee report, published **13 January 2017**, examines
sterling's **7 October 2016** flash event using Thomson Reuters Matching,
CME futures and other evidence. It reports an initial Reuters midpoint move
from **1.2600 to 1.2494** over **00:07:03–00:07:11 BST**. BST is UTC+01:00,
so that narrow interval is **23:07:03–23:07:11 UTC on 6 October**. Event dates
therefore depend on the stated clock; both labels describe the same interval.

The report's depth analysis treats gaps in its fixed-quantity sweep-to-fill
series as insufficient book depth for that quantity, not zero cost. It also
describes later dysfunction, stop/hedging-related amplification, platform
differences and revised or canceled trades. Its venue-specific evidence is
not a complete global FX tape or a claim that one actor caused every move.

For Hoshi, the distinction is operational. If the intended hypothetical size
cannot be costed from usable opposing depth, the data should reject the
candidate rather than assign the last midpoint as an executable entry. A
fast price rebound does not establish that depth or normal execution recovered
at the same instant. The raw order books and exact individual stop triggers
remain unavailable in this curriculum; no current GBPUSD order ticket is
manufactured from the historical report.

## How to use it to HUNT a trade

Begin by stating what evidence is available. With candles alone, label a
range/gap hypothesis and retain the limits. With a supported book feed,
validate sequence, timestamps, spread, usable depth and the intended paper
quantity before interpreting a shortfall. Never repair missing quotes with
an attractive midpoint or let stale data contribute full evidence coverage.

Freeze an entry and invalidation policy before replaying a disruption. Include
latency, price increments, conservative slippage, rejected opportunities and
ambiguous order sequencing. Historical resemblance may motivate a risk check;
it cannot supply the actual source price or a current direction. A war,
flash-event or gap label never substitutes for observed entry/SL/TP inputs.

Report the failed assumptions as carefully as any apparent success. Export
source event times, actual arrival where known, affected venue, missing inputs,
cost bounds and why the system waited. Independent chronological evaluation
must include ordinary periods and drawdown/cost checks before a probability
can be calibrated. Until then, Hoshi's concise output should be WAIT when
evidence is missing, with `win_probability=null` and no real orders enabled.
This is source education and a future integration requirement, not a delivered
runtime depth engine or model training.

## Sources

- [CFTC/SEC staff findings, 30 September 2010](https://www.sec.gov/news/studies/2010/marketevents-report.pdf): primary report checked 28 October 2026, executive summary and E-mini discussion, including printed pages 2–4 and 14–15. Staff findings are not an assertion that both Commissions adopted every conclusion.
- [Federal Reserve staff retrospective, 24 September 2020](https://www.federalreserve.gov/econres/notes/feds-notes/retrospective-the-agency-mbs-market-on-october-15-2014-20200924.html): primary event-window, venue and price-measure descriptions checked; retrospective staff analysis, not an October 2014 release.
- [BIS Markets Committee full sterling report, January 2017](https://www.bis.org/publications/sterling-flash-event-7-october-2016.pdf): primary report checked, especially printed pages 1, 3 and 5–9; exact early price/time and fixed-quantity depth-shortfall distinctions, not a universal FX tape.
- [BIS publication record, 13 January 2017](https://www.bis.org/publications/sterling-flash-event-7-october-2016): checked publication date separated from event date.
- [SEC Investor.gov stop-order bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15): primary stock-order trigger/execution distinctions checked; venue-specific parity is not assumed.

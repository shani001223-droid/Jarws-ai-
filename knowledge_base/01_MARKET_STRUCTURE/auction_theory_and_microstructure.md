# Auction theory and market microstructure: how observations become trades

Reviewed **28 October 2026, Asia/Karachi**. Source curriculum for bounded paper
research. This chapter adds no order routing, paid feed, exchange account or
runtime retrieval. Historical cases are sourced institutional observations;
they are not a reconstructed tick-by-tick trading backtest.

## What is it?

Market microstructure studies how a market's trading arrangements, information
and participant interactions affect observed prices and execution. Relevant
objects include orders, quotes, transactions, matching rules, trading states,
latency, fees, clearing and contract specifications. A candle is an aggregated
output of a process; it is not a complete record of that process. Two markets
with similar-looking candles can have different spreads, queue rules, trading
interruptions and settlement obligations.

An auction is a mechanism for bringing buying and selling interest together.
A continuous limit-order book matches eligible incoming and resting interest
over time. A call auction collects eligible interest for a crossing process
under venue-specific rules. Nasdaq's opening and closing crosses are actual
exchange mechanisms, with specified order types and imbalance information.
They are different from a trader informally describing price movement as an
auction between perceived value areas.

CME's published matching documentation lists several algorithms. In FIFO,
priority at the same price depends on time; pro-rata and hybrid arrangements
allocate differently. HOSHI must not assume every venue or product uses one
universal queue model. A displayed quantity ahead of an order is not a promise
that the quantity will remain, and an amendment can affect priority under the
applicable rules. Exact product rules need a dated check before simulation.

The best bid is the highest currently displayed eligible buying price in the
observed book; the best ask is the lowest eligible selling price. The quoted
spread is ask minus bid, while their midpoint is their arithmetic average.
Depth measures quantities at specified price levels and times. Traded volume
measures executed quantity over a specified interval. These are different
objects: many transactions can occur while little quantity remains immediately
available at the next observation.

In chart-based auction vocabulary, balance and value migration are hypotheses
about activity distribution. A TPO profile counts selected time-price
opportunities; a volume profile allocates observed volume by price. They must
not be treated as interchangeable or as an oracle of fundamental worth.
Time-bucket length, price-bin width, session boundaries and data coverage
change their output. A frequently visited price need not be the next target.

## Why does it form?

Different participants want different combinations of immediacy, price
certainty, size and inventory exposure. An aggressive order can trade against
available resting interest; a passive order offers price constraints while
accepting nonexecution and adverse-selection risks. Cancellation and revision
change what is available without necessarily producing a transaction. A
sequence of trades and quote changes can therefore produce a large price move
without the candle revealing a single identifiable motive.

Consider an **invented numerical illustration**, not a real historical book.
Suppose the best bid is 99.90 and the best ask is 100.10, with two units offered
at 100.10 and three at 100.30. A three-unit aggressive purchase, assuming those
offers remain and no other rules intervene, trades two units at 100.10 and one
at 100.30. Its average price is approximately **100.1667**. The initial
midpoint was 100.00; the average exceeds it by about 0.1667 per unit before
fees. Reporting a fill at the midpoint would understate this illustrative cost.

Now suppose the trader instead joins a bid at 99.90. A later chart touching
99.90 does not establish a fill: other orders may have priority, the trade may
be elsewhere, or the order may not yet have arrived. A snapshot is not an order
event stream. This is why the earlier chapters' wick contacts remain contacts
rather than being promoted to executed paper positions.

Liquidity provision can change when price uncertainty, inventory exposure or
operational risk changes. This is a possible mechanism to evaluate, not proof
that every disappearing quote is manipulation. Market-impact and adverse
selection hypotheses should be linked to observed messages and subsequent
prices where those data exist. A large red candle alone does not establish
spoofing, a stop hunt, dealer inventory or collusion.

Contract economics also matter. A futures contract can embed expiry and
delivery obligations absent from a cash spot position. A cash bond price and
its yield are different variables; a price rise can accompany a yield fall.
Mapping one instrument's tick, multiplier, currency or settlement rule to
another can reverse an interpretation or corrupt risk arithmetic. Unsupported
contracts should remain unavailable rather than being imitated with a vaguely
related series.

## Application zone

Use microstructure to specify what a paper strategy can honestly observe and
what it can simulate. Start with a contract record: venue, exact symbol or
expiry, price currency, quantity unit, tick size, multiplier where relevant,
session, matching method and allowed trading states. Historical contract
versions matter; today's rules are not automatically the rules in force during
a 2010 event.

Choose the data tier before choosing the claim. OHLCV supports aggregate path
descriptions and some conservative bar-based studies. Trades can support
executed-volume analysis, subject to timestamp, correction and coverage issues.
Top-of-book quotes support a more direct spread observation. Book-depth
snapshots support size-at-level observations at their capture instants. Full
sequenced messages can support more detailed queue reconstruction, but only
when initialization, dropped messages and venue rules are handled correctly.
Do not imply access to a finer tier because its terminology appears in a
system prompt.

Record an event clock and an availability clock. Exchange timestamps, feed
receipt times and local processing times answer different questions. A message
with an old exchange timestamp that arrives later was not available earlier.
Out-of-order data and sequence gaps require a declared recovery policy. A
historical reconstructed book cannot quietly forward-fill missing depth
through a volatile period and then claim continuous observed liquidity.

For an auction study, use the exchange's actual auction fields and rules.
Indicative imbalance information is an evolving observation, not a guaranteed
final auction print. Entry cutoffs, cancellation rules, collars and tie-breaks
must be read for the particular product and date. Nasdaq's public overview
identifies subscription-based imbalance data; this HOSHI upgrade has not
purchased or configured that feed. Missing auction evidence produces WAIT for
any model requiring it.

For profile research, predeclare session boundaries and distinguish prior
completed-session statistics from an evolving current profile. A full-session
point of control plotted retrospectively cannot become a morning feature before
the later trades exist. Daily OHLCV does not supply exact traded volume at
every price. Spreading a bar's entire volume uniformly across its range would
be an approximation and must be labelled accordingly; it is not an observed
footprint or DOM reconstruction.

Execution estimates must reflect the relevant mechanism. A small illustrative
spread assumption is not a measured spread for an unsupported market. Costs
should distinguish fees, crossing the spread, delayed observation and movement
while a candidate is pending. Minimum lot and cash-risk constraints can make a
candidate infeasible. Lowering assumed costs after a negative result is another
research choice to log, not an innocuous formatting adjustment.

Use the historical cases below as reasons to stress assumptions. They cover
different markets and mechanisms, so they must not be collapsed into one
universal crash signature. The reported events demonstrate that execution
conditions can matter enormously; they do not establish a calibrated entry
system based on matching a headline to a chart shape.

## Failure zones

**Volume mistaken for depth:** a busy market can still have little immediately
available quantity, and rapidly recycled transactions need not represent new
long-horizon risk absorption. A volume spike is not a guarantee that a bounded
order could execute near the displayed price. The 2010 case provides a
documented reason to keep these concepts separate.

**Displayed book mistaken for total supply:** hidden orders, other venues,
cancellations and message latency can make one snapshot incomplete. A large
displayed order is not a verified institutional commitment. Claims about intent
need appropriate evidence; descriptive book imbalance alone does not prove a
future directional outcome.

**Queue certainty from a chart touch:** OHLC does not identify order arrival,
size ahead, eligible matching priority or exact trade sequence. Treating every
touch as a full fill can create fictitious high accuracy. Conservative models
may reject ambiguous fills, cap size or require finer evidence; their policy
must be fixed before examining the result.

**Contract or unit substitution:** front-month oil, a later oil expiry, a
continuous adjusted chart and physical spot oil are different observations.
An adjusted historical series may be useful for some return studies but need
not contain prices that were ever executable in a single contract. A negative
futures settlement is not a statement that every oil product, storage location
or equity traded at that price.

**False positive-price universality:** a validator designed specifically for
positive-priced crypto spot candles is appropriate only within its supported
scope. The April 2020 WTI case does not justify removing checks from that
validator and pretending futures support exists. A separate contract adapter
would need its own price-domain, delivery, expiry and risk tests. Until then,
unsupported instruments remain unsupported.

**Post-event explanations becoming input features:** official reports can use
non-public data and months of investigation. A later conclusion cannot be
treated as a real-time signal on the event date. Preserve publication dates
and separate observed market conditions from explanations developed afterward.
When source material cannot be retrieved, record the exact missing detail.

**Universal auction stories:** balanced activity can break out, a low-volume
area can be traversed or revisited, and a previously active price can cease to
matter. No auction or profile pattern works 100%. A story about price discovery
is not a substitute for cost-aware chronological evaluation.

## Three real historical examples with dates

These are genuine documented market episodes, rather than invented profitable
chart setups. Sources distinguish the event day from the later publication.
No raw event-level feed has been captured for these three episodes in this
chapter; unavailable queue, spread, fill and exact path data remain unmeasured.

### Example 1 — 6 May 2010: U.S. equity and E-mini liquidity disruption

The joint CFTC/SEC staff report, published **30 September 2010**, documents a
rapid decline and rebound across U.S. equity products on **6 May 2010**. Its
analysis connects E-mini selling, changing liquidity provision and propagation
to related securities. It also describes rapid repeated trading that generated
large volume while absorbing little net inventory. The report's relevant
intraday timestamps use U.S. Eastern Time, not UTC daily crypto bars.

The HOSHI research implication is to stress a model's assumption that volume
means stable executable depth. This chapter does not reproduce a complete
order-message replay or assign an exact fill to the event's extreme. A later
rebound cannot establish that a chart-based limit order would have been active,
eligible, fully filled and safely exited. The report is evidence about this
episode, not proof that every future sharp wick will reverse.

### Example 2 — 15 October 2014: a rapid round trip in the U.S. Treasury market

On **13 July 2015**, five U.S. agencies released their joint analysis of the
**15 October 2014** Treasury episode. The checked Treasury announcement reports
record trading volumes, a rapid price round trip and diminished liquidity in a
narrow interval. It identifies several relevant developments, including order
book depth, order flow, liquidity provision, risk sentiment and positions,
rather than presenting one universally sufficient cause.

The announcement is the checked source for these facts. Its linked report PDF
exceeded the retrieval tool's size limit in this review; no uninspected
millisecond sequence, exact yield excursion or simulated fill is claimed.
The exercise is to distinguish cash Treasury prices, yields and Treasury
futures, and ask which source would be required to evaluate a proposed entry.
High daily activity alone would not resolve that execution question. The later
publication could not have been a feature on the 2014 event day.

### Example 3 — 20 April 2020: negative settlement in the expiring May WTI contract

The CFTC's interim staff report, published **23 November 2020**, records that
the **May 2020 NYMEX WTI** contract settled at **−US$37.63 per barrel on
20 April 2020**, before its April 21 expiration. It discusses demand, supply,
storage concerns and trading/liquidity conditions. Its scope does not establish
a definitive root cause for each individual price movement. The event concerns
a particular expiring futures contract, not all oil prices or cryptocurrency.

For HOSHI, the concrete lesson is to require instrument economics before
applying a chart model. Expiry, physical-delivery exposure, price-domain support
and spread/gap behavior cannot be replaced by a generic support line. No
position in this contract is implemented, and the negative settlement is not
an available BTC entry price. A backtest that substitutes a continuous chart or
clips negative prices to zero would answer a different and potentially
misleading question.

## How to use it to HUNT a trade

Begin with an observable paper hypothesis and verify the instrument contract
and data tier. State exactly which evidence the hypothesis needs: completed
candles, trades, quotes, book messages or auction fields. Unsupported feeds and
essential missing information produce WAIT. Do not buy access, create exchange
credentials or place orders as a consequence of reading this chapter.

Next reconstruct only information available at the decision time. Check
sequence continuity, clock alignment, source age and corrections. Build any
profile or imbalance from the permitted prefix; do not import a completed
future session. Keep a descriptive pattern separate from an inference about
participant identity or intent. Independent evidence can be absent, and that
absence should remain visible.

Then apply an execution model consistent with the available observations.
Record whether the model assumes a market-like fill, a conservative limit
fill, rejection or ambiguity. Bound hypothetical size by observed risk
distance, available cash and quantity constraints, incorporating realistic
costs. A favorable future endpoint with no defensible fill is not a successful
trade. A gap through a trigger is not an exit at an invented trigger price.

Finally stress the model against depth withdrawal, partial fills, stale quotes,
contract changes and missing data. Export evidence times, source versions,
unavailable fields and failed candidates. Default response may be
`WAIT — candles hain, lekin is setup ke liye required order-book evidence nahi
hai.` The user can request the detailed lesson; the concise response must still
identify the actual missing evidence and remain paper-only.

## Sources

- [CME Group Client Systems Wiki: Supported Matching Algorithms](https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457218479/Supported%2BMatching%2BAlgorithms) — checked exchange documentation for FIFO/pro-rata distinctions; product-specific dated rules remain necessary.
- [Nasdaq Trader: Opening and Closing Crosses](https://www.nasdaqtrader.com/trader.aspx?id=openclose) — actual auction order types and imbalance-data access, not a configured HOSHI feed.
- [TradingView's own TPO documentation](https://www.tradingview.com/support/solutions/43000725590-time-price-opportunity-charts-explained/) — a software provider's definition of its chart construction, not independent evidence of profitable prediction.
- [CFTC/SEC staff: Findings Regarding the Market Events of May 6, 2010, published 30 September 2010](https://www.sec.gov/files/marketevents-report.pdf) — original report, executive summary and E-mini liquidity discussion.
- [U.S. Treasury: joint-report release, 13 July 2015](https://home.treasury.gov/news/press-releases/jl0106) — checked announcement about the 15 October 2014 episode; the oversized linked report itself was not retrieved in this review.
- [CFTC interim WTI staff report, published 23 November 2020](https://www.cftc.gov/media/5296/InterimStaffReportNYMEX_WTICrudeOil/download) and [official release](https://www.cftc.gov/PressRoom/PressReleases/8315-20) — contract identity, negative settlement and the stated limits of causal analysis.

All exposition is original, with limited attributed source paraphrase; no
proprietary course or full report is reproduced. This source chapter does not
establish historical queue data, paid-feed rights or independent performance.

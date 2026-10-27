# Wars and Market Impact: Surprise, Transmission and Dated Event Studies

Document ID: `all_wars_and_market_impact`. Reviewed: **28 October 2026**.
Status: source-checked educational research; runtime integration is pending.
Scope: a framework and selected documented observations, not an exhaustive registry of every armed conflict. The companion `war_event_observations_20261028.json` contains the actual NASDAQ Composite observations used here. No historical episode is an executable present-day signal.

## What is it?

War-related market impact is the change in asset prices, market functioning or financing conditions associated with new information about conflict. “Associated with” matters: an observed return after an event is not automatically the event's causal effect. Economic releases, company news, monetary expectations, positioning and other developments continue during a conflict. A disciplined analysis distinguishes the event's occurrence, the market's earlier expectations and the change in beliefs produced by each new development.

A conflict also has many possible event dates. A threat, ultimatum, initial attack, invasion, sanction announcement, shipping interruption, ceasefire announcement and implemented ceasefire are different observations. Combining them under a single label erases useful information. A study of a weekend attack must distinguish the calendar date from the first subsequent trading session. A daily cash-market index cannot reveal the exact intraday reaction to a development that occurred while that market was closed.

The term “war pattern” should therefore mean a defined research comparison with explicit features. It must not mean that the system recognizes a headline and assigns the direction of a famous earlier chart. The relevant features can include surprise relative to expectations, energy exposure, geographical exposure, supply disruption, inflation conditions, financing constraints and the actual time horizon. A narrative resemblance is not a measured probability.

## Why does it form? Economic channels

**Cash-flow effects:** damaged infrastructure, interrupted production, reduced travel or disrupted shipping can change revenues and costs. The effects differ across firms and economies. An energy producer, an airline, an importer and a technology business do not have identical exposures. A broad index aggregates businesses whose sensitivities can offset or reinforce one another. A sector's apparent relative resilience is not proof that every company in that sector benefits.

**Energy and inflation effects:** a credible threat to production or transport can change expected commodity availability and risk premia. Higher input costs can lower some profit margins and affect expected monetary policy. But prices respond to the difference between anticipated and newly perceived conditions. If a feared disruption appears less severe than expected, a commodity price can fall even while fighting continues. A geopolitical label alone does not identify the size or sign of the supply surprise.

**Discount-rate and financing effects:** risk tolerance, required returns, credit spreads, exchange rates and government-bond yields can all change. Falling nominal yields can reflect growth concerns or demand for safer assets; rising yields can reflect inflation, fiscal or term-premium concerns. The presence of conflict does not force one response. A currency's relative behavior depends on both countries and on the structure of funding and external obligations.

**Liquidity and position effects:** hedging, margin calls, redemptions and changes in dealer risk capacity can move prices independently of a simple earnings story. A participant may sell a liquid asset to meet losses elsewhere. This can temporarily weaken a relationship usually treated as a hedge. HOSHI should examine observed funding and market conditions instead of assuming that gold, bonds or a particular currency must always provide immediate protection.

**Uncertainty resolution:** anticipated bad news can already be reflected in prices. New information may worsen the economic outlook while simultaneously narrowing a wide range of feared outcomes. The net result can be a rally, a decline or a reversal over different horizons. That is a reason to measure before and after separately, not a rule to mechanically “buy the invasion.”

## Historical research and instrument boundaries

Rigobon and Sack's research on Iraq-war risk uses an identification method rather than assuming every return after a headline was caused by that headline. Their reported war-risk factor was associated with lower equity prices and Treasury yields, wider lower-grade spreads, a weaker dollar and higher oil prices in the examined period [S1]. That result is evidence about an estimated factor under particular assumptions, not a trading instruction for all wars.

The RBA's May 2003 discussion is also instructive. It describes oil prices rising before military action and then falling, while noting other supply and demand influences alongside Iraq [S2]. The analysis demonstrates why an economic mechanism needs competing explanations. It does not establish that all future invasions lower oil prices or that a researcher can isolate causality from a single chart.

For 2022, the ECB documents the interaction of the invasion of Ukraine, the energy shock, inflation and changing financial conditions. Its discussion separates an initial risk-off period from the wider year's repricing [S3]. For 2026, the ECB's May review uses 28 February as the conflict event and 2 March as the first trading day after the weekend; it also analyzes shifting cross-asset behavior [S4]. These source-specific clocks must be preserved. Neither review is an observation of market conditions on this chapter's October review date.

The numerical table below concerns the **NASDAQ Composite cash closing index**, FRED series `NASDAQCOM` [S5]. It is not NASDAQ-100, a NAS100 CFD, an NQ futures contract, the local market of a combatant country, or a cryptocurrency exchange. Historical daily index availability does not create a live quote feed or a supported execution instrument inside Hoshi.

## A fixed before/after measurement protocol

For each selected calendar event, request daily NASDAQ Composite observations from ten calendar days before through thirty calendar days after the event. Remove missing holiday observations. Use the last observed close strictly before the event date as the baseline. Then select the first, fifth and twentieth observed trading sessions on or after that date. Calculate `100 × (selected close / baseline close − 1)`.

This rule deliberately avoids picking the most favorable later high or low. It does not remove all selection bias: the four historical episodes were chosen for educational examination, not sampled from a preregistered complete conflict universe. Nor is the pre-event close a guaranteed entry after the news. When an event happens overnight or on a weekend, an executable opening price can differ substantially. The resulting numbers describe index windows, not the profit from a trade placed after the event became known.

The raw-response SHA-256, request URL, event date, baseline and selected observations are recorded in the companion JSON. The content validator checks arithmetic, chronology and the saved file's digest. Those checks improve reproducibility; they do not prove that a political event caused the return or that the original daily data are free of every possible revision.

| Calendar anchor | Baseline close date | First observed session return | Fifth session return | Twentieth session return |
| --- | --- | --- | --- | --- |
| Iraq invasion anchor, 20 March 2003 | 19 March 2003 | 20 March: **+2.38%** | 26 March: **+0.35%** | 16 April: **+0.97%** |
| Russian invasion of Ukraine, 24 February 2022 | 23 February 2022 | 24 February: **+3.34%** | 2 March: **+5.48%** | 23 March: **+6.79%** |
| Israel/Hamas attack anchor, 7 October 2023 | 6 October 2023 | 9 October: **+0.39%** | 13 October: **−0.18%** | 3 November: **+0.35%** |
| Middle East conflict anchor, 28 February 2026 | 27 February 2026 | 2 March: **+0.36%** | 6 March: **−1.24%** | 27 March: **−7.59%** |

Event chronology is supported by the institutional discussions and official documentary records [S1–S4, S6, S7]. The returns are original calculations on actual downloaded FRED observations, not figures copied from a “war-trading pattern” advertisement. Values are rounded here; the JSON retains the underlying closes and unrounded calculations.

These observations already reject the categorical claim that every war headline must produce an immediate negative U.S. technology-index closing return. They do **not** establish the opposite rule that wars are bullish. A positive first session and a negative later window can both occur. Different instruments and observation horizons can tell different stories without either dataset being wrong.

## Application zone and the 100% question

**No war analogy or event window works 100% as a trade.** The useful application is scenario research that combines verified new information with actual instrument-specific evidence. The strongest use is identifying which channels deserve examination and which ordinary risk assumptions may fail. For example, a verified shipping disruption can motivate research on input costs and funding conditions. It cannot, by itself, identify a precise NAS100 entry and stop.

An applicable comparison matches exposures and prior expectations. Ask whether energy transport is actually threatened, whether the relevant country imports or exports that energy, whether inflation is constraining the monetary response, and whether the market had already priced a severe scenario. A forecast must also define the outcome horizon. Predicting an opening gap is a different problem from predicting the next twenty closing sessions.

Historical work can be used to design a candidate rule, but the rule needs separate chronological evaluation with costs and counterexamples. A history component receiving forty points in a confluence scheme should disclose the features and observations responsible for those points. The weight does not turn one selected comparison into forty percentage points of statistical confidence. Missing or incompatible features should reduce evidence or force `WAIT`, not be inferred from the conflict's name.

## Failure zones

**Event-time ambiguity:** news can arrive in stages and spread across time zones. A date in a newspaper's local edition can differ from the UTC date and the relevant exchange session. If the system cannot establish when information became available, it should not pretend an intraday entry was possible. The numerical windows here use documented calendar anchors and explicitly disclose their daily resolution.

**Expectation errors:** markets can respond positively to an outcome that is bad in absolute terms if a worse outcome had been expected. The reverse can happen after apparently favorable news that disappoints an optimistic consensus. HOSHI must avoid reading the emotional severity of a headline as an asset-return sign. It should seek evidence of the surprise and consider multiple plausible transmission paths.

**Instrument substitution:** a U.S. index is not a proxy for every local equity market, oil contract, exchange rate or token. Currency conversion, trading restrictions, settlement risk and sector composition matter. A backtest using an available American series cannot honestly claim that it reproduced a trade on an unavailable local or derivative instrument.

**Confounding and cherry-picking:** a twenty-session return can contain monetary decisions, earnings, economic releases and unrelated political developments. Picking the best entry date after inspecting the chart compounds the problem. A valid event study should fix its window rule, maintain the full sample and use a defensible comparison method if making causal claims. The simple table in this chapter intentionally does not make such a causal estimate.

**Execution and model risk:** overnight gaps, temporary closures and widening spreads can make a reference stop ineffective. Shorting can add contract, borrow and financing risks that a paper spot-long tool cannot model. A familiar chart pattern does not authorize the system to enable a new instrument, leverage or real orders. If a required live feed, risk input or supported contract is missing, the output remains unavailable or `WAIT`.

## Three real historical examples with dates

### Example 1 — Iraq event anchor, 20 March 2003

The downloaded NASDAQ Composite series rises from 1,378.57 on 19 March to 1,411.41 on 20 March, a first-session observation of approximately +2.38%. By the twentieth selected session, the return from that baseline is approximately +0.97% [S5]. These observations must not be described as a universal invasion rally. Rigobon and Sack's factor study and the RBA's contemporaneous discussion address changing risk and expectations using different approaches [S1, S2]. For HOSHI, the lesson is to separate a risk buildup, a new event and later developments. The event's name alone cannot select a short position or a ninety-two-percent confidence value.

### Example 2 — Ukraine invasion anchor, 24 February 2022

For the selected American index, the close rises from 13,037.49 on 23 February to 13,473.59 on 24 February, approximately +3.34%. The twentieth-session observation is positive relative to that baseline as well [S5]. This does not contradict the ECB's discussion of severe European risks and broader cross-asset repricing [S3]. The instruments, locations, horizons and questions differ. A responsible system should not overwrite the measured first-session result with a prewritten “war caused an immediate crash” story. It should retain both the observation and the limits on what that observation explains.

### Example 3 — Middle East event anchor, 28 February 2026

The ECB identifies the weekend event and uses the subsequent 2 March trading session in its analysis [S4]. The downloaded NASDAQ observations show approximately +0.36% for the first selected close, −1.24% at the fifth session and −7.59% at the twentieth, relative to 27 February [S5]. The changing signs demonstrate why the horizon cannot be omitted. They do not identify a trade that could have entered at the Friday close after a Saturday event. The historical chapter makes no assertion about the current state of hostilities, a guaranteed policy reaction or present trading levels.

## How to use it to HUNT a trade: an evidence-first procedure

1. **Verify the event and clock.** Obtain an original institutional release or other authoritative report. Record occurrence time, publication time, time zone, later corrections and whether the event is confirmed. Treat an unverified social-media claim as unverified information.
2. **Identify the actual supported market.** Name the venue, symbol, contract type, quote currency, trading calendar and live data source. If only BTC/ETH spot feeds are configured, do not fabricate a NAS100, gold or FX quote. Historical index knowledge is not current execution access.
3. **State the transmission hypothesis and alternatives.** Decide what new information would affect earnings, supply, discounting, funding or uncertainty. Record which observable developments would contradict the idea. Distinguish an adverse event from an adverse surprise.
4. **Compare more than the favorable analogy.** Use a versioned event table with comparable exposures, fixed windows and both positive and negative outcomes. Preserve event-selection rules and missing observations. A four-event educational table is not a validated forecasting dataset.
5. **Require present structure and liquidity confirmation.** Use genuine closed-candle timestamps and validated calculations. A historical story cannot create a missing pivot, market-wide liquidity map, order-flow reading or order-block confirmation. Explain missing evidence with a short reason rather than a fabricated confidence score.
6. **Build only a bounded paper hypothesis.** A candidate needs an invalidation level, adverse cost assumptions, realistic entry timing and an explicit loss budget. Simulate gaps and ambiguous bars, and reject a candidate whose estimated net reward does not justify its modeled loss. No historical resemblance overrides risk limits.
7. **Record outcomes prospectively.** Save the frozen rule, observation timestamp and eventual result, including abstentions and losses. Separate measured similarity, weighted rule coverage and any future calibrated probability. Do not present a plausible internal narrative as proof that a trade has a particular chance of winning.

The concise user-facing result may be a supported pair, `WAIT` or a labeled paper candidate, available reference levels, a timestamp and one brief explanation. Detailed teaching can be provided when requested. Concision must preserve the truth about data availability and uncertainty; it must not conceal that the historical analogy is weak or that the proposed instrument is unsupported.

## Sources

Original analysis and calculations, checked on 28 October 2026. The price observations are retrospective and contain no live signal or causal estimate.

- **S1:** Roberto Rigobon and Brian Sack, [The Effects of War Risk on U.S. Financial Markets](https://www.federalreserve.gov/econres/feds/the-effects-of-war-risk-on-us-financial-markets.htm), Federal Reserve research; findings are the authors' research conclusions.
- **S2:** RBA, [Statement on Monetary Policy, May 2003](https://www.rba.gov.au/publications/bulletin/2003/may/1.html), especially oil, uncertainty and international financial conditions.
- **S3:** ECB, [Financial Stability Review, November 2022](https://www.ecb.europa.eu/press/financial-stability-publications/fsr/html/ecb.fsr202211~6383d08c21.en.html), including Chart 2.2 and its defined invasion-related observation period.
- **S4:** ECB, [Financial Stability Review, May 2026](https://www.ecb.europa.eu/press/financial-stability-publications/fsr/pdf/ecb.fsr202605~50566915a7.en.pdf), especially the event-date notes and financial-markets chapter.
- **S5:** FRED, [NASDAQ Composite](https://fred.stlouisfed.org/series/NASDAQCOM); exact CSV request URLs, selected closes and response digests are recorded in `war_event_observations_20261028.json`.
- **S6:** United Nations, [October 2023 monthly documentary bulletin](https://www.un.org/unispal/document/october-2023-monthly-bulletin/), indexing institutional statements and the 7 October chronology.
- **S7:** Council of the European Union, [Middle East policy and official statements](https://www.consilium.europa.eu/en/policies/eu-position-situation-middle-east/), including the dated February–April 2026 statements. Their existence is not a real-time price feed.

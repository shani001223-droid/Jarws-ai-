# Market Crashes: Event History, Measurement and Failure-Aware Research

Document ID: `all_market_crashes`. Reviewed: **28 October 2026**.
Status: source-checked educational chapter; runtime integration is pending.
Scope: a selected, expandable crisis catalogue and a method for evaluating additional episodes. The filename is a curriculum category, not a claim that every local crash, security failure and intraday dislocation has been enumerated. A narrative event date, a price trough and an economic recession are separate observations.

## What is it?

A market crash is a severe price decline occurring over a specified interval, usually accompanied by unusually difficult trading conditions or a sudden reassessment of risk. There is no single threshold that makes every asset's decline a crash. A ten-percent move can be extraordinary for one instrument and an ordinary volatile period for another. Research therefore needs an explicit measurement rule rather than a dramatic label. The instrument, price convention, sampling interval, start rule and ending rule must be recorded before episodes are compared.

A **daily loss** compares one session's closing level with the previous session's close. A **peak-to-trough drawdown** compares a later low with a previously selected high. A **recovery period** ends when a chosen series regains a specified earlier level. These three quantities can differ by years. A price index, a dividend-reinvested return index and an inflation-adjusted purchasing-power series also have different recovery dates. HOSHI must name the measure instead of saying that a crash “lasted twenty-five years” when the statement actually refers to one nominal price index's return to an old high.

The drawdown calculation is `100 × (trough / peak − 1)`. The arithmetic recovery needed after a loss fraction `d` is `100 × (1 / (1 − d) − 1)`. In a purely illustrative example, a fifty-percent loss requires a one-hundred-percent gain to recover the starting amount. An eighty-percent loss requires a four-hundred-percent gain. These identities do not forecast how long recovery will take or establish that a failed security will recover at all.

## Why does it form? Mechanisms and feedback

A crash can reflect a change in expected cash flows, a change in discount rates, forced sales, impaired funding, uncertainty about counterparties, or a combination of these mechanisms. Distinguishing the initial shock from the amplification mechanism is essential. An earnings shock can start a decline; collateral calls can accelerate it; withdrawals can force further selling; and reduced willingness to make markets can make an otherwise modest order move prices substantially. Describing all of these stages as “fear” discards information needed for a testable hypothesis.

Consider a hypothetical leveraged investor whose collateral value falls. A lender may demand more margin. The investor might sell the asset that caused the loss, but might instead sell a different, more liquid holding. The second asset's decline need not mean its own fundamentals changed equally. A simultaneous fall in unrelated markets can therefore indicate common funding constraints. That explanation remains a hypothesis until exposures, funding conditions and actual market observations support it.

Price and liquidity can reinforce one another. Traders reduce quoted size when inventory is risky, stale prices become harder to hedge, and an order that would normally execute near the displayed market can cross several price levels. A historical closing-price chart does not contain all the information required to reconstruct an executable stop. A stop order is a trigger condition, not a guarantee of the eventual fill. A credible replay includes gap losses and states what it assumes when both stop and target fall inside one candle's range.

Policy can interrupt some feedback loops without reversing every underlying loss. Liquidity assistance addresses the ability to obtain funding or transact. It does not automatically make an insolvent borrower solvent, restore a lost business model or guarantee an immediate market bottom. The relevant research question is which constraint changed, when participants learned it, and how that compares with what had already been priced.

## Catalogue and measured observation windows

The following entries distinguish documentary chronology from calculations on downloaded observations. “Not measured here” is a data boundary, not a license to fill in a plausible return. The companion `market_crash_observations_20261028.json` records the FRED request windows and selected numerical observations used below.

| Episode | Instrument or evidence | Supported observation | Duration boundary |
| --- | --- | --- | --- |
| Dutch tulip speculation, early February 1637 | Archival historical research, not a modern equity index | Goldgar examines the collapse and the later mythology surrounding it [S1] | No continuous representative daily index or complete recovery series is supplied here |
| United States, 1929–1932 | Dow Jones Industrial Average price index | Federal Reserve History identifies a 381.17 close on 3 September 1929 and a 41.22 close on 8 July 1932; the decline was about 89% [S2] | Price recovery to the earlier high is reported for 23 November 1954; dividends and inflation are excluded |
| Black Monday, 19 October 1987 | Dow price index | One-session decline of 22.6% [S3] | A daily collapse is not the same as the entire later recovery period |
| Dot-com decline, 2000–2002 | NASDAQ Composite closing index, FRED `NASDAQCOM` | Downloaded window: 5,048.62 on 10 March 2000 to a later-window low of 1,114.11 on 9 October 2002, approximately −77.93% [S4] | 943 calendar days between these selected closes; no recovery date measured in this request window |
| Global financial crisis, 2007–2009 | Institutional chronology and economic activity | Mortgage-related stress, financial-institution distress and a deep recession [S5] | The eighteen-month recession ending June 2009 is not an equity-index drawdown duration |
| Pandemic drawdown, 2020 | S&P 500 closing price index, FRED `SP500` | Downloaded window: 3,386.15 on 19 February to a later-window low of 2,237.40 on 23 March, approximately −33.92% [S6] | 33 calendar days between those closes; the request through 1 April does not establish full recovery |
| Cross-asset repricing, 2022 | ECB November 2022 financial-stability review | The review documents declining asset prices, volatility, inflation and tighter conditions amid the war and energy shock [S7] | No single global crash duration or universally shared peak is assigned |
| Tariff-related repricing, April 2025 | RBA retrospective analysis dated 3 June 2025 | Equities declined following the 2 April announcements; the RBA's regional series had broadly regained their pre-announcement levels by its later review [S8] | Not a claim that each individual security recovered, or that the review date was the first recovery date |
| Financial vulnerabilities, 2026 | Federal Reserve May 2026 review, data cutoff 23 April 2026 | Elevated equity valuations and other vulnerabilities are described [S9] | A risk assessment is not proof that a particular crash occurred or a price trough was reached |

### What the downloaded numbers do and do not establish

The NASDAQ request covered 1 March 2000 through 31 October 2002 and yielded 671 numerical observations. The S&P request covered 1 February through 1 April 2020 and yielded 42 numerical observations. Missing holiday values were excluded. For each request, the maximum observed close was identified, then the minimum close at or after that observation within the requested window. That procedure establishes extrema **inside the declared window**, not extrema over all future history.

These are closing index levels, not trade executions, total returns, futures contracts, CFDs or a current NAS100 quote. They do not include the investor's fees, financing, dividends, taxes or currency translation. A hypothetical strategy that entered at a closing peak using knowledge of the later trough would be using future information. The arithmetic observations are useful for documenting events, but do not by themselves validate any entry rule.

The first NASDAQ download attempt was unavailable; a bounded later request succeeded. The failed attempt was not converted into a zero return. HOSHI should preserve that distinction in live operation: source failure means the requested measurement is unavailable until a valid response is obtained. It must never silently substitute another symbol, use an old cache without labeling it, or report a successful strategy test from a failed download.

## Application zone and the 100% question

**There is no crash pattern that works 100% as a trade.** This chapter is useful for classifying risk, examining execution assumptions and building conditional event studies. It is especially relevant when market functioning, leverage or funding pressure could invalidate ordinary backtest assumptions. It is less useful when a user expects the name of an old crisis to determine the next candle's direction.

An applicable historical comparison matches the instrument's economic exposure, policy regime, financing structure, trading hours, event surprise and observation horizon. The 1987 episode can motivate questions about feedback selling and liquidity. The global financial crisis can motivate questions about credit exposure and balance-sheet uncertainty. A pandemic shock can motivate questions about abrupt restrictions on activity and simultaneous demand for cash. The examples are starting points for different tests, not interchangeable members of a universal “crash pattern.”

Research must also include non-crash observations. If a model sees only famous failures, it cannot estimate how often similar warning signs occurred without a collapse. A useful event table includes warnings followed by stability, policy announcements followed by further losses, and apparent recoveries followed by renewed declines. Without that denominator, even a visually convincing historical match cannot justify a numerical win probability.

## Failure zones

**Hindsight-selected turning points:** a peak and trough can be identified after the fact even when no real-time rule could have recognized them. Backtests should generate decisions from point-in-time inputs, enter only after the trigger is known, and preserve all rejected or losing observations. A chart that draws a perfect entry at the final low is not evidence of an executable strategy.

**Wrong instrument or horizon:** a one-day Dow return does not describe the NASDAQ Composite, a leveraged NAS100 CFD or a cryptocurrency venue. A recession's beginning and ending months do not identify an equity drawdown. A market can rise while economic data remain weak because the price reflects expected future developments. HOSHI must not force these distinct clocks into a single duration field.

**Unobserved execution:** market closures, price limits, halted instruments, spreads, order-size constraints and inaccessible liquidity can dominate the result. A candle touching a target does not prove the entire hypothetical order filled there. Short selling adds borrow, recall, financing and contract issues that a long-only spot simulator does not represent. A price-history chapter supplies none of those missing capabilities.

**Misleading causality:** a war, earnings release, policy action and funding shock can overlap. Assigning the entire period's price change to one headline overstates what the observation establishes. Likewise, a report describing vulnerability does not predict the exact date of a collapse. Recent 2025–2026 observations must retain their publication dates, data cutoffs and measured windows; later information cannot be smuggled into an earlier signal.

**Survivorship and selective memory:** looking only at an index that eventually recovered can conceal securities that disappeared. A modern index contains a changing set of constituents. Research needs the correct historical composition when evaluating security selection, rather than applying today's survivors to an old crisis. Famous examples also receive more attention than quiet periods, so an anecdotal catalogue is not a representative statistical sample.

## Three real historical examples with dates

### Example 1 — Dow decline, 28–29 October 1929

Federal Reserve History records falls of nearly 13% and nearly 12% on the two successive dates [S2]. The catalogue separately records the later trough and nominal price recovery. The research lesson is to separate an acute shock from a prolonged drawdown and from the surrounding economic contraction. A new model must not treat the eventual 1932 low as information available in October 1929. It must specify which observations would have triggered risk reduction and what would have invalidated that decision. The documented past does not imply that every future two-day decline will become a depression.

### Example 2 — Black Monday, 19 October 1987

The documented one-session Dow loss was 22.6% [S3]. The same institutional account describes feedback selling, market-structure weaknesses and a liquidity response. The appropriate hypothesis is conditional: under what observed financing and execution conditions could selling amplify itself? The event does not establish that all automated strategies are harmful, that every apparent liquidity sweep predicts a reversal, or that the rebound could be captured without execution risk. A simulator should stress gaps and uncertain intrabar order instead of assuming a stop always limits the loss to its displayed reference level.

### Example 3 — S&P 500 window, 19 February–23 March 2020

The independently downloaded FRED request supports the approximately 33.92% closing-index decline over 33 calendar days stated above [S6]. The calculation is reproducible from the recorded endpoints and formula. It does not identify a profitable decision rule. To investigate a candidate strategy, freeze its pre-entry features and evaluate later returns after costs across both crisis and ordinary periods. Do not label 23 March the obvious buying opportunity at the time simply because it is the later-window minimum. Recovery beyond the request's ending date remains outside this particular measurement.

## How to use it to HUNT a trade: conditional investigation

1. **Define the event before matching it.** Record whether the shock is a verified announcement, a funding disruption, a measured price decline or merely an inferred risk. Use the actual release timestamp and the instrument's trading calendar. If there is no supported current data feed, say that the price-based assessment is unavailable.
2. **Choose the benchmark and horizon.** Specify the precise index, contract or spot pair and whether the outcome is the next bar, session, week or longer period. Define price or total return and the reference currency. A historical return from the wrong series is not a substitute for missing data.
3. **Write competing hypotheses.** A sell-off might continue through forced liquidation, stabilize after funding conditions improve, or reverse as expectations change. Name observable conditions favoring each scenario and conditions invalidating the intended setup. Abstaining is a valid outcome.
4. **Require current structure and liquidity evidence.** A historical resemblance may select an experiment for attention, but cannot manufacture a present support level, stop location or market-wide order map. Use confirmed closed-candle observations and distinguish a pivot reference from actual resting liquidity.
5. **Stress the paper execution.** Model a next-available entry, adverse costs, gaps through the stop, ambiguous bars, position limits and the inability to transact during halts. If these assumptions erase the planned reward-to-risk ratio, reject the setup rather than improving the backtest with optimistic fills.
6. **Keep the full experiment record.** Preserve source URLs, retrieval times, dataset identity, rules, assumptions, chronological evaluation windows, rejected candidates and losses. A similarity weight can be a transparent evidence score; a probability requires independently evaluated outcomes and calibration. This catalogue alone supplies neither a reliable win rate nor authority to place an order.

The useful output is an auditable paper-research decision, including `WAIT` when evidence is insufficient. More historical detail should improve the quality of questions and error detection. It should not conceal uncertainty behind a dramatic crisis name or a precise-looking confidence percentage.

## Sources

Original synthesis, with source facts and calculations kept distinct. Sources and downloaded observations were checked on 28 October 2026.

- **S1:** Anne Goldgar, [Tulipmania: author excerpt](https://press.uchicago.edu/Misc/Chicago/301259.html), University of Chicago Press; distinguishes archival research from repeated legends.
- **S2:** Federal Reserve History, [Stock Market Crash of 1929](https://www.federalreservehistory.org/essays/stock-market-crash-of-1929).
- **S3:** Federal Reserve History, [Stock Market Crash of 1987](https://www.federalreservehistory.org/essays/stock-market-crash-of-1987).
- **S4:** FRED, [NASDAQ Composite series](https://fred.stlouisfed.org/series/NASDAQCOM), with the [declared CSV request](https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM&cosd=2000-03-01&coed=2002-10-31); selected observations and arithmetic stored in the companion JSON.
- **S5:** Federal Reserve History, [The Great Recession and Its Aftermath](https://www.federalreservehistory.org/essays/great-recession-and-its-aftermath).
- **S6:** FRED, [S&P 500 series](https://fred.stlouisfed.org/series/SP500), with the [declared CSV request](https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500&cosd=2020-02-01&coed=2020-04-01); selected observations and arithmetic stored in the companion JSON.
- **S7:** ECB, [Financial Stability Review, November 2022](https://www.ecb.europa.eu/press/financial-stability-publications/fsr/html/ecb.fsr202211~6383d08c21.en.html).
- **S8:** Reserve Bank of Australia, [Joining the Dots, 3 June 2025](https://www.rba.gov.au/speeches/2025/sp-ag-2025-06-03.html), especially the discussion of April tariff announcements and Graph 2.
- **S9:** Federal Reserve Board, [Financial Stability Report, May 2026: overview](https://www.federalreserve.gov/publications/2026-may-financial-stability-report-overview.htm), data cutoff 23 April 2026.

# Global Money Flow: Dollar, Bonds, COT and Intermarket

Knowledge version: `hoshi-trading-knowledge-v2`. Language: English definitions with Roman Urdu-ready explanations.

## Evidence boundary

Educational knowledge, not a signal or a win-probability model. Prices, stops,
position sizes and outcomes must not be invented. Each link below opens a live
chart for inspection; the conditional walkthrough is **not a verified live
pattern detection**, replay result, or recommendation. Record venue, symbol,
timeframe, closed-candle UTC timestamps, timezone and source retrieval time
before calling an observation current. Reject missing/stale candles. Multiple
features derived from one OHLCV history are correlated evidence.

## Definition

Intermarket research compares currencies, rates, equities, commodities and
crypto across matched timestamps. ICE DXY is a specific currency basket; the
Fed's broad trade-weighted dollar index is a different series, NOT DXY. Treasury
yields and prices usually move inversely for a fixed bond, but duration, coupon
and maturity matter. COT classifies reportable futures positions, not all global
capital flows or real-time spot positioning.

## Application Zone

Use named primary series, units, release time, observation date and revision
status. Compare rolling returns/correlations rather than assuming a permanent
BTC-dollar inverse relationship. CFTC COT ordinarily publishes Friday 15:30 ET
with the preceding Tuesday's positions; holidays can delay it. Use it as lagged
context. Hoshi currently has no live DXY/bond/COT ingest and must say unavailable.

## Failure Zone

Correlation changes by regime. Daily bond/dollar data cannot confirm a 15m
entry, and a delayed report must not be backdated into a backtest. Nominal yields
are not real yields. Risk-off moves can raise both dollar and demand for bonds;
crypto can decouple. Do not fabricate current COT values, Fed actions or news.

## 3 Live Chart Examples

1. **[Fed broad dollar (daily; not ICE DXY)](https://fred.stlouisfed.org/series/DTWEXBGS)** — Open the Fed broad dollar index and a BTC chart at matched daily closes. Test a declared rolling-return window; label the dollar series correctly and do not call it ICE DXY.

2. **[US 10-year yield (daily)](https://fred.stlouisfed.org/series/DGS10)** — Open the daily 10-year constant-maturity yield. Record percent units and observation date; a yield rise is not a live Treasury price quote or an automatic crypto short.

3. **[COT futures positioning (weekly)](https://www.cmegroup.com/tools-information/quikstrike/commitment-of-traders.html)** — Open the CFTC release schedule and CME positioning chart. Record both position-as-of Tuesday and publication Friday; any replay decision before publication must not use that report.

## Dated source observations — 27 October 2026

These three examples add actual source observations to the conditional chart
walkthroughs above. They are **point-in-time measurements**, not a claim that a
profitable setup exists now. After this date, treat them as historical examples.
[Captured values, timestamps, source/replay URLs and series digests](chart_examples_snapshot_20261027.json)
are retained for review. The macro series are daily/weekly and lag retrieval.
For 1h/4h OB/FVG observations the same geometric detector is demonstrated on
that frame; the actual V2 API uses 15m for entry-pattern checks.

| Chart / series | Closed bar / observation date | Observed fact and limit |
| --- | --- | --- |
| Fed broad dollar, daily | 2026-10-23 | DTWEXBGS = 121.3202 (Jan 2006=100), retrieved 27 Oct. Different basket from ICE DXY; no current 15m dollar signal. |
| US 10-year yield, daily | 2026-10-23 | DGS10 = 5.00 percent, retrieved 27 Oct; observation date precedes retrieval. This is a yield, not a tradable bond price. |
| CFTC Euro FX, weekly | positions 2026-10-20 | Noncommercial long 226,421 vs short 360,945; computed net -134,524 contracts. Open interest 877,940. Retrieved 27 Oct from the primary report; publication time is not established by that page, so do not backdate availability. |

## Sources and attribution

- https://fred.stlouisfed.org/series/DTWEXBGS
- https://fred.stlouisfed.org/series/DGS10
- https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
- https://www.cmegroup.com/tools-information/quikstrike/commitment-of-traders.html

SMC/ICT descriptions above are HOSHI operational heuristics, not certified exchange facts or evidence of predictive accuracy. Source educators may make stronger claims; those claims are not adopted here.

Primary positioning data for the dated example: https://www.cftc.gov/dea/futures/deacmesf.htm

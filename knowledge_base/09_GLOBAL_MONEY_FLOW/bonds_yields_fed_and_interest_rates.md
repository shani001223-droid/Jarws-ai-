# Bonds, yields, Federal Reserve decisions and interest-rate evidence

Reviewed on 28 October 2026. Historical rate levels below are percent per
annum from attributed Federal Reserve statistical series retrieved through
FRED. They are neither live quotes nor bond-price returns. Original
publication vintages, client arrivals and executable bond/futures prices
were not reconstructed. All diagnostic decisions remain `WAIT`.

## What is it?

A bond is a claim on specified cash flows subject to its contractual terms
and relevant risks. Its price is the present value the market assigns to
those flows. A yield summarizes that pricing under a particular convention;
it is not the same object as the price, coupon, realized holding-period
return or a central bank's policy target.

For fixed cash flows and a single discount-yield convention, increasing the
discount yield reduces present value. That conditional relationship does
not imply that a central-bank rate cut must raise every bond price. A
longer-term yield reflects expected future short rates and compensation for
bearing risk over time. Market expectations and risk compensation can change
in ways that differ from the latest overnight policy decision.

The FOMC announces a target range for the federal funds market. Actual
overnight transactions generate an effective rate. The New York Fed describes
the current effective federal funds rate as a volume-weighted median, with
publication for the prior business day. The Board's H.15 notes identify the
March 2016 change from an earlier mean-based method. Method versions matter
when comparing long historical samples.

Hoshi's retained observations are Board H.15 series `DFF`, `DGS2`, `DGS10`
and `DFII10`: federal funds effective rate, nominal two-year and ten-year
constant-maturity Treasury yields, and a ten-year inflation-indexed yield.
The source `DFF` is explicitly a daily seven-day series. It is not relabelled
as the separate FRED `EFFR` feed, whose rights metadata and publication channel
differ. Actual provider-supplied weekend labels in DFF are preserved rather
than being invented by Hoshi's forward-fill code.

## Why does it form?

Interest rates connect the value of money across time. A borrower and lender
consider liquidity needs, expected future conditions, credit risk, collateral
and alternative investments. Central-bank implementation tools influence
short-term funding conditions, while market participants continually reprice
future paths. An announcement already expected by participants can produce
a different response from a similarly sized surprise.

This distinction explains why “the Fed cut, therefore yields fall” is
incomplete. The decision, accompanying statement, growth outlook, inflation
news, supply expectations and required compensation can all change together.
A lower policy target can coexist with a higher ten-year yield. The
historical examples below demonstrate that coexistence without claiming to
identify which explanation dominated.

Different maturities also respond differently. A two-year yield and a
ten-year yield need not move by the same number of basis points. Their
spread can steepen or flatten even when both yields rise, and the same
spread change can arise when both fall. A curve label should preserve both
legs and their changes, not just a color-coded slope.

Inflation-linked securities add another distinction. TreasuryDirect describes
TIPS principal as adjusted for inflation, with interest paid on adjusted
principal. A real yield is not a realized future purchasing-power outcome
for every possible holding period. Market liquidity, inflation risk
compensation, indexation and the purchase/sale prices affect interpretation.
The nominal-minus-real spread is therefore a useful descriptive proxy,
not a pure forecast of future CPI.

## Application zone

### Keep units and instruments explicit

One percentage point equals one hundred basis points. Moving from 3.65%
to 3.73% is an eight-basis-point increase. It is not an eight-percent bond
price gain, and it is not the relative percentage increase of the yield
itself. The replay calculates `100*(ending_percent-starting_percent)` and
exports the result with a basis-point label.

A local price approximation for a fixed-rate bond is
`change_in_price/price ≈ -modified_duration*change_in_yield`, with yield
expressed as a decimal. A convexity term can improve that approximation.
It still needs the actual security, duration, cash flows, valuation convention
and yield-curve movement. No duration or price is inferred from the name
“ten-year constant maturity.” The receipt leaves bond-price returns null.

Constant-maturity yields describe curve-based rate observations, rather than
a continuous holding in a single identified Treasury security. A futures
contract introduces its own deliverable basket, expiry, conversion factors,
margin and basis. A Treasury ETF has expenses, distributions and portfolio
changes. Those products cannot silently inherit a rate-series change as
their executable return.

### Read the curve and real-rate proxy together

The original diagnostic computes `DGS10-DGS2` in basis points at the exact
requested dates. It also computes `DGS10-DFII10`, naming it a nominal-minus-real
ten-year proxy. A missing value in either leg leaves the corresponding
spread unavailable. Negative observed real yields are valid data, not missing
values to discard or convert to zero.

The Federal Reserve's yield-curve research pages explain fitted curves and
inflation compensation, while identifying revision and research-model
limitations. A San Francisco Fed research letter dated 20 June 2011
separately explains inflation-risk and relative-liquidity components. Those
sources support the interpretation caution; Hoshi's simple H.15 subtraction
does not replicate their fitted-curve or decomposition models.

### Separate policy, observation and availability clocks

The three official FOMC statements provide dated release times. Those times
are different from the daily statistical observation labels and from the
time FRED later served the data. The current H.15 page describes a scheduled
business-day publication process with holiday/closure exceptions. The
New York Fed's effective-rate page describes publication for the prior
business day at approximately 09:00. Neither generic rule reconstructs
every historical actual arrival or revision.

The raw CSVs, request bounds, source IDs and digests in the macro receipt
are later captures on 28 October 2026. They preserve what was retrieved,
not an independently verified real-time stream from the event year. A
decision earlier on a date cannot assume that date's final yield or
effective-rate value was already public. All original arrival fields remain
null and the current cases estimate no causal policy effect.

## Failure zones

**Conflating the target and effective rate:** a target is an announced
policy setting; effective funding statistics reflect transactions and
publication conventions. A market rate need not equal a target bound.
Do not stamp a target change onto every maturity or equate a daily effective
rate with an intraday funding quote.

**Confusing a forecast and compensation:** a nominal-real difference can
include expected inflation and risk/liquidity effects. Subtracting two
series does not reveal each unobserved component. It cannot establish that
a one-basis-point change represents precisely that much change in expected
future CPI.

**Treating inversion as a timer:** a negative selected curve spread is a
descriptive state, not an exact countdown to a recession, equity crash or
profitable short. Maturity choice, observation window and other conditions
matter. The studies here do not estimate an inversion alarm or its false
positive rate.

**Ignoring security-specific losses:** holding a bond to maturity under
specified terms differs from selling it tomorrow. Duration, credit, liquidity,
collateral and currency exposures can matter before maturity. A historical
rate-level observation supplies none of the queue, quote or transaction-cost
evidence required to claim a fill.

**Reading a daily event window causally:** other news occurs during the
window, and market prices can anticipate the decision. The start/end
comparisons do not isolate the announcement's surprise, information effects
or later data releases. No trading pattern works 100%; a familiar rate-cut
headline is not a calibrated confidence score.

## Three real historical examples with dates

These are exact requested daily windows around three primary-source FOMC
announcements, not high-frequency event studies. Series are in percent per
annum. Policy target ranges and release clocks come from the statements;
daily observations come from the separately hashed statistical captures.

### Example 1 — 13–20 March 2020: funding rates and real yields move differently

The 15 March 2020 FOMC statement was released at 17:00 EDT, or 21:00 UTC,
and announced a target range of 0–0.25%. It also described actions supporting
Treasury and agency-MBS market functioning. That is a Sunday announcement;
it should not be mistaken for an ordinary daily cash-market close.

Across the fixed 13–20 March statistical window, DFF falls from 1.10%
to 0.15%, a 95-basis-point decline. The two-year nominal Treasury series
falls from 0.49% to 0.37%, twelve basis points; the ten-year nominal series
falls from 0.94% to 0.92%, two basis points. The ten-minus-two spread
therefore rises from 45 to 55 basis points.

Meanwhile, the ten-year real-yield series rises from 0.04% to 0.17%, thirteen
basis points. The simple nominal-minus-real proxy falls from 90 to 75 basis
points. Thus easing overnight conditions and a rising real-yield observation
coexist in this selected stress window. Those facts do not identify a bond's
realized return or isolate why TIPS and nominal securities repriced. The
current source history and missing original arrivals cannot support an
intraday gold or NAS100 entry based on this comparison.

### Example 2 — 15–18 March 2022: the curve flattens while the policy rate rises

The 16 March statement, released at 14:00 EDT or 18:00 UTC, raised the
federal-funds target range to 0.25–0.50%. It discussed elevated inflation
and uncertainty surrounding Russia's invasion of Ukraine. Those are
documented statement contents, not Hoshi's causal allocation of market returns.

From 15 to 18 March, DFF rises from 0.08% to 0.33%, twenty-five basis
points. The two-year yield rises from 1.85% to 1.97%, twelve basis points,
while the ten-year yield falls from 2.15% to 2.14%, one basis point. The
ten-minus-two spread narrows from 30 to 17 basis points. A short policy
decision and the longer yield do not have the same direction in this window.

The real ten-year series moves from negative 0.69% to negative 0.72%, a
three-basis-point decline. The nominal-real proxy consequently rises from
284 to 286 basis points. Discarding negative real yields would destroy this
calculation. The proxy's two-basis-point rise is not a measured two-basis-point
change in expected CPI and does not establish the next move of a currency,
equity index or commodity.

### Example 3 — 17–20 September 2024: a fifty-basis-point cut with a higher ten-year yield

The FOMC statement released on 18 September at 14:00 EDT, or 18:00 UTC,
announced a half-percentage-point target reduction to 4.75–5.00%. Its
statement addressed progress on inflation and the balance of employment
and inflation risks. The release and source windows are dated precisely;
no later statement is inserted into the earlier decision.

DFF falls from 5.33% on 17 September to 4.83% on 20 September, fifty basis
points. Yet the ten-year nominal yield rises from 3.65% to 3.73%, eight basis
points, while the two-year yield falls from 3.59% to 3.55%, four basis
points. The ten-minus-two spread steepens from six to eighteen basis points.

The real ten-year series rises from 1.53% to 1.58%, five basis points, and
the nominal-real proxy rises from 212 to 215 basis points. These are genuine
counterexamples to a rule that every maturity's yield must fall after a
policy cut. They do not prove a profitable short-bond strategy: the dataset
contains no tradable security price, duration, entry timing, spread or fee
path. All bond-price-return fields remain null.

## How to use it to HUNT a trade

Identify the precise question: policy surprise, future-rate expectations,
curve slope, real-yield context or security-specific valuation. Select the
appropriate public and permitted source, units and horizon. Keep an
announcement timestamp separate from the observation and original publication
times of statistical inputs. If those availability requirements are missing,
the historical feature is unsuitable for an earlier simulated decision.

For paper research, freeze the curve legs, thresholds, entry instrument,
cancellation rule and observation cutoff. Require actual current supported
venue quotes, realistic costs and bounded risk before proposing levels.
Do not convert a ten-year yield into a fabricated gold, BTC or NAS100 price.
A local structure/liquidity setup needs its own evidence.

Evaluate later on untouched chronological periods with revisions, unexpected
decisions, nonparallel curve moves, missing inputs and no-trade outcomes.
Retain negative results and quantify costs, ambiguity and drawdown only from
actual computations. Hoshi's eventual evidence weights remain rule coverage,
with `win_probability=null` until independently calibrated. This chapter is
source knowledge; runtime retrieval, causal replay and final integrated
release checks are still pending.

## Sources

Primary sources actually checked on 28 October 2026; report facts are
paraphrased briefly, with original arithmetic above:

1. Federal Reserve statements: [15 March 2020](https://www.federalreserve.gov/newsevents/pressreleases/monetary20200315a.htm),
   [16 March 2022](https://www.federalreserve.gov/newsevents/pressreleases/monetary20220316a.htm),
   [18 September 2024](https://www.federalreserve.gov/newsevents/pressreleases/monetary20240918a.htm).
   Release clocks and announced ranges, not causal return estimates.
2. [H.15 release and technical notes](https://www.federalreserve.gov/releases/h15/)
   and public-domain-tagged source metadata for [DFF](https://fred.stlouisfed.org/series/DFF),
   [DGS2](https://fred.stlouisfed.org/series/DGS2), [DGS10](https://fred.stlouisfed.org/series/DGS10)
   and [DFII10](https://fred.stlouisfed.org/series/DFII10).
   Board of Governors data via FRED; citation requested.
3. New York Fed, [effective-rate methodology/publication description](https://www.newyorkfed.org/markets/reference-rates/effr).
   Methodology attribution only; the separate copyrighted EFFR array is not
   republished as a public-domain series.
4. TreasuryDirect, [TIPS terms](https://www.treasurydirect.gov/marketable-securities/tips/).
   Instrument explanation, not a security-specific return model.
5. Federal Reserve, [TIPS yield-curve research and inflation compensation](https://www.federalreserve.gov/data/tips-yield-curve-and-inflation-compensation.htm),
   and Christensen/Gillan, [SF Fed Economic Letter, 20 June 2011](https://www.frbsf.org/research-and-insights/publications/economic-letter/2011/06/tips-liquidity-breakeven-inflation-expectations/).
   Risk/liquidity and revision caveats; no fitted-model replication claimed.
6. [Exact rate captures and calculations](macro_observations_20261028.json)
   and [original replay arithmetic](../../scripts/v3_macro_evidence.py).
   Daily source labels and later capture clocks remain distinct.

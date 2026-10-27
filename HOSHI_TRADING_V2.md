# HOSHI trading knowledge and confluence V2

Development extension of the existing assistant on PR #24. Source delivery is
not Render deployment or physical Realme Note 50 acceptance. No new AI key,
paid model, exchange account or real order capability is introduced.

## Files and deployment

- `modules/trading_history_complete.md`: corrected historical timeline.
- `modules/01_*.md` through `10_*.md`: definitions, application/failure zones
  and **30 conditional linked live-chart inspection exercises**. These are not
  claims of currently detected profitable setups or completed chart replay.
- `cloud_backend/brain.py`: bounded integrity-checked load of all eleven
  lessons; relevant two-lesson retrieval for trading chat, including short
  Groq voice requests. Model weights are not trained or replaced.
- `HOSHI_SYSTEM_PROMPT_FINAL.txt`: versioned supplemental system policy used
  by the actual assistant providers along with existing persona/language rules.
- `cloud_backend/strategy_engine.py`: deterministic closed-bar heuristic score.
- `cloud_backend/main.py`: extends the existing app rather than a second server.

After editing canonical Markdown or the final prompt, run:

```bash
python -m pip install -r requirements-dev.txt
python scripts/build_trading_knowledge.py
python scripts/build_trading_knowledge.py --check
python -m unittest discover -s tests -p 'test_*.py'
```

`cloud_backend/knowledge_bundle.json` is a generated snapshot with per-file
SHA-256 digests. Corpus parity is checked in tests and CI. The Dockerfile copies
it because Render's existing build root is only `cloud_backend/`. The `tzdata`
dependency supplies New York timezone definitions on images without a system
timezone database. The loader accepts fixed lesson IDs, never user paths/URLs.

## New HTTP API

| Request | Result |
| --- | --- |
| `GET /history` | Market timeline; **not private conversation history** |
| `GET /learn` | Eleven fixed lesson IDs/titles/digests |
| `GET /learn?module=ict` | A complete lesson with integrity metadata |
| `POST /learn` with `{"module":"ict"}` | Same read-only selection; extra fields rejected |
| `GET /confluence_score?symbol=BTCUSDT&direction=long` | Server-fetched closed-candle research score |

Lesson IDs: `history`, `market_structure`, `candlestick_psychology`,
`order_blocks`, `smc`, `ict`, `liquidity`, `fvg_imbalances`,
`indicators_order_flow`, `global_money_flow`, `risk_psychology`.

Confluence accepts only `BTCUSDT` / `ETHUSDT` and `long` / `short` descriptions.
`short` is a bearish chart study; it does not add short-selling or futures.
Clients cannot provide pass flags, current time or an authoritative score.
The backend reuses the existing bounded public data cache/research semaphore
and fixed Binance Spot URLs. Responses use no-store/no-sniff headers. Busy =
429; unsupported inputs = 422; missing lesson = 404; invalid/stale source or
unavailable trusted knowledge = 503. Source errors never become fabricated scores.

## Exact five-factor score (version `hoshi-confluence-v2`)

| Factor | Points | Reproducible condition |
| --- | --- | --- |
| HTF trend | 20 | Both 1h and 4h confirmed 2-left/2-right HH/HL plus close > EMA20 > EMA50 for long; mirrored LH/LL and EMA test for short |
| Liquidity reference / target | 20 | A last-12-bar 15m wick penetration and closed reclaim of the most recent pivot confirmed **before** that bar, plus a still-unbreached confirmed opposing 1h pivot beyond current 15m close |
| Location + OB | 20 | Current close inside the latest confirmed 1h high/low range, discount (long) or premium (short) relative to its midpoint, plus current bar overlap with a still-valid OB belonging to a retested gap |
| FVG retest | 20 | A confirmed three-bar nonzero wick gap, displacement body >=1.5x preceding 20-body mean and close beyond prior five-bar extreme, then a **later** partial gap retest closing on the directional half; full mitigation invalidates |
| Time window | 20 | Weekday America/New_York local time within London 02–05, New York 07–10, Silver Bullet AM 10–11 or PM 14–15; end times excluded and DST converted |

OB is the **full wick range** of the most recent opposite candle among the
five bars preceding displacement. Its long close-below-low / short
close-above-high invalidation is evaluated after formation. Gap search is
bounded to the most recent 64 bars. All computations use already closed
15m/1h/4h candles; malformed, gapped, nonfinite, oversized, future or stale
histories fail validation. No pivot is available before its two right bars
close. The engine never uses a gap's formation bar as a later retest.

**Score = sum of five passed weights, 0 to 100.** It is deliberately named
`weighted_rule_coverage_not_win_probability`; `win_probability` is null.
All five matching yields `paper_watchlist_only`; any missing factor yields
`wait`. Neither response is an entry, stop/TP plan or order. The score does not
replace the older six-family setup endpoint, which stays available unchanged.

## Limits that must remain visible

SMC/ICT/OB/liquidity labels are explicit operational hypotheses, not evidence
of institutional intent or actual resting orders. Five factors from the same
venue are correlated. No independent Kraken certification is inherited from
the separate data-quality endpoint. OHLCV is not full order flow; live COT,
DXY, bond prices and economic-calendar inputs are not ingested by this change.
Time windows are HOSHI's versioned convention and are unvalidated for crypto;
weekends and holidays require separate treatment. Ordinary chat receives
educational knowledge, **not automatically attached live market candles**.

No 99.999% accuracy, calibrated confidence, alpha, profit, HFT latency or
out-of-sample performance claim is made. Walk-forward validation, execution
cost studies, independent live data and production/device QA are outstanding.

## Verification evidence

See [AUDIT_REPORT.md](AUDIT_REPORT.md) for exact commits, checks and limitations.
New tests distinguish actual five-rule calculations on labelled **synthetic**
fixtures from current market observations, verify long/short symmetry,
invalidation, absent/malformed sources, NY summer/winter boundaries, knowledge
tampering/parity, API input validation and both full/fast provider integration.

# Hoshi Market Structure Research (Task 38)

Development-only, read-only, no account actions or orders. Source: `cloud_backend/market_structure.py`, endpoint `GET /api/trading/structure?symbol=BTCUSDT` (also ETHUSDT), regression `tests/test_market_structure.py`.

## What it calculates

For each of **15m, 1h and 4h**, fetch 65–500 Binance Spot public bars through the existing bounded, cached `_research_history` reader. That reader rejects stale, malformed, gapped or still-forming candles. The analysis uses only those validated **closed** bars. It finds strict local swing highs/lows: a candidate needs two preceding and **two subsequently closed** bars to confirm, and equal highs/lows are not swings. Last two closed candles cannot themselves be confirmed pivots.

The last two confirmed highs and lows determine descriptive higher-high/higher-low, lower-high/lower-low, mixed or insufficient structure. The latest confirmed low at or below price is support; the latest confirmed high at or above price is resistance. If none qualifies, the corresponding level is **null**, not a guessed future target. Prior-20-bar extremes exclude the most recent candle. Every returned swing has pivot and confirmation timestamps. Timeframes align only when all three individually agree; a mixed or insufficient result is explicitly reported, never forced into a trade.

## Trust boundary and limitations

This endpoint uses **one Binance Spot venue**, not the independent Binance/Kraken quality gate at `/api/trading/data-quality`. It is therefore labeled `independently_cross_checked: false`; no cross-exchange confirmation or live production availability is claimed. Request concurrency, upstream timeouts and 120-second source freshness are bounded. No user-provided URL, API key, leverage, futures position, buy/sell recommendation, automatic order, publishing or paid API is involved.

The calculation is a descriptive historical heuristic, **not** an accurate prediction, a validated profitable strategy or proof that S/R will hold. Two-right-bar pivot confirmation necessarily lags. The server may be blocked by provider/network limits. Browser/Android production acceptance and Realme Note 50 QA remain separate. Do not merge or deploy without explicit authorization.

## Verification

Full Python/Node/Playwright and Docker backend CI links are recorded in the **only** canonical task scoreboard `HOSHI_60_TASK_MASTER_ROADMAP.md` once the final source/test commit passes. CI uses deterministic fixtures and does not prove live Binance access.

# HOSHI Task 42 — annotated spot charts (development)

This implementation adds **actual 1000×620 PNG chart rendering** and JSON analysis export, from the existing strict Binance Spot closed-candle reader, not the looser public market-chart endpoint.

- GET /api/trading/annotated-chart?symbol=BTCUSDT&interval=15m&output=json returns up to 96 closed timestamped OHLCV candles, base volume, confirmed 2-left/2-right pivots and confirmed support/resistance, with source fetch time and an explicit single-venue disclaimer.
- output=png returns a bounded real PNG with candle bodies/wicks, relative base-volume bars, confirmed pivot markers and S/R lines. Hypothetical paper entry/stop/TP1/TP2 overlays appear **only** on 15m when Task 41 returns paper_plan_only from the same three-timeframe snapshot; WAIT never invents them.
- BTCUSDT and ETHUSDT only; 15m, 1h, 4h only. Invalid pair: HTTP 422 before network. Stale/missing/invalid provider history: HTTP 503, no chart. Both formats are read-only and no-store. Separate JSON and PNG requests can have different source timestamps; compare them before treating them as the same snapshot.
- No real trades, accounts, leverage, paid APIs, image uploads or extra model. Uses the existing Pillow dependency. This is single Binance venue, not independent Kraken certification.

**Acceptance pending:** Full GitHub Python/Node/Playwright and Docker checks, mobile UI preview/download integration and physical Realme Note 50 testing. Keep canonical Task 42 unchecked until relevant verification is complete.

# Hoshi Task 40 — six-family spot setup assessment (development only)

`GET /api/trading/setup-assessment?symbol=BTCUSDT` accepts only BTCUSDT or
ETHUSDT and reads the same three 15m/1h/4h closed Binance Spot histories
for Task 38 confirmed structure and Task 39 indicators. The API is read-only,
uses the existing bounded research slots, 120-second fetch-age guard,
no-store/no-sniff response headers and returns 422 for unsupported pairs,
429 when busy or 503 for stale/malformed sources. There is **no order API**.

## Version `spot-setup-assessment-v1`

A `paper_watchlist_only` decision requires **all six** of the following:
1. Confirmed 2-right-bar swing structure is higher-highs/higher-lows on all
   three timeframes (Task 38).
2. EMA9 > EMA21, EMA20 > EMA50 and latest close > EMA20 on all three
   timeframes (Task 39).
3. RSI14 in [52,68] on 15m and [50,75] on 1h/4h.
4. 15m base-volume ratio to its latest 20-bar SMA >= 1.2, with positive
   baseline volume.
5. 15m close above a **complete** UTC-session HLC3 VWAP. Missing opening
   bar or zero session volume means no VWAP confirmation.
6. 15m ATR14 as a percent of latest close between 0.05% and 5% inclusive.

Otherwise decision is `wait`. Every family has a fixed safe reason code and
a support/does-not-support flag; `positive_families` is an evidence count,
**not** a calibrated confidence or win probability. Any invalid source
identity, mismatched candle timestamp/close, missing frame, nonfinite value,
unverified formula version or corrupted history fails closed instead of
issuing a watchlist signal. No entry/stop/TP, leverage, short, trade execution,
notification, auto-worker, provider key, posting or real trading is added.

These families share the same Binance candles and are **correlated**, not
independent exchanges, independent statistical samples or validated alpha.
The Task 37 Binance/Kraken quality check remains separate and does **not**
certify this result. This is a deliberately strict, uncalibrated long-only
paper **watchlist** filter, not a trade recommendation or a demonstrated
profitable strategy. Task 41 must independently assess paper-only risk,
stops/targets and fees. Backtests, walk-forward evaluation and out-of-sample
acceptance are still pending. Physical Realme Note 50, live provider access,
Render deployment, production release/rollback and OpenJarvis remain pending.

Tests: `tests/test_setup_assessment.py`. CI evidence and the only completion
checkbox are recorded in `HOSHI_60_TASK_MASTER_ROADMAP.md` **after** passing
full backend/JS/Playwright and Docker checks. Android source is unchanged;
do not infer physical phone acceptance.

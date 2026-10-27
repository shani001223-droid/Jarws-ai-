# Hoshi Task 41 — bounded paper-only risk illustrations (development)

The read-only GET /api/trading/paper-risk endpoint accepts BTCUSDT/ETHUSDT,
optional illustrative equity_usdt (10–100000; default 100), risk_pct (0.1–1%;
default 0.5), fee_bps (1–100; default 10 each side), and slippage_bps (1–100;
default 5 each side). No keys, orders, leverage, accounts, signals for execution,
futures or auto-trading are involved.

It fetches ONE shared 15m/1h/4h closed Binance Spot history and re-runs the
Task 40 six-family assessment plus Task 38 confirmed pivots and Task 39
indicators. The assessment must explicitly be paper_watchlist_only; otherwise
the result is WAIT with no fabricated entry, stop, target or position. Even
when six families pass, a valid confirmed 15m support and positive ATR are
mandatory. A hypothetical stop is support minus max(0.25 * ATR14, 0.1% of
the last closed price), and must be 0.2–5% below the reference close.
Missing/invalid levels, excessive distance or insufficient modeled net
reward mean WAIT. Targets are illustrative 1R/2R distances, not forecasts.

The reference entry is the **last closed candle price**, NOT a live quote or
fill. Estimated entry adds adverse slippage; stop/target exit estimates subtract
slippage. Both sides incur assumed fees. Position size is rounded DOWN to
eight decimal places and capped by the smaller of risk-budget / modeled
stop-loss-per-unit and available cash / fee-inclusive entry. Modeled
stop-loss <= equity * risk_pct / 100, and estimated spot notional <= equity.
No actual exchange minimum quantity/notional, market depth, spread, taxes,
funding, margin or partial fill is checked. Gaps and actual fees/slippage
can cause losses greater than the estimate; no protective stop is placed.

The output is hypothetical-paper-risk-only, orders_enabled=false,
independently_cross_checked=false, with a nullable paper_plan and fixed
reason codes. Task 37's separate Kraken quality endpoint does NOT certify
this Binance-only analysis. No profitability, backtest, walk-forward or
live data guarantee. Only trusted validated closed bars are accepted.
Provider timestamps are checked for freshness before analysis.

Tests: tests/test_paper_risk.py; real Uvicorn route smoke in the existing
Docker backend workflow. GitHub CI links and completion checkbox belong
ONLY in HOSHI_60_TASK_MASTER_ROADMAP.md after final checks pass.
Realme Note 50, Render production, OpenJarvis and Task 06 remain pending.

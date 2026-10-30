"""Read-only local CLI for bounded, operator-supplied spot 15m candles.

Usage: python -m scripts.evaluate_trading_paper --input private-candles.json
JSON: {"symbol":"BTCUSDT","interval":"15m","candles":[[open_ms,o,h,l,c,base_volume,close_ms], ...]}
No network, account credentials, orders, disk writes or automatic publishing.
"""
import argparse
import json
from pathlib import Path
import sys

from cloud_backend.paper_evaluation import evaluate_chronological
from cloud_backend.trading_research import Candle, SimulationConfig


def load_local(path: Path):
    if not path.is_file() or path.stat().st_size > 250_000:
        raise ValueError("invalid_input_file")
    payload = json.loads(path.read_text(encoding="utf-8"),
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid_json")))
    if (not isinstance(payload, dict) or set(payload) != {"symbol", "interval", "candles"}
            or payload["interval"] != "15m" or not isinstance(payload["candles"], list)):
        raise ValueError("invalid_input_shape")
    bars = []
    for row in payload["candles"]:
        if (not isinstance(row, list) or len(row) != 7
                or type(row[0]) is not int or type(row[6]) is not int):
            raise ValueError("invalid_candle_row")
        bars.append(Candle(row[0], *(float(x) if type(x) in (str, int, float) else
                                     (_ for _ in ()).throw(ValueError("invalid_numeric_field"))
                                     for x in row[1:6]), row[6]))
    return payload["symbol"], bars


def main():
    parser = argparse.ArgumentParser(description="Offline, unverified-source 15m paper evaluation")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--strategy", choices=("trend_pullback", "breakout_retest"),
                        default="trend_pullback")
    parser.add_argument("--equity", type=float, default=1000)
    parser.add_argument("--risk-pct", type=float, default=.5)
    parser.add_argument("--daily-loss-limit", type=float, default=10)
    parser.add_argument("--fee-bps", type=float, default=10)
    parser.add_argument("--slippage-bps", type=float, default=5)
    args = parser.parse_args()
    try:
        symbol, bars = load_local(args.input)
        config = SimulationConfig(args.equity, args.risk_pct, args.daily_loss_limit,
                                  args.fee_bps, args.slippage_bps)
        result = evaluate_chronological(bars, symbol, args.strategy, config)
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError):
        print("Offline paper evaluation refused: invalid input or settings.", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

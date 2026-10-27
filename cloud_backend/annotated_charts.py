"""Closed BTC/ETH spot candles, confirmed S/R and actual bounded PNG export.

No trading orders, live fill predictions or independent Kraken certification.
"""
from __future__ import annotations

from io import BytesIO
import math
from PIL import Image, ImageDraw

try:
    from .market_structure import analyze_market_structure, MarketStructureError
    from .paper_risk import assess_paper_risk, PaperRiskError
except ImportError:
    from market_structure import analyze_market_structure, MarketStructureError
    from paper_risk import assess_paper_risk, PaperRiskError

VERSION = "spot-annotated-chart-v1"
FRAMES = ("15m", "1h", "4h")


class AnnotatedChartError(ValueError):
    """Reject unverified or inconsistent chart evidence."""


def build_annotated_chart(histories, symbol, interval, fetched_at):
    """All annotations and prices come from ONE shared closed-candle snapshot."""
    if (symbol not in ("BTCUSDT", "ETHUSDT") or interval not in FRAMES
            or not isinstance(histories, dict) or set(histories) != set(FRAMES)
            or type(fetched_at) is not int or fetched_at <= 0):
        raise AnnotatedChartError("invalid_request")
    try:
        structure = analyze_market_structure(histories, symbol)
        paper = assess_paper_risk(histories, symbol)
        frame = structure["timeframes"][interval]
        bars = histories[interval][-96:]
        if (len(bars) < 64 or paper["orders_enabled"] is not False
                or structure["orders_enabled"] is not False
                or paper["symbol"] != symbol
                or paper["last_closed_at"][interval] != frame["last_closed_at"]
                or bars[-1].close_time != frame["last_closed_at"]
                or bars[-1].close != frame["last_close"]):
            raise AnnotatedChartError("snapshot_mismatch")
        candles = [
            {"time": b.time, "close_time": b.close_time, "open": b.open,
             "high": b.high, "low": b.low, "close": b.close, "volume_base": b.volume}
            for b in bars
        ]
        levels = [{"kind": k, "price": frame[k], "paper_only": False}
                  for k in ("support", "resistance") if frame[k] is not None]
        if interval == "15m" and paper["decision"] == "paper_plan_only":
            plan = paper["paper_plan"]
            if not isinstance(plan, dict):
                raise AnnotatedChartError("missing_paper_plan")
            levels += [
                {"kind": "paper_entry", "price": plan["reference_entry_close"], "paper_only": True},
                {"kind": "paper_stop", "price": plan["reference_stop"], "paper_only": True},
            ]
            for target in plan["targets"]:
                multiple = target["multiple_before_costs"]
                if multiple not in (1, 2):
                    raise AnnotatedChartError("invalid_target")
                levels.append({"kind": "paper_tp" + str(multiple),
                               "price": target["reference_price"], "paper_only": True})
        if any(type(x["price"]) not in (int, float) or not math.isfinite(x["price"])
               or x["price"] <= 0 for x in levels):
            raise AnnotatedChartError("invalid_level")
        pivots = []
        for side, key in (("high", "confirmed_swing_highs"), ("low", "confirmed_swing_lows")):
            for p in frame[key]:
                if candles[0]["time"] <= p["pivot_at"] and p["confirmed_at"] <= bars[-1].close_time:
                    pivots.append({"side": side, "price": p["price"], "pivot_at": p["pivot_at"],
                                   "confirmed_at": p["confirmed_at"]})
        return {
            "version": VERSION, "symbol": symbol, "market": "spot",
            "mode": "annotated-spot-chart-research-only", "orders_enabled": False,
            "independently_cross_checked": False, "source": "Binance Spot single venue",
            "interval": interval, "fetched_at": fetched_at,
            "last_closed_at": bars[-1].close_time, "candles": candles,
            "confirmed_pivots": pivots, "levels": levels,
            "structure": frame["structure"], "paper_decision": paper["decision"],
            "paper_reason_code": paper.get("reason_code"),
            "note": "Closed candles only. Pivots require two later closed bars. Paper levels are illustrative, not fills or orders. No independent Kraken certification.",
        }
    except (MarketStructureError, PaperRiskError, KeyError, TypeError,
            IndexError, AttributeError, ArithmeticError, OverflowError) as exc:
        raise AnnotatedChartError("invalid_evidence") from exc


def render_annotated_png(chart):
    """Static 1000x620 image, no file/network/user HTML, fixed safe labels."""
    try:
        if (chart["version"] != VERSION or chart["orders_enabled"] is not False
                or chart["symbol"] not in ("BTCUSDT", "ETHUSDT")
                or chart["interval"] not in FRAMES
                or not 64 <= len(chart["candles"]) <= 96):
            raise AnnotatedChartError("invalid_chart")
        bars = chart["candles"]
        for b in bars:
            values = [b[k] for k in ("open", "high", "low", "close", "volume_base")]
            if (any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
                    or min(values[:4]) <= 0 or b["volume_base"] < 0
                    or not b["low"] <= min(b["open"], b["close"]) <= max(b["open"], b["close"]) <= b["high"]):
                raise AnnotatedChartError("invalid_candle")
        low, high = min(b["low"] for b in bars), max(b["high"] for b in bars)
        pad = max((high-low)*.08, high*.0001)
        low, high = low-pad, high+pad
        left, right, top, bottom = 65, 830, 78, 435
        img = Image.new("RGB", (1000, 620), "#081421")
        draw = ImageDraw.Draw(img)
        def y(price):
            return int(bottom-(price-low)/(high-low)*(bottom-top))
        draw.text((left, 20), "HOSHI | "+chart["symbol"]+" | "+chart["interval"]+
                  " | CLOSED SPOT CANDLES", fill="#e8f3ff")
        draw.text((left, 42), "PAPER RESEARCH ONLY - NO ORDERS / NO FILLS", fill="#a8bfd4")
        for j in range(5):
            yy = top+j*(bottom-top)//4
            draw.line((left, yy, right, yy), fill="#25394d")
            draw.text((right+8, yy-7), format(high-(high-low)*j/4, ".4f"), fill="#a8bfd4")
        step = (right-left)/len(bars)
        width = max(2, min(6, int(step*.65)))
        vmax = max(b["volume_base"] for b in bars)
        x_by_close = {}
        for i, b in enumerate(bars):
            x = int(left+(i+.5)*step)
            x_by_close[b["close_time"]] = x
            color = "#5ad6b1" if b["close"] >= b["open"] else "#f58a9a"
            draw.line((x, y(b["high"]), x, y(b["low"])), fill=color)
            a, z = sorted((y(b["open"]), y(b["close"])))
            draw.rectangle((x-width//2, a, x+width//2, max(a+1,z)), fill=color)
            if vmax:
                vh = int(b["volume_base"]/vmax*62)
                draw.rectangle((x-width//2, 535-vh, x+width//2, 535), fill=color)
        colors = {"support":"#48c5b6", "resistance":"#e9a85d",
                  "paper_entry":"#e4dfff", "paper_stop":"#ff718d",
                  "paper_tp1":"#b9a9ff", "paper_tp2":"#898cff"}
        for item in chart["levels"]:
            kind, price = item["kind"], item["price"]
            if (kind not in colors or type(price) not in (int,float)
                    or not math.isfinite(price) or price <= 0):
                raise AnnotatedChartError("invalid_level")
            if low <= price <= high:
                yy = y(price)
                draw.line((left, yy, right, yy), fill=colors[kind], width=2)
                draw.text((right+8, yy+6), kind+" "+format(price, ".4f"), fill=colors[kind])
        for p in chart["confirmed_pivots"]:
            x = x_by_close.get(p["pivot_at"])
            if x is not None and p["confirmed_at"] <= chart["last_closed_at"]:
                yy = y(p["price"])
                draw.ellipse((x-3,yy-3,x+3,yy+3),
                             fill="#ffd166" if p["side"]=="high" else "#57caff")
        draw.text((left, 546), "Base volume (relative) | UTC timestamps in JSON", fill="#a8bfd4")
        draw.text((left, 573), "Last closed ms: "+str(chart["last_closed_at"])+
                  " | Fetched UTC s: "+str(chart["fetched_at"]), fill="#a8bfd4")
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        output = buffer.getvalue()
        if not output or len(output) > 1_000_000:
            raise AnnotatedChartError("png_size_limit")
        return output
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise AnnotatedChartError("png_failed") from exc

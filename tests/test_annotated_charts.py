"""Task 42: actual closed-candle PNG and JSON export regression."""
import io
import unittest
from dataclasses import replace
from unittest.mock import patch
from fastapi import Response
from PIL import Image
from cloud_backend import main
from cloud_backend.annotated_charts import (
    AnnotatedChartError, build_annotated_chart, render_annotated_png,
)
from cloud_backend.trading_research import INTERVALS, closed_candles

NOW = 1_800_000_000_000
FRAMES = ("15m", "1h", "4h")


def history(tf):
    step = INTERVALS[tf]
    start = (NOW//step-90)*step
    wave = (0,1,3,1,0,-1,-3,-1)
    rows = []
    for i in range(90):
        t = start+i*step
        p = 100+.16*i+wave[i%8]
        rows.append([t,p,p+.2,p-.2,p,10,t+step-1])
    return closed_candles(rows, tf, NOW)


def histories():
    return {tf:history(tf) for tf in FRAMES}


class ChartTests(unittest.TestCase):
    def test_closed_candles_pivots_and_wait(self):
        data = histories()
        chart = build_annotated_chart(data,"BTCUSDT","15m",NOW//1000)
        self.assertFalse(chart["orders_enabled"])
        self.assertFalse(chart["independently_cross_checked"])
        self.assertEqual(chart["last_closed_at"],data["15m"][-1].close_time)
        self.assertEqual(len(chart["candles"]),90)
        self.assertTrue(all(c["close_time"]<NOW for c in chart["candles"]))
        self.assertTrue(all(p["confirmed_at"]>p["pivot_at"]
                            and p["confirmed_at"]<=chart["last_closed_at"]
                            for p in chart["confirmed_pivots"]))
        self.assertEqual(chart["paper_decision"],"wait")
        self.assertFalse(any(x["paper_only"] for x in chart["levels"]))

    def test_png_decodes_and_bounded(self):
        chart = build_annotated_chart(histories(),"ETHUSDT","1h",NOW//1000)
        png = render_annotated_png(chart)
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertLess(len(png),1_000_000)
        with Image.open(io.BytesIO(png)) as im:
            im.verify()
        with Image.open(io.BytesIO(png)) as im:
            self.assertEqual(im.size,(1000,620))

    def test_rejects_invalid_or_tampered_history(self):
        data=histories()
        for pair,tf in (("SOLUSDT","15m"),("BTCUSDT","5m")):
            with self.assertRaises(AnnotatedChartError):
                build_annotated_chart(data,pair,tf,NOW//1000)
        data["4h"][10]=replace(data["4h"][10],volume=-1)
        with self.assertRaises(AnnotatedChartError):
            build_annotated_chart(data,"BTCUSDT","15m",NOW//1000)
        chart=build_annotated_chart(histories(),"BTCUSDT","15m",NOW//1000)
        chart["levels"].append({"kind":"paper_tp1","price":float("nan")})
        with self.assertRaises(AnnotatedChartError):
            render_annotated_png(chart)

    def test_api_json_png_and_invalid_pair(self):
        data=histories()
        calls=[]
        def fetch(pair,tf):
            calls.append((pair,tf))
            return data[tf],NOW//1000
        with patch.object(main,"_research_history",side_effect=fetch),patch.object(
                main.time,"time",return_value=NOW/1000):
            response=Response()
            chart=main.trading_annotated_chart(response,"BTCUSDT","15m","json")
            self.assertEqual(response.headers["Cache-Control"],"no-store")
            self.assertFalse(chart["orders_enabled"])
            png=main.trading_annotated_chart(Response(),"BTCUSDT","15m","png")
        self.assertEqual(set(calls),{("BTCUSDT",tf) for tf in FRAMES})
        self.assertEqual(png.media_type,"image/png")
        self.assertEqual(png.headers["Cache-Control"],"no-store")
        self.assertTrue(png.body.startswith(b"\x89PNG"))
        self.assertEqual(len([r for r in main.app.routes
                              if r.path=="/api/trading/annotated-chart"]),1)
        with patch.object(main,"_research_history") as fetch:
            with self.assertRaises(main.HTTPException) as err:
                main.trading_annotated_chart(Response(),"SOLUSDT","15m","json")
            self.assertEqual(err.exception.status_code,422)
            fetch.assert_not_called()

    def test_stale_provider_fails_closed(self):
        with patch.object(main,"_research_history",
                          return_value=(history("15m"),NOW//1000-300)),patch.object(
                main.time,"time",return_value=NOW/1000):
            with self.assertRaises(main.HTTPException) as err:
                main.trading_annotated_chart(Response(),"BTCUSDT","15m","json")
            self.assertEqual(err.exception.status_code,503)


if __name__=="__main__":
    unittest.main()

"""Strict server-side public market JSON parsing: no ambiguous trading evidence.

Deterministic transport fixtures only; no provider, orders or device claims.
"""
from collections import OrderedDict
from io import BytesIO
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from cloud_backend import main


class PublicTradingJsonTests(unittest.TestCase):
    def test_valid_json_remains_compatible(self):
        payload = b'{"result":{"BTCUSDT":[[1,"100"]]},"error":[]}'
        with patch.object(main, "urlopen", return_value=BytesIO(payload)):
            self.assertEqual(main._read_public_json("https://data-api.binance.vision/test"),
                             {"result": {"BTCUSDT": [[1, "100"]]}, "error": []})

    def test_duplicate_root_and_nested_keys_are_rejected(self):
        for payload in (b'{"price":"100","price":"999"}',
                        b'{"result":{"BTCUSDT":{"close":100,"close":999}}}'):
            with self.subTest(payload=payload), patch.object(
                    main, "urlopen", return_value=BytesIO(payload)):
                with self.assertRaisesRegex(ValueError, "Ambiguous public market JSON"):
                    main._read_public_json("https://data-api.binance.vision/test")

    def test_nonstandard_nonfinite_constants_are_rejected(self):
        for literal in (b"NaN", b"Infinity", b"-Infinity"):
            with self.subTest(literal=literal), patch.object(
                    main, "urlopen", return_value=BytesIO(b'{"close":' + literal + b'}')):
                with self.assertRaisesRegex(ValueError, "Non-finite public market JSON"):
                    main._read_public_json("https://data-api.binance.vision/test")

    def test_exponent_overflow_is_not_cached_as_infinite_market_price(self):
        with patch.object(main, "urlopen", return_value=BytesIO(b'{"price":1e999}')):
            with self.assertRaisesRegex(ValueError, "Non-finite public market JSON"):
                main._read_public_json("https://data-api.binance.vision/test")

    def test_ambiguous_provider_response_is_not_cached(self):
        cache = OrderedDict()
        with patch.object(main, "_PUBLIC_CACHE", cache), patch.object(
                main, "urlopen", return_value=BytesIO(b'{"price":1,"price":2}')):
            with self.assertRaises(main.HTTPException) as err:
                main._public_data("strict-json-regression", "https://data-api.binance.vision/test", 30)
        self.assertEqual(err.exception.status_code, 503)
        self.assertNotIn("Ambiguous", str(err.exception.detail))
        self.assertFalse(cache)

    def test_actual_mobile_desk_refuses_ambiguous_provider_payload(self):
        client = TestClient(main.app)
        cache = OrderedDict()
        # Each of the three concurrent timeframes receives its own invalid body.
        def invalid_response(request, timeout):
            return BytesIO(b'{"candles":[],"candles":[1]}')
        with patch.object(main, "_PUBLIC_CACHE", cache), patch.object(
                main, "urlopen", side_effect=invalid_response), patch.object(
                main, "load_knowledge", return_value=None):
            response = client.get("/api/trading/desk?symbol=BTCUSDT")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("paper_plan_only", response.text)
        self.assertNotIn("Ambiguous", response.text)
        self.assertFalse(cache)


if __name__ == "__main__":
    unittest.main()

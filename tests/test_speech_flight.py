"""No-network regression for shared, cancellable Urdu TTS work."""
import asyncio
import hashlib
import unittest
from cloud_backend.speech_flight import SpeechFlightCache, SpeechCapacityError

KEY = hashlib.sha256(b"urdu phrase").digest()
OTHER = hashlib.sha256(b"other phrase").digest()


class SpeechFlightTests(unittest.IsolatedAsyncioTestCase):
    async def test_identical_requests_share_one_generation_and_cache(self):
        cache = SpeechFlightCache()
        gate = asyncio.Event()
        calls = 0
        async def make():
            nonlocal calls
            calls += 1
            await gate.wait()
            return b"encoded-mp3"
        a = asyncio.create_task(cache.get(KEY, make))
        b = asyncio.create_task(cache.get(KEY, make))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertEqual(calls, 1)
        gate.set()
        self.assertEqual(await asyncio.gather(a, b), [b"encoded-mp3"] * 2)
        self.assertEqual(await cache.get(KEY, make), b"encoded-mp3")
        self.assertEqual(calls, 1)

    async def test_cancelling_one_waiter_does_not_cancel_other(self):
        cache = SpeechFlightCache()
        gate = asyncio.Event()
        calls = 0
        async def make():
            nonlocal calls
            calls += 1
            await gate.wait()
            return b"mp3"
        a = asyncio.create_task(cache.get(KEY, make))
        b = asyncio.create_task(cache.get(KEY, make))
        await asyncio.sleep(0)
        a.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await a
        gate.set()
        self.assertEqual(await b, b"mp3")
        self.assertEqual(calls, 1)

    async def test_all_cancelled_stops_generation_without_cache(self):
        cache = SpeechFlightCache()
        entered = asyncio.Event()
        stopped = asyncio.Event()
        async def make():
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()
        waiter = asyncio.create_task(cache.get(KEY, make))
        await entered.wait()
        waiter.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await waiter
        # A new request must not attach to the cancelled in-flight task.
        self.assertEqual(await cache.get(
            KEY, lambda: asyncio.sleep(0, result=b"retry")), b"retry")
        await asyncio.wait_for(stopped.wait(), 1)

    async def test_expiry_failure_and_capacity(self):
        now = [100.0]
        cache = SpeechFlightCache(ttl=2, max_inflight=1, clock=lambda: now[0])
        calls = 0
        async def make():
            nonlocal calls
            calls += 1
            return b"mp3"
        self.assertEqual(await cache.get(KEY, make), b"mp3")
        now[0] = 103
        self.assertEqual(await cache.get(KEY, make), b"mp3")
        self.assertEqual(calls, 2)
        gate = asyncio.Event()
        async def wait():
            await gate.wait()
            return b"mp3"
        a = asyncio.create_task(cache.get(OTHER, wait))
        await asyncio.sleep(0)
        with self.assertRaises(SpeechCapacityError):
            await cache.get(hashlib.sha256(b"third").digest(), make)
        gate.set()
        await a

    async def test_failed_or_oversized_audio_is_never_cached(self):
        cache = SpeechFlightCache(max_bytes=4)
        async def fail():
            raise RuntimeError("secret provider message")
        with self.assertRaises(RuntimeError):
            await cache.get(KEY, fail)
        with self.assertRaises(ValueError):
            await cache.get(KEY, lambda: asyncio.sleep(0, result=b"12345"))
        self.assertEqual(await cache.get(
            KEY, lambda: asyncio.sleep(0, result=b"1234")), b"1234")

    async def test_invalid_digest_is_rejected(self):
        cache = SpeechFlightCache()
        with self.assertRaises(ValueError):
            await cache.get(b"not-a-sha", lambda: asyncio.sleep(0, result=b"mp3"))


if __name__ == "__main__":
    unittest.main()

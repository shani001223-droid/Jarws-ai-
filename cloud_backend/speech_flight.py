"""Bounded in-process coalescing for identical Urdu TTS requests.

Only a SHA-256 digest of the normalized text/style is used as a key. This is
not durable caching, streaming, a model, or a guarantee of phone latency.
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict
import time
from typing import Awaitable, Callable


class SpeechCapacityError(RuntimeError):
    """The in-process speech generation budget is already exhausted."""


class SpeechFlightCache:
    def __init__(self, *, ttl: float = 120.0, max_cache: int = 16,
                 max_inflight: int = 8, max_bytes: int = 2_000_000,
                 clock: Callable[[], float] = time.monotonic):
        self._ttl = ttl
        self._max_cache = max_cache
        self._max_inflight = max_inflight
        self._max_bytes = max_bytes
        self._clock = clock
        self.cache: OrderedDict[bytes, tuple[float, bytes]] = OrderedDict()
        # Each task is owned by its event loop; never await it from another loop.
        self._inflight: dict[tuple[asyncio.AbstractEventLoop, bytes], dict] = {}

    async def get(self, key: bytes, generate: Callable[[], Awaitable[bytes]],
                  *, timeout: float = 25.0) -> bytes:
        if type(key) is not bytes or len(key) != 32:
            raise ValueError("Speech key must be a SHA-256 digest.")
        now = self._clock()
        cached = self.cache.get(key)
        if cached is not None:
            if cached[0] > now:
                self.cache.move_to_end(key)
                return cached[1]
            self.cache.pop(key, None)

        loop = asyncio.get_running_loop()
        flight_key = (loop, key)
        flight = self._inflight.get(flight_key)
        if flight is None:
            if len(self._inflight) >= self._max_inflight:
                raise SpeechCapacityError("Too many pending speech requests.")

            async def produce() -> bytes:
                try:
                    audio = await asyncio.wait_for(generate(), timeout=timeout)
                    if type(audio) is not bytes or not 0 < len(audio) <= self._max_bytes:
                        raise ValueError("Speech provider returned invalid audio bytes.")
                    self.cache[key] = (self._clock() + self._ttl, audio)
                    self.cache.move_to_end(key)
                    while len(self.cache) > self._max_cache:
                        self.cache.popitem(last=False)
                    return audio
                finally:
                    if self._inflight.get(flight_key) is flight:
                        self._inflight.pop(flight_key, None)

            task = loop.create_task(produce())
            # If all callers disconnect, consume any late exception without
            # logging a prompt or triggering an unhandled-task warning.
            def consume_failure(done: asyncio.Task) -> None:
                if not done.cancelled():
                    done.exception()
            task.add_done_callback(consume_failure)
            flight = {"task": task, "waiters": 0}
            self._inflight[flight_key] = flight
        flight["waiters"] += 1
        try:
            return await asyncio.wait_for(asyncio.shield(flight["task"]), timeout=timeout)
        finally:
            flight["waiters"] -= 1
            if flight["waiters"] == 0 and not flight["task"].done():
                if self._inflight.get(flight_key) is flight:
                    self._inflight.pop(flight_key, None)
                flight["task"].cancel()

"""Bounded, process-local request diagnostics. Never record application payloads."""
from __future__ import annotations

import asyncio
from collections import Counter, deque
from contextvars import ContextVar
import json
import logging
import math
import os
import secrets
import threading
import time
import uuid

from fastapi import FastAPI, Header, HTTPException
from starlette.responses import JSONResponse

LOGGER = logging.getLogger("hoshi.requests")
LOGGER.setLevel(logging.INFO)
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
LOGGER.propagate = False
REQUEST_ID: ContextVar[str | None] = ContextVar("hoshi_request_id", default=None)


def current_request_id() -> str | None:
    """Available to async handlers and FastAPI's context-propagating threadpool."""
    return REQUEST_ID.get()


def _error_class(status: int) -> str | None:
    if status == 429:
        return "rate_limited"
    if status in (408, 504):
        return "timeout"
    if status in (502, 503):
        return "upstream_unavailable"
    if status in (400, 422):
        return "invalid_request"
    if status in (401, 403):
        return "access_denied"
    if status >= 500:
        return "server_error"
    if status >= 400:
        return "http_error"
    return None


def _route_name(scope: dict) -> str:
    # Only framework-declared route templates; never raw URLs, query strings or IDs.
    path = getattr(scope.get("route"), "path", None)
    if not isinstance(path, str) or not path.startswith("/"):
        return "unmatched"
    return path[:100]


class RequestMetrics:
    def __init__(self, max_routes: int = 32, sample_limit: int = 256, clock=time.monotonic):
        if max_routes < 1 or sample_limit < 1:
            raise ValueError("Metrics bounds must be positive")
        self.max_routes, self.sample_limit, self.clock = max_routes, sample_limit, clock
        self.started = clock()
        self._lock = threading.Lock()
        self._routes: dict = {}
        self._active = 0
        self._total = 0

    def begin(self):
        with self._lock:
            self._active += 1

    def end(self, method: str, route: str, status: int, elapsed_ms: float, error: str | None):
        key = (method, route)
        elapsed_ms = max(0.0, float(elapsed_ms))
        if not math.isfinite(elapsed_ms):
            elapsed_ms = 0.0
        with self._lock:
            self._active = max(0, self._active - 1)
            self._total += 1
            # Reserve one bucket so arbitrary new routes cannot grow memory.
            if key not in self._routes and len(self._routes) >= self.max_routes - 1:
                key = ("OTHER", "other")
            bucket = self._routes.setdefault(key, {
                "count": 0, "status_classes": Counter(), "errors": Counter(),
                "samples": deque(maxlen=self.sample_limit),
            })
            bucket["count"] += 1
            bucket["status_classes"][str(status // 100) + "xx"] += 1
            if error:
                bucket["errors"][error] += 1
            bucket["samples"].append(elapsed_ms)

    def snapshot(self) -> dict:
        def percentile(samples, fraction):
            return round(samples[max(0, math.ceil(len(samples) * fraction) - 1)], 3) if samples else None
        with self._lock:
            routes = []
            for (method, route), bucket in self._routes.items():
                samples = sorted(bucket["samples"])
                routes.append({
                    "method": method, "route": route, "requests": bucket["count"],
                    "status_classes": dict(bucket["status_classes"]), "errors": dict(bucket["errors"]),
                    "recent_samples": len(samples), "p50_ms": percentile(samples, .5),
                    "p95_ms": percentile(samples, .95),
                })
            return {
                "scope": "current_process", "persistent": False,
                "uptime_seconds": round(max(0, self.clock() - self.started), 3),
                "requests_completed": self._total, "active_requests": self._active,
                "sample_limit_per_route": self.sample_limit, "route_bucket_limit": self.max_routes,
                "queue_depth": None, "queue_status": "not_instrumented",
                "routes": routes,
            }


class RequestObservabilityMiddleware:
    """Pure ASGI: do not buffer responses or consume request bodies."""
    def __init__(self, app, metrics: RequestMetrics):
        self.app, self.metrics = app, metrics

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = str(uuid.uuid4())  # Do not trust client-supplied IDs/log content.
        token = REQUEST_ID.set(request_id)
        started_at = self.metrics.clock()
        started = False
        status, error = 500, None
        method = scope.get("method", "OTHER")
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}:
            method = "OTHER"
        self.metrics.begin()

        async def traced_send(message):
            nonlocal started, status
            if message["type"] == "http.response.start":
                started = True
                status = int(message["status"])
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"x-request-id"]
                message = {**message, "headers": headers + [(b"x-request-id", request_id.encode("ascii"))]}
            await send(message)

        try:
            await self.app(scope, receive, traced_send)
        except asyncio.CancelledError:
            status, error = status if started else 499, "client_cancelled"
            raise
        except Exception:
            error = "internal_error" if not started else "stream_error"
            if started:
                # Don't leak an exception/provider body through outer server logs.
                raise RuntimeError("Response interrupted; consult the request ID.") from None
            status = 500
            response = JSONResponse(
                {"detail": "Request failed. Use the request ID when reporting the error.", "request_id": request_id},
                status_code=500, headers={"Cache-Control": "no-store"},
            )
            await response(scope, receive, traced_send)
        finally:
            elapsed_ms = max(0, (self.metrics.clock() - started_at) * 1000)
            error = error or _error_class(status)
            route = _route_name(scope)
            self.metrics.end(method, route, status, elapsed_ms, error)
            REQUEST_ID.reset(token)
            LOGGER.info(json.dumps({
                "event": "http_request", "request_id": request_id, "method": method,
                "route": route, "status": status, "duration_ms": round(elapsed_ms, 3),
                "error_class": error,
            }, separators=(",", ":")))


def install_observability(app: FastAPI) -> RequestMetrics:
    metrics = RequestMetrics()
    app.state.request_metrics = metrics
    app.add_middleware(RequestObservabilityMiddleware, metrics=metrics)

    @app.get("/api/diagnostics", include_in_schema=False)
    def diagnostics(authorization: str | None = Header(default=None)):
        expected = os.getenv("DIAGNOSTICS_TOKEN", "").strip()
        if len(expected) < 32:
            raise HTTPException(503, "Private diagnostics are not configured.", headers={"Cache-Control": "no-store"})
        supplied = authorization or ""
        scheme, _, value = supplied.partition(" ")
        if scheme.lower() != "bearer" or not secrets.compare_digest(value.strip().encode(), expected.encode()):
            raise HTTPException(401, "Private diagnostics require authorization.", headers={"Cache-Control": "no-store"})
        return JSONResponse(metrics.snapshot(), headers={"Cache-Control": "no-store"})

    return metrics

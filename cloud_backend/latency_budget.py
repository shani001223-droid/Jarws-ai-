"""Strict per-request budgets for ordinary fast Hoshi replies.

This limits *serial provider socket timeouts*. It does not guarantee wall-clock
latency during Render cold starts, DNS, audio synthesis, or rate-limiting.
No parallel duplicate API calls or paid models are introduced.
"""
import math


def provider_timeout(started_at: float, now: float, *, fast: bool, cap: float = 7.0) -> float:
    """Return usable per-provider seconds, or 0 when no safe budget remains."""
    if any(not isinstance(n, (float, int)) or not math.isfinite(n)
           for n in (started_at, now, cap)):
        return 0.0
    if cap <= 0:
        return 0.0
    total = 13.0 if fast else 29.0
    # Reserve time for response decoding / HTTP serialization.
    available = total - max(0.0, now - started_at) - 0.75
    if available < 1.0:
        return 0.0
    return min(cap, available)

# Hoshi request diagnostics — roadmap task 03 checkpoint

This adds runtime traceability to the existing API. It does not claim that all 60 tasks, the full observability phase, or a durable backend workforce are complete.

## Implemented

- Every HTTP response passing through the middleware gets a server-generated UUID in `X-Request-ID`; client-provided IDs are ignored. CORS exposes the header to the frontend.
- `current_request_id()` exposes the same ID to async endpoints and FastAPI worker-thread handlers, without storing request contents.
- The default `uvicorn.access` records are suppressed because they contain raw client IPs and URL/query strings; safe structured request events replace them for this API.
- One structured `hoshi.requests` log event records request ID, HTTP method, registered route template, status, elapsed milliseconds and a fixed error category. The middleware does not read or log request/response bodies, raw URL paths, query strings, authorization headers, IP addresses, model text or exception messages.
- Unhandled failures before a response starts get a generic 500 and the request ID. Existing handled HTTP error payloads remain controlled by their handlers. Late streaming errors retain the already-sent wire status and are counted separately as `stream_error`; the stream is not replaced with a second response.
- Bounded process-local aggregate counters and recent-sample p50/p95 timings. At most 32 route buckets, including an overflow bucket; at most 256 durations per bucket. The percentile window is the latest 256 completed request lifecycles for that route, not a fixed time interval or a permanent history.
- Concurrency-safe counters; streaming frames pass through immediately. Client cancellation resets context and active-request counts.
- Private `/api/diagnostics` endpoint. It is absent from generated API docs, requires a Bearer token, and sends `Cache-Control: no-store` for successful and rejected access.

## Frontend safe report

`hoshi-diagnostics.js` records the last backend response ID, the latest failed-response ID, fixed client error/cancellation categories and up to 10 error events in page memory only. Script names come from a fixed allowlist and source positions are bounded integers. It never records full URLs, request bodies or chat text, and never reads exception messages, stacks or rejection reasons. Unrecognized response IDs are discarded. Reloading the page clears the report.

The existing assistant, public-market, health, Urdu audio and product-ad responses feed this tracker without consuming their bodies or modifying payloads. Settings → Safe error report supports user-initiated Copy and Clear. No diagnostics are automatically uploaded; copying is a separate explicit user action. A last API ID is a debugging reference, not proof that a particular client error was caused by that request.

## Private metrics setup

Add `DIAGNOSTICS_TOKEN` to the backend's private environment only. Use a fresh random token of at least 32 characters, for example generated with Python `secrets.token_urlsafe(32)`. Never put it in the frontend, APK, GitHub or screenshots. The route returns 503 if the token is missing/too short, and 401 for a mismatched or missing Bearer token when configured.

A trusted operator can call `GET /api/diagnostics` with `Authorization: Bearer <private token>`. No token value is included in metrics or logs. This implementation does not configure or rotate any Render secrets automatically.

## Limits and next work

- Metrics reset on process restart and are separate for each worker/instance. They do not establish durable storage or service-wide SLOs.
- `queue_depth` is null and `queue_status` is `not_instrumented`. This is not evidence that a persistent job queue exists or is empty.
- Timings cover the HTTP request lifecycle, not individual model/TTS steps or actual audible playback. Native voice acceptance and real-phone latency remain separate tests.
- Provider-specific step timings and worker/queue metrics remain pending integrations. Client reports are only local to one page; they are not a remotely collected crash-analysis service.
- Authorized live metrics retrieval remains unverified until a private diagnostics token is configured. Anonymous production checks should confirm the route stays closed and health responses carry a valid request ID.

## Verification

Local targeted tests cover generated IDs and context, CORS/preflight, sensitive exception/query/body/header exclusion, route-template grouping, private authentication/disabled behavior, percentile windows, route/sample bounds, concurrent accounting, cancellation, streaming and unchanged health payloads.

Run `python -m pip install -r requirements-test.txt` then `python -m unittest discover -s tests -p 'test_*.py'` in a full checkout. CI also retains the existing JavaScript, browser, product-ad, phone-action and memory tests. No Android changes or physical-device acceptance are implied by this backend checkpoint.

Middleware reference: https://starlette.dev/middleware/ (pure ASGI middleware and lifecycle handling).

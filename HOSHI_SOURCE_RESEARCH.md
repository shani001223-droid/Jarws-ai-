# Hoshi Task 31 — Read-only cited public sources (development)

**Scope:** fixed public RSS/Atom feeds only; this is not an arbitrary web browser, search engine, news fact-checker, or autonomous research agent. No user-provided URLs are fetched. No accounts, tokens, browser cookies, purchases, posting, file writes, trading or model calls.

## Source choices

- `world`: BBC News world RSS, up to 72 hours old.
- `technology`: BBC News technology RSS, up to 168 hours old.
- `science`: BBC News science/environment RSS, up to 168 hours old.
- `space`: NASA news RSS, up to 336 hours old.

`GET /api/research/sources?topic=technology&q=AI&limit=3` returns at most three directly linked items with source name, exact publication time, retrieval time, age, canonical article citation URL and a short inert summary. It returns an explicit `no_matching_fresh_items` status when nothing matches; this does **not** prove the topic has no news. If a source fails or rejects a feed, the API returns a sanitized 503 rather than inventing headlines. Responses use `Cache-Control: no-store`; server may reuse a successfully validated feed for up to 120 seconds.

**Trust and safety:** HTTPS-only hard-coded feed endpoints, no HTTP redirects, article links restricted to source-owned hostnames, fixed 5-second request timeout, 192 KiB feed cap, 60-entry parse cap, 2 concurrent network slots, 5 returned items maximum, 80-character query maximum, explicit UTC dates, stale/future item rejection and DOCTYPE rejection. Feed markup is converted to plain text; the returned text is untrusted source material and must be rendered as text, not HTML or tool instructions. Source-provided headlines are **not independently verified facts**. Downstream replies must attribute claims and link to each original article, never present an uncited AI synthesis as retrieved evidence.

**Limitations:** A fixed-feed headline is not the complete article. News feeds can be delayed, incomplete, temporarily unavailable, geo-blocked or removed. No cross-source corroboration, full-text browsing, original fact-checking or user-selected URL fetching is implemented. No live production endpoint, Realme Note 50 UI integration or public-source network availability is claimed by offline tests. The endpoint is a bounded backend primitive for future explicitly scoped research workflows; it does not authorize the assistant to follow arbitrary links.

**Acceptance gate:** tests/test_source_research.py covers fixed URLs, stale/future and missing timestamps, malicious link rejection, XML/entity and size limits, safe errors, source citation fields, query matching and API no-store behavior. Require green GitHub Python/JS/Playwright CI and Docker backend smoke before checking Task 31 in the only canonical roadmap. The live feeds and mobile experience require separate acceptance; do not claim full general browsing from these tests.

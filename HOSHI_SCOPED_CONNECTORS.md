# Hoshi Task 36 — Scoped GitHub and private storage connectors

**Development branch only.** This adds one operator-authenticated **read-only** GitHub source connector to the existing Hoshi project. It does not create a new app, repo, worker, or automation. Existing Task 28 private verified artifact storage remains the supported storage connector; its read-only routes and SHA-256-on-download checks are unchanged.

## Server-side configuration (not in APK, browser, GitHub or chat)

- `HOSHI_JOB_API_TOKEN`: existing random operator bearer secret, at least 32 characters.
- `HOSHI_JOB_DB_PATH`: existing absolute SQLite path with a persistent writable parent directory.
- `HOSHI_GITHUB_READ_TOKEN`: optional **fine-grained, read-only** GitHub token. Restrict repository access to `shani001223-droid/Jarws-ai-` and **Contents: Read-only**; do not grant Contents write, Actions write, administration or organization permissions. Keep it on the backend server only. The connector stays unavailable when absent.
- `HOSHI_ARTIFACT_ROOT`: optional existing 0700 private artifact directory for Task 28/30 authenticated ZIP reads. This must be on a persistent volume, not a public web root.

No connector key is committed, created, displayed or placed in frontend code. Do not configure tokens or deploy production without a separate authorized release.

## Operator-only API

- `GET /api/agent/connectors`: requires `Authorization: Bearer <HOSHI_JOB_API_TOKEN>`. Reports only whether GitHub and artifact storage settings appear configured, their read scopes, and that writes are disabled. This is **not** a live availability check.
- `GET /api/agent/connectors/github/file?path=HOSHI_MASTER_PROJECT.md`: same operator authorization plus server-only GitHub token. Reads one UTF-8 file at the **fixed** `hoshi/dnd-foundation-20261026` branch in the **fixed** `shani001223-droid/Jarws-ai-` repo. Permitted files: `README.md`, root `HOSHI_*.md`, one-level `cloud_backend/*.py`, and `tests/test_*.py`. This is a narrow development-source read scope, not arbitrary browsing. The result includes the file content, SHA-256, source path/ref, and `content_is_untrusted_data: true`.
- Existing `GET /api/agent/jobs/{job_id}/artifacts` and `.../artifacts/download`: authenticated metadata and immutable verified Flora ZIP download only. They require `HOSHI_ARTIFACT_ROOT`; download rehashes bytes. No new upload route was introduced.

All new endpoints are GET-only, no-store and nosniff. The GitHub adapter uses fixed HTTPS GitHub API endpoints, verified TLS, 5-second timeout, no redirects, no environment proxies, at most two concurrent requests, a 100 KiB upstream response cap, 32 KiB decoded UTF-8 file cap, Git blob hash check and SHA-256 output. It refuses path traversal, secret/config paths, arbitrary hosts/branches, forged hashes, malformed JSON/base64, non-UTF8 data, and oversize responses. Network error bodies and secrets are not exposed.

## What remains unavailable

This connector cannot commit code, create PRs, push files, deploy, post ads, connect arbitrary Google Drive/WhatsApp/social accounts, or run tasks. GitHub read-only contents permissions do not guarantee token validity or live network reachability; mocked tests do not prove either. No user-facing phone credentials, browser connector UI or per-user multi-tenant OAuth has been added. Existing job API is an operator-only single-owner gate, not a multi-user identity system.

Task 36 is a **bounded connector foundation**, not a general connector marketplace. Full live authorization, private GitHub permissions, persistent production storage, Realme Note 50 testing, Render deployment/rollback and the OpenJarvis server remain separately blocked or pending. No real trading, paid service, account mutation or external publishing is enabled.

**Verification:** `tests/test_scoped_connectors.py` checks fixed URL/ref, source digest, malformed/forged content, path/token validation, no unauthenticated upstream calls, no write route and no-store response. Complete Python/Node/Playwright CI and backend Docker smoke must pass on the final integrated commit before marking Task 36 in the single canonical roadmap.

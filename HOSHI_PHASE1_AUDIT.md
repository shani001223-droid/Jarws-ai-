# HOSHI Phase 1 — Initial Code and Capability Audit
Date: 2026-10-26
Baseline: main commit `556c907c0f4b65b09d3cea5fd4d931bf23255069`
Scope: implementation inventory, risks, next safe fixes. No claim of 60-task completion.

## Existing verified repository components
- `cloud_backend/main.py`: FastAPI routes for assistant, Urdu TTS, public market data, product-ad generation.
- `cloud_backend/openjarvis_bridge.py`: optional remote OpenJarvis HTTP adapter (not an installed/running OpenJarvis server).
- `cloud_backend/agent_tools.py`: bounded offline calculator.
- `cloud_backend/ad_studio.py`: real PNG/ZIP Flora ad renderer (storyboard text is **not** an MP4).
- `index.html`, `hoshi-product-ads.js`, `android/`: Hoshi UI, product ad button/download flow, Android/native actions.
- `tests/` and `.github/workflows/`: backend, frontend contract, browser E2E, API, APK and live smoke coverage.
- Latest baseline GitHub basic checks passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40296883339
- Latest baseline product-ad live workflow passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40296883145
- Previous Android APK build passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40296754432
Those are historical results for the identified commits, **not** acceptance of new changes.

## Gaps observed from code, prioritized
1. General commands currently route to model chat; only `create_product_ads` is registered as an executable backend agent task. Arbitrary game/anime projects cannot execute yet.
2. There is no durable generic job queue, checkpoint store, cancellation/recovery, or private per-job authorization. Free hosted processes may restart; in-memory state and ordinary local filesystem do not guarantee persistence.
3. App screen controls are Android permission scoped. Device tests and service-dependent behavior need separate real verification.
4. Existing product-ad rate limiter is per-client in-process, not a cross-instance durable quota; concurrent workers or instance restarts do not share quota.
5. Optional OpenJarvis works only with a separately configured reachable server and model; configuration flag alone is not evidence it is online.
6. Full 300x30-minute animated episodes require an asset/render/storage production pipeline and significant resources; no live service currently demonstrates that ability.
7. Existing `ALLOWED_ORIGINS` defaults to `*`. Because this is a personal app, production should specify trusted origins; origin controls alone are **not** user authentication.
8. `cloud_backend/.env.example` omits relevant current OpenJarvis/Groq/Gemini settings; configuration docs should remain secret-free and accurate.
9. Live Render logs/metrics could not be retrieved in this session because no Render workspace was selected; never treat that as a passed production audit.

## Security/reliability rules for next phases
- No arbitrary `eval`, shell commands, unrestricted URL fetch, auto-posting, paid upgrades or live futures orders from user prompts.
- Never expose API keys in GitHub, Android APK, web UI or job records.
- Complex jobs require per-user authentication, budget limits, bounded retries, timeouts, authorization, durable progress, idempotency and stop/cancel.
- Never pretend a generated outline/ZIP template is a fully rendered game, commercial ad, or episode.
- After each implementation change: syntax/unit/E2E CI, verify corresponding acceptance; failed checks mean incomplete.

## Phase 1 checkpoint
- [x] Task 01, initial repository architecture/capability audit completed at baseline (source + existing CI); production deployment metrics/device acceptance still pending.
- [x] Task 02, remove provably unused/broken code safely (no speculative deletions).
- [x] Task 03, error logging and validation improvements.
- [x] Task 04, scoped permission design and integration.
- [x] Task 05, comprehensive tests for new features.
- [ ] Task 06, verified merge/deployment/rollback.
- [ ] Tasks 07–60, **not implemented by this audit**.

Keep this audit as a source of truth. Only mark tasks done with implementation + passing verification.

## Verified follow-up commits
- Tasks 02-03: provider JSON validation, sanitized logging and regression tests passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40299987975
- Tasks 04-05: backend action permission matrix denies unapproved high-risk operations; Python/JS/browser checks passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40300338206
- Task 06 remains pending production deployment/workspace and new APK verification; prior main APK checks are historical baseline only.

## Task 17 privacy follow-up (26 Oct 2026)
- New installations have local conversation memory OFF by default. Users must opt in before browser storage or contextual history transmission; opting out deletes saved history.
- A bounded local-only store filters likely credentials, validates allowed roles, supports per-turn editing/deletion, JSON export and explicit history clear. Exports are generated in-browser without an upload endpoint. Heuristic secret detection is not a substitute for data minimization.
- Browser and unit tests verify default-off, opt-in, filtered export, opt-out and context suppression: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40318081029
- Storage is browser/device-local and can disappear on uninstall or cache/data clearing; cross-device durable storage, encrypted backups, user authentication and physical-device testing are **not** claimed. Task 06 Render deployment/rollback is still pending.


## Docker backend import failure reproduced and fixed in development (26 October 2026)

- Render's extra Docker web service `Jarws-ai-` is failing on the deployed `main` Dockerfile because `cloud_backend/Dockerfile` did `COPY main.py .` but `main.py` imports sibling `ad_studio.py`. The Render logs show exactly `ModuleNotFoundError: No module named 'ad_studio'` followed by unsuccessful deployment/port probe.
- Fixed on development branch only by copying all required `cloud_backend/*.py` files into the image with `COPY *.py ./`. No secrets or model weights are added.
- Added `.github/workflows/docker-backend-smoke.yml` that **builds a real Python Docker image, starts its Uvicorn server and executes no-key /health + agent routing + capabilities HTTP probes**. This passed for development commit `82bf4835abac3883ee2ecd35cdfd6955256df1dc`: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40325617352
- This **does not repair the currently deployed duplicate Docker Render service** until a deliberate reviewed release merges and deploys the change. Primary `Jarws-ai--2` Python backend is a separate live service; do not conflate the two.
- Retain roadmap Task 06 unchecked because full production release, rollback and physical Realme Note 50 acceptance have not been verified. GitHub CI's Docker smoke is not a substitute for those.

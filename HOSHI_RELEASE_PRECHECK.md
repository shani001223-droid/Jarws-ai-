# HOSHI release precheck — 27 October 2026

This is preparation for the existing Hoshi release, not a production deployment.

## Exact sources

- Existing repository and draft PR: [shani001223-droid/Jarws-ai- #24](https://github.com/shani001223-droid/Jarws-ai-/pull/24).
- Verified V2 development audit head before reconciliation: `bfc032a3230d419570c0bc6681f391d1cd4f404a`.
- GitHub main observed during release preparation: `081370ba23acbb7a9f9a6efab1978e39f4efe05e`.
- Original rollback backup remains `backup-before-v2`. No shared history is force-pushed.

## Why preparation was necessary

PR #24 was draft and conflicted with newer main changes. A real merge of the
captured main head into the development candidate resolves conflicts in CI,
index.html, service-worker cache and frontend contracts. It preserves main's
approved canvas core, private opt-in profile context, payload-free diagnostics
and first-audio/brief-reasoning improvements alongside development's trading
curriculum, confluence, bounded tools and Stop controls. The default interface
renders one canvas core with minimal controls, with existing tools in Settings.
The obsolete competing orb is not layered on top.

The offline cache includes the union of actually required assets under a new
cache generation. CI keeps tests from both branches, with one complete test
requirements entry point; the legacy requirements-test file delegates to it.

## Verification before pushing

- Local full Python regression: **390 tests passed** (14.059 s).
- Local Node regression: **75 tests passed**, zero skips/failures.
- Dashboard inline JavaScript syntax, backend Python compilation and versioned
  knowledge-bundle parity passed.
- Real browser / Docker / relevant APK checks on the merged source must be
  verified from the actual GitHub run results below; a local unit pass is not
  enough to infer them.

## Observed public live state

Read-only checks of existing URLs, without credentials or account changes:

| URL | Observed result |
| --- | --- |
| https://jarws-ai-1.onrender.com | HTTP 200; downloaded HTML lacks the new focus toggle. It does not establish the live commit. |
| https://jarws-ai-2.onrender.com/health | HTTP 200, service hoshi-cloud-api, version 0.9.1. This does not identify its commit or prove a successful live AI response. |
| https://jarws-ai-2.onrender.com/learn | HTTP 404 — the V2 lesson route is not currently live on this URL. |

Actual Render service configuration, plans, live commit/deploy IDs and rollback
targets have **not** been retrieved. The connected Render tool reports no
selected workspace and explicitly requires the user to identify the workspace
before continuing. Its read-only workspace list contains one entry named
**My Workspace**; it was not silently selected. No Render resources, settings,
secrets, plan, deployment or production main branch were changed.

## Next release steps after workspace identity is established

1. Inspect the actual existing frontend/backend services, selected branches,
   auto-deploy settings, free plan and current successful deploy IDs/commits.
2. Re-check the exact PR head, main head and passing release checks before any
   merge or deploy; do not release a moving unverified head.
3. Preserve current good deploy references for rollback, then use the existing
   services and deployment policy. Do not create a paid resource or duplicate
   backend. Avoid a duplicate manual deploy if auto-deploy already started it.
4. Follow the specific deploy IDs to a terminal live result, inspect safe logs
   and verify health, lesson/history endpoints, unsupported-input rejection,
   source-failure handling and the actual mobile interface.
5. Test a scoped live AI request only with the existing server-held provider
   keys; never disclose them. Physical Realme mic/TTS acceptance requires the
   actual phone; cloud/browser checks do not substitute for it.

Passing source checks are not proof of 99.999% trading accuracy, real order
execution, deployed behavior or physical-device acceptance.

## Merged-candidate clean-runner correction

The first merged-source CI (40509641702 / 40509636857) exposed a missing declared `httpx` dependency used by main's existing observability concurrency test. The new FastAPI TestClient also needs `httpx2`; these are distinct clients. `requirements-dev.txt` now includes both, and `requirements-test.txt` delegates to that complete set. No test was skipped, and the first failed run is not counted as passed. Actual Docker and sandbox checks on merge source 9ffabcc6c5cce8cbd7b9c6efb440d1dab48d9f54 already passed; final CI evidence follows after the dependency correction.

# HOSHI release precheck — 27 October 2026

## 31 October 2026 — unmerged trading-only quality gate (development only)

[Source/test e48dedeb](https://github.com/shani001223-droid/Jarws-ai-/commit/e48dedebd2bcf265c100455e7dac7d264dc73175) adds 20-bar aligned Binance/Kraken **OHLC** comparison to the separate public quality API, refusing discrepant opens/wicks with HTTP 503. This is not a live data capture, a change to the single-source mobile desk, or evidence of profitable fills. Exact-source [full Python/Node/Chromium CI 41202402163](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/41202402163) and [Docker/Uvicorn CI 41202402034](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/41202402034) passed. These are development checks, not live acceptance. Independent forward paper performance and physical Realme Note 50 QA remain unverified. No production deploy, release authorization, merge or real-money orders. Existing 27 October production source below remains the last verified deployment; do not infer live changes from a newer branch/main commit.

Production is live; current status and actual checks appear first.

## Production release — 27 October 2026

**PR #24 is merged and HOSHI V2 is live** at https://jarws-ai-1.onrender.com.
Released application source: `1a0f532afb34d5f3f1d939b2daef86ec9fd46e29`.
User follow-up authorized proceeding with the previously identified My Workspace;
the actual existing services were then verified before the production merge.
The backend plan is Free and the frontend is the existing static site. No new
resource, subscription, secret or real-money order capability was added.

| Service | Verified new deploy | Status / completed time (PKT) | Previous good deploy / commit |
| --- | --- | --- | --- |
| Existing frontend, jarws-ai-1.onrender.com | `dep-dbgaj3vf3r2c73bemuu0` | live, 27 Oct 18:39:41 | `dep-dbg9au29lscs73947rh0` / `081370ba23acbb7a9f9a6efab1978e39f4efe05e` |
| Existing primary Python backend, jarws-ai-2.onrender.com | `dep-dbgaj3vf3r2c73bemup0` | live, 27 Oct 18:40:23 | `dep-dbg9au29lscs73947rk0` / same previous commit |
| Pre-existing auxiliary Docker backend, jarws-ai.onrender.com | `dep-dbgaj3vf3r2c73bemv1g` | live, 27 Oct 18:40:17 | Prior recent deploys had already failed; this is not the frontend's API target |

All three deploys were automatically triggered by the verified main merge.
No redundant manual deploy or paid upgrade was triggered. Rollback IDs above
are retained as references; no rollback or persistent-data restoration occurred.

### Actual live checks

- `/health`: 200; `/learn`: 200 with all **11** lessons; `/learn?module=ict`
  and `/history`: 200 with version `hoshi-trading-knowledge-v2`.
- Unsupported SOLUSDT confluence: **422**. Real BTCUSDT confluence: **200**,
  score **60**, decision **wait**, orders disabled and win probability null.
  This is one dated rule-coverage observation, not a trade recommendation.
- One real short Urdu request returned **200 via Groq**, Roman Urdu reply
  `Mera naam Hoshi hai.` and an Urdu-script speech field. Total request time
  from this test environment was **8.777 s**, including network; it is not a
  model-only latency, first-audio measurement or Realme benchmark.
- Production merge CI: full checks **40513968698**, APK **40513968761**,
  live backend **40513968687**, trace/private-boundary **40513968822** and
  real offline ad rendering **40513968515** passed.
- The old live browser test **40513968778 failed** by attempting to click the
  intentionally hidden Outfit tab. A test-only follow-up replaces the obsolete
  wardrobe assertions with actual core, Settings/tools, V2 route and mobile
  overflow checks. **Corrected live run [40515342689](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40515342689)
  passed** against the released public site using test source `1a68b754720e94dfcf375c8b51fdee37a218232a`.
  It checked 320/390/768/1440px layouts, Settings, V2 lessons/history, invalid-pair
  rejection, live market-source loading, zero uncaught browser errors and zero
  broken same-origin assets. [Screenshot artifact](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40515342689/artifacts/12738891639)
  records the 390px trading screen. The earlier failed run remains recorded.
- Full follow-up [40515342724](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40515342724)
  passed on the same test source: **390 Python / 75 Node tests**, knowledge parity
  and desktop/mobile Chromium regression. PR #28 changes only tests, workflow
  and release documents; its merge uses `[skip render]`. Main can therefore have
  a newer documentation/test commit while the live application correctly stays
  on release source `1a0f532afb34d5f3f1d939b2daef86ec9fd46e29`.
- Production Android debug APK: [artifact 12737034849](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40513968761/artifacts/12737034849),
  22,446,364-byte archive from the released source. Recorded archive digest:
  `sha256:683364e3ec4cefcbfb2cc56a0fd3b733d1f15c61be63aa7dfdedc6a09f9d085d`.
- Opera connector reported **Browser not connected**. No Opera or physical
  Realme microphone/TTS interaction is claimed. Actual Chromium live-browser
  testing is performed by the existing GitHub workflow.

**Historical pre-release notes below describe earlier states, not a current
workspace blocker.** Task 06 physical-device acceptance and a real OpenJarvis
server remain separate; no unrelated roadmap checkbox is checked by this release.

## Archived pre-release checkpoints

The following records are chronological evidence retained from preparation.

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

## Release candidate verification complete

Verified source and test-dependency head: `f62237b15ba2cd383c136042fe5c3732973c51b6`.

| Check | Actual evidence | Result |
| --- | --- | --- |
| Full Python/API/security, Node and desktop/mobile Chromium | [PR run 40509935031](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40509935031), [push run 40509928879](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40509928879) | Passed |
| Actual backend Docker build, Uvicorn health and V2 lesson/timezone checks | [40509935055](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40509935055) | Passed |
| Docker sandbox isolation / denial / output limit / deadline | [40509935295](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40509935295), second attempt | Passed |
| Android debug APK | [40509935254](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40509935254) | Passed; not a physical phone test |

The sandbox first attempt timed out while starting the first tiny container on
the CI runner; an explicit re-run passed with the same source and original
wall-clock/network/isolation limits. No assertion or safety boundary was removed.
The earlier missing-client failure is recorded above and fixed by declaring both
HTTP clients. Local merged-source counts remain **390 Python / 75 Node passed**.

APK artifact: `hoshi-debug-apk`, ID `12736950866`, recorded archive digest `sha256:4ecd57a7874d925037502dfb39b3b2bab2910f2da560801315989cdefd3fe26f`, from the exact verified source above. It is a debug build, not proof the new backend is live.

PR #24 is conflict-free and remains draft while release prerequisites are
completed. The only current deployment blocker is the connected Render tool's
required workspace identification: **My Workspace** must be confirmed before
service/deploy configuration can be inspected. There has been no production
merge, Render deployment, new charge, secret edit or physical-phone test.

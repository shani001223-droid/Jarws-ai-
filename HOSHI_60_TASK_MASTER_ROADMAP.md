# HOSHI — 60-Task Autonomous Development Roadmap

**Status:** tasks are not presumed implemented. Checkmarks only for verified artifacts.
**Date:** 26 Oct 2026. **Active implementation:** draft PR #24.
**Rules:** work serially; after each task run relevant unit/E2E/security tests; repair failures before advancing; make no purchases; never execute live trades; ask for explicit approval on destructive or account-affecting changes.
**Limitation:** third-party models, GPU render, background workers and persistent free storage depend on actual reachable infrastructure; do not claim a placeholder is functional.

## Phase 1 — Foundation & Reliability
- [x] **01** Audit current code and capabilities. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **02** Remove only demonstrably obsolete or duplicate code. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **03** Harden error handling, logging and diagnostics. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **04** Introduce permission and action risk gates. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **05** Run regression tests after every implementation step. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **06** Verify deployment, rollback and APK builds. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 2 — Intelligent Brain
- [x] **07** Classify chat, device and backend tasks. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **08** Convert user goals into clear deliverables. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **09** Break large goals into verified milestones. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **10** Route to available free models intelligently. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **11** Activate and test a real OpenJarvis endpoint. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **12** Detect mistakes and retry with bounded repair. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 3 — Voice & Memory
- [x] **13** Improve Roman Urdu and Pakistani Urdu STT. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **14** Improve female Urdu voice and pronunciation. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **15** Measure and reduce end-to-end latency. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **16** Support speech interruption and cancellation. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [x] **17** Add consent-based durable memory with export/delete. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **18** Improve warm, consistent, non-manipulative personality. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 4 — Android Live Agent
- [ ] **19** Request explicit user-approved screen access. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **20** Understand screenshots and OCR-like UI structure. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **21** Execute bounded permitted tap/type/scroll actions. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **22** Verify screen state after actions. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **23** Integrate supported Android apps via safe intents. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **24** Show action history, pause and emergency stop. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 5 — Backend Job Engine
- [ ] **25** Create persistent job IDs and status records. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **26** Implement bounded worker queue and scheduling. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **27** Delegate to planner/coder/designer/tester steps. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **28** Store authenticated artifacts and checkpoints. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **29** Recover and resume failed or interrupted jobs. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **30** Offer silent progress, selective blockers and final reports. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 6 — Tools & Production
- [ ] **31** Browse and cite reliable fresh sources. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **32** Read/edit PDFs, images and project files. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **33** Run code only inside controlled sandbox. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **34** Orchestrate scoped specialist agents. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **35** Validate generated code/media/artifact formats. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **36** Add authenticated GitHub/storage and supported connectors. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 7 — BTC Trading Research
- [ ] **37** Use reliable current public candles and volume. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **38** Calculate multi-timeframe S/R and market structure. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **39** Calculate indicators with reproducible formulas. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **40** Assess setups from several independent signals. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **41** Report stop/TP/risk and paper-only proposals. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **42** Draw real annotated charts and export analysis. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 8 — Flora Business
- [ ] **43** Maintain verified product/price/photo catalog. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **44** Plan platform-specific campaigns and copy. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **45** Compose original-photo posters and preview files. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **46** Generate rendered MP4 ads with licensed audio. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **47** Draft/schedule posts using approval gates. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **48** Produce grounded sales and campaign reports. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 9 — Game Studio
- [ ] **49** Produce scoped Game Design Document. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **50** Initialize legally free project engine/template. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **51** Develop original licensed assets and animation. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **52** Write playable game code, levels and save flow. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **53** Run automated gameplay and crash tests. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **54** Export and verify playable game APK/web release. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 10 — Anime Studio
- [ ] **55** Maintain series bible and 300-episode chronology. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **56** Write and review individual Urdu/Hindi scripts. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **57** Build consistent original character/voice system. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **58** Generate storyboards, shots and scene packages. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **59** Produce actual synchronized audio/video files. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **60** QC, export and archive each episode and batch. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Evidence and status
- Task 01 initial source/CI audit: [HOSHI_PHASE1_AUDIT.md](HOSHI_PHASE1_AUDIT.md)
- All remaining milestones: planned unless a dated test-supported completion note is added below.
- Use branch `hoshi/dnd-foundation-20261026` and draft PR #24 for changes; main remains protected until CI green.
## Verified phase 1 progress (26 Oct 2026)
- Task 02: duplicate imports cleaned; `urllib.request.Request` vs FastAPI request alias collision found by CI and fixed. Green full checks: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40299493480
- Task 03: malformed AI provider responses no longer leak uncaught shape exceptions; defensive error handling and sanitized diagnostics for ad renderer and Urdu TTS; regression tests in `tests/test_provider_payload_resilience.py` and `tests/test_safe_errors.py`. Green full checks: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40299987975
- Task 04: server-side explicit risk/permission policy rejects screen/account actions and disabled real trading/shell; test `tests/test_permission_policy.py`. Green full checks: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40300338206 (does NOT mean Android screen actions are implemented).
- Task 05: regression gate exercised across Python unit tests, JavaScript syntax/parser tests and Playwright browser E2E, including negative/security cases. Same passing full run https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40300338206. Continue running tests for every future task.

## Additional implementation checkpoints
- Task 06 **blocked/unfinished**: branch CI works, previous main APK was successful, but current branch APK build and live Render deployment/rollback are not newly verified; Render connector requires explicit workspace selection. Do not mark completed.
- Task 07 **verified routing layer**: backend `task_router.py` and `/api/agent/route` plus browser `hoshi-task-router.js` classify chat, device, Flora ad execution and unavailable BTC/game/anime workflows. The UI never claims an unimplemented worker completed work. Browser dispatch, offline precache, JS unit tests and Playwright E2E passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40306542927. **This verifies classification only, not actual game/anime/screen executors.**

- Task 08 **verified specification layer**: `cloud_backend/goal_spec.py` and `POST /api/agent/spec` convert recognized user goals into explicit artifact formats and acceptance requirements, including 300 x 30-minute anime scope (9,000 minutes), playable game deliverables, Flora ad ZIP contents, and paper-only chart analysis. Every deliverable remains `planned` until genuinely produced; no job is started. Python unit tests, JS tests and Playwright E2E passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40306839489. This does not implement game/anime rendering.

- Task 09 **verified planning-only**: `cloud_backend/milestone_planner.py` and `POST /api/agent/milestones` produce dependency-ordered deliverable checkpoints, finite anime batches, status/evidence gates and clear non-execution flags. Tested by `tests/test_milestone_planner.py` in passing full run https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40307087025. This does not render anime or start backend jobs.

- Task 10 **verified**: `cloud_backend/provider_policy.py` is integrated into actual `/api/assistant` provider selection. Configured-only ordering prioritizes Groq for spoken requests, real OpenJarvis for eligible complex requests, then OpenRouter/Gemini/Groq fallback without duplicate provider entries. Includes five regression tests `tests/test_provider_policy.py` and full passing CI https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40310457245. **This does not assert any unconfigured provider or OpenJarvis server is reachable.**

- Task 12 **verified on the currently executable local backend tool only**: `artifact_verifier.py` validates generated Flora ZIP files, PNG dimensions, trusted catalog metadata, captions, video storyboard and matching preview. `/api/agent/execute` attempts **at most one** regeneration if verification fails; two failures return HTTP 502 without claiming completion. Security and error-boundary tests in `tests/test_artifact_verifier.py` passed alongside full CI: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40312499196. This is **not** a generic game/anime agent or universal self-healing capability; their workers are still unavailable.

- **Free-LLM directory integration (Task 10 extension):** Z.AI Flash, Mistral Free and NVIDIA developer/prototyping adapters added to `cloud_backend/free_llm_providers.py`; routed only when explicit matching backend secrets and safeguards are configured. Fixed URLs/models, bounded errors, Urdu parsing and fallback tests in `tests/test_free_llm_providers.py`. **Code and full CI verified**: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40315895539. **No actual API keys installed, no provider account verified, no production deployment.** Setup: [HOSHI_FREE_LLM_PROVIDERS.md](HOSHI_FREE_LLM_PROVIDERS.md).

- Task 13 **verified implementation (real-device microphone QA still pending)**: Added `hoshi-speech-input.js` with exact and safe Urdu/Roman Urdu wake-word extraction, bounded transcript sanitization, and recognition-alternative selection. Wired native Android `SpeechRecognizer` to return up to 3 alternatives via JSON to the same client parser; updated browser microphone and PWA precache; tests in `tests/hoshi-speech-input.test.cjs` and Playwright browser voice interaction. **Full CI passed:** https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40317232660 ; **Android debug APK built:** https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40317232839 . No actual recording/audio is uploaded by this processing layer. **Cannot claim recognition accuracy or Realme Note 50 device microphone behavior without physical installation and testing.** If locale speech recognition is unavailable on the phone, recognizer remains dependent on installed Google/Android Urdu speech service.

- Task 14 **code/test verified, voice quality remains device/user-dependent**: `cloud_backend/urdu_tts_text.py` adds conservative Urdu-script TTS-only pronunciation of BTC, USDT, AI/API, Hoshi and known brand names without modifying displayed chat or translating arbitrary input. Hoshi online Urdu voice `ur-PK-UzmaNeural` styles now use moderated pitch/rate; Android/browser soft preset lowered to near-natural pitch. Backend mock audio and frontend contract tests passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40317960350 ; debug Android build passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40317960352 . **Actual audible quality, voice availability and resemblance to requested reference audio remain untested on the user's phone; do not claim a bespoke anime voice or perfect pronunciation.**

- Task 17 **verified scoped device-local memory (26 Oct 2026)**: Added `hoshi-memory-store.js` with explicit opt-in default OFF for new users, up to 12 filtered persisted turns, role/content validation, fail-closed handling of blocked storage, no remote memory database, secret filtering before export or AI context, and opt-out deletion. Hoshi Chat UI provides opt-in toggle, per-turn edit/delete, `Export JSON` local download and `Clear history`. Service worker precaches the module. Unit tests `tests/hoshi-memory-store.test.cjs`, Python/frontend contracts and Playwright browser smoke tests verified including opt-in, export filtering and opt-out not sending context. **Full CI passed:** https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40318081029 ; **APK build verified on integration commit:** https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40318040333 . Device-local `localStorage` persists across normal reloads but is not cross-device sync, a backed-up database, or guaranteed after app uninstall/browser data clearing. Production/phone QA remains pending; do not imply cloud durability or actual phone test.

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
- [ ] **07** Classify chat, device and backend tasks. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **08** Convert user goals into clear deliverables. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **09** Break large goals into verified milestones. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **10** Route to available free models intelligently. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **11** Activate and test a real OpenJarvis endpoint. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **12** Detect mistakes and retry with bounded repair. Acceptance: implementation or evidence, passing tests, limitations recorded.

## Phase 3 — Voice & Memory
- [ ] **13** Improve Roman Urdu and Pakistani Urdu STT. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **14** Improve female Urdu voice and pronunciation. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **15** Measure and reduce end-to-end latency. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **16** Support speech interruption and cancellation. Acceptance: implementation or evidence, passing tests, limitations recorded.
- [ ] **17** Add consent-based durable memory with export/delete. Acceptance: implementation or evidence, passing tests, limitations recorded.
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
- Task 07 **partial**: the deterministic task router and `POST /api/agent/route` now classify chat, executable product-ads, BTC screen analysis, and game/anime backend projects. It explicitly reports unavailable executors rather than pretending to have made outputs. New regression tests passed: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40301113491. Still requires client dispatch wiring and real game/anime/trading executors before marking fully complete.

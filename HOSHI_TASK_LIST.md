# HOSHI AI — Master Transformation Task List

**Status:** Implementation in progress — the main personality, memory, responsive dashboard, avatar-expression, backend fallback, and native Android foundations are present. Latest basic checks passed after context role-boundary hardening, voice-selection improvements, mobile overflow fixes, and final-art hero/speech-wave integration. The live Render responsive smoke test and live backend AI smoke test passed; full conversational/voice acceptance and target-phone tests remain pending.  
**Repository:** [shani001223-droid/Jarws-ai-](https://github.com/shani001223-droid/Jarws-ai-)  
**Final design:** The two user-provided HOSHI character and dashboard images are the final design, not inspiration. Preserve the character appearance, layout, dark navy / electric-blue / cyan neon palette, and panel arrangement as closely as implementation permits.

## Phase 1 — HOSHI identity and personality
- [x] Character identity: HOSHI name, Yuki-inspired appearance, and consistent personality prompt implemented.
- [x] Emotional brain: happiness, sadness, affection, excitement, shyness, concern, and annoyance prompt/labels implemented; quality still needs end-to-end conversation review.
- [x] Age-appropriate affectionate/girlfriend-style role-play guidance, warmth, and playful romance prompt implemented; full behavior acceptance test pending.
- [x] Fun and teasing guidance: jokes, mischief, playful challenges, and funny reactions.
- [x] Anger/annoyance guidance: context-appropriate mild frustration, complaints, and constructive explanations.
- [x] Apologies and reconciliation guidance: acknowledge mistakes, respond caringly when the user is upset, and resolve misunderstandings.
- [x] Emotional boundaries in the system prompt: no guilt-tripping, emotional blackmail, coercion, or manipulative dependency.

## Phase 2 — Intelligence and emotional understanding
- [x] Rule-based mood detection for English and Roman Urdu covers sadness, frustration, anxiety, affection, playfulness, positivity, and curiosity; short acknowledgements can carry forward only the immediately previous user mood. This is a lightweight heuristic, not a trained emotion model.
- [x] Bounded recent-turn context is sent to the AI; robust context construction avoids accidentally dropping the last saved turn when a message is filtered from memory. Topic tracking remains basic.
- [x] A suitable emotion label is returned with cloud replies, with a deterministic fallback classifier.
- [x] Added prompt guidance against repetitive greetings/stock lines, echoing the user, and forced end-of-reply questions; multi-turn conversation quality acceptance still pending.
- [x] Honesty and respectful disagreement guidance is included in the assistant prompt.

## Phase 3 — Voice and expressions
- [ ] Female Urdu voice with Pakistani Urdu accent; prefer free-first TTS.
- [x] Emotional TTS pitch/rate modulation is implemented where the active speech engine supports it; physical voice quality still needs testing.
- [x] Voice input and speech-to-text wiring are implemented through available browser/WebView APIs; target-device verification remains pending.
- [x] Voice conversation flow and voice-reply control are implemented; natural turn-taking acceptance testing is pending.
- [x] Avatar expressions: an 8-tile WebP sprite cut from the final character sheet now switches for happy, affectionate, excited, thinking, sad/concerned, playful, shy, and annoyed states.
- [ ] Lip-sync with avatar mouth movement if technically feasible.

## Phase 4 — Memory and personalization
- [x] Preference memory for language, tone, and assistant settings (language, personality, voice replies, wake-word toggle, and voice tuning persist locally).
- [x] Maintain bounded recent conversation context for cloud replies.
- [x] Recent-turn context and explicit continuity guidance cover fictional affectionate role-play, playful annoyance, apology, and reconciliation; full multi-turn acceptance still pending.
- [x] User controls to review, edit, delete individual entries, disable memory, and clear memory.
- [x] Local-memory filter blocks common credential language, token formats, recovery phrases, OTPs, email addresses, phone-like strings, and long numeric identifiers. It is heuristic, not a guarantee.

## Phase 5 — JARVIS interface and Android
- [x] Responsive UI breakpoints for desktop, tablet, and phone widths are implemented; Realme Note 50 runtime/layout verification remains pending.
- [x] HOSHI home screen with avatar, chat, microphone/voice controls, and settings exists in the frontend.
- [x] Added functional hero-level Chat / Voice / Vision / Create / More shortcuts with responsive styling; Chromium smoke test covers click actions and browser-only voice/screenshot fallback (run #160).
- [x] Emotion-driven avatar expression sprite positions and glow changes are mapped to the response emotion label.
- [x] Local conversation history is displayed and can be reviewed, edited, deleted entry-by-entry, disabled, or cleared.
- [x] Settings for voice, language, personality, memory, and auto-speak are available; language/voice-reply/wake-word selections persist locally, and an explicitly selected browser voice now bypasses the native-TTS override.
- [x] User-facing cloud timeout/offline/provider errors and speech-recognition/TTS failure messages exist; overlapping AI requests now abort the earlier browser request and stale replies are ignored. Measured latency/data use and device-specific edge cases still need verification.
- [x] Integrated the final-art hero background and animated speech waveform into the dark navy/cyan dashboard without replacing the user's design. The full dashboard remains a responsive adaptation, not a pixel-perfect copy of every panel.
- [x] Source audit confirms no BTC/Bitcoin text or floating-icon selectors remain in `index.html`; the live Render responsive smoke test passed. [Run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235).

## Phase 6 — Existing JARVIS features
- [x] Audited the existing repository, CI, Android APK workflow, reminder functionality, voice/gesture bridge, and backend fallback before modifying them.
- [x] Gemini primary + Groq fallback preserved; latest live backend smoke test #29 passed after retry/status-parsing fixes and received a valid AI reply. [Run #29](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40236085531).
- [x] Existing service integrations remain explicit and supported: external app links, local reminders, and opt-in basic accessibility gestures.
- [x] Backend provider keys are read from environment variables; no provider key was added to the frontend or repository.
- [x] Changes were applied in small commits to the existing project; reminder parsing, native bridge, and existing workflows were retained.

## Phase 7 — Testing and delivery
- [ ] Full acceptance of natural multi-turn conversation, real voice, full role-play quality, and physical avatar/voice behavior is still pending.
- [x] Desktop Chromium browser smoke test checks dashboard load, local command, AI text chat, emotion state, context deduplication, saved history, memory toggle, stale-response protection, all five hero shortcuts, graceful web-mode fallback, and uncaught browser errors. [Run #160 passed](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40235361114).
- [x] Cloud HTTP/provider errors, timeouts, offline failures, and speech recognition restart failures now produce user-facing recovery messages; physical TTS/microphone acceptance remains pending.
- [ ] Test on a real Realme Note 50 Android device.
- [x] Deployed to existing Render hosting with auto-deploy and rollback steps documented in `DEPLOYMENT_ROLLBACK.md`; backend and frontend live smoke checks passed.
- [x] Added `DEPLOYMENT_ROLLBACK.md` with pre-release checks, service-by-service rollback steps, health/UI smoke checks, secret-handling guidance, and a reminder that dashboard rollbacks disable auto-deploys. Current backend and frontend smoke checks passed.
- [ ] Final report clearly separates working features, limitations, and pending work.

## Render backend and frontend verification
- [x] Backend health/AI path verified by the live backend smoke workflow after the role-boundary fix; latest backend deployment is live. [Run #35](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237196850).
- [x] Frontend: https://jarws-ai-1.onrender.com — Render responsive smoke test passed on the final-art hero/speech-wave dashboard, including narrow viewport checks. [Run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235).
- [x] Confirmed frontend/backend compatibility and checked browser console/network errors in the live Render smoke test. [Run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235).

## GitHub Actions verification
- [x] Latest confirmed backend/contract suite `HOSHI basic checks` run #202 passed, including context role-boundary injection regression, privacy, mood-negation, and frontend contract tests. [Run #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519).
- [x] `Build HOSHI Android APK` run #32 passed and uploaded `hoshi-debug-apk` after the native HOSHI launcher icon update. [Run #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290). Installing and testing it on the target phone remains pending by design.
- [x] `HOSHI basic checks` run #202 passed with backend role-boundary tests, frontend contract checks, and browser smoke tests. [Run #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519). Realme testing remains pending.
- [ ] Install the generated debug APK and verify core flows on the target Android phone (deferred until all other available tasks are complete, as requested).

## Initial audit notes
- [x] Read the repository README and inspect the CI workflow definition at `.github/workflows/ci.yml`.
- [x] Inspect the Android APK workflow definition at `.github/workflows/android-apk.yml`.
- [x] Latest live backend smoke test #29 passed after mood-negation and retry workflow updates, confirming a valid live AI reply using the configured fallback provider. [Run #29](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40236085531).
- [x] Re-checked the current Render frontend after hero-art/cache updates; the live responsive smoke test passed and the dashboard contains no BTC/floating-icon panel. [Run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235).
- [x] GitHub Actions checks: basic checks #202 passed after the role-boundary regression and hero-art cache updates. [Run #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519).
- [ ] Real-device Android testing: **pending**.

## Progress / verification log
- [x] Phase 1 foundation: HOSHI identity/personality prompt added; compact avatar crop from the final character sheet embedded in the frontend.
- [x] Phase 2 foundation: response emotion labels added with deterministic fallback classification and unit-test cases.
- [x] Phase 3 foundation: HOSHI voice labels/input, limited pitch/rate modulation, and an 8-expression sprite with emotion-to-expression mapping added. Full lip-sync and device voice acceptance remain pending.
- [x] Phase 4 foundation: bounded recent context, local history, memory toggle/clear, entry edit/delete, persistent preferences, and a stronger fail-closed privacy filter for likely secrets/contact details. UI discloses that recent context is sent to AI when memory is enabled.
- [x] HOSHI memory controls expanded: individually edit/delete saved user and assistant entries; edits reject obvious sensitive strings, and UI updates use text nodes rather than HTML injection.
- [x] Local preference persistence: language, voice replies (auto-speak), wake-word toggle, personality, pitch, and rate restore after reload.
- [x] Frontend regression suite checks unique HTML IDs and script references, emotion sprite mappings, sprite file validity, and memory/preference controls.
- [x] Phase 5 foundation: responsive dashboard navigation, app shortcuts, HOSHI branding, emotion-linked expression sprite, memory history controls, and Android notification/activity labels updated.
- [x] Phase 6 foundation: existing Gemini/Groq fallback preserved; API keys remain environment variables; README documents current limitations.
- [x] Frontend inline JavaScript compiles successfully in CI; dedicated frontend contract tests also pass.
- [x] Latest Render frontend deployment reached **live**; responsive visual smoke test passed after hero-art and speech-wave integration. [Run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235).
- [x] Render backend deployment reached **live** at commit `21d6409ddfd45055e32e573fcfb3d2a8133ab253`; Render logs showed repeated `GET /health` responses with HTTP 200 and no recent error-level application logs during the check.
- [x] Historical baseline checks were superseded by the newer #160 Chromium dashboard run, #167 backend/contract suite, and #29 live backend smoke test linked above.
- [ ] Realme Note 50 device testing: pending by design; do not start until the remaining task list is addressed.
- [ ] Pixel-perfect full dashboard reproduction, a full animation rig/true lip-sync, end-to-end voice acceptance, and Realme Note 50 testing remain pending/limited. The optimized hero art and animated speech waveform are integrated, but they do not constitute a full animation rig.

## Latest implementation update (2026-10-26)

- [x] Backend context input hardened: accepts only `user:` / `assistant:` history rows, collapses actual control characters and literal escaped newline/tab sequences, limits each entry and retains at most eight recent turns.
- [x] Regression tests added for invalid context roles, multiline entries, literal escaped control sequences, and per-entry/eight-turn bounds.
- [x] Provider request User-Agent and backend module branding updated from stale JARVIS 0.7.0 to HOSHI 0.9.1.
- [x] Confirmed the newest GitHub Actions backend/contract and Chromium browser suites pass after context role-boundary hardening, voice-selection, mobile-overflow fixes, and hero-art/speech-wave integration. [Run #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519).
- [x] Confirmed updated Render backend deployment and current frontend UI with live backend smoke #35 and live responsive dashboard smoke #7. Physical Realme Note 50 test remains deferred until all other available tasks are complete.

- [x] Added `assets/hoshi-expressions.webp`, an 8-state sprite made from the final user-provided character sheet; the dashboard switches sprite positions based on `data-emotion`.
- [x] Bumped the service-worker cache to `hoshi-shell-v11`; it precaches the emotion sprite, privacy helper, and optimized hero art and fetches the current online document before using offline cache.
- [x] Added reusable `memory-privacy.js` and Node tests for credentials, token formats, recovery phrase language, OTPs, email addresses, phone-like strings, and long numeric strings.
- [x] Added Python frontend-contract checks for duplicate/missing HTML IDs, sprite file signature, emotion mappings, local memory controls, and service-worker cache contents.
- [x] Corrected a Gemini multi-block reply separator bug and added a regression test; the assertion was corrected after the first test run exposed an over-escaped expectation.
- [ ] Physical target-device testing remains deferred until the other pending work is addressed, as requested.

- [x] Phase 2 mood signal added: deterministic English/Roman Urdu phrase detection plus safe continuity across short acknowledgements; negation handling prevents common phrases like “udaas nahi” and “not sad” being misread. Regression tests cover positive/negative wording, context carry, and neutral-context reset.
- [x] Phase 3 voice failure handling improved: permission, missing microphone, unsupported language, network, and unknown speech-recognition errors stop automatic restart loops and display actionable states; explicitly selected browser voices are respected. Service-worker cache is `hoshi-shell-v11`.
- [x] Current validation: basic checks #202, live backend smoke #35, and live Render responsive smoke #7 passed. Full conversational/voice acceptance and physical device testing remain pending.

## Working rules
1. This document records requirements; it does not mean implementation is complete.
2. Inspect the current repository and identify working functionality before editing.
3. Keep the two user-provided HOSHI images as the final design source.
4. Make changes in small, testable steps and avoid destructive rewrites.
5. Use free options where practical; explain any unavoidable cost before proceeding.
6. Mark phases complete only after their tests pass; unchecked items remain pending.


## Latest implementation update (2026-10-26 — continued)

- [x] Improved automatic voice choice: prefer exact Urdu-Pakistan voice when installed, then Urdu voices, then female Hindi/other voice fallback; an explicitly selected device voice remains respected. This is still dependent on the device's installed TTS engines and does not create a new neural voice.
- [x] Fixed narrow-screen horizontal overflow in the responsive dashboard. The first browser run exposed a 3px overflow; a viewport-width guard was added and the subsequent full basic check passed.
- [x] Added a native vector HOSHI neon-star launcher icon and pointed Android normal/round icon fields to it.
- [x] Android debug APK build passed after the launcher icon change. [Build run #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290).
- [x] Full basic suite and real-browser dashboard smoke test passed after the mobile overflow fix. [Run #193](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237061426).
- [x] Live Render responsive screenshot/visual smoke test passed after the final-art hero integration. [Run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235).
- [ ] Lip-sync/full avatar rig remains unimplemented because the current asset is a static 8-expression sprite; the existing speaking pulse is only a visual indicator, not mouth synchronization.
- [ ] Target-device Realme Note 50 test remains intentionally deferred until all other available tasks are completed.

# HOSHI AI — Master Transformation Task List

**Current status (26 October 2026):** Core HOSHI persona, Roman Urdu/English mood guidance, context memory, privacy controls, responsive dashboard, native Android bridge, reminders, Gemini/Groq fallback, and existing hosting are implemented. The dashboard has been brought closer to the final user-provided reference with its HOSHI artwork, responsive hero layout, and a speaking waveform/mouth indicator. Prior automated checks and live smoke tests passed; new regression tests for multi-turn context, speaking state, narrow-phone overlap, and native Urdu voice selection were added after those recorded runs and require a fresh CI result. **Realme Note 50 testing remains on hold until all other available work is complete, as requested.**

Repository: [shani001223-droid/Jarws-ai-](https://github.com/shani001223-droid/Jarws-ai-)

Final design sources are the two user-provided images. Keep the navy / electric-blue / cyan palette and retain the existing functional controls; do not replace the live interface with a static screenshot.

## Phase 1 — HOSHI identity and personality

- [x] HOSHI identity and consistent personality guidance.
- [x] Warm, affectionate, playful, shy, annoyed, apologetic, and caring conversation styles where context fits.
- [x] Respectful disagreement and honesty guidance.
- [x] Boundaries against guilt, threats, emotional blackmail, coercion, or dependency pressure.
- [x] Replies match the user's language, including natural Pakistani Roman Urdu guidance.
- [ ] Stochastic real-model multi-turn personality and role-play quality still requires a final acceptance review; automated tests inspect the prompt and context flow, not every possible AI response.

## Phase 2 — Intelligence and emotional understanding

- [x] English/Roman Urdu mood detection with common negation handling.
- [x] Short acknowledgements carry only the immediately preceding user mood; unrelated turns reset it.
- [x] Responses return an emotion label and map it to a close avatar expression.
- [x] Recent conversation context is bounded and sanitized server-side: only user/assistant rows, normalized control sequences, limited entry lengths and at most eight recent entries.
- [x] Regression tests cover role-boundary injection, multiline/escaped sequences, and context limits.
- [ ] Topic tracking remains lightweight; this is a heuristic mood signal, not a trained emotion model.

## Phase 3 — Voice and expressions

- [x] Browser/native speech input and output wiring, voice choice, pitch/rate tuning, speaking-state callbacks, and actionable voice failure messages.
- [x] Automatic voice selection prefers installed Pakistani Urdu (`ur-PK`) when available, then another Urdu voice, then a best-effort feminine-sounding fallback.
- [x] Native Android TTS now gives preference to a matching feminine-hinted `ur-PK` voice, then Urdu, then a fallback voice.
- [x] Emotion-linked 8-expression avatar sprite.
- [x] Visible animated waveform and lightweight mouth overlay while speech is playing; both clear when speaking ends.
- [ ] A natural female Pakistani Urdu accent cannot be guaranteed by code alone. It depends on installed Android/WebView speech engines and downloaded voices; physical voice quality has not been verified on the target phone.
- [ ] True phoneme-synchronized lip-sync is not implemented. The current art is a static expression sprite, not a rigged avatar or timed mouth-shape set. The mouth overlay approximates opening/closing during TTS; it is not timed to phonemes, and true lip-sync remains unimplemented.

## Phase 4 — Memory and personalization

- [x] On-device conversation history with review, edit, delete, clear, and disable controls.
- [x] Persisted settings for language, personality, voice replies, wake-word option, pitch, and rate.
- [x] Secret/contact-information heuristic filter; privacy detection is helpful but not guaranteed to catch all sensitive content.
- [x] UI explains that bounded recent context is sent with cloud requests while memory is enabled.
- [x] Browser UI uses text nodes for saved content and rejects obvious sensitive strings during edits.

## Phase 5 — Final dashboard interface and Android foundation

- [x] Dark navy / neon-cyan theme and responsive sidebar, dashboard panels, shortcuts, chat, status, voice, memory, and settings.
- [x] Integrated compressed HOSHI artwork into the hero and added a speech waveform without replacing live UI controls.
- [x] Responsive breakpoints for desktop, tablet, and phone widths; automated checks guard horizontal overflow and narrow-phone avatar/reply overlap.
- [x] Old BTC/Bitcoin panel and floating icon removed from the dashboard source.
- [x] Native HOSHI branding/launcher icon and a controlled Android WebView-to-native speech/reminder/accessibility bridge.
- [ ] The interface is an interactive responsive adaptation, not a pixel-perfect reconstruction of every lower panel in the reference image. Final visual acceptance still needs checking on the target phone after the code/tests are stable.

## Phase 6 — Existing JARVIS functionality

- [x] Preserved Gemini primary / Groq fallback in the cloud backend.
- [x] API keys remain in the hosting environment; no provider keys are committed to front-end code or the repository.
- [x] Local one-shot reminders, reminder management/recovery wiring, and opt-in basic accessibility actions are retained.
- [x] Existing front-end, reminder, privacy, backend, and Android build workflows retained.
- [x] Context input hardening and tests added without removing the existing service features.

## Phase 7 — Testing, deployment, and delivery

- [x] Previous **HOSHI basic checks #202** passed before the newest follow-up E2E, phone-layout, and native Urdu voice-priority test additions: [run #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519).
- [x] Previous live Render responsive smoke test passed, including narrow viewport checks: [run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235).
- [x] Previous live backend health/AI smoke test passed: [run #35](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237196850).
- [x] Previous Android debug APK build passed and uploaded `hoshi-debug-apk`: [run #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290).
- [x] Rollback steps and release pre-checks documented in [`DEPLOYMENT_ROLLBACK.md`](https://github.com/shani001223-droid/Jarws-ai-/blob/main/DEPLOYMENT_ROLLBACK.md).
- [ ] Obtain a new green automated run after the newest dashboard E2E tests, native voice-priority change, and narrow-phone overlap fix.
- [ ] Confirm the latest Android APK workflow succeeds after the native TTS selection change.
- [ ] Final end-to-end live AI conversation / role-play / real voice acceptance is not equivalent to mocked CI; voice behavior depends on installed device features and the AI provider.
- [ ] Install the current APK and test on the **Realme Note 50 only after all other available code and automated work is complete**. This device test is deliberately deferred.

## Current services and source

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- CI workflow: [HOSHI basic checks](https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/ci.yml)
- APK workflow: [Build HOSHI Android APK](https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/android-apk.yml)
- README: [README.md](https://github.com/shani001223-droid/Jarws-ai-/blob/main/README.md)

## Immediate next steps

1. Confirm the fresh CI run for the most recent commits is green and fix any failures before calling the automated phase done.
2. Confirm the updated frontend deployment is live and the backend remains healthy.
3. Regenerate/confirm the Android debug APK after the native Urdu voice-selection change; do not install it on the target phone yet.
4. Once all available automated and hosted checks are complete, perform the deferred Realme Note 50 test.
5. Publish a final report that separates verified working features from device/provider limitations.

## Working rules

1. Task checkboxes represent implementation or verification, not wishful status.
2. Keep the two user-supplied images as the final design source.
3. Prefer free options; explain unavoidable cost before proceeding.
4. Do not test on the Realme Note 50 until all other available work is finished.

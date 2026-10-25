# HOSHI AI — Android Companion

A mobile-first HOSHI AI companion for Android, using a hosted backend and a responsive web dashboard. The user-provided HOSHI character sheet is used for the dashboard avatar; the dark navy/cyan dashboard is implemented as a responsive layout.

## Current features

- HOSHI dashboard with responsive sidebar navigation, chat, voice, memory, settings, and external app shortcuts.
- Installable web-app metadata uses a scalable SVG HOSHI app icon (`sizes: any`) with explicit 512×512 view dimensions; the browser tab uses the same icon.
- HOSHI identity prompt with language matching, affectionate/playful tone, honesty, and emotional boundaries.
- Conversation emotion labels (happy, sad, affectionate, excited, shy, concerned, annoyed, playful, thinking, caring), character-sheet expression switching, TTS pitch/speed modulation, an animated waveform, and a lightweight mouth overlay while HOSHI speaks.
- Optional local conversation memory with bounded recent context, entry-by-entry review/edit/delete, clear/disable controls, and a tested privacy filter for common credentials, token formats, recovery phrases, OTPs, email addresses, phone-like strings, and long numeric identifiers. Privacy detection is heuristic; it cannot guarantee detection of every sensitive detail.
- Local persistence for language selection, voice-reply (auto-speak) toggle, wake-word toggle, personality, and voice tuning.
- Cloud requests sanitize client-provided conversation context: only `user:` and `assistant:` entries are retained, control characters and escaped newline/tab sequences are flattened, and the latest eight entries are bounded to under 500 characters each.
- Cloud AI using Gemini Interactions API with Groq as a fallback provider.
- Voice reply settings: choose an installed phone voice, adjust pitch/speed, and play a preview. Browser and native Android auto-selection prefer an installed Pakistani Urdu (`ur-PK`) voice where available, then Urdu and best-effort alternatives.
- `assets/hoshi-expressions.webp` is a compact 8-tile WebP sprite cropped from the final user-provided character sheet. The dashboard switches the sprite position for each response emotion; ten emotion labels map to the closest of the eight available expressions.
- Local one-shot reminders can be listed/cancelled from **View / cancel reminders**, scheduled from **Set reminder**, or created by typing commands such as “remind me to drink water in 10 minutes,” “remind me in 2 hours to call mom,” or “mujhe 10 minute baad pani peene yaad dilao.” They use Android notifications and are scheduled again after reboot, without needing cloud AI to trigger.
- Optional user-triggered Accessibility actions: Back, Home, Swipe up, and Swipe down. The service does not retrieve screen content or upload screen text.
- GitHub Actions runs Python tests, JavaScript syntax checks, a Chromium dashboard smoke test with a mocked cloud API, a live backend smoke test, and an Android debug APK build.

## Install the Android test APK

1. Open the latest successful **Build HOSHI Android APK** workflow in the [GitHub Actions page](https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/android-apk.yml).
2. Open its **Artifacts** section and download `hoshi-debug-apk`.
3. Extract the ZIP, then open `app-debug.apk` on the Android phone.
4. Android may ask you to allow your browser or file manager to install unknown apps. Allow it only for the app you used to download this APK, then install.
5. Open **HOSHI AI** and keep internet access enabled.
6. To enable basic phone gestures, tap **Screen controls**, accept the explanation, and turn on **HOSHI basic screen controls** in Android Accessibility settings. Only Back/Home/Swipe actions from the dashboard are available.
7. Tap **Set reminder** to schedule locally, or type a supported reminder command into the dashboard. Allow notifications when requested; tap **View / cancel reminders** to manage them.
8. The dashboard will ask for microphone permission when you deliberately start voice recognition.

## Important limitations

- This is a debug/test APK, not a Play Store release. It has not been validated on the target Realme Note 50 during this session.
- The full character sheet and complete dashboard screenshot are not embedded as full-resolution backgrounds; the optimized HOSHI hero artwork and key dashboard arrangement are implemented as a responsive interactive adaptation, not a pixel-perfect reproduction of every reference panel.
- Eight compact expressions are available in a sprite and mapped to ten emotion labels. During TTS, an approximate mouth overlay opens/closes alongside the animated waveform; it follows speech start/stop state but is not phoneme-synchronized lip-sync. A true rig/timed mouth-shape set is not implemented.
- Local memory stores recent turns in browser local storage. Entry review/edit/delete and clear/disable controls are available. The privacy filter blocks common credential terms, token shapes, recovery-phrase language, OTPs, email addresses, phone-like strings, and long numbers; it is heuristic and cannot guarantee every secret is detected. If the privacy utility fails to load, local storage fails closed and does not save messages. When memory is enabled, a bounded recent context is sent to the backend with AI requests; turn memory off to stop that context being sent.
- Voice quality and choices depend on the speech engines installed on the Android device. Automatic selection prioritizes `ur-PK` where present, then Urdu, then an available feminine-sounding fallback; no code-only change can guarantee a natural female Pakistani accent or install a missing voice.
- The hosted backend requires internet. Gemini free-tier limits can be exhausted; Groq is configured as the backup, but provider policies and free limits can change. Local reminders run on-device; Android power-saving may deliver them a little late.
- API keys remain in the private Render environment; never place them in frontend code, an APK, or a public repository.

## HOSHI implementation and verification status

- Backend personality, contextual mood guidance for English/Roman Urdu, recent-context support, anti-repetition guidance, negation-aware mood detection, and Groq fallback are implemented in `cloud_backend/main.py`. Mood detection remains a lightweight rule-based heuristic and carries prior mood only across short acknowledgements.
- Backend service deployed successfully after a transient syntax error was caught and fixed. Render logs showed `/health` returning HTTP 200 and no recent error-level application logs at the time of verification.
- Frontend source checks and the prior live Render responsive smoke test passed on the hero-art/speech-wave dashboard. [Run #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235). The latest narrow-phone overlap fix and expanded multi-turn/speaking-wave E2E checks were committed afterward and need a fresh CI/live responsive confirmation.
- GitHub Actions **HOSHI basic checks run #202 passed** for the then-current backend/unit, frontend-contract, privacy, reminder/parser, roleplay-boundary, mood-negation, JavaScript, and browser smoke tests. [Run #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519). Fresh checks are pending after the later multi-turn E2E, mouth-animation lifecycle, narrow-phone, native Urdu voice-priority, and PWA icon/cache additions.
- GitHub Pages publish workflow **run #227 passed** after the hero-art/speech-wave contract update. [Run #227](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303752).
- GitHub Actions **HOSHI live backend smoke test run #35 passed** after adding transient gateway retries and correcting HTTP status parsing; it verified a non-empty live AI reply from the configured provider. [Run #35](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237196850).
- GitHub Actions **Build HOSHI Android APK run #32 passed** after the HOSHI neon-star launcher icon update. [Run #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290). The native TTS voice-priority code changed after that run, so a fresh APK build is required before target-device testing. No physical phone test has been started.
- The lightweight mouth overlay is an approximation and has a lifecycle test; accurate phoneme-synchronized lip-sync, real-device voice/microphone acceptance, and confirmation of a natural female Pakistani Urdu accent remain pending.

## Services

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- Repository: https://github.com/shani001223-droid/Jarws-ai-

## Latest frontend improvements

- Memory history has per-entry **Edit**/**Delete**, plus clear/disable controls. Text uses DOM text nodes, edited content is limited to 500 characters, and obvious sensitive strings are rejected.
- Language selection, voice replies, wake-word toggle, personality, pitch, and rate persist locally across reloads. An explicitly selected browser/device voice is respected rather than always forcing native Android TTS. Overlapping cloud requests supersede prior requests so stale results do not overwrite newer replies.
- Hero-level Chat / Voice / Vision / Create / More shortcuts have working click handlers with browser-mode fallbacks.
- Automatic browser and native Android voice selection now prefer installed `ur-PK` voices when available, then other Urdu voices, then best-effort feminine-sounding fallbacks. An explicit browser voice selection takes priority. Accent and gender are device-engine-dependent; missing voices cannot be installed by HOSHI.
- The face is an 8-expression WebP sprite from the final character sheet. `data-emotion` switches the sprite position; service-worker cache `hoshi-shell-v12` precaches the sprite, privacy helper, optimized hero artwork, and HOSHI app icon for offline loading. Speaking shows an animated waveform and a lightweight mouth overlay; it is not phoneme-synchronized lip-sync.
- A shared `memory-privacy.js` helper applies privacy filters before local history save/edit. Node tests exercise common credential/token formats, recovery phrases, OTPs, contact information, and long numeric strings.
- Python frontend-contract tests verify unique HTML IDs, script references, valid WebP headers, emotion mappings, memory controls, cache contents, and actionable voice-error recovery paths.
- Previously confirmed runs: [HOSHI basic checks #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519), [live Render dashboard smoke #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235), [live backend smoke #35](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237196850), and [Android APK #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290). The latest multi-turn, waveform/mouth-lifecycle, narrow-phone, native Urdu voice, and PWA icon/cache regression additions need fresh automated run results.
- Deployment safety notes are in [`DEPLOYMENT_ROLLBACK.md`](https://github.com/shani001223-droid/Jarws-ai-/blob/main/DEPLOYMENT_ROLLBACK.md). The frontend Render service reports the latest source deployment as live; a fresh visual/browser smoke confirmation after the final narrow-phone change remains pending.

## Remaining real-device checks

- Install the latest debug APK and verify audible speech through Android Text-to-Speech. The app uses native TTS first and browser speech synthesis only as a browser fallback.
- Test microphone permission and voice recognition on the phone; Web Speech recognition support depends on installed browser/WebView support.
- Test local reminder delivery and reboot recovery on the target phone.

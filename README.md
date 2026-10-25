# HOSHI AI — Android Companion

A mobile-first HOSHI AI companion for Android, using a hosted backend and a responsive web dashboard. The user-provided HOSHI character sheet is used for the dashboard avatar; the dark navy/cyan dashboard is implemented as a responsive layout.

## Current features

- HOSHI dashboard with responsive sidebar navigation, chat, voice, memory, settings, and external app shortcuts.
- HOSHI identity prompt with language matching, affectionate/playful tone, honesty, and emotional boundaries.
- Conversation emotion labels (happy, sad, affectionate, excited, shy, concerned, annoyed, playful, thinking, caring), actual character-sheet expression sprite switching, and limited TTS pitch/speed modulation.
- Optional local conversation memory with bounded recent context, entry-by-entry review/edit/delete, clear/disable controls, and a tested privacy filter for common credentials, token formats, recovery phrases, OTPs, email addresses, phone-like strings, and long numeric identifiers. Privacy detection is heuristic; it cannot guarantee detection of every sensitive detail.
- Local persistence for language selection, voice-reply (auto-speak) toggle, wake-word toggle, personality, and voice tuning.
- Cloud requests sanitize client-provided conversation context: only `user:` and `assistant:` entries are retained, control characters and escaped newline/tab sequences are flattened, and the latest eight entries are bounded to under 500 characters each.
- Cloud AI using Gemini Interactions API with Groq as a fallback provider.
- Voice reply settings: choose an installed phone voice, adjust pitch/speed, and play a preview.
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
- The full character sheet and full dashboard reference are not embedded as full-resolution files; the dashboard is responsive but not a pixel-perfect reproduction of every reference panel.
- Eight compact expressions are available in a sprite and mapped to ten emotion labels. There is no full animation rig or lip-sync yet.
- Local memory stores recent turns in browser local storage. Entry review/edit/delete and clear/disable controls are available. The privacy filter blocks common credential terms, token shapes, recovery-phrase language, OTPs, email addresses, phone-like strings, and long numbers; it is heuristic and cannot guarantee every secret is detected. If the privacy utility fails to load, local storage fails closed and does not save messages. When memory is enabled, a bounded recent context is sent to the backend with AI requests; turn memory off to stop that context being sent.
- Voice quality and voice choices depend on the speech engines installed on the Android device. The dashboard can select and tune available voices but cannot install a premium neural voice on its own.
- The hosted backend requires internet. Gemini free-tier limits can be exhausted; Groq is configured as the backup, but provider policies and free limits can change. Local reminders run on-device; Android power-saving may deliver them a little late.
- API keys remain in the private Render environment; never place them in frontend code, an APK, or a public repository.

## HOSHI implementation and verification status

- Backend personality, contextual mood guidance for English/Roman Urdu, recent-context support, anti-repetition guidance, negation-aware mood detection, and Groq fallback are implemented in `cloud_backend/main.py`. Mood detection remains a lightweight rule-based heuristic and carries prior mood only across short acknowledgements.
- Backend service deployed successfully after a transient syntax error was caught and fixed. Render logs showed `/health` returning HTTP 200 and no recent error-level application logs at the time of verification.
- Frontend source checks and Chromium dashboard smoke tests pass after the narrow-phone overflow fix; the live Render responsive smoke test is being rechecked after the latest deployment.
- GitHub Actions **HOSHI basic checks run #167 passed**, including Python/unit tests, frontend-contract tests, privacy-filter tests, reminder/parser tests, roleplay-boundary assertions, negation-aware mood tests, and JavaScript syntax checks. [Run #167](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40235947933).
- GitHub Pages publish workflow **run #192 passed** after the mood-negation test update. This verifies the static site build; it does not replace live Render frontend/device checks. [Run #192](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40235947839).
- GitHub Actions **HOSHI live backend smoke test run #29 passed** after adding transient gateway retries and correcting HTTP status parsing; it verified a non-empty live AI reply from the configured provider. [Run #29](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40236085531).
- GitHub Actions **Build HOSHI Android APK run #32 passed** after adding the HOSHI neon-star native launcher icon; the `hoshi-debug-apk` artifact was uploaded. [Run #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290). It has not been installed on a physical phone in this session.
- Real-device voice/microphone testing and lip-sync remain pending.

## Services

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- Repository: https://github.com/shani001223-droid/Jarws-ai-

## Latest frontend improvements

- Memory history has per-entry **Edit**/**Delete**, plus clear/disable controls. Text uses DOM text nodes, edited content is limited to 500 characters, and obvious sensitive strings are rejected.
- Language selection, voice replies, wake-word toggle, personality, pitch, and rate persist locally across reloads. An explicitly selected browser/device voice is respected rather than always forcing native Android TTS. Overlapping cloud requests supersede prior requests so stale results do not overwrite newer replies.
- Hero-level Chat / Voice / Vision / Create / More shortcuts have working click handlers with browser-mode fallbacks.
- Automatic browser voice selection now prefers an installed `ur-PK` voice, then other Urdu voices, then a female Hindi/other fallback. An explicit user-selected voice always takes priority; the app cannot install a voice that is missing from Android.
- The face is an 8-expression WebP sprite from the final character sheet. `data-emotion` switches the sprite position; service-worker cache `hoshi-shell-v10` precaches the sprite and privacy helper for offline loading. Speaking currently adds a gentle pulse; it is not true lip-sync.
- A shared `memory-privacy.js` helper applies privacy filters before local history save/edit. Node tests exercise common credential/token formats, recovery phrases, OTPs, contact information, and long numeric strings.
- Python frontend-contract tests verify unique HTML IDs, script references, valid WebP headers, emotion mappings, memory controls, cache contents, and actionable voice-error recovery paths.
- Latest basic checks and the local Chromium dashboard smoke test passed: [HOSHI basic checks #193](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237061426). [Android APK #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290) passed with the new native HOSHI launcher icon. The live Render responsive check, full voice acceptance, and target-phone testing remain separate items.
- Deployment safety notes are in [`DEPLOYMENT_ROLLBACK.md`](https://github.com/shani001223-droid/Jarws-ai-/blob/main/DEPLOYMENT_ROLLBACK.md); actual live Render UI verification remains pending.

## Remaining real-device checks

- Install the latest debug APK and verify audible speech through Android Text-to-Speech. The app uses native TTS first and browser speech synthesis only as a browser fallback.
- Test microphone permission and voice recognition on the phone; Web Speech recognition support depends on installed browser/WebView support.
- Test local reminder delivery and reboot recovery on the target phone.

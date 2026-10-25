# HOSHI AI — Android Companion

A mobile-first HOSHI AI companion for Android, using a hosted backend and a responsive web dashboard. The user-provided HOSHI character sheet is used for the dashboard avatar; the dark navy/cyan dashboard is implemented as a responsive layout.

## Current features

- HOSHI dashboard with responsive sidebar navigation, chat, voice, memory, settings, and external app shortcuts.
- HOSHI identity prompt with language matching, affectionate/playful tone, honesty, and emotional boundaries.
- Conversation emotion labels (happy, sad, affectionate, excited, shy, concerned, annoyed, playful, thinking, caring), actual character-sheet expression sprite switching, and limited TTS pitch/speed modulation.
- Optional local conversation memory with bounded recent context, entry-by-entry review/edit/delete, clear/disable controls, and a tested privacy filter for common credentials, token formats, recovery phrases, OTPs, email addresses, phone-like strings, and long numeric identifiers. Privacy detection is heuristic; it cannot guarantee detection of every sensitive detail.
- Local persistence for language selection, voice-reply (auto-speak) toggle, wake-word toggle, personality, and voice tuning.
- Cloud AI using Gemini Interactions API with Groq as a fallback provider.
- Voice reply settings: choose an installed phone voice, adjust pitch/speed, and play a preview.
- `assets/hoshi-expressions.webp` is a compact 8-tile WebP sprite cropped from the final user-provided character sheet. The dashboard switches the sprite position for each response emotion; ten emotion labels map to the closest of the eight available expressions.
- Local one-shot reminders can be listed/cancelled from **View / cancel reminders**, scheduled from **Set reminder**, or created by typing commands such as “remind me to drink water in 10 minutes,” “remind me in 2 hours to call mom,” or “mujhe 10 minute baad pani peene yaad dilao.” They use Android notifications and are scheduled again after reboot, without needing cloud AI to trigger.
- Optional user-triggered Accessibility actions: Back, Home, Swipe up, and Swipe down. The service does not retrieve screen content or upload screen text.
- GitHub Actions runs Python tests, JavaScript syntax checks, a live backend smoke test, and an Android debug APK build.

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

- Backend personality, emotion labels, recent-context support, and Groq fallback are implemented in `cloud_backend/main.py`.
- Backend service deployed successfully after a transient syntax error was caught and fixed. Render logs showed `/health` returning HTTP 200 and no recent error-level application logs at the time of verification.
- Frontend source build and static contract checks pass; a fresh live Render visual check after the latest sprite/privacy changes remains pending.
- GitHub Actions **HOSHI basic checks run #112 passed** on implementation commit `e4141eea0e01396be09380bb4b2e2095a68e1a26`, including Python/unit tests, frontend-contract tests, privacy-filter tests, reminder/parser tests, and JavaScript syntax compilation.
- GitHub Pages publish workflow **run #137 passed** on the same implementation/test commit. This verifies the static site build; it does not replace a live Render frontend/device check.
- GitHub Actions **HOSHI live backend smoke test run #23 passed** after the Gemini multi-block reply fix, including a successful live AI request through the configured Groq fallback.
- GitHub Actions **Build HOSHI Android APK run #24 passed** on commit `c5737b886e108c9aa368a9ce8efe27f88f8073a2`; the `hoshi-debug-apk` artifact was uploaded. No native Android source changes were made after that build.
- Real-device voice/microphone testing and lip-sync remain pending.

## Services

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- Repository: https://github.com/shani001223-droid/Jarws-ai-

## Latest frontend improvements

- Memory history has per-entry **Edit**/**Delete**, plus clear/disable controls. Text uses DOM text nodes, edited content is limited to 500 characters, and obvious sensitive strings are rejected.
- Language selection, voice replies, wake-word toggle, personality, pitch, and rate persist locally across reloads.
- The face is now an 8-expression WebP sprite from the final character sheet. `data-emotion` switches the sprite position; service-worker cache `hoshi-shell-v9` precaches the sprite and privacy helper for offline loading.
- A shared `memory-privacy.js` helper applies privacy filters before local history save/edit. Node tests exercise common credential/token formats, recovery phrases, OTPs, contact information, and long numeric strings.
- Python frontend-contract tests verify unique HTML IDs, script references, valid WebP headers, emotion mappings, memory control elements, and cache contents.
- Current check links: [HOSHI basic checks #112](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40231996689), [GitHub Pages publish #137](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40231996381), [Android APK #24](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40231091328). Render live visual validation and target-phone testing are still pending.

## Remaining real-device checks

- Install the latest debug APK and verify audible speech through Android Text-to-Speech. The app uses native TTS first and browser speech synthesis only as a browser fallback.
- Test microphone permission and voice recognition on the phone; Web Speech recognition support depends on installed browser/WebView support.
- Test local reminder delivery and reboot recovery on the target phone.

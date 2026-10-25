# HOSHI AI — Android Companion

A mobile-first HOSHI AI companion for Android, using a hosted backend and a responsive web dashboard. The user-provided HOSHI character sheet is used for the dashboard avatar; the dark navy/cyan dashboard is implemented as a responsive layout.

## Current features

- HOSHI dashboard with responsive sidebar navigation, chat, voice, memory, settings, and external app shortcuts.
- HOSHI identity prompt with language matching, affectionate/playful tone, honesty, and emotional boundaries.
- Conversation emotion labels (happy, sad, affectionate, excited, shy, concerned, annoyed, playful, thinking, caring) with avatar styling and limited TTS pitch/speed modulation.
- Optional local conversation memory, bounded recent context, clear/disable controls, and basic filtering to avoid saving obvious secrets.
- Cloud AI using Gemini Interactions API with Groq as a fallback provider.
- Voice reply settings: choose an installed phone voice, adjust pitch/speed, and play a preview.
- A cropped avatar from the final HOSHI character sheet is embedded in the dashboard.
- Local one-shot reminders can be listed/cancelled from **View / cancel reminders**, scheduled from **Set reminder**, or created by typing commands such as “remind me to drink water in 10 minutes,” “remind me in 2 hours to call mom,” or “mujhe 10 minute baad pani peene yaad dilao.” They use Android notifications and are scheduled again after reboot, without needing cloud AI to trigger.
- Optional user-triggered Accessibility actions: Back, Home, Swipe up, and Swipe down. The service does not retrieve screen content or upload screen text.
- GitHub Actions runs Python tests, JavaScript syntax checks, a live backend smoke test, and an Android debug APK build.

## Install the Android test APK

1. Open the latest successful **Build JARVIS Android APK** workflow in the [GitHub Actions page](https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/android-apk.yml).
2. Open its **Artifacts** section and download `jarvis-debug-apk`.
3. Extract the ZIP, then open `app-debug.apk` on the Android phone.
4. Android may ask you to allow your browser or file manager to install unknown apps. Allow it only for the app you used to download this APK, then install.
5. Open **HOSHI AI** and keep internet access enabled.
6. To use the draggable icon, tap **Grant overlay permission** or **Start / show floating icon**, and grant Android's **Display over other apps** permission.
7. To enable basic phone gestures, tap **Screen controls**, accept the explanation, and turn on **JARVIS basic screen controls** in Android Accessibility settings. Only Back/Home/Swipe actions from the dashboard are available.
8. Tap **Set reminder** to schedule locally, or type a supported reminder command into the dashboard. Allow notifications when requested; tap **View / cancel reminders** to manage them.
9. The dashboard will ask for microphone permission when you deliberately start voice recognition. The floating icon can be stopped from the app or its persistent notification.

## Important limitations

- This is a debug/test APK, not a Play Store release. It has not been validated on the target Realme Note 50 during this session.
- The full character sheet and full dashboard reference are not embedded as full-resolution files in the repository; only a compact avatar crop is embedded. The responsive dashboard implements the core layout but is not a pixel-perfect reproduction of every reference panel.
- Emotional expressions are currently CSS effects and keyword/model labels, not a full animation rig. Lip-sync is not implemented.
- Local memory stores recent turns in browser local storage. When memory is enabled, a bounded recent context is sent to the backend with AI requests; turn memory off to stop that context being sent.
- Voice quality and voice choices depend on the speech engines installed on the Android device. The dashboard can select and tune available voices but cannot install a premium neural voice on its own.
- The hosted backend requires internet. Gemini free-tier limits can be exhausted; Groq is configured as the backup, but provider policies and free limits can change. Local reminders run on-device; Android power-saving may deliver them a little late.
- API keys remain in the private Render environment; never place them in frontend code, an APK, or a public repository.

## HOSHI implementation and verification status

- Backend personality, emotion labels, recent-context support, and Groq fallback are implemented in `cloud_backend/main.py`.
- Backend service deployed successfully after a transient syntax error was caught and fixed. Render logs showed `/health` returning HTTP 200 and no recent error-level application logs at the time of verification.
- Frontend deployed successfully; its inline JavaScript passed a syntax compilation check in this session.
- GitHub Actions workflow definitions exist for Python tests, JavaScript checks, and Android debug APK builds. The latest GitHub Actions run results could not be independently read through the available GitHub connection, so they are not claimed as passing here.
- Real-device voice/microphone testing and lip-sync remain pending.

## Services

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- Repository: https://github.com/shani001223-droid/Jarws-ai-

## Remaining real-device checks

- Install the latest debug APK and verify audible speech through Android Text-to-Speech. The app uses native TTS first and browser speech synthesis only as a browser fallback.
- Test microphone permission and voice recognition on the phone; Web Speech recognition support depends on installed browser/WebView support.
- Test local reminder delivery and reboot recovery on the target phone.

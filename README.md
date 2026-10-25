# JARVIS Assistant

A mobile-first personal AI assistant prototype for Android, with a hosted AI backend and an optional floating companion icon.

## Current features

- Hosted assistant dashboard with Urdu/Roman Urdu and English text commands.
- Cloud AI using Gemini Interactions API with Groq as a fallback provider.
- Voice reply settings: choose an installed phone voice, adjust pitch/speed, and play a preview.
- Generated anime avatar shown on the dashboard and the draggable Android floating icon.
- Floating icon size slider, saved locally on the phone.
- The floating service has a persistent Android notification and an explicit Stop action.
- GitHub Actions runs Python tests, JavaScript syntax checks, a live backend smoke test, and an Android debug APK build.

## Install the Android test APK

1. Open the latest successful **Build JARVIS Android APK** workflow in the [GitHub Actions page](https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/android-apk.yml).
2. Open its **Artifacts** section and download `jarvis-debug-apk`.
3. Extract the ZIP, then open `app-debug.apk` on the Android phone.
4. Android may ask you to allow your browser or file manager to install unknown apps. Allow it only for the app you used to download this APK, then install.
5. Open **JARVIS Assistant** and keep internet access enabled.
6. To use the draggable icon, tap **Enable floating icon** and grant Android's **Display over other apps** permission.
7. The dashboard will ask for microphone permission when you deliberately start voice recognition. The floating icon can be stopped from the app or its persistent notification.

## Important limitations

- This is a debug/test APK, not a Play Store release. It has only been build-tested with GitHub Actions; it has not been validated on every phone model.
- The floating icon opens the JARVIS dashboard; it does not yet independently tap buttons in other apps, read all screen contents, or control the whole phone.
- Voice quality and voice choices depend on the speech engines installed on the Android device. The dashboard can select and tune available voices but cannot install a premium neural voice on its own.
- The hosted backend requires internet. Gemini free-tier limits can be exhausted; Groq is configured as the backup, but provider policies and free limits can change.
- API keys remain in the private Render environment; never place them in frontend code, an APK, or a public repository.

## Services

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- Repository: https://github.com/shani001223-droid/Jarws-ai-

## Next roadmap

1. Test the current APK on the target Android phone and refine the anime/voice experience.
2. Add opt-in, clearly disclosed accessibility actions for limited user-triggered screen navigation.
3. Add persistent reminders and local settings.
4. Build separate, user-approved integrations for trading analysis, Flora business management, and social/video automation instead of giving one assistant unlimited access by default.

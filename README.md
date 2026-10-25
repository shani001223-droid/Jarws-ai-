# JARVIS Assistant — v0.9.0

A mobile-first personal assistant prototype with a FastAPI cloud backend, HTML/JavaScript dashboard, and Android WebView/native Text-to-Speech bridge.

## v0.9.0 features

- **Conversation memory:** server-side SQLite stores successful user/assistant turns per opaque conversation UUID. The model receives a bounded recent history (up to 12 messages / 6 turns), with a default 30-day retention policy and an 80-message per-conversation cap.
- **Gemini + Groq:** Gemini Interactions API is the primary provider; Groq is the fallback. Provider HTTP timeouts default to 15 seconds each and can be configured from 3–30 seconds.
- **Stop speaking:** the dashboard has a dedicated control that calls Android native TTS stop and cancels browser speech. It also suppresses speech for an AI response that arrives after the user presses Stop.
- **Allowlisted Android intents:** local voice commands can open the installed YouTube app or WhatsApp; the Browser command opens a fixed HTTPS destination in the default browser. Unknown package names and arbitrary URLs are rejected by the native bridge.
- **Dynamic theme and natural tone:** Cyan, Violet, and Rose accent themes are switchable and saved locally. AI instructions encourage clear, natural Roman Urdu/English and prohibit unsupported claims about device control.
- Existing local reminders, reboot rescheduling, optional user-triggered basic Accessibility gestures, voice settings, and reminder management remain available.

## Configure Render environment

Set secrets only in the **backend service's Render Environment**. Never commit API keys, embed them in `index.html`, or package them in the APK.

- `GEMINI_API_KEY`: primary provider key.
- `GROQ_API_KEY`: optional fallback key.
- `GEMINI_MODEL` / `GROQ_MODEL`: optional model overrides.
- `GEMINI_TIMEOUT_SECONDS` / `GROQ_TIMEOUT_SECONDS`: optional request timeout values (3–30 seconds; default 15).
- `ALLOWED_ORIGINS`: comma-separated origins allowed by CORS. The default is only `https://jarws-ai-1.onrender.com`; add development origins intentionally.
- `JARVIS_DB_PATH`: optional absolute path for the SQLite memory file.
- `JARVIS_MEMORY_RETENTION_DAYS`: optional retention from 1 to 365 days (default 30).

The API accepts a client-generated random UUID as `conversation_id`; the front end stores it locally and sends it with each cloud message. The API does not expose an endpoint to retrieve arbitrary conversation records. Memory content and conversation IDs are not logged by the memory layer.

### Important persistence limitation

SQLite is server-side and survives ordinary requests while its database file remains available. **Render Free web services have an ephemeral filesystem**: local files can be lost when the service spins down, restarts, or redeploys. Setting `JARVIS_DB_PATH` to another path inside the same ephemeral filesystem does not make it durable. For reliable memory across those events, configure a genuinely persistent storage location or a durable external database. The default database path is suitable for a free-tier prototype, not guaranteed long-term storage.

### Free-tier latency

The front end checks backend health at startup and sends a light health request about every four minutes only while the dashboard is visible. This can keep the API warm during active use but is not an always-on guarantee: Render Free web services spin down after 15 minutes without inbound traffic and may take about a minute to start again. External keep-alive spam is not used. Provider timeouts are bounded so one slow provider cannot hold the request indefinitely.

## Install the Android test APK

1. Open the latest successful **Build JARVIS Android APK** workflow in the [GitHub Actions page](https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/android-apk.yml).
2. Open its **Artifacts** section and download `jarvis-debug-apk`.
3. Extract the ZIP, then open `app-debug.apk` on the Android phone.
4. Android may ask you to allow your browser or file manager to install unknown apps. Allow it only for the app you used to download this APK.
5. Open **JARVIS Assistant** and keep internet access enabled.
6. Start voice recognition only when needed; the app asks for microphone permission when the dashboard requests it.
7. Use **Stop speaking** to immediately stop current speech. Use **New chat** to start a fresh conversation context while the older session remains available until its retention window expires.
8. App launch commands are restricted to YouTube, WhatsApp and the default browser. JARVIS requests no contacts, SMS, call-log, or broad package permissions to support them.

## Security and limitations

- This is a debug/test APK, not a Play Store release. CI build success does not replace testing on the target Android phone.
- API keys stay server-side in Render Environment. The frontend and APK contain only public service URLs, never provider secrets.
- CORS restricts browser origins; it is not authentication. Do not expose personal or sensitive conversations through a public production deployment without proper user authentication and authorization.
- Conversation context is bounded to limit latency and input cost. It is not a permanent personal knowledge base and is not shared between different conversation IDs.
- Android TTS voice quality depends on speech engines installed on the phone. Browser speech recognition support varies by WebView/device.
- Render Free storage is ephemeral; local SQLite memory can disappear at spin-down or redeploy. Free hosting is appropriate for testing/hobby use rather than a durability guarantee.

## Services

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- Repository: https://github.com/shani001223-droid/Jarws-ai-

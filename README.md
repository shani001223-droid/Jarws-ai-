# JARVIS — Mobile-first Personal AI Assistant

A mobile-first prototype for Android, initially targeting the user's Realme Note 50. This is the first UI/voice milestone, not yet a full AI agent or native Android application.

## Current prototype
- Responsive dark mobile interface.
- Text command input and browser speech output.
- Browser speech-recognition controls where supported.
- Optional “Hey JARVIS” wake phrase while the page is open and foregrounded.
- Basic local commands: time, date, greetings, help, open Google, open YouTube.
- PWA manifest and a small service-worker cache for the app shell.

## Important limitations
- Wake-word detection is NOT a system-wide or always-on Android service. The browser must remain open/foregrounded and microphone access must be granted. It may stop when the screen locks, the browser is backgrounded, or Android suspends the tab.
- Browser speech recognition support varies by browser, device, language and network.
- The current command handler is local demo logic. A real AI backend, secure tool routing, persistent memory and account integrations are not connected.
- The app cannot freely control every app or website. Native Android accessibility and other platform permissions require a native Android implementation and explicit user consent.
- Do not put API keys, Telegram tokens, passwords or exchange secrets in browser code or this public repository.

## Architecture roadmap
1. Stage 1 — Mobile voice shell (current): responsive interface, text/voice commands, wake-word prototype.
2. Stage 2 — AI core: small backend API, provider abstraction, safe intent/tool router, user-approved memory. Keep provider keys server-side.
3. Stage 3 — Native Android shell: package with a maintained Android framework; implement microphone lifecycle and foreground service only within Android policy, with a visible notification and battery/privacy controls.
4. Stage 4 — Phone actions: explicit, permission-gated accessibility/intent actions; ask before sending messages, purchases, account changes or other sensitive actions.
5. Stage 5 — Integrations: calendar/reminders, then Flora marketing/social workflows, then existing JARVES Telegram bot. Trading remains demo-only until independently tested.

## Free-first choices and costs
- Static web app/PWA and GitHub repository: can be developed without a paid service.
- Browser speech recognition: availability and limits are controlled by the browser; it is not guaranteed to work offline.
- AI brain: no paid provider is configured yet. A hosted model/API may have free quotas but can impose limits or later charges. Do not enable billing until cost and quota are reviewed.
- Native Android build and 24/7 backend hosting may need a cloud build/runtime. We will choose a free tier where available and explain any unavoidable cost before using it.

## Test on phone
1. Open the repository in GitHub and confirm index.html, manifest.json, and sw.js exist.
2. Publish the repository with GitHub Pages (Settings → Pages → deploy from main branch, root folder), if Pages is available.
3. Open the HTTPS Pages URL in Chrome on Android.
4. Grant microphone permission, tap Start listening, and test “Hey JARVIS”, “what time is it”, and “open Google”.
5. Test with screen unlocked and app foregrounded. This web prototype is not expected to listen after the phone is locked.

## Security principles
- Keep secrets out of GitHub and client-side JavaScript.
- Prefer least-privilege permissions.
- Ask for confirmation before consequential external actions.
- Do not claim automation succeeded unless the connected service confirms it.

# JARVIS — Cloud-first Personal AI Assistant

## Product decision
The phone should be a lightweight dashboard/control panel only. Heavy work belongs on a cloud backend. Do not turn this into a large on-device AI app or download a model onto the phone.

## Architecture
- **Mobile dashboard (static PWA):** hosted as a small web page; shows status, chat/voice controls and settings. It should not contain provider secrets or heavy models.
- **Cloud API:** `cloud_backend/main.py` is a FastAPI starter with `/health` and `/api/assistant` endpoints. The dashboard sends non-basic chat to this API. Gemini replies require a valid `GEMINI_API_KEY` configured as a Render environment secret.
- **Cloud workers (later):** scheduled jobs and queued workflows for reminders, social content, Flora marketing and Telegram integrations.
- **Integrations:** add one at a time with minimum permissions and server-side credentials. Trading remains demo-only until independently tested.

## Current implementation
- Responsive mobile dashboard at `index.html`.
- Browser voice input/output where supported, with Urdu/Roman Urdu and English command modes.
- Basic local commands for time, date, Google, YouTube, greeting, and help.
- Cloud status badge distinguishes API availability from AI-key readiness.
- A foreground-only browser wake phrase prototype. It is not an always-on system wake word.
- PWA manifest and service worker for a small app shell.
- Initial FastAPI backend, requirements, environment template and Dockerfile under `cloud_backend/`.

## Important wake-word limitation
To avoid heavy on-device processing, the realistic design is a small on-device wake-word detector that listens locally, then streams/processes audio in the cloud only after activation. Cloud-only continuous listening would require the phone to continuously send microphone audio, which drains battery, uses data and raises privacy concerns. A browser page cannot reliably listen while closed or the phone is locked. A native Android foreground service with a visible notification may be required for a true background wake word.

## Deploy the cloud API
1. Create a Python web service on a provider with a suitable free tier (availability and free quotas can change).
2. Set its root/build context to `cloud_backend/`, install `requirements.txt`, and run `uvicorn main:app --host 0.0.0.0 --port $PORT` (or use the included Dockerfile).
3. Configure `ALLOWED_ORIGINS` to the exact HTTPS origin serving the dashboard. Do not use `*` in production.
4. Open `/health` on the deployed service. It returns `ok: true`; `ai_connected` is true only when `GEMINI_API_KEY` is present in the backend environment.
5. The dashboard is connected to `/api/assistant`; check the dashboard status and Render logs if chat fails.

## Cost policy
- Static dashboard and this starter backend do not require a paid AI API key.
- Cloud hosts may offer free tiers but can have sleep, usage, or runtime limits. Confirm current terms before deployment.
- Gemini is supported by the backend when its API key is configured. Check current Google AI Studio quotas and terms; do not assume unlimited free usage.

## Security
- Never commit `.env` files, API keys, Telegram tokens, passwords or exchange secrets.
- Put credentials in the cloud host's secret/environment settings.
- Before adding account actions, use authentication, rate limits, logs that exclude secrets, and user confirmation for sensitive actions.
- Never expose the cloud API publicly for consequential actions without authentication.

## Roadmap
1. Deploy and verify cloud API health.
2. Connect dashboard chat to cloud API.
3. Add server-side AI provider adapter after reviewing free quotas/costs.
4. Add user authentication and private preferences/memory.
5. Add a native Android shell for background wake word and permission-gated phone actions.
6. Add workflow workers and integrations: reminders, Flora, social platforms, Telegram bot.

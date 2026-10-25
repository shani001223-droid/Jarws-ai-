# HOSHI deployment verification and rollback runbook

This runbook covers the existing HOSHI dashboard and cloud API. It is a manual recovery guide; it does not change Render settings or trigger a rollback by itself.

## Services

- Dashboard: https://jarws-ai-1.onrender.com
- Backend health: https://jarws-ai-2.onrender.com/health
- Source of truth: https://github.com/shani001223-droid/Jarws-ai-/

## Before a release

1. Confirm the latest **HOSHI basic checks** pass. This includes backend tests, JavaScript syntax checks, privacy tests, and the Chromium dashboard smoke test.
2. Confirm the **live backend smoke test** is green after any backend change.
3. Save the currently live commit and deploy ID for both services from each service's Render **Deploys** page.
4. After a deploy, verify the backend health endpoint returns HTTP 200 and the expected HOSHI API version. Verify the dashboard loads, can send a chat request, and shows no visible broken assets. The Chromium CI run uses a mocked API, so it does not replace these live checks.

## Roll back a bad Render deploy

Use this procedure for the dashboard and backend separately; rolling back one service does not roll back the other.

1. Open the affected service in the [Render Dashboard](https://dashboard.render.com/).
2. Open **Deploys** and identify a previous successful deploy that is known to work. Check its commit and timestamp before selecting it.
3. Choose **Rollback**, review the target, then confirm **Rollback to this deploy**.
4. Wait for Render to report the rollback deployment as live. Re-check the service endpoint and the main HOSHI flow.
5. Dashboard-triggered rollbacks disable automatic deploys for that service as a safeguard. Leave auto-deploy disabled until the fault is fixed; re-enable it in service Settings only when you are ready for the next commit to deploy.

Important: Render rollback reuses a retained build artifact and selected deploy configuration, not the entire historical state of the service. It does not restore persistent-disk data or undo external side effects. Do not use application rollback as a substitute for a database/data backup.

## Repository-level source rollback

For a source correction, prefer a new, reviewed **revert commit** rather than rewriting shared `main` history. Identify the exact bad commit in GitHub first, then revert it and allow CI to run before the next deploy. Never remove or overwrite Render environment variables to fix a code regression, and never commit API keys to the repository.

## Secret handling

Keep `GEMINI_API_KEY` and `GROQ_API_KEY` in Render's environment settings. The dashboard, APK, repository, logs, and this runbook must not contain their values.

## Verified references

- Render rollback instructions: https://render.com/docs/rollbacks
- Render deploy lifecycle and deploy history: https://render.com/docs/deploys

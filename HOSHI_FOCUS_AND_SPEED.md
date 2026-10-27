# Hoshi Focus Home & Fast Replies — verified development change

Updated: 27 October 2026. **Development branch only, not production.**

## Interface
- Default `focus-mode` shows a nearly black, CSS-animated blue energy core instead of the large anime/room background. No image-generation API, downloaded character asset, WebGL or paid GPU is required for the core.
- Minimal home keeps the microphone, speaking/thinking status, bounded last reply, one **Settings** entry and a **Stop** action while Hoshi is generating or speaking.
- In Settings, `Minimal home screen: ON/OFF` is explicitly reversible and saved locally (`hoshiFocusModeV1`). Turning it OFF restores the existing Chat, Trading, Outfit, Influencer and Settings tabs; none of those workflows were deleted.
- `prefers-reduced-motion` removes the core's continuous animations.
- No background screenshot, hidden permission grant, trading order or auto-publishing action was added.
- Outfits are not fetched on the initial minimal home; a selected outfit is loaded when switching to the expanded interface.

## Reply latency boundaries
- Quick casual/short voice requests already prioritize configured Groq. Added `cloud_backend/latency_budget.py` to limit the *combined serial provider timeout allowance* for short requests to approximately **13 seconds, with a response margin** (individual OpenRouter, Gemini and directory requests are capped by remaining budget). This is **not a hard 13-second real-world wall-clock guarantee** because DNS, provider responses and Render cold starts vary.
- Rich writing/research requests retain the existing 29-second backend provider allowance. No model keys, payments, API duplicates or speculative second parallel provider are introduced.
- The frontend now aborts quick AI fetches after 18 seconds; detailed AI requests retain 32 seconds. Previous Stop cancellation and late-reply protection remain.
- Added backend HTTPS connection preconnect and preserved early Render `/health` check. This may reduce connection setup or cold-start effects but does not guarantee a measurable improvement.
- Voice TTS remains device-first when appropriate Pakistani Urdu speech is installed; online voice can still be delayed by the TTS service. No fabricated 0.1-second promise or first-token-streaming claim.

## Verification
- Python budget/contract tests: `tests/test_latency_budget.py` and `tests/test_hoshi_focus_ui.py`.
- Playwright real Chromium smoke: `tests/dashboard.e2e.cjs` opens a 390x844 fresh focus session, verifies image-free CSS home, Settings entry, and restoration of full Chat workspace. Existing full-workspace regressions run with `hoshiFocusModeV1=false`.
- **Full Python/Node/Playwright CI passed:** https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40484238773 (head at verification `074dcce8a6`).
- **Docker image and boot checks passed:** https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40483915103 (backend latency code `8c899f5c5f`).
- **Not yet verified:** deployed mobile webpage, real Realme Note 50 visual readability, real Gemini/Groq response time, online TTS first audio, or real mobile data/Wi-Fi benchmarks. Production Render services still follow `main`, not this draft development branch.
- This improvement does **not** add a new numbered completion task to the canonical 60-task roadmap. Preserve its existing verification requirements.

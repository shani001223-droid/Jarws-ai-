# HOSHI AI — One Unified Project

> **START HERE:** [HOSHI_MASTER_PROJECT.md](HOSHI_MASTER_PROJECT.md) is the single canonical project overview for all former JARVIS/JARWS/ALTRON/VALTRON ideas and today's Hoshi AI assistant. [HOSHI_60_TASK_MASTER_ROADMAP.md](HOSHI_60_TASK_MASTER_ROADMAP.md) is the **only current 60-task completion tracker**. The historical material below may describe older versions of the app; the master document and current verified CI/deploy evidence take precedence.

**30 October 2026 — active scope: trading only.** Other feature development is
pending/deferred by the user's latest instruction. The same repository now has
a dedicated [Hoshi Trading paper desk](trading.html), using one bounded
`GET /api/trading/desk` response for BTC/ETH structure, indicators, V2 rule
coverage and hypothetical risk. Stop/clear, snapshot expiry and an opt-in local
journal/export/delete are included. No real orders or paid model calls.
This is development source in [existing draft PR #29](https://github.com/shani001223-droid/Jarws-ai-/pull/29),
not a claim that the page/backend have been deployed. The source-blocked V3
curriculum and its runtime/evaluation/release gates remain separate and pending.

Local operator preview: start the existing backend with
`python -m uvicorn cloud_backend.main:app --host 127.0.0.1 --port 8000`, serve the
repository frontend with `python -m http.server 8765 --bind 127.0.0.1`, and open
`http://127.0.0.1:8765/trading.html?backend=local`. The override works only on
loopback HTTP pages; public pages always use the existing approved backend
origin. Install the existing development requirements first. No credentials
are needed for this paper desk. Missing/unavailable market data produce WAIT.


**Current structure:** one GitHub repository with web frontend, Python backend, Android bridge, verified tools and user-approved design assets. New work goes to the reviewed Hoshi development branch ([draft PR #29](https://github.com/shani001223-droid/Jarws-ai-/pull/29)); it is **not automatically live** on Render. Do not duplicate the project or silently merge production changes. PR #24 was the released V2 predecessor.

**Trading V2 development update (27 Oct 2026):** [audit and commit evidence](AUDIT_REPORT.md), [ten-module curriculum + history](modules/), and [exact API/rules/deployment guide](HOSHI_TRADING_V2.md). Adds `/history`, `/learn`, `/confluence_score`, integrity-checked knowledge retrieval and a five-factor 0–100 **rule-coverage** score. It is paper research, not calibrated accuracy or real trading. Older interface/voice descriptions below are historical; current master decisions take precedence.

---

## Free public API integrations (read-only, zero new API keys)

Hoshi's **Trading** tab now requests public Binance **Spot** ticker and recent candles via the Hoshi backend, displaying the price, 24-hour change, a simple close-price trend, EMA 9, SMA 20, RSI 14, and Crypto Fear & Greed. These are **not Futures quotes or trade signals**. Trade placement, exchange-account access and automated trading are **not** implemented by this change.

The backend also offers opt-in, on-demand keyless information endpoints. All use provider-side rate limits, server-side caching, short timeouts, fixed trusted hosts, bounded responses and allowlisted query parameters. It does **not** scrape exposed keys or authenticate to any account.

| Hoshi endpoint | Keyless source | Cache |
| --- | --- | --- |
| \`/api/public/sources\` | Registry and source documentation, no network call | n/a |
| \`/api/public/market?symbol=BTCUSDT\` | Binance Spot 24h ticker | 25 seconds |
| \`/api/public/candles?symbol=BTCUSDT&interval=5m\` | Binance Spot 80 candles; indicators calculated locally | 45 seconds |
| \`/api/public/sentiment\` | Alternative.me Fear & Greed (show attribution) | 10 minutes |
| \`/api/public/defi\` | DefiLlama top chains by TVL | 15 minutes |
| \`/api/public/bitcoin-fees\` | mempool.space fee estimates | 90 seconds |
| \`/api/public/weather\` | Open-Meteo current weather (rounded coordinates) | 10 minutes |

Documentation and terms:
- [Binance public market data only](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md)
- [Alternative.me crypto Fear & Greed](https://alternative.me/crypto/fear-and-greed-index/) (attribution required next to displayed data)
- [DefiLlama free API](https://api-docs.defillama.com/)
- [mempool.space API](https://mempool.space/docs/api/rest)
- [Open-Meteo](https://open-meteo.com/en/docs) (free non-commercial use, CC BY 4.0 attribution)

This adds **five independent keyless external providers**, not five secret AI keys. Binance exposes multiple public endpoints. Existing Gemini/Groq/OpenRouter secrets remain unchanged and continue to belong exclusively in private Render environment variables.

Public APIs can be blocked by region, provider outages, free hosting timeouts or rate limits. The UI deliberately reports failure instead of inventing prices. No real-device / external-network acceptance claim is made until separately verified.

## Interactive wardrobe and mood reactions

Outfit tab provides 15 selectable main-screen looks (original plus 14 everyday/fashion variants). Each choice renders an individual panel from the supplied artwork atlas, applies it to the main scene, and persists locally across reloads. It is not a static screenshot-only menu. Intimate/swimsuit/bunny and school variants are not included. These are 2D illustrated looks, not a layered clothing simulator; pose and scene follow each source panel. Runtime crop avoids title/footer labels; grid source resolution limits sharpness.

Conversation emotion now drives a visible mood indicator, reaction colors/animation and online speech delivery (playful vs gentle styles). Thinking state appears during cloud requests. The outfit selection remains independent of emotion. This is not a facial rig: facial expressions in the source artwork do not transform, and the mood indicator must not be presented as full facial animation.

## Reference nightroom home screen

Home uses the supplied nightroom composition as cleaned artwork with real HTML controls: Hoshi title, actual cloud status, reply/status area, microphone and five bottom tabs. Dashboard panels are removed from the home screen. Chat opens text/history; Settings holds voice, language, memory and existing device controls. Trading is an external chart link; AI Influencer and Outfit explicitly state that their tools are not connected. They do not pretend to execute features. The large artwork is static; old expression animation is not layered over the reference character. The mic indicates speaking state. No fake clock/battery indicator is drawn.

## Consistent Urdu voice and shorter chat replies

Urdu now uses the online Hoshi voice first, avoiding installed device speakers that may sound different. Soft/Warm/Playful use modest brighter pitch and less slowed delivery. These are tuning presets, not a clone of the uploaded reference clip. Casual replies request 1–2 short sentences and a smaller OpenRouter output budget; detailed requests retain the larger budget. This reduces generated text but cannot remove free-model queueing or Render cold starts.

Repeated speech is cached in process memory for at most two minutes, bounded to 16 audio clips. Cache keys are hashed text/style; no transcript or audio is written to disk. First replies still require model generation followed by online speech generation. Device listening and subjective voice quality remain unverified.

## Online Urdu speech fallback

If a matching native/browser Urdu voice is unavailable or fails, `/api/speech` generates MP3 with `edge-tts` and `ur-PK-UzmaNeural`. This uses Microsoft's online speech service through an unofficial client, requires internet and can become unavailable. No key or paid speech account is introduced. Spoken reply text is sent to that service only when voice output/preview is requested; audio stays in memory, responses use no-store, and there is no file persistence. Stop aborts pending synthesis playback and discards the audio URL. The visible audio player permits tap-to-play if browser autoplay is blocked. Native Urdu speech remains first choice.

## OpenRouter free provider

In the Render **Jarws-ai--2** backend Environment, set `OPENROUTER_API_KEY` privately and `OPENROUTER_MODEL=openrouter/free`, then save/deploy. Never paste the key into chat, frontend code, GitHub or the APK. When the key is configured OpenRouter is primary. Without it the existing Gemini/Groq path is unchanged. OpenRouter errors are reported directly; there is no silent paid upgrade or retry loop. Only `openrouter/free` or a model ID ending in `:free` is allowed. Free requests still have account/provider limits and availability can vary.

`/health` exposes only configuration flags/model names. A real successful reply with `mode: openrouter` is required to verify the key; a flag is not evidence that the key is valid. Context, personality and Urdu `speech_text` handling remain shared across providers. No new Python dependency or APK is required.

## Urdu pronunciation correction (Android 0.8.1)

Requests now send the selected conversation language instead of navigator.language. In Urdu mode the existing Gemini/Groq request asks for Roman Urdu chat plus equivalent Urdu-script speech_text. No second model request or extra TTS provider is introduced. Local commands and preview include Urdu-script speech text. Roman-only and Devanagari speech are not sent to Urdu TTS.

Urdu mode selects only Urdu device voices. Hindi/English/default-language substitution is removed in browser and Android paths. If no Urdu engine is available the reply stays visible and the app reports that an Urdu voice is needed. It does not claim to install a missing voice. The updated native capability check requires the 0.8.1 APK; older APKs use matching browser Urdu speech when available. Real-device pronunciation remains unverified until listening tests.

## Hoshi voice studio update

Country/device voice picker removed. Soft, Warm and Playful are delivery presets for the installed speech engine, not new voice models. Android native TTS remains first choice. Preview works with automatic replies disabled and does not save a chat turn. Stop Speaking invalidates delayed browser speech and stops native/browser output. Fine tuning is optional; old country voice selections are discarded.

A studio-quality anime voice is not implemented or claimed. Actual Urdu pronunciation and voice quality require target-device listening. No paid TTS service is configured. The online Urdu fallback is described above.

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
- Voice reply settings: choose Soft, Warm or Playful delivery, optionally adjust pitch/speed, and play a preview. Browser and native Android auto-selection prefer an installed Pakistani Urdu (`ur-PK`) voice where available, then Urdu and best-effort alternatives.
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
- Language selection, voice replies, wake-word toggle, personality, pitch, and rate persist locally across reloads. Android uses native TTS first; browser mode automatically selects an available voice. Overlapping cloud requests supersede prior requests so stale results do not overwrite newer replies.
- Hero-level Chat / Voice / Vision / Create / More shortcuts have working click handlers with browser-mode fallbacks.
- Automatic browser and native Android voice selection now prefer installed `ur-PK` voices when available, then other Urdu voices, then best-effort feminine-sounding fallbacks. Country/device voice selection has been removed. Accent and gender are device-engine-dependent; missing voices cannot be installed by HOSHI.
- The face is an 8-expression WebP sprite from the final character sheet. `data-emotion` switches the sprite position; service-worker cache `hoshi-shell-v19` precaches the sprite, privacy helper, optimized hero artwork, and HOSHI app icon for offline loading. Speaking shows an animated waveform and a lightweight mouth overlay; it is not phoneme-synchronized lip-sync.
- A shared `memory-privacy.js` helper applies privacy filters before local history save/edit. Node tests exercise common credential/token formats, recovery phrases, OTPs, contact information, and long numeric strings.
- Python frontend-contract tests verify unique HTML IDs, script references, valid WebP headers, emotion mappings, memory controls, cache contents, and actionable voice-error recovery paths.
- Previously confirmed runs: [HOSHI basic checks #202](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237303519), [live Render dashboard smoke #7](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237284235), [live backend smoke #35](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237196850), and [Android APK #32](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40237013290). The latest multi-turn, waveform/mouth-lifecycle, narrow-phone, native Urdu voice, and PWA icon/cache regression additions need fresh automated run results.
- Deployment safety notes are in [`DEPLOYMENT_ROLLBACK.md`](https://github.com/shani001223-droid/Jarws-ai-/blob/main/DEPLOYMENT_ROLLBACK.md). The frontend Render service reports the latest source deployment as live; a fresh visual/browser smoke confirmation after the final narrow-phone change remains pending.

## Remaining real-device checks

- Install the latest debug APK and verify audible speech through Android Text-to-Speech. The app uses native TTS first and browser speech synthesis only as a browser fallback.
- Test microphone permission and voice recognition on the phone; Web Speech recognition support depends on installed browser/WebView support.
- Test local reminder delivery and reboot recovery on the target phone.

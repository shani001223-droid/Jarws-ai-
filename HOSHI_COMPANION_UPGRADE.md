# HOSHI AI companion upgrade — incremental audit (2026-10-26)

**Never rebuild or replace approved character art.** This is a voice-first code increment on a draft PR, not a claim that all six phases are finished. Default `main` remains unchanged until review/merge.

## Audited existing behavior
- Android Kotlin WebView bridge: native one-shot microphone, native TTS, reminders, accessibility-backed Android actions.
- Frontend: responsive nightroom, persistent outfit selection, local memory controls, Chat/Trading/AI Influencer/Outfit/Settings tabs.
- Backend: OpenRouter-free primary where configured, Gemini/Groq fallback, Urdu-script speech text, Edge Urdu TTS and temporary memory-only MP3 cache.
- Existing approved graphics: `assets/hoshi-nightroom.webp` is one combined bedroom portrait; `assets/hoshi-expressions.webp` is an **8-cell sprite sheet** (CSS uses 4 columns × 2 rows). These **are not** a layered rig. Outfit images replace the full nightroom image.
- Existing speaking-mouth CSS is a fixed-rate illustration, **not** phoneme- or audio-energy-synced mouth tracking. The static room figure cannot genuinely change facial expressions without new aligned layers.

## Priority: Urdu voice reliability
Changes in this PR:
- Fix the frontend request guard so a failed online Urdu audio generation can be retried after it finishes.
- Distinguish actual audio playing versus buffering/waiting; on error expose an explicit retry.
- Keep one outstanding speech controller with `AbortController`; Stop Speaking aborts current synthesis and stops audio/native speech.
- Expose client-observed *numeric-only* diagnostics in Settings: speech-recognition duration, model response-header duration, full model response, TTS transfer/generation duration, first audible playback event and approximate end-to-end time.
- The model API is non-streaming, so first-token time is **not measured**, and displayed as unavailable, not invented.
- Bound individual OpenRouter/Gemini/Groq provider network calls to **10 seconds** (still sequential; overall time including Render cold starts and provider processing is not guaranteed).
- Ignore stale Android TTS utterance callbacks when a new utterance replaces an old one.
- Automated frontend regression covers failed Urdu synthesis retry and Stop Speaking. GitHub Actions also builds Android APK for native-code PRs.

**Limitations:** Urdu voice depends on internet and an external service. Current TTS downloads a whole MP3 before playback; no verified progressive/chunk streaming. Real speech quality, audio stalls, energy-based lip-sync and pronunciation remain unverified. This PR does not invent a new female voice.

## Phase 1 — character animation
Existing: eight expression cells for a small secondary avatar, CSS light mouth/wave effects, one full-scene room portrait.

Not implemented: true eye blink, layered lip-sync, arms, face swap on full-room Hoshi, gestures, hair physics or crying frames. **Never animate the whole room image as if it were the character.**

Required approved, transparent, spatially registered art before rendering these states in the nightroom:
1. Room *background only*, with the Hoshi figure removed, and approved Hoshi foreground character separated from the same composition.
2. Full-body base with fixed pivot coordinates for head, torso, upper/lower arms and hands, front/back hair, ears, outfit.
3. Eye-open/half-closed/closed/blink layers; eyebrows; neutral, happy, sad, shy and tear facial layers; at least closed/small/medium/wide mouth shapes for approximate lip-sync.
4. Approved hair-adjusting, looking-down, hand-wave and speaking hand pose frames or individually pivoted hand/arm layers.
5. A transparent outfit overlay for each wardrobe item, aligned to the **same approved character proportions and anchor points**, not a substituted generated face.
6. Alpha-correct WebP/PNG exports and a sprite manifest declaring image dimensions, pivots, per-outfit availability and missing states.

Until these assets exist, request metadata may be stored and existing small avatar sprite aliases selected, but actual Hoshi in the room stays static.

## Phase 2 — emotion
Added: stand-alone backend `cloud_backend/emotions.py` validates allowed emotions, bounded intensity, animation, gesture and voice style; unknown states use neutral/default fallbacks. API includes these fields without adding an extra model request. Frontend maps new emotion labels to known sprite cells, and tracks requested but **not yet renderable** animation and gesture metadata.

Remaining: approved main portrait facial overlays and controlled expression transitions. No claim that a model is conscious, distressed, or in a relationship. Keep existing non-manipulative companion prompt.

## Phase 4 — opt-in awareness
Not implemented in this PR. Existing Android screenshot action triggers a user-visible **system screenshot**, not programmatic screenshot reading. No continuous capture, trading execution, secret screen access or hidden upload. Future app-awareness requires explicit Android permissions and an allowlist. Screenshot analysis requires intentional sharing, redaction and a real image-processing integration before any capability claims.

## Phase 5 — mobile interface
Preserved: original room and all five tabs. No generic art, new paid UI kit, mood sidebars or extra dashboards were added. Outfit changes preserve existing browser session. Accurate facial animation is asset-blocked.

## Phase 6 — testing and cost
- Python/Node/Playwright checks run in HOSHI basic checks CI; Android compile/build runs in the PR Android APK workflow.
- Test slow/no network, cloud/provider fallback, failed TTS retry, Stop Speaking, stale callbacks, small viewport, permissions and memory with actual device before release.
- **Realme Note 50 verification pending**. No device heat, frame-rate, battery, microphone pronunciation, emotion transitions or screen privacy validation has been done by this PR.
- Existing free-first services only. No new paid API/model/framework dependencies. Network/hosting services can have limits and availability changes; do not claim permanently free unlimited usage.

## Merge/acceptance gate
Review the linked PR's latest commit and CI results. Do not merge solely on compilation or mocked tests. Next priorities: real-device voice acceptance; obtain layered approved artwork; implement audio-energy-based lip-sync only after a matching mouth layer exists; then opt-in app awareness.

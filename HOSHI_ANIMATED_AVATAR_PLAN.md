# HOSHI Animated Anime Avatar — implementation plan (Task 57 sub-plan)

**Status:** 4/28 avatar subtasks VERIFIED AT CODE/BROWSER LEVEL as of 28 October 2026; 24 pending. Android physical-device QA, layered rig and release remain separate unfinished acceptance. This is a subordinate breakdown of **canonical Task 57** ("Build consistent original character/voice system") in `HOSHI_60_TASK_MASTER_ROADMAP.md`; it does **not** create a second 60-task scoreboard or increase the completed-task count.

## User-approved direction

- Keep **anime girl Hoshi**, not the JARVIS sphere as the final character: silver-white medium/bob-length hair, ice-blue eyes, fox ears, soft face, familiar blue-white futuristic kimono.
- UI: **black, uncluttered, futuristic** Android/phone-first screen; Hoshi is visually central, with only core chat/microphone and Settings up front. Trading, outfits, memory and other existing features remain reachable without deleting them.
- Hoshi should look naturally **alive and reactive**: blink, subtle breathing, small head shifts and ear/hair movement, facial expression changes, listening/thinking cues and actual speaking-mouth animation.
- No static picture pasted onto an unrelated body or outfit; maintain an identifiable consistent Hoshi character through all expressions/outfits.
- **Free-first**, compatible with existing HTML/JS frontend, FastAPI cloud backend and native TTS bridge in Android WebView on Realme Note 50. Never require or silently enable a paid model/SDK.
- Never claim audio-accurate lip synchronization if only a speaking-state mouth loop is available. Distinguish mouth-reactive vs genuine amplitude/viseme-derived lip-sync.

## 28 implementation subtasks — all pending

### Phase A — source art and character rig (01–04)
- [ ] **01.** Freeze a reference/model sheet for Hoshi: face proportions, hair length, eye colors, ears, clothing, expression consistency. Review original art use rights.
- [ ] **02.** Prepare separate transparent, correctly aligned layers: torso/shoulders, head, hair (front/back), ears, eyes, eyelids, eyebrows, mouth, and clothing attachments.
- [ ] **03.** Export eyes open/half/closed and mouth shapes closed/open/wide/round; label coordinate anchors and export sprite atlases for the 2D renderer.
- [ ] **04.** Validate assets against mobile caps, color/alpha integrity, consistent alignment, deterministic file names, compressed dimensions and transparent edges.

**Gate:** one coherent layered character, no visible seams when eyes/mouth/ears are swapped. A single flattened PNG is not an acceptable rig.

### Phase B — continuous idle animation (05–08)
- [ ] **05.** Implement layered 2D animation controller using free native web technologies (Canvas 2D and/or CSS transforms) without heavy 3D/paid runtime dependencies.
- [ ] **06.** Add randomized, nonmechanical blinks including half-blink and eye close; ensure animation never covers the eyes with misaligned sprites.
- [ ] **07.** Add subtle breathing/shoulder movement and occasional small head tilt/bob, with a genuinely calm idle pose.
- [ ] **08.** Add gentle fox-ear and hair secondary motion with sane bounds; throttle or disable effects on lower-end devices.

**Gate:** smooth idle scene without sending AI requests, and graceful rendering if animations are off.

### Phase C — expressions and transitions (09–12)
- [ ] **09.** Make a consistent **10-state expression pack**: neutral, happy, soft-smile/caring, listening, thinking, surprised, sad, annoyed, shy, excited.
- [x] **10.** Create a central explicit emotion-state controller; existing backend moods and voice/mic state should map into supported states with safe fallbacks.
- [ ] **11.** Blend/transition eyes, brows, mouth and head poses smoothly rather than hard-switching complete portraits; prevent race conditions from late replies.
- [ ] **12.** Set priorities for states (speaking/listening/stop/error overrides ordinary moods); validate that expressions suit the actual message and do not imply real human feelings.

**Gate:** every supported state appears visibly distinct on actual small-phone dimensions and restores neutral correctly.

### Phase D — speech reaction and lip-sync (13–16)
- [ ] **13.** Wire native Android TTS + web audio lifecycle callbacks to avatar start, pause, resume, finish, error, cancellation and Stop control.
- [x] **14.** Provide clearly labeled **speaking-reactive mouth animation** as the minimum fallback when native Android TTS supplies speaking state but no phoneme or audio samples.
- [ ] **15.** For decoded in-web audio actually available to Web Audio, use an `AnalyserNode` envelope/energy threshold with smoothing to animate mouth openness. Respect browser gesture/permission restrictions.
- [ ] **16.** Optionally add timed Urdu-script/phonetic viseme cues only when true timing data is available; test silence, interruptions, quick replies, multiple segments and no lingering mouth loop.

**Gate:** mouth reacts as Hoshi speaks, closes immediately when stopped, and does not falsely claim phoneme-perfect sync.

### Phase E — mobile UI and interaction (17–20)
- [x] **17.** Make the anime avatar the **default home** with a black futuristic setting (not room art or image-only static screen), clean framing and readable reply bubble.
- [ ] **18.** Implement distinct real listening, hearing, thinking, speaking and failed/offline cues, including subtle glow and progress that never implies a task succeeded before confirmation.
- [x] **19.** Keep home controls minimal: microphone, optional text composer and **Settings**; move advanced options to Settings without removing existing functionality.
- [ ] **20.** Include reduced-motion, low-motion/battery mode, pause avatar animation, text fallback and accessible touch targets.

**Gate:** first-time user can ask a question and hear/read a reply without hunting through cards and buttons.

### Phase F — outfits and consistency (21–24)
- [ ] **21.** Establish stable shared face/hair/ear/body proportions for all existing outfits; no sudden identity/face change after selection.
- [ ] **22.** Rig clothes/accessories as aligned overlay layers on the **same character**, or openly label any outfit that only has a static preview until rigged.
- [ ] **23.** Preload the selected outfit and apply it to the **visible main avatar** immediately upon tap, with a loading/error state and no unrelated background-only swap.
- [ ] **24.** Persist selected outfit only on this device if user opts to keep it, recover after reload, and reject rapid stale-image callbacks.

**Gate:** visibly change garments on the animated Hoshi, not merely change wallpaper.

### Phase G — safety, performance, real-phone release (25–28)
- [ ] **25.** Add deterministic tests for animation-state transitions, late speech callbacks, stop cancellation, asset dimensions/missing layers and outfit switching.
- [ ] **26.** Run mobile Chromium responsive/gesture tests at representative Realme Note 50 viewport sizes, plus screenshot checks for alignment/clipping.
- [ ] **27.** Profile frame rate, load time, RAM/battery and memory leaks on low-power Android; target a smooth **24–30fps where practical**, dynamically throttle when not visible/low battery, never promise a hard FPS without testing.
- [ ] **28.** Build debug APK through existing GitHub Actions; run **physical Realme Note 50** microphone/voice, expressions, outfit and Stop controls QA; fix findings, re-run CI, prepare rollback and only release with explicit approval.

**Gate:** automated CI and actual phone acceptance both independently documented; final production deployment and rollback remain canonical Task 06.

## Integration notes

- Keep ONE repository: `shani001223-droid/Jarws-ai-`. No duplicate app, branch, tracker or automation.
- Preserve existing private safety/consent behavior, chat memory controls, trading safety and existing backend.
- Current code may have sprite-sheet emotion switching or speaking-state mouth approximation; those are **not evidence** that a fully layered animated avatar or real audio-driven lip-sync is done.
- Do not mark canonical Task 57 complete until the character/voice deliverables and their tests are actually verified. The 28 subtasks are planning detail only.
- Do not silently merge to `main`, deploy Render or publish an APK. User asked for a **task list**, not immediate build.


## Approved V2 design and working sprint (28 October 2026)

The approved image board establishes a **silver-white-haired, blue-eyed, fox-eared anime Hoshi** framed by a black/cyan holographic mobile UI. The final animated home should be expressive, with subtle natural motion, visibly distinct emotional moods and a working speech-mouth response. The approved board is a **concept image**, not an existing sprite rig, actual working app, or licensed audio/character model. Maintain a consistent, age-appropriate outfit.

**Current development implementation (awaiting final green CI at this checkpoint):**
- Added `hoshi-anime-avatar.js` with a testable browser-side state controller, speech/listening/thinking priority, supported emotion aliases, randomized blink scheduling, reduced-motion cancellation and disposal.
- Added `hoshi-anime-avatar.css` reusing existing 4×2 Hoshi expression art for changing face moods, subtle CSS idle sway, eyelid overlay blink, cyan status signal and a **speaking-state mouth loop**. This is a lightweight **portrait sprite**, **not** layered ears, hair, clothing, physical full-body movement, viseme matching or audio-amplitude sync.
- The same `index.html` home uses the animated Hoshi instead of the holographic orb, with existing mic/Settings/Stop and preserved complete hidden workspace; emotion and microphone/AI/TTS callbacks are linked without new provider requests or permissions.
- Added `tests/hoshi-anime-avatar.test.cjs` and a mobile Chromium regression; `sw.js` caches new assets, and GitHub CI executes the new tests.
- **Do not count** as complete until the latest full Python/Node/Playwright workflow is green, and **never** count as production or physical-phone verified.

**Next concrete sprint:**
1. Check that the portrait sprite face and eyelid/mouth overlays align correctly on real phone screenshot and remove inaccurate overlays before claiming a natural blink/lip-sync.
2. Make actual **rigged transparent layers** (eyelids/eyes, front/back hair, fox ears, neck, shoulders, mouths and kimono) from consistent rights-cleared source art, replacing the flattened sprite.
3. Animate individual hair/ears, expression transitions and realistic blinks using that rig; add measured app responsiveness/animation throttling.
4. Wire voice audio amplitude envelope when web audio is playable; keep honest speaking-state fallback for native TTS.
5. Make outfit swapping alter clothing layers on the visible character, not background wallpaper.
6. Physical Realme Note 50 performance and voice QA, then approved staged release and rollback.

This is an updated sub-plan of canonical Task 57, not a separate project or another completion scoreboard.

## V1 verification checkpoint (28 October 2026)

- **First source/test head:** `6af573d08886d69b2e3b8e535020fb6806e83bfa`. Full Python/backend tests, Node avatar emotion/blink tests, mobile Playwright/Chromium dashboard and Game Studio regression tests **passed**: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40649425847 . Docker backend build/startup passed for the same source head: https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40649433743 .
- **Subtask 10 (state controller)** checked: `hoshi-anime-avatar.js` maps backend emotion aliases and listening/thinking/speaking states deterministically; Node tests assert priority, stop and disposal.
- **Subtask 14 (speaking fallback)** checked: portrait mouth loops while the browser/native speech lifecycle declares "speaking", and closes when stopped. This **does not mean** phoneme-level lip-sync, audio amplitude tracking or native-device verification.
- **Subtask 17 (anime home)** checked at **browser code level** only: existing expressive Hoshi sprite is visible on black minimal home, not the old orb/room; 390×844 Playwright verifies sprite, state changes, tool visibility and the older core hidden. This is not yet the final concept-board character rig; physical color/alignment still requires review.
- **Subtask 19 (minimal controls)** checked at **browser code level**: microphone, one Settings entry and Stop are maintained. Advanced tabs remain available through the existing explicit Settings toggle; no phone control permissions are changed.
- **Not yet done:** independent animated eyelid layer registration, face landmarks and fitting, 10 fully distinct moods, per-ear/hair/body rig, actual audio-driven visemes, outfit garment swaps, full synthetic asset validation and real Realme Note 50 tests. The existing 4×2 sprite means only a limited distinct-expression set; aliases are not new artwork.
- GitHub CI regression temporarily failed because old smoke tests still expected the retired holographic core and because a new sprite URL matcher was over-escaped; both assertions were corrected and the cited final run is green. No production merge, release, payment or user-account change.

# HOSHI Animated Anime Avatar — implementation plan (Task 57 sub-plan)

**Status:** PLAN ONLY — none of these subtasks is verified or complete. Do not start implementation based solely on this file. This is a subordinate breakdown of **canonical Task 57** ("Build consistent original character/voice system") in `HOSHI_60_TASK_MASTER_ROADMAP.md`; it does **not** create a second 60-task scoreboard or increase the completed-task count.

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
- [ ] **10.** Create a central explicit emotion-state controller; existing backend moods and voice/mic state should map into supported states with safe fallbacks.
- [ ] **11.** Blend/transition eyes, brows, mouth and head poses smoothly rather than hard-switching complete portraits; prevent race conditions from late replies.
- [ ] **12.** Set priorities for states (speaking/listening/stop/error overrides ordinary moods); validate that expressions suit the actual message and do not imply real human feelings.

**Gate:** every supported state appears visibly distinct on actual small-phone dimensions and restores neutral correctly.

### Phase D — speech reaction and lip-sync (13–16)
- [ ] **13.** Wire native Android TTS + web audio lifecycle callbacks to avatar start, pause, resume, finish, error, cancellation and Stop control.
- [ ] **14.** Provide clearly labeled **speaking-reactive mouth animation** as the minimum fallback when native Android TTS supplies speaking state but no phoneme or audio samples.
- [ ] **15.** For decoded in-web audio actually available to Web Audio, use an `AnalyserNode` envelope/energy threshold with smoothing to animate mouth openness. Respect browser gesture/permission restrictions.
- [ ] **16.** Optionally add timed Urdu-script/phonetic viseme cues only when true timing data is available; test silence, interruptions, quick replies, multiple segments and no lingering mouth loop.

**Gate:** mouth reacts as Hoshi speaks, closes immediately when stopped, and does not falsely claim phoneme-perfect sync.

### Phase E — mobile UI and interaction (17–20)
- [ ] **17.** Make the anime avatar the **default home** with a black futuristic setting (not room art or image-only static screen), clean framing and readable reply bubble.
- [ ] **18.** Implement distinct real listening, hearing, thinking, speaking and failed/offline cues, including subtle glow and progress that never implies a task succeeded before confirmation.
- [ ] **19.** Keep home controls minimal: microphone, optional text composer and **Settings**; move advanced options to Settings without removing existing functionality.
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

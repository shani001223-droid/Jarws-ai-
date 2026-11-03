# Hoshi Game Studio — Task 51 original procedural art and animation

**Scope:** Development-only, review-only work in the existing Hoshi repository/branch. This is still a **non-playable design preview**, not a game release or APK. No production deployment.

## Original artwork and provenance

- `game-studio/art.mjs` draws original vector shapes from primitive Canvas circles, 10-point stars, wall highlights and dots. The blue start marker, gold collectible and mint exit portal are generated mathematically by this project's source code; no downloaded images, fonts, character art, music, third-party sprite packs or external requests.
- `game-studio/engine.mjs` renders those vector tiles at the existing bounded 350 CSS px board and device-pixel-ratio cap of 2. All six Task 49 levels and the non-playable manifest are preserved.
- `game-studio/animation.mjs` implements an opt-in, requestAnimationFrame-based phase loop, capped at 24 painted frames per second. `game-studio/index.html` exposes an accessible Animate/Stop preview toggle; static rendering remains the default.
- OS `prefers-reduced-motion: reduce` disables animation. Hidden tabs stop the loop; returning to a visible tab only resumes if the user still opted in. The loop cancels pending frames on stop and does not start gameplay, saves, timers, audio or phone actions.
- No audio is shipped. This avoids any licensing ambiguity and provides a silent fallback; optional original synthesized tones can be considered separately with a user gesture and QA.

## Verification and limits

- Node unit tests cover tile geometry, rejected invalid sprite parameters, invalid phase, opt-in, 24-fps throttling and stop/cancel semantics.
- Playwright Chromium regression checks on 320/390px screens cover pixel changes only after the animation toggle, no horizontal overflow and no third-party requests. An emulated reduced-motion browser must disable the toggle.
- The existing backend Python/security, JS/dashboard, Docker and Android workflows remain the project verification gates. Android native code is unchanged; a web Chromium test or CI APK build is not physical Realme Note 50 acceptance.
- **Verified source/test evidence:** On integrated code/test head `3a410550090b78f0079f2f5ac59ac398da598fd7`, [full Python/backend/security, JavaScript and real Playwright/Chromium mobile checks passed](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40620856218), including new Task 51 original art/animation unit tests and 320px/390px/reduced-motion browser tests. [Actual Docker backend build/Uvicorn smoke passed](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40620856224) on the same commit. These are source/CI checks, not phone or production acceptance. No owner genre approval, gameplay, offline package, APK, external publishing or paid service is claimed.

Tasks 52–54 still own movement/collection/undo/save, gameplay and crash QA, and actual offline web/APK packaging. Task 06 physical Realme QA, Task 11 OpenJarvis, and Flora owner approvals remain independent blockers.

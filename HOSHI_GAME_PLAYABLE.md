# Hoshi Star Trail — Task 52 playable local MVP

**Scope:** Development branch only, inside the single existing Hoshi AI repository. This is an original offline-first 7×7 Canvas puzzle. It is not the production Hoshi app, an APK, a publicly hosted game, or physical Realme Note 50 acceptance. The proposed genre has not been separately approved by the owner.

## Playable behavior

- `game-studio/gameplay.mjs`: deterministic pure state transitions, orthogonal wall rejection, one collectible bit per original star, win only when all stars are collected and the player reaches E, one-move undo and restart. No timers, paywalls, background execution or network.
- `game-studio/engine.mjs`: paints current player position and hides collected stars while preserving the original Task 51 procedural vector art.
- `game-studio/index.html`: 44px+ on-screen arrow controls, keyboard arrows/WASD, pause/resume, undo, restart, six-level selection with win-gated unlocking, optional animation, Roman Urdu instructions and accessible live status. The existing 320/390px responsive and reduced-motion design remains.
- `game-studio/levels.json`: same six canonical Task 49 boards, now `playable_local_mvp`. The canonical Python GDD remains design provenance and the levels must stay identical.

## Privacy, save and limits

The game never reads browser storage until the user **opts in** by checking the save box. Only `{version:1,highest_unlocked:1..6,muted:boolean}` is allowed under a game-specific localStorage key. Invalid, oversized, corrupted or unavailable storage fails closed; unchecking attempts deletion and reports whether deletion succeeded. Game state, transcripts, prompts, accounts, passwords, tokens, location and other-app actions are not stored. No audio is played; `muted:true` is reserved for a future explicitly opt-in sound feature. No server persistence or cross-device sync.

This is a **playable source-level web MVP**. It is not a packaged offline web release, tested Android APK, live Render deployment or physical device result. Task 53 owns broader gameplay/crash/performance testing and Task 54 owns actual release packaging. Task 06 physical Realme Note 50 QA, Task 11 real OpenJarvis, and owner-approved Flora photos/prices remain separate blockers.

## Verification gates

- `node --test tests/hoshi-gameplay.test.cjs` exercises all six level shortest paths, walls, early exit, collectible undo, unlock and save corruption.
- `node --test tests/hoshi-game-engine.test.cjs` verifies rendering, level data and original animation.
- `node tests/game-studio.e2e.cjs` exercises Chromium at 320/390px, on-screen completion, locked levels, undo, keyboard, pause, local opt-in/out, original animation and reduced-motion.
- Full `.github/workflows/ci.yml` includes Python backend, Node, Chromium; `docker-backend-smoke.yml` verifies the existing backend. Passing these checks is not equivalent to physical phone QA.

**Do not mark Task 52 complete until the final integrated code/test head passes.** Only `HOSHI_60_TASK_MASTER_ROADMAP.md` controls the scoreboard. No production merge/deploy, secret changes, purchases, external publishing or real trading.

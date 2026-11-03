# Hoshi Game Studio — Task 53 Gameplay, Crash and Performance QA

**Status:** Task 53 automated source/Chromium QA **verified** on code/test head `a0dfc40a7e3305bcfad65b0714d3e4803c1ffd93`. This is not physical Realme Note 50 acceptance, an offline packaged release, or an Android APK.

## Acceptance coverage

- `tests/hoshi-game-qa.test.cjs`: each of the six original level manifests is solved independently by a bounded breadth-first search; shortest paths match the recorded minimum moves. Every winning path is replayed through the actual `moveGame` state transition. Tests verify immutable state, undo restoration, restart, win terminality, and sequential unlock gates.
- A seeded 24,000-move replay (4,000 per level) checks wall collision, legal positions, star bitmasks, move counts, frozen state, and undo. A generous 20-second CI guard detects runaway logic; it is **not** a benchmark of phone frame rate or model latency.
- Invalid move names, corrupted/oversized or blocked browser storage, and forged progress fields fail closed.
- `tests/game-studio-qa.e2e.cjs`: a real headless Chromium browser at 320px plays **all six levels** using touch-button UI controls. It checks terminal controls, sequential unlocking, no local persistence without opt-in, no external network traffic, no uncaught JavaScript exceptions, and no horizontal overflow.
- Separate Chromium contexts simulate a malformed level manifest and denied localStorage access; the game must show a truthful unavailable/error state rather than silently claim saved progress. The local browser test uses a static HTTP server; no Render deployment or external account is touched.
- `.github/workflows/ci.yml` runs the new Node tests, JS syntax checks and Chromium QA alongside existing Python/backend, frontend and Playwright checks. Docker backend smoke is unchanged; Android native sources are unchanged.

## Honest limits

Automated source/Chromium tests cannot prove Realme Note 50 touch latency, memory pressure, backgrounding, audio, offline packaging, installed APK behavior, real battery drain or accessibility quality. Task 54 still needs a deliberately reviewed offline web/APK export; Task 06 physical phone QA remains unchecked. The separate OpenJarvis endpoint and owner-approved Flora product media remain external blockers. No new app/repo/PR, production merge, deployment, paid service, publishing, account change or trading action is authorized.

## Verification record

- **Full Python/backend, Node and Playwright Chromium: passed** [GitHub Actions 40635360245](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40635360245).
- **Docker backend/Uvicorn smoke: passed** [GitHub Actions 40635360247](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40635360247).
- The first CI run failed on Playwright `.check()` because the application correctly unchecks the opt-in box on denied storage. A follow-up test edit accidentally inserted literal `\\n` inside a JavaScript comment and suppressed the intended action. Both test errors were fixed; the final green run exercises the actual denied-storage change event.
- The **only** completion scoreboard is `HOSHI_60_TASK_MASTER_ROADMAP.md`: **46/60** after Task 53. Task 54 and real-device acceptance remain pending.

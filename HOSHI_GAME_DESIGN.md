# Hoshi Star Trail — Game Design Document (Task 49)

**Status:** PROPOSED DESIGN ONLY — not owner-approved, not a playable game, not an APK.
**Source of truth for level layouts and shortest-path checks:** `cloud_backend/game_design.py` (`gdd-v1`). This document is a reviewable design proposal, not proof that gameplay has been built.

## 1. Goal and scope

An original, private, free-first 2D touch/keyboard grid puzzle for the Realme Note 50. Guide a glowing star from S to E, collecting every C. This is a bounded six-level MVP concept for the existing Hoshi Game Studio, not a new app/repository. No franchise art, purchases, ads, accounts, leaderboards, analytics or network dependency. The owner has not yet selected or approved a genre; this is a safe default proposal.

## 2. Rules and state machine

- Board: 7×7 tiles. `#` blocks movement; `.` is walkable; `S` is start; `C` is a collectible star; `E` is the exit. Orthogonal moves only, one tile per input.
- Exit succeeds only after all stars are collected. Walking onto E early does not finish the level. Wall/invalid moves do nothing and do not consume a move.
- States: `title → level_select → playing → won → level_select`; `playing ↔ paused`. Restart resets the current level. No timer, lives or paywall.
- A move counter is informational; 30 is a design-time solvability bound, not a player timeout. One-move undo is required for the MVP.
- Unlock the next level only after verified completion; replay earlier levels at any time.

## 3. Controls, visual/audio direction and accessibility

- Mobile: four large on-screen direction buttons and optional swipe, touch targets at least 44 CSS px. Desktop: arrow keys/WASD. No permission to control other apps; keyboard focus remains in the game.
- Geometric blue/white stars on a dark background; draw original vector shapes in Canvas/CSS. No third-party media or copied Hoshi character art is required.
- Muted by default. Optional original synthesized confirmation tones only after a user gesture; no-audio mode must be fully playable. No licensed song dependency.
- High contrast, reduced-motion support, visible focus, non-color star indicators, screen-reader labels for controls/status, and Roman Urdu/English interface copy.

## 4. MVP level layouts and proof

Each layout is 7×7. A breadth-first search over position plus collected-star bitmask proves the exit is reachable after all stars, within 30 moves. These are design-time results, not actual gameplay tests.

### Level 1 — one star; minimum 8 moves
```text
#######
#S...E#
#.....#
#..C..#
#.....#
#.....#
#######
```

### Level 2 — one star; minimum 8 moves
```text
#######
#S.#.E#
#..#..#
#..C..#
#.....#
#.....#
#######
```

### Level 3 — two stars; minimum 8 moves
```text
#######
#S....#
#.#.#.#
#C....#
#.#.#.#
#...CE#
#######
```

### Level 4 — two stars; minimum 16 moves
```text
#######
#S...C#
#.#.#.#
#...#.#
#.#...#
#C...E#
#######
```

### Level 5 — three stars; minimum 16 moves
```text
#######
#S...C#
#.#.#.#
#C..#.#
#.#...#
#C...E#
#######
```

### Level 6 — three stars; minimum 12 moves
```text
#######
#S.C..#
#.#.#.#
#C....#
#.#.#.#
#..C.E#
#######
```

## 5. Implementation and persistence contract (future Tasks 50–54)

- Task 50: select a legally free HTML5 Canvas engine/template **inside this same repository**. Do not install paid tools or create another Hoshi app/repo.
- Task 51: create original geometric assets, animation and optional synthesized sounds with provenance and a no-audio fallback; never silently reuse unlicensed assets.
- Task 52: implement deterministic movement, star collection, exit checks, undo, restart, level unlock and optional local saves. Save schema: `{version:1, highest_unlocked:1..6, muted:boolean}`; validate before loading. No prompts, API tokens or conversation history in saves.
- Task 53: test every level's shortest path, wall rejection, premature exit, undo, save corruption, keyboard/touch controls, focus and reduced-motion with Python/JS and Playwright at 320/390 CSS px. Include crash/performance checks.
- Task 54: export an actual playable offline web package first; only build an Android APK if the existing Hoshi packaging workflow can safely include it. A screenshot, document or CI compilation is not a playable build.

## 6. Safety, performance and acceptance

- Free first; offline first; no real trading, social publishing, purchases, arbitrary Android taps, third-party account access or background workers.
- Target smooth interaction on Realme Note 50 at 320–390 CSS px with bounded memory and pause when hidden. These are targets, not measured results.
- Task 49 acceptance: complete reproducible GDD, six finite valid solvable layouts, honest scope and owner-approval flag, plus passing unit/CI verification. Task 49 does not certify gameplay, APK or physical-device acceptance.
- Later acceptance requires actual source, playable web/APK artifact, automated browser/gameplay tests and physical Realme Note 50 QA.

## 7. Open decisions

This mini-game is a safe default proposal, **not** a claim the owner selected the genre. A different genre, artwork, voice or public release requires explicit direction before changing approved Hoshi scope. Independent offline work can continue without routine interruption.

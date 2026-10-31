# HOSHI Anime Studio — EP001 Roman Urdu pilot draft (Task 56, partial)

**EDITORIAL DRAFT ONLY. NOT HUMAN-REVIEWED, NOT APPROVED, NOT 30 MINUTES OF VERIFIED DIALOGUE, NOT RENDERED.**

This stays in the single `shani001223-droid/Jarws-ai-` Hoshi project and the existing review PR. It expands only **EP001** of the original proposed `Aasmaan Ka Daira` chronology; it does not replace the separate `Deewar Mein Dafan` concept or reuse the Hoshi assistant's user-supplied character artwork.

## What is authored

`cloud_backend/anime_scripts.py` contains **ten original scene drafts**, at least four Pakistani Roman Urdu dialogue turns per scene, named speaking roles, original locations and physical action descriptions. The story follows Laila's first passive radio pulse, a clock calibration discrepancy, witness consent and evidence custody. It explicitly avoids claiming to know the relay source or later energy-diversion, guardian-protocol and reset revelations.

| Scene | Story purpose | Planned time |
|---|---|---|
| 01 Subah ka sannata | Observatory and power scarcity | 00:00–03:00 |
| 02 Pehli dhun | First time-stamped radio pulse | 03:00–06:00 |
| 03 Kaghaz ki gawahi | Receiver provenance and archivist | 06:00–09:00 |
| 04 Band hoti roshni | Clinic and battery trade-offs | 09:00–12:00 |
| 05 Doosra sample | Passive sample and uncertainty | 12:00–15:00 |
| 06 Gawah ka sawal | Independent inspector and custody | 15:00–18:00 |
| 07 Aik chhoti ghalti | Correcting the clock transparently | 18:00–21:00 |
| 08 Bahar ki awaaz | Community concerns without rumors | 21:00–24:00 |
| 09 Saboot ki do copies | Copy custody and witness rights | 24:00–27:00 |
| 10 Agla qadam | Handoff to the next observation | 27:00–30:00 |

The **1,800 seconds are an editorial scene allocation**, not a measured voice-performance duration. These are short first-pass scenes with action descriptions, **not a production-ready 30-minute screenplay**. Dialogue expansion, shot pacing, human language review, cast and recording consent, rights, voice direction and independent owner approval remain outstanding. No model-generated actor voice, animation, MP4 or sound recording exists.

## Reproducible, private output

- `python -m unittest tests.test_anime_scripts -v` checks episode linkage, 10 unique sequential scenes, 40+ dialogue turns, speaker allowlist, exact scene timing, early-spoiler rejection, status truthfulness and revision hash.
- `python -m scripts.export_hoshi_anime_pilot --out Hoshi-EP001-draft.json` creates a local UTF-8 review artifact; it refuses to overwrite an existing file. Without `--out` it prints the draft JSON. No network, account action, paid API, storage service or publishing.
- The draft's SHA-256 binds its own JSON revision. It **does not** establish creative quality, rights, human review or a recorded duration. The source outline digest links EP001 to the Task 55 chronology; any future outline change requires deliberate script reconciliation.

## Acceptance still required

**Task 56 remains unchecked** until individual complete episode scripts are independently authored/reviewed with fluent Urdu/Roman Urdu language checks, continuity across episodes, verified spoken/action pacing and owner approval. This single unreviewed pilot draft is an incremental foundation only. Tasks 57–60 (original licensed character/voice, storyboards, synchronized media and episode QC) are also pending.

Physical Realme Note 50 testing (Task 06), real OpenJarvis endpoint (Task 11), Flora owner inputs and any production deployment are separate unresolved gates. No main merge, production deploy, new app/repo, secret change, paid tool, account posting or real-money trading is authorized.

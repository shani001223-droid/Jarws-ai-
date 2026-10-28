# HOSHI Anime Studio — Aasmaan Ka Daira (Task 55)

**PROPOSED DESIGN ONLY — not owner-approved, not scripts, not rendered episodes.** This is an original candidate series bible and a reproducible 300-episode *beat chronology* inside the **same** Hoshi AI repository. It is not a second Hoshi app or repository. No studio worker, soundtrack, voice clone, animation, account posting or paid GPU is implied.

## Production reality and scope

- Format target: **300 episodes × 30 minutes = 9,000 minutes (150 hours)** of hypothetical future Urdu/Roman Urdu anime. This is a target, **not** a claim of finished scripts, voice tracks, or MP4s.
- Primary language: Pakistani **Roman Urdu** for planning, with human-reviewed Urdu dialogue planned for Task 56. Do not silently translate the whole series to Hindi or assume a particular actor/voice is licensed.
- Intended audience: general/family; no explicit sexual material, graphic violence, coercive romance or unsafe instruction.
- Proposed title: **Aasmaan Ka Daira**. Genre: original near-future mystery / community sci-fi / hopeful drama. Tone: discovery, responsibility, teamwork and earned trust.
- The user's separate **Deewar Mein Dafan** 60-episode family-thriller concept remains separate; this 300-episode anime plan does **not** rewrite or overwrite it.
- Hoshi's existing silver-haired fox-ear assistant avatar is not automatically an anime cast asset. Do not repurpose user reference artwork or imitate a copyrighted character without approval.

## Logline and stakes

In the fictional city of **Noorabad**, technician **Laila** discovers a repeating radio pulse during a rolling power shortage. Her friends follow the physical signal into a conflict over scarce energy, erased infrastructure history and public accountability. The mystery has a finite technical explanation: the stakes are human safety, records and governance, not magical omnipotence.

**Main cast and immutable motivations:** Laila (curious observatory technician, refuses unsafe live-grid overrides); Rayan (engineer, models repairs offline first); Meher (archivist, documents provenance and witness consent); Aman (community medic, prioritizes patients); Zoya (independent inspector, demands corroboration). Council representatives and the guardian protocol are institutions/technical systems, not magically omniscient villains. Characters may disagree, but evidence and consent matter.

**World rules:** Signals use physical relays; energy is finite; no time travel, mind control or miraculous resurrection; every power reroute has a cost; testimony and artifacts require source, timestamp and custody; public grid changes require a qualified safety process. A character cannot suddenly solve a problem with unintroduced superpowers. No character may be treated as proof of a real-world technology claim.

## Chronology contract

The canonical machine-readable source is `cloud_backend/anime_series.py`, not a manually maintained duplicate tracker. It contains **10 authored arcs**, each with **6 distinct authored five-episode sequences**. Each sequence is expanded into **five ordered beats**: Ishara (lead), Rukawat (obstacle), Tadbeer (safe plan), Qeemat (cost), Hawala (evidence handoff). This yields 10 × 6 × 5 = **300 numbered episode outlines** (EP001–EP300), with two episodes per fictional story day (days 1–150), a previous-episode link, arc/sequence/beat, authored event and consequence, and explicit reveal gates. The five-beat expansion is a *planning scaffold*, **not 300 individually reviewed 30-minute scripts**. A scriptwriter must expand, revise and approve each beat and check pacing before production.

| Arc | Episodes | Story days | Arc focus and continuity |
|---|---|---|---|
| 1. Band Awaaz | 001–030 | 1–15 | Observatory pulse, library records, first custody packet |
| 2. Zameen Ka Naqsha | 031–060 | 16–30 | Relay route and public source verification |
| 3. Roshan Qeemat | 061–090 | 31–45 | Hospital/bazaar outages and witness consent |
| 4. Do Shehr | 091–120 | 46–60 | Rural electricity records and unequal allocation |
| 5. Aaina Council | 121–150 | 61–75 | Hearing, forged timestamp, responsibility |
| 6. Bunyad Ka Code | 151–180 | 76–90 | Founders' documents and safety protocol origin |
| 7. Sheesha Dar | 181–210 | 91–105 | Independent oversight and fail-closed safety |
| 8. Aakhri Reset | 211–240 | 106–120 | Archive retention and the reset risk |
| 9. Naya Muahida | 241–270 | 121–135 | Rural/urban shared governance |
| 10. Subah Ka Daira | 271–300 | 136–150 | Repair verification and public accountability |

**Spoiler/continuity locks:** EP060 confirms the terrestrial relay; EP120 confirms the rural energy-diversion pattern; EP180 confirms the founder-built guardian protocol; EP240 proves the proposed reset threatens audit evidence; EP300 establishes public oversight. Earlier episodes' `revelations_known` must not include a later lock. Later scripts must preserve these gates unless the owner explicitly approves a versioned rewrite.

**Story arcs vs. production batches:** Arc is a narrative unit of 30 episodes; a future production batch should begin with a single pilot and only scale after verified media, audio rights, review and storage. Never promise 300 full episodes on a free Render web container.

## Reproducible output and quality gates

Use `python -c "from cloud_backend.anime_series import series_manifest; m=series_manifest(); print(len(m['episodes']), m['sha256'])"` to regenerate the manifest in memory. The manifest is deterministic, UTF-8 JSON-serializable and includes a SHA-256 digest over canonical sorted JSON. `validate_series` checks episode count/order, arc and sequence boundaries, day progression, predecessor links, distinct beats, spoiler gates and truthful completion flags. Regression: `python -m unittest tests.test_anime_series -v` (or full `unittest discover`). No network or paid dependency is needed.

**Do not treat a hash as creative approval or factual authenticity.** All generated entries have `status=outline_only`, `reviewed_scripts=0`, `rendered_episodes=0`, and `approval=proposed_not_owner_approved`. The generated 300 rows are concise continuity beats, not final screenplay dialogue or audiovisual assets.

## Future acceptance, not yet done

- **Task 56:** Pilot EP001 screenplay with scene-by-scene Urdu/Roman Urdu dialogue, estimated timings, human editorial review and continuity lint; then independent scripts per episode.
- **Task 57:** Consistent original character sheets and voice casting with explicit asset/voice rights; no impersonation or assumed ownership of user reference images.
- **Task 58:** Actual original storyboard images, shot lists, camera continuity and per-shot revision IDs.
- **Task 59:** Real synchronized and licensed audio plus rendered video files; verify media codecs, duration and scene alignment before claiming a produced episode.
- **Task 60:** Per-episode QC, accessibility/subtitles, archive checksum, provenance and private review; release/publishing requires separate approval.

The target phone is **Realme Note 50**, so any later viewing/review interface must be tested at 320px/390px and physically on that device. Task 06 still lacks physical phone acceptance; Task 11 still lacks a real OpenJarvis endpoint. No production merge/deploy, account changes, purchases, external publishing, secret changes or real trading are authorized by this bible.

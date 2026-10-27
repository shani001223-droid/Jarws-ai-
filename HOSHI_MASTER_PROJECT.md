# HOSHI AI — ONE MASTER PROJECT
**Start here. Single canonical index for the whole assistant.**

> Updated: 26 October 2026. This is a unified project map, **not** a declaration that unfinished features work. Keep every future Hoshi/JARVIS discussion, decision, code change, test, build and issue linked to this one repository and this one project file.

## 1. Identity, history and final scope

**One project name:** HOSHI AI. Earlier concepts JARVIS, JARWS, ALTRON and VALTRON inform this project; do **not** start separate competing assistant repositories or duplicate implementations. The Javes trading bot remains a **separate demo-only experiment**, not silently merged into the Hoshi runtime. A future integration must be explicit and tested.

**Purpose:** a private, mobile-first Pakistani Roman Urdu / Urdu voice assistant, practical enough to **complete permitted tasks and return real deliverables**, not merely say that work is done. It should understand goals, plan stages, execute the tools actually available, verify files, report failures clearly, and stop instantly when asked.

**User constraints (mandatory):**
- Realme Note 50 / Android-first; changes must work without requiring a personal PC.
- **Free first.** No paid subscription, GPU, API or top-up without explaining why and the actual cost **before** proceeding. Free tiers have quotas; they are not permanent unlimited compute.
- Pakistani Roman Urdu conversation, natural soft Urdu female voice; text and voice must not accidentally change to Hindi or Arabic.
- Minimal, private interface; preserve usable phone/voice controls. **The added fake Room Life feature must stay removed.** Do not mistake preserved original background artwork/wardrobe assets for the removed Room Life feature. Intelligence, speed and real task execution take priority over new appearance changes.
- The selected Hoshi identity is silver-white hair, ice-blue eyes, fox ears, soft anime face and blue-white futuristic kimono. Treat saved visual reference images as design source; don't fabricate unseen originals or replace them arbitrarily.
- Warm, playful and emotionally expressive conversation without claiming real human feelings, guilt, coercion or dependency. Keep role-play age-appropriate.
- No secret API keys in GitHub, chats, APKs or browser bundles. Memory off until explicitly enabled by user; export/delete controls.
- Screen actions require user-granted Android permissions, allowlisting, observable results and emergency stop. Messages/posts, account changes, paid actions or destructive actions require separate explicit approval. Never place **real-money trades**.
- User prefers no routine confirmations or interruptions. Record blockers and continue independent safe work; don't claim that a chat session continuously codes while closed.

## 2. The ONE home for Hoshi

| Role | Canonical location | Reality |
|---|---|---|
| Code (only canonical repo) | https://github.com/shani001223-droid/Jarws-ai- | Existing combined Android + web + Python backend source |
| Stable production branch | `main` | Do not silently merge or auto-deploy unverified changes |
| Work-in-progress branch | `hoshi/dnd-foundation-20261026` | Development-only changes |
| Development review | https://github.com/shani001223-droid/Jarws-ai-/pull/24 | Draft PR; not proof of production deployment |
| **Project entry point** | `HOSHI_MASTER_PROJECT.md` (this file) | Authority for vision, module map and handoff |
| **Only task-status scoreboard** | `HOSHI_60_TASK_MASTER_ROADMAP.md` | Update checkboxes only after relevant verification |
| Implementation history | `HOSHI_TASK_LIST.md`, `README.md`, `HOSHI_PHASE1_AUDIT.md` | Older notes may contain outdated status/URLs/wording |
| Design assets in repo | `assets/` and `assets/outfits/` | Do not delete or claim higher fidelity than actual images |
| Dashboard | https://jarws-ai-1.onrender.com | May reflect **main**, not the development branch |
| Cloud health | https://jarws-ai-2.onrender.com/health | Configured flag does not prove a provider successfully answers |
| Android APK build | https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/android-apk.yml | CI artifact, not proof of Realme phone behavior |
| Backend/Browser CI | https://github.com/shani001223-droid/Jarws-ai-/actions/workflows/ci.yml | Mocked tests do not validate live API keys |
| Rollback instructions | `DEPLOYMENT_ROLLBACK.md` | No production rollback performed by reading the guide |

**Do not make a second Hoshi source repository.** GitHub PRs, workflow artifacts, chat discussions and design references are parts of **this project**, not new projects to start over.

## 3. The unified code map

| Module | Location | Purpose |
|---|---|---|
| Mobile web dashboard | `index.html`, `trading.css`, `sw.js`, `manifest.json` | Main personal app / PWA |
| Frontend task + real ad workflow | `hoshi-task-router.js`, `hoshi-product-ads.js` | Routes known requests and downloads backend-generated ZIP |
| Urdu speech input | `hoshi-speech-input.js` | Urdu/Roman Urdu wake-word handling and transcript alternatives |
| Local privacy and consent | `hoshi-memory-store.js`, `memory-privacy.js` | Optional bounded user-controlled local memory |
| Local commands / reminders | `assistant-commands.js`, `reminder-parser.js` | Offline deterministic commands |
| Backend API | `cloud_backend/main.py` | Chat, speech, health, action endpoints, public market data |
| Spot research lab | `cloud_backend/trading_research.py`, `hoshi-trading-research.js` | BTC/ETH closed-candle analysis and historical paper simulation; no orders |
| Model decisions and free providers | `cloud_backend/provider_policy.py`, `free_llm_providers.py` | Only configured models with bounded fallback |
| Real OpenJarvis adapter | `cloud_backend/openjarvis_bridge.py` | Requires an actual separate configured OpenJarvis model/server |
| Planning and permissions | `cloud_backend/task_router.py`, `goal_spec.py`, `milestone_planner.py`, `permission_policy.py` | Classify/plan; **not** persistent autonomous workers |
| Private job records + scheduler (development) | `cloud_backend/job_records.py`, `cloud_backend/job_queue.py`, `/api/agent/jobs` | Auth-gated SQLite metadata and due-time queue; worker polling is explicit/opt-in, **no registered production executor**, no prompt storage; requires operator-configured persistent volume |
| Trusted role delegation (development) | `cloud_backend/role_delegation.py` | Operator-only planner → designer → coder/producer → tester for a fixed Flora catalogue product; verified ZIP remains in memory, not a queued job |
| Private verified artifact store (development) | `cloud_backend/verified_artifact_store.py`, `/api/agent/jobs/{job_id}/artifacts` | Operator-authenticated, immutable SHA-256-checked ZIP and sanitized role checkpoints on configured private storage; **no auto-worker** |
| Real product poster output | `cloud_backend/ad_studio.py`, `artifact_verifier.py` | Flora PNGs, copy and ZIP with verified contents |
| Urdu voice quality | `cloud_backend/urdu_tts_text.py` | Pronunciation fixes for common terms |
| Android APK/bridge | `android/app/src/main/java/com/valtron/jarvis/` | WebView, native mic/TTS, reminders, limited permitted accessibility |
| Regression and browser tests | `tests/`, `.github/workflows/` | Unit, JS, Playwright and Android build checks |

## 4. What is real vs what still needs work

**Implemented at code/test level, depending on actual configuration:** chat/personality hints, Gemini/Groq/OpenRouter routing, optional Z.AI/Mistral/NVIDIA key-gated fallback adapters, text/Urdu speech and cancellation, basic phone actions with permission, reminders, consent-based local memory, read-only trading/public-data tools, arithmetic, product **feed/story PNG** ads and ZIP verification, structured goal planning.

**Job record configuration (development only):** The private job metadata API stays disabled until the backend operator configures a random server-only `HOSHI_JOB_API_TOKEN` (at least 32 characters) and absolute `HOSHI_JOB_DB_PATH` on a persistent writable volume. It creates `planned` records, supports authenticated reads and an operator-authenticated `/api/agent/jobs/{job_id}/schedule` endpoint for bounded due-time queue entries. `cloud_backend/job_queue.py` provides atomic claims, limited concurrency, pending cancellation and explicitly invoked polling for **trusted Python handlers only**. No production handlers are registered and the FastAPI process starts **no** workers; scheduling a record is not executing a user task. It stores no prompts, files or secrets. Ordinary Render ephemeral disk can lose records after redeploy; never label it production-durable without mounted storage, recovery tests and per-user authorization. Never place this token in frontend JavaScript or an APK.

**Role delegation (Task 27 development):** `run_product_ad_roles("gold_kit" | "shampoo")` executes four actual trusted local steps: strict catalogue planning, approved design-theme selection, the existing offline PNG/ZIP renderer, and PNG/copy/ZIP verification with a SHA-256 digest. It rejects free-form instructions and unapproved products, never executes model-written code, and returns sanitized failure codes. The verified ZIP is only returned to the trusted Python caller **in memory**. It is not connected to an auto-started worker and cannot honestly mark a queued job succeeded. Task 28 provides a separate operator-only verified artifact store, but standalone role delegation does not save to it automatically; Task 29 still needs safe recovery and explicit worker handoff. No native phone actions, real photo claims, MP4 rendering, external posting, model requests or purchases are added.

**Private verified artifact storage (Task 28 development):** A trusted Python operator may pass the actual verified result of run_product_ad_roles to VerifiedArtifactStore.save_verified(job_id, result) **only for an already-running create_product_ads queue record**. The store re-runs PNG/ZIP/catalogue verification, validates the role receipts and SHA-256, publishes one immutable flora_ads.zip per job with 0600 permissions, and records sanitized planner/designer/coder/tester/persist checkpoints in the job SQLite database. A second call with the same bytes is idempotent; mismatches and tampering fail closed. The authenticated read-only endpoints GET /api/agent/jobs/{job_id}/artifacts and /api/agent/jobs/{job_id}/artifacts/download require the existing server-only job bearer token and also HOSHI_ARTIFACT_ROOT. The root must be an existing absolute 0700 private directory; configure it and HOSHI_JOB_DB_PATH on persistent storage **outside web roots**. Downloads rehash the ZIP and set Cache-Control: no-store. There is no HTTP upload/write route, no public download, no auto-started executor, no queue completion on save, no recovery guarantee across a crash, and no production volume configured. An artifact metadata record is not proof the blob is still healthy until the private download re-verifies it. Realme phone QA and live deployment remain separate.

**Operator-only crash recovery (Task 29, verified at source/test level):** `cloud_backend/job_recovery.py` adds a trusted-Python-only `JobRecovery` for SQLite queue records. The operator must explicitly confirm all workers using the database are stopped; an old running record must be at least five minutes stale. If a previously saved Flora ZIP passes private file rehash and all five checkpoint checks, the running job and queue are reconciled atomically to succeeded. Otherwise the job is quarantined as failed for review; no job is blindly replayed. For the strictly offline Flora ad kind only, a failed job with **no** artifact metadata, checkpoint or orphan directory may receive at most one distinct new pending job ID, atomically and within queue limits. Old handlers cannot complete the new ID. The retry does **not** know a product selection, register/start a worker or create media; it requires a separate trusted handler and verified inputs. This is not safe to invoke while any old worker may still be running. No HTTP recovery endpoint, public token, background daemon, auto-resume or production storage has been added. **Task 29 has passed Python/Node/Playwright CI** (https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40421559804) **and Docker smoke** (https://github.com/shani001223-droid/Jarws-ai-/actions/runs/40421529816). Device, persistent live volume and production deployment remain unverified.

**Private quiet job reporting (Task 30, development; acceptance pending CI):** `cloud_backend/job_reporting.py` builds a read-only report from authenticated SQLite metadata, queue state and optional verified artifact storage. `GET /api/agent/jobs/{job_id}/report` uses the existing server-only job bearer token, responds with `Cache-Control: no-store`, never starts a worker or sends a notification, and emits only bounded status/message codes, operator-only blocker codes and trusted checkpoint stage names. Planned/queued/running records remain explicitly unverified. A succeeded database flag is **not** enough for a final report: only a Flora ZIP rehashed on disk with all five matching checkpoints can yield a verified final artifact/download path. Missing/corrupted blobs, incomplete checkpoints, unsupported task kinds and queue/record disagreement yield `review_required`, never false success. Failed/canceled jobs receive sanitized terminal status reports; unknown worker detail codes are never echoed. This is an operator-authenticated **pull API**, not an end-user phone progress feed, a notification sender, an autonomous job executor or proof of production persistence. Full CI and Docker acceptance must pass before Task 30 is checked. No production merge/deployment.\n\n**Do NOT claim these as completed:** remotely running OpenJarvis server; unprovided Free-LLM provider keys; general persistent overnight creative jobs with reliable recovery; arbitrary screen reading/tap/type everywhere; native full video/MP4 ad production; automatic publishing; real trading; full animated episodes; finished games; unlimited AI intelligence; zero-errors across all user environments; sub-0.1-second voice replies. A storyboard is **not** an MP4; a milestone plan is **not** an executed job. Raw code passing CI is **not** the same as deploying it or passing phone QA.

**Current verified roadmap snapshot at consolidation:** 15 of 60 tasks marked completed in `HOSHI_60_TASK_MASTER_ROADMAP.md`; check the latest file for changes, never hard-code progress elsewhere. Tasks 06 (live deploy/rollback/phone acceptance) and 11 (real OpenJarvis server) require resources/permissions not currently verified. Later tasks remain in the roadmap.

## 5. Feature tracks — one assistant, modular execution

1. **Hoshi chat & voice:** low-latency measured reply, robust Roman Urdu STT, soft Urdu female TTS, natural safe personality, explicit Stop and privacy controls.
2. **Real phone assistant:** open supported apps, compose and edit writing, on-device reminders, stepwise user-approved screen actions; observe success/failure instead of inventing it.
3. **Flora By M/S&Co. business:** verified 24K Gold Facial Kit (6 products, Rs 3,500, gold/white packaging), Herbal Shampoo (500 mL, Rs 1,500), print assets, posters, eventually actual 15–60 s MP4 ads **using genuine supplied pack imagery** and license-safe audio. Current ad generator is PNG + script only.
4. **BTC / trading research:** read current public data, chart S/R and indicators, entry/SL/TP with explanatory risk, paper/demo testing only; **do not enable real trade execution**.
5. **Creative projects:** game planning → sandboxed code → playable mini-game and tests; anime planning → pilot sample → scene and episode generation only after real media worker/storage resources are demonstrated. Never claim 300 produced episodes without rendered files and checks.
6. **Autonomous job engine (future):** bounded background queue, checkpoints, persistent authenticated artifacts, error recovery, quiet progress/real final proof; implement and verify before marketing it as hands-off operation.

## 6. Design reference inventory (preserve, don't substitute)
Existing `assets/` visuals are source assets actually in this repo. Previously saved **ChatGPT Library** references include:
- `Hoshi: Blue Star Foxgirl Character Sheet.png`
- `Hoshi: Celestial Fox-Eared AI Companion.png`
- `Hoshi: Your Neon Voice Companion.png`
- `Hoshi’s Futuristic AI Dashboard.png`
- `Hoshi Neon Anime Assistant UI Collage.png`
- `Neon Hoshi AI Assistant Interface.png`
- `Hoshi’s Neon Bedroom Assistant.png`, `Hoshi’s Neon Nightroom Assistant.png`

These are **reference filenames**, not files automatically imported from Library into GitHub. The final selection/ordering across older image variations must be reviewed against the user's approved imagery before any visual replacement. User's latest priority: postpone appearance changes, improve intelligence and real work first.

**ChatGPT Library consolidation (26 October 2026):** all located Hoshi/JARVIS reference files and historical downloadable artifacts were **moved, not deleted**, into the Library folder `/HOSHI AI - Master Project/`. It contains 51 files: this portable handoff `HOSHI_AI_Master_Project_Handoff.md`, an archived Library copy of the roadmap, and 49 organized assets/prototypes under `01-Character-and-Emotions/`, `02-Interfaces-and-Trading/`, `03-Outfits-and-Poses/`, and `04-Legacy-JARVIS/`. **The current canonical task progress is in GitHub**; the Library roadmap is a historical snapshot. Archived JARVIS APKs are not current release APKs and must not be assumed safe/current on the phone. ChatGPT conversations themselves cannot be moved into a ChatGPT Project through GitHub or Library organization; users may group them with the ChatGPT Projects UI.

## 7. Rules for every new coding session / automated run

1. Read **this file**, the current `HOSHI_60_TASK_MASTER_ROADMAP.md`, relevant real source files, current PR head and GitHub CI status. Preserve earlier decisions, don't recreate the project.
2. Select the earliest safe independent unchecked task; avoid blocked live services and keep them explicitly pending.
3. Code only on the existing reviewed development branch (or a properly reviewed successor); never paste live secrets.
4. Run **relevant unit, security, front-end browser and Android build checks**, fix every discovered regression before checking off task. Evidence must link to actual run IDs and commit SHAs; mocked vs live must be explicit.
5. Mark just the verified task in **one** roadmap. Keep audit/README history but do not maintain competing checklists or duplicate PRs/automations.
6. Do not merge to production, change Render secrets or make external-account operations without explicit user authorization and required validation.
7. When blocked, record the exact missing dependency and progress another truly independent safe task; no fake success, no background work claims beyond configured automation.

## 8. Handoff text for a new ChatGPT conversation / Project

> Continue the **same HOSHI AI project**, NOT a new app. Canonical GitHub repo: `shani001223-droid/Jarws-ai-`; current development branch: `hoshi/dnd-foundation-20261026`; draft PR #24. Read `HOSHI_MASTER_PROJECT.md` and `HOSHI_60_TASK_MASTER_ROADMAP.md` first, then inspect current CI and code. Keep free-first, Realme Note 50, Pakistani Roman Urdu, soft Urdu voice, no fake Room Life, no secret commits, no real trading, no unauthorized phone/account actions. Work on the next feasible unchecked task; test, fix, and only then mark it verified. Do not merge/deploy to main without a separate release validation. Preserve previous Hoshi designs and actual Flora product assets. Never imply an unprovisioned OpenJarvis endpoint is running.

## 9. Supporting documents (not parallel projects)
- [60-task roadmap](HOSHI_60_TASK_MASTER_ROADMAP.md)
- [Original transformation notes](HOSHI_TASK_LIST.md)
- [Current foundation audit](HOSHI_PHASE1_AUDIT.md)
- [Real OpenJarvis requirements](HOSHI_OPENJARVIS_INTEGRATION.md)
- [Free provider configuration, no supplied keys](HOSHI_FREE_LLM_PROVIDERS.md)
- [Flora ad generator](HOSHI_AGENT_PRODUCT_ADS.md)
- [Production release and rollback](DEPLOYMENT_ROLLBACK.md)
- [Spot research rules, formulas and simulation limits](HOSHI_TRADING_RESEARCH.md)

**Any new feature belongs inside this one project and must be linked back here.**

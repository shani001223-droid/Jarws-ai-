# HOSHI Trading V3 — curriculum and integration progress

Start date: **28 October 2026, Asia/Karachi**. Current day: **Day 1**.
Work branch: `hoshi-v3-god-mode`. Backup: `backup-v2-to-v3`.
Both were created from the fetched development source
`51b88506d8c65dd0280f0f68783e86bd4bae6548`, preserving the existing project.
That source includes earlier development work; it is not a claim that the
entire branch was already deployed. Production V2 remains a separate release.

## Current measured progress

**Day 1: completed 1 of 48 planned knowledge chapters — 2.08%; 47 chapters,
97.92% of the declared curriculum, remain.**

The denominator is the initial, expandable file manifest in
`knowledge_base/manifest.json`. It is not a percentage of every fact on Earth,
all possible trading concepts, the separate 60-task Hoshi project, runtime
integration, profitability or completion of the entire V3 release. Additional
topics require an explicit manifest/progress revision, never silent omission.

| Delivery area | Actual status |
| --- | --- |
| Requested work/backup branches | Created and preserved |
| `00_HISTORY_OF_EVERYTHING/history_of_money.md` | Written; source-checked; actual body count and SHA-256 recorded in manifest |
| Remaining curriculum documents | Pending; no empty placeholder chapters counted as complete |
| Brain loader and runtime knowledge bundle | Pending — the new chapter is not yet consumed by Hoshi |
| 40/20/20/20 history/liquidity/structure/global-flow engine | Pending — weights will mean evidence coverage, not an invented win probability |
| Full V3 backend, UI, historical evaluation and release tests | Pending |
| Merge to main / production V3 | Pending — no early production merge |

## Work log

- **28 October, Day 1:** fetched latest development code; created the exact
  requested branches before editing; wrote the first substantive chapter with
  thirteen source references, application/failure analysis and three dated
  historical case studies. Institutional-event evidence is distinguished from
  missing quantitative market-return data. No annual events, current quotes,
  100% trade reliability or 92% probability were fabricated.
- Added the machine-readable 48-chapter scope, deterministic word/digest/section
  checks and a narrowly scoped GitHub content-integrity workflow. The validator
  checks mechanical receipts; historical accuracy still requires source review.
- First chapter commit message: `HOSHI V3: Completed history_of_money.md - 2.08% Done`.
  A commit cannot contain its own hash; use this file's GitHub history for the
  first receipt, and record it in the next chapter's work log.
- **Continuation configured:** the separate **Build Hoshi Trading V3** task is
  enabled for hourly work, starting **28 October 2026 at 02:45 PKT**, with 1,608
  occurrences (a 67-day schedule). This schedules bounded runs; it is not a
  continuously running process or a guarantee of completion on a fixed date.
  Existing Hoshi automations are unchanged. Subsequent runs must read actual
  source/CI/progress and commit real verified work, not repeat a plan.

## Completion and release rules

Every curriculum Markdown chapter requires at least 1,000 substantive body
words, the required what/why/application/failure sections, three genuinely
documented dated examples and original source-attributed prose. Bibliographies
do not count toward the body-word minimum. Use primary technical sources and
verify current or uncertain facts. A historical statement and a measured asset
reaction are different kinds of evidence. Missing event prices, durations,
unsupported markets and uncertain chronology must stay explicitly missing.

When the curriculum is source-checked, integrate integrity-checked bounded
retrieval into the existing brain and backend build context. Concise trading
responses may use internal knowledge without giving a lecture; they must
still disclose supported symbols, observed evidence times, paper-only status
and important missing inputs. Similarity scores are not calibrated confidence.
No pattern is promised to work 100% and no real-money order capability is added.

The user's conditional automatic main merge applies only after the declared
curriculum, actual loader/engine/API/UI integration and exact-head release
checks are complete. Reconcile current main, inspect inherited changes, verify
Python/JavaScript/mobile browser/Docker and relevant APK checks, and inspect
existing free Render deploy results if a merge triggers deployment. File-count
completion alone must never trigger a merge or a claim of universal knowledge.
Physical Realme and long-horizon trading performance require actual evidence.

Run locally before a chapter commit:

```bash
python scripts/check_v3_knowledge.py
git diff --check
```

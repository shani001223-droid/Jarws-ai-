# HOSHI Task 48 — grounded offline Flora reporting foundation (PARTIAL)

Existing Hoshi development branch and single draft PR #29 only. The trusted
Python-only module `cloud_backend/flora_reporting.py` accepts up to 250
redacted sales records and 250 redacted campaign metric records in a bounded
1–31-day date window. `tests/test_flora_reporting.py` exercises aggregation,
date/schema/PII rejection, missing evidence, price drift and unverified
attribution. This does not create a new project, account integration or API.

Only exact opaque record IDs, dates, product/placement IDs, numeric reported
receipts/refunds, counts and evidence source labels are allowed. Customer
names, addresses, phones, emails, platform tokens and arbitrary extra fields
are rejected. Input data is not stored, transmitted or echoed; output includes
a SHA-256 revision of the normalized records, not proof of source authenticity.
Catalogue consistency is checked against the existing owner-reported Flora
products; catalogue list prices are never multiplied to invent sales.

A report with no records has sales=null and campaigns=null, **not zero**.
Missing spend coverage yields null spend, not a fabricated zero. When supplied,
totals are explicitly operator-reported and unverified; no conversion rate,
profit, ROAS, independently confirmed attribution, campaign success, or
verified financial performance is inferred. There is no HTTP endpoint, worker,
posting, purchase, external account access, new key or production deployment.

**Task 48 remains UNCHECKED** until genuine redacted owner-authorized sales
and platform evidence is supplied, reconciled, privacy-reviewed and tested in
the actual owner workflow. Tasks 43/45/46/47, physical Realme Note 50 QA (06)
and real OpenJarvis server (11) also remain pending. The canonical scoreboard
is only `HOSHI_60_TASK_MASTER_ROADMAP.md`.

CI results for this change must be checked on the exact GitHub commit before
any verification claim. Passing unit tests does not establish live data truth.

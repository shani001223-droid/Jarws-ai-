# HOSHI Task 47 — offline Flora post preview (partial, not accepted)

The existing Hoshi project now has a deterministic, read-only post preview in
cloud_backend/flora_post_planning.py and GET /api/flora/post-preview. It reuses
the fixed Task 44 campaign planner and owner-reported Task 43 catalogue.
Allowed products are gold_kit and shampoo; platforms are Instagram feed/story,
Facebook feed and WhatsApp status; objectives are awareness and inquiries.

An optional proposed_local_time must be a full Karachi (+05:00) ISO 8601
timestamp with seconds, at least two hours and no more than 30 days ahead.
The result includes the UTC equivalent, an hour-before review deadline,
a SHA-256 digest binding the exact copy/brief/slot, and explicit approval gates.
This is a proposal, NOT a scheduled or queued post.

All owner-approval gates remain false. Every response says publishable=false,
approved=false, persisted=false, queued=false, scheduled=false,
published=false, external_account_connected=false and auto_post_enabled=false.
No external APIs, tokens, HTTP upload, database writes, notifications, real
account permissions or post publishing are implemented. This route is GET-only
with no-store/nosniff headers; invalid times/options fail with HTTP 422.

The canonical Task 47 checkbox stays UNCHECKED. Real Task 47 acceptance needs
owner-approved current prices/stock, actual rights-cleared photos/media,
final copy approval, an explicitly authorized account, a private durable
approval record bound to the revision digest, supported scheduling integration,
and end-to-end live-account QA with separate explicit permission. Do not
infer those from offline code tests. Task 43, 45, 46, 06 and 11 remain blocked
as recorded in the sole canonical roadmap. No production merge/deploy.

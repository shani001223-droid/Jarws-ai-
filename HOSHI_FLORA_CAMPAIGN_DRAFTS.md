# HOSHI Task 44 — Flora platform campaign drafts (development only)

This is a deterministic, offline, **review-only** campaign planner within the
existing Hoshi project. `cloud_backend/flora_campaign.py` reads the existing
Task 43 owner-reported catalogue, and the read-only
`GET /api/flora/campaign-draft` route returns a platform-specific draft.
It does **not** generate a photograph, post, schedule, purchase, run a model,
use a social-media API, or alter an external account.

Supported fixed options:

| Parameter | Allowed values |
| --- | --- |
| `product_id` | `gold_kit`, `shampoo` |
| `platform` | `instagram_feed`, `instagram_story`, `facebook_feed`, `whatsapp_status` |
| `objective` | `awareness`, `inquiries` |

Feed drafts specify a 1080x1350 canvas; Story/Status drafts use 1080x1920.
English and Roman Urdu copy, a platform brief, and an explicit four-stage
owner review sequence are returned. The price appears **only** with an
owner-reported/reconfirm-before-posting warning. The creative brief says
`illustrated_template_only` and explicitly requires a genuine owner-supplied,
rights-approved photo before a publishable ad. No unsupported medical,
hair-growth, discount, stock or guaranteed-result claims are inserted.

Every response sets `publishable=false`, `published=false`,
`scheduled=false`, `auto_post_enabled=false`,
`photo_rights_verified=false`, `price_verified=false`, and
`orders_enabled=false`. Unsupported IDs/platforms/objectives return HTTP
422. A catalogue price mismatch fails closed. The route is GET-only and sets
no-store/nosniff headers.

Task 43 remains unchecked: actual owner-approved photos/rights, current
price/stock confirmation and private photo intake are still absent. Task 44
may be source/test verified independently because planning a draft does not
depend on publishing or the physical product photo. No production release,
Realme Note 50 physical QA or OpenJarvis server is implied. Only the
canonical `HOSHI_60_TASK_MASTER_ROADMAP.md` may mark task completion
after actual GitHub Python/JS/Playwright and Docker checks pass.

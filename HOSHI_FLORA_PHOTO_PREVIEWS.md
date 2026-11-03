# Hoshi Task 45 — Flora genuine-photo poster preview foundation

Development-only, in the existing Hoshi repository and draft PR #29.

`cloud_backend/flora_photo_posters.py` exposes **trusted Python only**
`render_flora_photo_preview(product_id, photo_bytes, mime_type, placement)`.
It accepts only fixed Flora catalogue IDs, a verified bounded PNG/JPEG/WebP
input and fixed feed/story placements. It returns a real 1080×1350 or
1080×1920 PNG in memory, its SHA-256, source-photo SHA-256 and a clearly
watermarked **DRAFT** filename/status. The source image is fitted without
cropping or inventing packaging details. The output is reopened and checked.

Caller-provided rights/price attestations are **not independently verified**.
Every preview remains `approved_for_publication=false`,
`published=false`, `saved=false`. This module does not create an upload
route, read device files, persist images, change the public catalogue, schedule
posts, access social accounts, or send a photo to an LLM. Tests use **synthetic
photos only**, never claim to show a genuine Flora product.

**Task 45 remains unchecked:** owner-supplied genuine photos, their rights,
current prices/stock, actual product-specific visual review, Android/Realme
acceptance and a reviewed user-facing preview workflow are still missing.
Task 43 likewise remains unchecked. Do not merge/deploy production without
authorization. No real-money trading.

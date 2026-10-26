# Hoshi Backend Task Execution — Product Ad Studio v1

Hoshi now recognizes a user command such as **"Mere products ke ads bana kar do"** and executes an allowlisted, real backend task instead of merely describing how to make ads.

## Execution flow
1. Android microphone or Chat message is recognized by `hoshi-product-ads.js`.
2. The app calls `POST /api/agent/execute` with `{"task":"create_product_ads","message":"..."}`.
3. The existing FastAPI backend selects a known product from a trusted local catalog.
4. Pillow renders **real feed (1080×1350) and story (1080×1920) PNG advertisements**, plus ready copy and a 15-second video **storyboard text**.
5. Backend streams no user files to third parties: a downloadable ZIP and PNG preview are returned in the single response, with no persisted job queue.
6. A browser can download the ZIP. Android 10+ APK can save it to `Downloads/Hoshi` via a constrained MediaStore bridge.

## Available products, verified from the owner's earlier brief
- **Flora 24K Gold Facial Kit** — six products, Rs. 3,500, gold-and-white theme.
- **Flora Herbal Shampoo** — 500 ml, Rs. 1,500, with amla, shikakai, tulsi, curry leaf and onion as listed by the owner.

The **ads are illustration/typographic templates, not product pack photographs**. No unverified claims about skin whitening, hair regrowth or health results appear. No QR code, WhatsApp number or contact is fabricated. A 15-second storyboard is **not a rendered MP4/video**. Authentic packaging imagery is required for genuine product-photo/video advertising; new user photos are never collected automatically.

## How to use
- Say or type: `Mere products ke ads bana do` (both products)
- `24K Gold Facial Kit ka ad banao` (facial kit)
- `Shampoo ka poster bana do` (shampoo)

The result appears in the existing Chat tab with a preview, copy, and **Download PNG ads + captions** button. For older APKs without `saveAdZip` bridge, Chrome browser download is the fallback.

## Safety, scale & pricing
The agent task endpoint uses an explicit allowlist, request size limits, a 2-job concurrency semaphore, a small in-memory rate limit (3 requests/minute per client), and maximum ZIP size. No arbitrary shell, crypto trading, external publishing, spending or payments. Free Pillow runs on the existing backend; large usage is still subject to Render hosting quota/resource limits. Secrets remain server-side.

## Next capability milestones (NOT yet implemented)
- Upload user-approved genuine product pack photos, logo and WhatsApp contact, then composite real photos
- Optional model-driven multi-step planner for general tasks beyond the product-ad tool
- Actual MP4 render workflow when media assets and a suitable free video encoder are available
- Explicit approval for posting ads directly to social accounts
- Persistent authenticated job history, queues and retry/recovery across Render restarts

Backend ad task **is real and immediately usable without an OpenJarvis server or any paid AI key**. Other OpenJarvis features remain dependent on separately configured real server/model.

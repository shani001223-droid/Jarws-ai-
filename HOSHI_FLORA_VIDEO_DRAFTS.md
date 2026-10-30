# Hoshi Task 46 — offline Flora MP4 DRAFT foundation

Development-only in the **existing** `shani001223-droid/Jarws-ai-` repository, successor draft PR #29. This does not authorize production deployment or social publishing.

`cloud_backend/flora_video_ads.py` exposes trusted-Python-only `render_flora_video_draft(product_id, photo_bytes, mime_type, placement="story", *, audio_wav=None, audio_rights_attested=False)`. It first validates the fixed owner-reported Flora catalogue and a bounded caller-supplied product photo using the existing Task 45 renderer. It renders an actual **3-second 12-fps H.264 MP4** with a DRAFT watermark and fade in/out, at 360x450 (feed) or 360x640 (story), using a locally installed **free FFmpeg** binary. FFprobe reopens the actual file and checks duration, video codec, dimensions and optional AAC track. SHA-256 and output size are returned; temporary files are cleaned up. No network, API keys, user uploads, scheduled workers, posting or real orders.

**Audio:** silent MP4 by default. Optional caller-supplied **16-bit PCM WAV** must meet strict rate/length/size checks and explicit caller rights attestation; it is encoded as AAC. A caller checkbox/attestation **does not independently establish a license**. No copyrighted soundtrack, voice impersonation or third-party music is bundled. Tests synthesize their own simple tone. Never label this as licensed audio until actual owner evidence is reviewed.

**Deployment limit:** FFmpeg/FFprobe are optional local runtime dependencies, **not** installed in the existing Render Python-slim Docker image by this change. The function fails closed when absent. There is no public video endpoint or phone-facing flow. Do not confuse local CI video generation with production support.

**Task 46 remains unchecked** pending real owner-approved Flora photographs, current prices/stock, audio licensing evidence, actual user-facing preview/acceptance, approved deployment support and Realme Note 50 QA. Task 43 and Task 45 remain unchecked. Do not publish, merge or deploy without explicit authorization.

## Private one-step operator handoff (30 October 2026; partial)

On a local machine with Python dependencies plus **free FFmpeg and ffprobe**, prepare a private output directory yourself and run:

```bash
python -m scripts.prepare_flora_private_photo \
  --photo ./owner-photo.jpg --mime image/jpeg \
  --product-id shampoo --output-dir ./existing-private-dir \
  --rights-attested --render-video --placement story
```

Choose `--placement feed` for a 360×450 draft or `story` for 360×640. Supported photo MIME types are JPEG, PNG and WebP. This produces four **create-only** local files: `flora_shampoo_PRIVATE_photo.png`, `flora_shampoo_PRIVATE_photo_provenance.json`, `flora_shampoo_story_DRAFT.png` and `flora_shampoo_story_DRAFT.mp4`. It never writes the original photo, EXIF/GPS or source path to output. The JSON binds sanitized-photo, poster and video SHA-256 and explicitly retains `owner_approved=false`, `publication_permitted=false`, unverified rights/price flags and `silent_no_music`. Existing outputs cannot be replaced. The original photo is unchanged. Omit `--render-video` for the previous photo-only intake.

**Verification:** source/test commit `feab1f4e46388bd12c0b78503789ce43b834d0a5` passed [Python/backend, JS and Playwright CI](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/41031302670) and [Docker smoke](https://github.com/shani001223-droid/Jarws-ai-/actions/runs/41031302683). Tests used a synthetic EXIF-bearing photo and real H.264/FFprobe output, not an approved Flora product image. Actual owner-approved photo, photo/music licenses, price/stock review, phone playback and human acceptance are **not verified**. This is an offline draft workflow only; no Render runtime, HTTP upload, social post or automatic approval is added. Canonical Tasks 43/45/46 stay unchecked and the 48/60 scoreboard is unchanged.

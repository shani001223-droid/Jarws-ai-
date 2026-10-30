# HOSHI Task 43 — Flora catalogue foundation (development only)

The existing `cloud_backend/ad_studio.py` is the single source of the current
two ad-template product records. `cloud_backend/flora_catalog.py` validates
their brand and prices against explicit owner-reported PKR amounts and serves
a read-only JSON snapshot via `GET /api/flora/catalog` (optional fixed
`product_id=gold_kit|shampoo`). It never edits the source, creates a new
business project, fetches a remote price, publishes an ad or places an order.

- Gold kit: six products, Rs. 3,500, premium gold/white creative theme.
- Herbal shampoo: 500 ml, Rs. 1,500; the existing caption remains unchanged.
- These values come from earlier owner instructions and the existing ad
  renderer, **not** a current independent inventory/price confirmation.
  Reconfirm prices, stock, ingredients and exact pack contents before public
  advertising. No medical/hair-growth claims are validated.
- **Actual owner-supplied product photos are not available in the repo's
  trusted catalogue.** Decorative template artwork is not product photography.
  The endpoint reports missing photo, null asset/digest, and no rights approval.
- A bounded offline `inspect_owner_photo(bytes, mime)` checks actual PNG,
  JPEG or WebP encoding, 400–4096px sides, <=8 MB and SHA-256. It does
  not save/upload the bytes, remove EXIF, verify ownership, authorize a
  publication, or register a photo in the catalogue. A future approved
  private asset intake must strip metadata, verify rights and persist securely.

Security: fixed IDs only, no arbitrary URLs/paths, no photo bytes or private
files in API output, no write routes, no purchases or external publishing.
The catalogue endpoint exposes the same marketing product/price information
already used by the existing public ad generator; it is not an authenticated
private inventory system.

Task 43 stays **unchecked** until real owner photo/rights approval, current
price confirmation, and relevant CI/browser/API acceptance are demonstrated.
Task 06 physical Realme Note 50 QA and Task 11 live OpenJarvis remain pending.

## 30 October 2026 — private photo normalization (development draft)

An operator can now prepare a **real locally supplied** product photograph for
an offline Flora poster/MP4 draft without storing the original. The new
`cloud_backend/flora_private_photo_intake.py` decodes all image pixels,
normalizes EXIF orientation, scales to a maximum 2048px side, flattens alpha
onto white and saves a fresh metadata-free RGB PNG **in memory**. Source and
sanitized SHA-256 digests are kept distinct; EXIF/GPS/ICC/camera metadata are
not copied into the output. `inspect_owner_photo` now rejects animated/APNG
sources and files that pass container verification but fail full pixel decode.

For a private, create-only local handoff, run:

```bash
mkdir -p ./private-flora
python -m scripts.prepare_flora_private_photo --photo ./owner-supplied.jpg --mime image/jpeg --product-id shampoo --output-dir ./private-flora --rights-attested
```

This writes only `flora_shampoo_PRIVATE_photo.png` and a separate private
provenance JSON, with restrictive file permissions and no overwrite. The
original source is never copied, deleted, uploaded or published. The sanitized
PNG may be supplied to existing `render_flora_photo_preview` and
`render_flora_video_draft` using MIME `image/png`; the original source digest
remains in the intake provenance. The operator's rights attestation is **not**
independent rights verification or owner/publication approval. Real Flora
product identity, actual photos, stock, current price, cleared audio and final
owner acceptance are still missing; synthetic CI fixtures do not satisfy them.

**Code-complete:** private normalization and create-only handoff. **CI-verified:**
await exact-head GitHub Python/JS/browser and Docker checks. **Real-world
verified:** no. Task 43, 45 and 46 remain unchecked; the only canonical
60-task scoreboard is `HOSHI_60_TASK_MASTER_ROADMAP.md` (48 checked, 12 pending).

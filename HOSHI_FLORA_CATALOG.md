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

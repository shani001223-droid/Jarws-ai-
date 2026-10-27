# Hoshi Task 32 — bounded offline document tools (development only)

The existing Hoshi backend now has `cloud_backend/document_tools.py`. It provides **trusted Python operator** functions that take bytes and return bytes/metadata; it does not create a new application, public upload route, file browser, phone permission or background worker.

## Supported operations

| Operation | Verified behavior | Explicit limits |
| --- | --- | --- |
| `inspect_document(name, data)` | Inspect UTF-8 TXT/MD/JSON, PDF page count + first-three-page text preview, PNG/JPEG/WebP dimensions | 3 MB input, 16 PDF pages, 4,000-character preview, 6 MP image pixel limit |
| `rotate_pdf(name, data, degrees, page_numbers)` | Rotate explicitly selected 1-based pages by 90/180/270 degrees and re-open output for validation | No arbitrary PDF content rewriting, forms, OCR, signatures or redaction |
| `resize_image(name, data, max_side)` | Downscale single-frame PNG/JPEG/WebP to a metadata-stripped PNG, keeping aspect ratio | 128–2048 max side; 6 MB output; not an image editor or photo generator |
| `replace_project_text(name, data, old, new, expected_sha256)` | Exactly one text replacement with source SHA-256 revision check; JSON syntax revalidated | TXT/MD/JSON only, max 64 KB; no automatic code editing or execution |

The module accepts **bytes only**, not file paths or URLs. File names must be simple base names, with known extensions; path traversal, executable files, malformed images/PDFs, encrypted PDFs, duplicate text matches, invalid JSON, oversized inputs, and stale edit revisions are rejected with sanitized errors. No data is saved to disk, uploaded, posted, sent to an LLM or used for a real-money trade. It does not expose secrets.

### Example (trusted Python caller only)

```python
from hashlib import sha256
from cloud_backend.document_tools import inspect_document, replace_project_text

original = b'{"brand":"Flora","price":3500}'
preview = inspect_document("catalog.json", original)
edited = replace_project_text("catalog.json", original, "3500", "3600",
                              sha256(original).hexdigest())
# edited["data"] is new JSON bytes; original stays untouched.
# Caller must separately review and approve any permanent write.
```

## Security and operational limitations

- This is **not a safe public file-upload API**. PDF parsing and image decoding are complex native/Python libraries and can consume CPU/RAM even when compressed input bytes are small. Before accepting untrusted files from a phone, execute the parser in a **separate resource-limited sandbox/process** with strict wall-clock, memory, CPU and output limits (Task 33). The current helpers have input/page/pixel limits but **do not** guarantee CPU or memory isolation.
- Scanned/image-only PDFs will not magically yield OCR text. PDFs may have fonts/layout that extract poorly; rotation is not redaction and may invalidate digital signatures. Inspect original and output visually before production use.
- No arbitrary filesystem access, network fetch, automatic overwrite, external sharing, publishing, production deploy or background execution. The user must explicitly authorize any account-affecting operation.
- Pillow and the free `pypdf` package are included in backend dependencies. No paid provider or API key is needed.
- CI acceptance must include `tests/test_document_tools.py`, existing Python/Node/Playwright regression and backend Docker build/health. Passing mocked/unit tests is **not** proof of Realme Note 50 device acceptance, PDF rendering fidelity on every document, or production persistence.

The canonical progress checkbox is **only** in `HOSHI_60_TASK_MASTER_ROADMAP.md`. Do not mark Task 32 complete until relevant CI/Docker evidence is green. Task 06 (production/device QA), Task 11 (real OpenJarvis) and Task 33 (sandboxing) remain separate.

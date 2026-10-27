# Hoshi Task 35 — Generated Output Format Gate

**Scope:** Development branch only; trusted Python callers. This gate is not a public upload API, autonomous worker, code security scanner or deployment claim.

The new cloud_backend/output_validation.py module implements four offline checks:

- validate_python_source(bytes): strict UTF-8, 64 KB max, Python AST parse/compile **without executing**. A syntactically valid script can still be malicious, incorrect or unsafe; it must never be run outside the Task 33 controlled sandbox.
- validate_json_document(bytes): strict UTF-8, 64 KB max, top-level object/array, duplicate-key and non-finite-number rejection. This checks format, not semantic truth.
- validate_png_media(bytes, expected_size=...): actual PNG decoding/verification, bounded bytes, one frame and only the existing 1080x1350 feed / 1080x1920 story sizes. Generated images are not claimed to depict real Flora packaging/photos.
- validate_campaign_zip(bytes): at most 10.1 MB, exact allowlisted one/two Flora product filenames, no encrypted or duplicate entries, bounded expanded sizes, fixed manifest schema, SHA-256 and byte-count agreement, nested product ZIP checks, actual PNG decoding and catalogue caption + **not a rendered video** storyboard checks. No extraction or arbitrary paths.

Task 34's offline orchestrate_flora_campaign() now requires this independent format validation before returning a successful campaign ZIP. Any failure is a sanitized campaign_verification_failed, without returning partial artifacts, marking a queued job succeeded, saving to disk or publishing to accounts.

**Limits:** No JavaScript parser/Node executor, video/MP4 validator, arbitrary ZIP support, malware scan, legal-license verification or proof that generated text/code is useful. Pillow/ZIP parsing occurs in-process, so untrusted uploads must first be isolated with separate resource limits; this validator is only for bounded trusted generator output. Python syntax acceptance is not permission to execute code. No production volume, phone QA, live provider or background worker is configured.

**Verification:** tests/test_output_validation.py checks real generated ZIP/PNG and rejects malformed Python, duplicate JSON keys, forged manifests, nested PNG corruption, digest mismatch, duplicate ZIP entries and fake MP4 claims. CI additionally runs all existing backend, JS and Playwright tests. The Docker smoke workflow exercises actual backend import and a real offline specialist. Only cite passing GitHub workflow run IDs once they finish; do not infer Android/production acceptance from CI.

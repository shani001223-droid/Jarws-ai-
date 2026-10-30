"""Offline, script-free mobile review of a private Flora DRAFT MP4.

This is a deterministic HTML artifact, never a publication or owner approval.
All file references are fixed same-directory names; no network or JavaScript.
"""
from __future__ import annotations

from html import escape
import re


_ALLOWED_PRODUCTS = {"gold_kit", "shampoo"}
_ALLOWED_PLACEMENTS = {"feed", "story"}


def build_flora_private_review_html(
    product_id: str, placement: str, photo_sha256: str,
    poster_sha256: str, video_sha256: str,
) -> bytes:
    """Build a local phone-friendly review page with byte-bound evidence."""
    if (type(product_id) is not str or product_id not in _ALLOWED_PRODUCTS
            or type(placement) is not str or placement not in _ALLOWED_PLACEMENTS):
        raise ValueError("Unsupported private Flora review identity.")
    digests = (photo_sha256, poster_sha256, video_sha256)
    if any(type(d) is not str or re.fullmatch(r"[0-9a-f]{64}", d) is None
           for d in digests):
        raise ValueError("Invalid private Flora review SHA-256.")
    photo = f"flora_{product_id}_PRIVATE_photo.png"
    poster = f"flora_{product_id}_{placement}_DRAFT.png"
    video = f"flora_{product_id}_{placement}_DRAFT.mp4"
    page = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; connect-src 'none'">
<title>Flora PRIVATE DRAFT review</title>
<style>
:root { color-scheme: dark; }
body { margin: 0; background: #0e1419; color: #f5f1e9; font: 16px/1.5 system-ui, sans-serif; }
main { max-width: 680px; padding: 16px; margin: auto; }
h1 { font-size: 1.4rem; margin: 0 0 12px; }
h2 { font-size: 1.05rem; margin-top: 22px; }
.warning { border: 2px solid #e7b35b; padding: 12px; background: #252016; }
img, video { display: block; max-width: 100%; width: auto; max-height: 70vh; height: auto; margin: 8px auto; }
video { background: #000; width: min(100%, 360px); }
code { overflow-wrap: anywhere; font-size: .75rem; }
small { color: #c7cbd0; }
</style>
</head>
<body><main>
<h1>Flora private product-ad review</h1>
<p class="warning"><strong>DRAFT — NOT APPROVED FOR PUBLICATION.</strong>
Photo ownership, product identity, current price/stock, music rights and final ad quality
have not been independently verified. This preview has no audio and must not be uploaded
or published automatically.</p>
<p>Product: <strong>__PRODUCT__</strong> · Placement: <strong>__PLACEMENT__</strong></p>
<h2>Actual encoded silent H.264 MP4</h2>
<video controls playsinline preload="metadata" poster="__POSTER__" src="__VIDEO__">
Your browser cannot play this local MP4.</video>
<h2>DRAFT poster</h2><img alt="Unapproved Flora DRAFT poster" loading="lazy" src="__POSTER__">
<h2>Sanitized source photo</h2><img alt="Locally sanitized unapproved product photo" loading="lazy" src="__PHOTO__">
<h2>Local SHA-256 evidence</h2>
<p><small>Sanitized photo:</small> <code>__PHOTO_SHA__</code></p>
<p><small>Poster:</small> <code>__POSTER_SHA__</code></p>
<p><small>MP4:</small> <code>__VIDEO_SHA__</code></p>
<p><small>Review the actual product, price, rights, readability and phone playback
before any separate human approval. Hashes prove local byte consistency, not authenticity.</small></p>
</main></body></html>
"""
    values = {
        "__PRODUCT__": product_id,
        "__PLACEMENT__": placement,
        "__PHOTO__": photo,
        "__POSTER__": poster,
        "__VIDEO__": video,
        "__PHOTO_SHA__": photo_sha256,
        "__POSTER_SHA__": poster_sha256,
        "__VIDEO_SHA__": video_sha256,
    }
    for key, value in values.items():
        page = page.replace(key, escape(value, quote=True))
    encoded = page.encode("utf-8")
    if len(encoded) > 16_000:
        raise ValueError("Private review page exceeded safe limit.")
    return encoded

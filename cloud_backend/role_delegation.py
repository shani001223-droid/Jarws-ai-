"""Trusted four-role delegation for a small, *in-memory* Flora ad job.

Task 27: planner -> designer -> coder/producer -> tester. Each role runs a
known local Python function; no model-written Python, shell, web fetch,
arbitrary URLs, user prompts, purchases or account actions are executed.
The only supported input is an exact key from the trusted product catalogue.
This module is NOT registered as a queue handler or public API endpoint.
Task 28 must supply private authenticated artifact persistence before a
queued job can honestly be marked succeeded.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
from io import BytesIO
from zipfile import BadZipFile, ZipFile

try:
    from .ad_studio import CATALOG, create_ad_pack
    from .artifact_verifier import verify_ad_pack
except ImportError:  # direct cloud_backend working-directory imports
    from ad_studio import CATALOG, create_ad_pack
    from artifact_verifier import verify_ad_pack


# Fixed strings are instructions to an existing local renderer, not model prompts.
_PRODUCT_REQUESTS = {
    "gold_kit": "Create Flora gold facial kit ads",
    "shampoo": "Create Flora shampoo ads",
}
_ROLE_ORDER = ("planner", "designer", "coder", "tester")
_MAX_ZIP = 5_000_000
_MAX_BASE64 = (_MAX_ZIP * 4 // 3) + 12


class DelegationError(ValueError):
    """Predictable failure code without leaking exception text."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _expected_files(key: str) -> frozenset[str]:
    return frozenset({
        f"{key}_feed_1080x1350.png",
        f"{key}_story_1080x1920.png",
        f"{key}_caption.txt",
        f"{key}_video_storyboard.txt",
    })


def _receipt(role: str, status: str, code: str) -> dict:
    return {"role": role, "status": status, "evidence_code": code}


def run_product_ad_roles(product_key: str, *, producer=None, verifier=None) -> dict:
    """Run four bounded trusted roles, return a verified in-memory artifact.

    Callers may supply test doubles as Python functions. These are NOT
    accepted over HTTP and must never be built from user/model code. The
    returned base64 ZIP remains in caller memory; no persistence, publishing,
    scheduled execution or durable completion is implied.
    """
    receipts = []
    role = "planner"
    try:
        # Planner: strict allowlist; no arbitrary free-form job instructions.
        if type(product_key) is not str or product_key not in _PRODUCT_REQUESTS:
            raise DelegationError("unsupported_product")
        if product_key not in CATALOG:
            raise DelegationError("catalog_unavailable")
        request = _PRODUCT_REQUESTS[product_key]
        expected = _expected_files(product_key)
        receipts.append(_receipt(role, "verified", "trusted_scope"))

        # Designer: enforce the approved catalogue's existing illustration
        # palette. No unseen user photography is invented or modified.
        role = "designer"
        if CATALOG[product_key].get("theme") not in {"ivory", "dark"}:
            raise DelegationError("unapproved_design")
        receipts.append(_receipt(role, "verified", "catalog_theme"))

        # Coder/producer: use the already-implemented local renderer. No
        # arbitrary code execution, model calls, disk writes or remote calls.
        role = "coder"
        build = create_ad_pack if producer is None else producer
        if not callable(build):
            raise DelegationError("invalid_producer")
        pack = build(request)
        if not isinstance(pack, dict):
            raise DelegationError("invalid_artifact")
        encoded = pack.get("zip_base64")
        if not isinstance(encoded, str) or len(encoded) > _MAX_BASE64:
            raise DelegationError("artifact_too_large")
        receipts.append(_receipt(role, "verified", "local_renderer"))

        # Tester: the existing PNG/ZIP verifier validates dimensions,
        # expected entries, copy, catalogue and image integrity.
        role = "tester"
        check = verify_ad_pack if verifier is None else verifier
        if not callable(check):
            raise DelegationError("invalid_verifier")
        result = check(pack, request)
        if not isinstance(result, dict) or result.get("passed") is not True:
            raise DelegationError("verification_failed")
        try:
            archive_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise DelegationError("invalid_artifact") from None
        if not archive_bytes or len(archive_bytes) > _MAX_ZIP:
            raise DelegationError("artifact_too_large")
        try:
            with ZipFile(BytesIO(archive_bytes)) as archive:
                if set(archive.namelist()) != expected or len(archive.namelist()) != len(expected):
                    raise DelegationError("unexpected_artifacts")
        except (BadZipFile, OSError):
            raise DelegationError("invalid_artifact") from None
        receipts.append(_receipt(role, "verified", "zip_png_copy_verified"))
        return {
            "ok": True,
            "status": "verified_in_memory",
            "kind": "create_product_ads",
            "product_key": product_key,
            "role_order": list(_ROLE_ORDER),
            "steps": receipts,
            "artifact": pack,
            "artifact_sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "artifact_size_bytes": len(archive_bytes),
            "persisted": False,
            "queued_job_completed": False,
            "note": "Real PNG/ZIP verified in memory only; no durable storage or publishing.",
        }
    except Exception as exc:
        # No raw exception, private file path or renderer payload leaves the
        # boundary. Even a broken injected test double cannot fake success.
        code = exc.code if isinstance(exc, DelegationError) else "role_failed"
        receipts.append(_receipt(role, "failed", code))
        return {
            "ok": False,
            "status": "failed",
            "kind": "create_product_ads",
            "steps": receipts,
            "failed_role": role,
            "error_code": code,
            "artifact": None,
            "persisted": False,
            "queued_job_completed": False,
        }

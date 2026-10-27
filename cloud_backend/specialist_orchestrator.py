"""Task 34: bounded, operator-only orchestration of scoped offline specialists.

This is a *real* in-memory two-product campaign pipeline, not an LLM agent
swarm, daemon, queue executor, file uploader or external-account integration.
Only approved Flora catalogue keys are accepted. Each delegated creative runs
the already-tested planner/designer/producer/tester workflow; an independent
auditor re-verifies every artifact before the packager combines ZIPs.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
from io import BytesIO
import json
import re
from zipfile import BadZipFile, ZIP_STORED, ZipFile

try:
    from .ad_studio import CATALOG
    from .artifact_verifier import verify_ad_pack
    from .role_delegation import run_product_ad_roles
    from .output_validation import validate_campaign_zip, OutputFormatError
except ImportError:  # Direct Uvicorn working-directory imports.
    from ad_studio import CATALOG
    from artifact_verifier import verify_ad_pack
    from role_delegation import run_product_ad_roles
    from output_validation import validate_campaign_zip, OutputFormatError


_REQUESTS = {
    "gold_kit": "Create Flora gold facial kit ads",
    "shampoo": "Create Flora shampoo ads",
}
_ROLES = ("planner", "designer", "coder", "tester")
_MAX_INNER_ZIP = 5_000_000
_MAX_CAMPAIGN_ZIP = 10_100_000
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class SpecialistError(ValueError):
    """Safe, bounded code; never expose third-party exception details."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _receipt(specialist: str, status: str, code: str, product: str | None = None) -> dict:
    record = {"specialist": specialist, "status": status, "evidence_code": code}
    if product is not None:
        record["product_key"] = product
    return record


def _scope(keys: object) -> tuple[str, ...]:
    if type(keys) not in (tuple, list) or not 1 <= len(keys) <= 2:
        raise SpecialistError("invalid_campaign_scope")
    if any(type(key) is not str or key not in _REQUESTS or key not in CATALOG for key in keys):
        raise SpecialistError("unapproved_product")
    if len(set(keys)) != len(keys):
        raise SpecialistError("duplicate_product")
    return tuple(keys)


def _check_stop(callback) -> None:
    if callback is None:
        return
    try:
        stopped = callback()
    except Exception:
        raise SpecialistError("stop_check_failed") from None
    if type(stopped) is not bool:
        raise SpecialistError("invalid_stop_result")
    if stopped:
        raise SpecialistError("operator_stopped")


def _audit(key: str, result: object) -> bytes:
    """Never trust a delegate's success flag, digest or role receipts alone."""
    if not isinstance(result, dict) or (
        result.get("ok") is not True or result.get("status") != "verified_in_memory"
        or result.get("kind") != "create_product_ads"
        or result.get("product_key") != key
        or result.get("persisted") is not False
        or result.get("queued_job_completed") is not False
        or result.get("role_order") != list(_ROLES)
    ):
        raise SpecialistError("unverified_delegation")
    steps = result.get("steps")
    if not isinstance(steps, list) or len(steps) != len(_ROLES) or any(
        not isinstance(step, dict)
        or step.get("role") != role
        or step.get("status") != "verified"
        for role, step in zip(_ROLES, steps)
    ):
        raise SpecialistError("invalid_role_evidence")
    pack = result.get("artifact")
    if not isinstance(pack, dict):
        raise SpecialistError("missing_artifact")
    encoded = pack.get("zip_base64")
    if not isinstance(encoded, str) or len(encoded) > (_MAX_INNER_ZIP * 4 // 3 + 12):
        raise SpecialistError("invalid_artifact_size")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise SpecialistError("invalid_artifact_encoding") from None
    if not data or len(data) > _MAX_INNER_ZIP:
        raise SpecialistError("invalid_artifact_size")
    digest = hashlib.sha256(data).hexdigest()
    if (
        type(result.get("artifact_size_bytes")) is not int
        or result["artifact_size_bytes"] != len(data)
        or not isinstance(result.get("artifact_sha256"), str)
        or not _SHA256_RE.fullmatch(result["artifact_sha256"])
        or result["artifact_sha256"] != digest
    ):
        raise SpecialistError("artifact_digest_mismatch")
    try:
        verification = verify_ad_pack(pack, _REQUESTS[key])
    except Exception:
        raise SpecialistError("artifact_unverified") from None
    if not isinstance(verification, dict) or verification.get("passed") is not True:
        raise SpecialistError("artifact_unverified")
    return data


def _package(artifacts: list[tuple[str, bytes]]) -> tuple[bytes, dict]:
    manifest = {
        "schema_version": 1,
        "kind": "flora_offline_campaign",
        "rendered_video": False,
        "products": [
            {"product_key": key, "filename": key + ".zip",
             "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for key, data in artifacts
        ],
    }
    manifest_bytes = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    if sum(len(data) for _, data in artifacts) + len(manifest_bytes) + 2048 > _MAX_CAMPAIGN_ZIP:
        raise SpecialistError("campaign_size_limit")
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_STORED) as archive:
        archive.writestr("manifest.json", manifest_bytes)
        for key, data in artifacts:
            archive.writestr(key + ".zip", data)
    payload = output.getvalue()
    if len(payload) > _MAX_CAMPAIGN_ZIP:
        raise SpecialistError("campaign_size_limit")
    try:
        with ZipFile(BytesIO(payload)) as archive:
            expected = {"manifest.json", *(key + ".zip" for key, _ in artifacts)}
            names = archive.namelist()
            if len(names) != len(expected) or set(names) != expected:
                raise SpecialistError("campaign_verification_failed")
            if archive.read("manifest.json") != manifest_bytes:
                raise SpecialistError("campaign_verification_failed")
            for key, data in artifacts:
                if archive.read(key + ".zip") != data:
                    raise SpecialistError("campaign_verification_failed")
    except (BadZipFile, OSError, ValueError, EOFError):
        raise SpecialistError("campaign_verification_failed") from None
    # Task 35: a second, format-focused validator re-opens the finished
    # archive and verifies the manifest, nested PNGs and honest storyboard.
    # A hash or the producer's own success flag is not sufficient evidence.
    try:
        format_evidence = validate_campaign_zip(payload)
        if format_evidence["products"] != [key for key, _ in artifacts]:
            raise SpecialistError("campaign_verification_failed")
    except (OutputFormatError, SpecialistError):
        raise SpecialistError("campaign_verification_failed") from None
    return payload, manifest


def orchestrate_flora_campaign(product_keys: object, *, stop_requested=None,
                               delegate=None) -> dict:
    """Execute only known offline specialists and return verified in-memory ZIP.

    Trusted Python callers may inject a delegate/stop callback for testing.
    Never expose those callables, arbitrary tool names or a prompt executor via
    HTTP. The callback is checked between stages, not during a synchronous
    renderer; it cannot forcibly interrupt an already running specialist.
    No disk persistence, job status mutation, web request or publication occurs.
    """
    steps: list[dict] = []
    stage = "catalog_planner"
    product = None
    try:
        keys = _scope(product_keys)
        if stop_requested is not None and not callable(stop_requested):
            raise SpecialistError("invalid_stop_handler")
        if delegate is not None and not callable(delegate):
            raise SpecialistError("invalid_delegate")
        _check_stop(stop_requested)
        steps.append(_receipt(stage, "verified", "catalog_allowlist"))
        run = run_product_ad_roles if delegate is None else delegate
        generated = []
        for key in keys:
            product = key
            stage = "creative_specialist"
            _check_stop(stop_requested)
            result = run(key)
            if not isinstance(result, dict) or result.get("ok") is not True:
                raise SpecialistError("creative_failed")
            steps.append(_receipt(stage, "verified", "offline_role_pipeline", key))
            stage = "artifact_auditor"
            _check_stop(stop_requested)
            data = _audit(key, result)
            generated.append((key, data))
            steps.append(_receipt(stage, "verified", "independent_png_zip_check", key))
        product = None
        stage = "campaign_packager"
        _check_stop(stop_requested)
        payload, manifest = _package(generated)
        steps.append(_receipt(stage, "verified", "combined_zip_reverified"))
        return {
            "ok": True,
            "status": "verified_in_memory",
            "kind": "flora_offline_campaign",
            "specialists": steps,
            "manifest": manifest,
            "artifact": {
                "mime_type": "application/zip",
                "filename": "flora_campaign.zip",
                "zip_base64": base64.b64encode(payload).decode("ascii"),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            },
            "persisted": False,
            "queued_job_completed": False,
            "published": False,
        }
    except Exception as exc:
        code = exc.code if isinstance(exc, SpecialistError) else "specialist_failed"
        canceled = code == "operator_stopped"
        steps.append(_receipt(stage, "canceled" if canceled else "failed", code, product))
        return {
            "ok": False,
            "status": "canceled" if canceled else "failed",
            "kind": "flora_offline_campaign",
            "specialists": steps,
            "failed_specialist": stage,
            "error_code": code,
            "artifact": None,
            "persisted": False,
            "queued_job_completed": False,
            "published": False,
        }

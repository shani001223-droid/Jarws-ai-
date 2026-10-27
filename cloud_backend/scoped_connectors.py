"""Read-only, operator-authenticated GitHub connector for ONE Hoshi repository.

This module has no write methods, arbitrary URL support, redirect following,
GitHub search, token persistence, or browser/mobile credential exposure.
Callers must authenticate independently before invoking this adapter.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import ssl
from threading import BoundedSemaphore
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import (
    HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener,
)

_REPOSITORY = "shani001223-droid/Jarws-ai-"
_BRANCH = "hoshi/dnd-foundation-20261026"
_ALLOWED_PATH = re.compile(
    r"(?:README\.md|HOSHI_[A-Z0-9_]+\.md|"
    r"cloud_backend/[a-z][a-z0-9_]*\.py|"
    r"tests/test_[a-z0-9_]+\.py)\Z"
)
_TOKEN = re.compile(r"[A-Za-z0-9_.-]{20,512}\Z")
_GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
_MAX_FILE = 32_768
_MAX_RESPONSE = 100_000
_SLOTS = BoundedSemaphore(2)


class InvalidConnectorPath(ValueError):
    """A file path is outside the operator-approved read scope."""


class ScopedConnectorError(Exception):
    """A safe fixed error; upstream response bodies and tokens are never echoed."""


class _DenyRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def github_connector_ready(token: str) -> bool:
    """Configuration only, never evidence that the token works remotely."""
    return isinstance(token, str) and _TOKEN.fullmatch(token) is not None


def _request_json(url: str, token: str) -> dict:
    # Never use environment HTTP proxies or forward credentials on redirects.
    opener = build_opener(
        ProxyHandler({}), HTTPSHandler(context=ssl.create_default_context()),
        _DenyRedirect(),
    )
    request = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Hoshi-Private-ReadOnly-Connector",
    }, method="GET")
    try:
        with opener.open(request, timeout=5) as response:
            if response.status != 200:
                raise ScopedConnectorError("github_read_unavailable")
            raw = response.read(_MAX_RESPONSE + 1)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        raise ScopedConnectorError("github_read_unavailable") from None
    if len(raw) > _MAX_RESPONSE:
        raise ScopedConnectorError("github_response_too_large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        raise ScopedConnectorError("github_response_invalid") from None
    if not isinstance(payload, dict):
        raise ScopedConnectorError("github_response_invalid")
    return payload


def read_scoped_github_file(path: str, token: str) -> dict:
    """Fetch a bounded UTF-8 source file from the fixed development branch.

    Returned repository content is untrusted data, not agent instructions.
    No external calls occur for invalid paths or missing server-only tokens.
    """
    if not isinstance(path, str) or _ALLOWED_PATH.fullmatch(path) is None:
        raise InvalidConnectorPath("github_path_not_allowed")
    if not github_connector_ready(token):
        raise ScopedConnectorError("github_connector_not_configured")
    if not _SLOTS.acquire(blocking=False):
        raise ScopedConnectorError("github_connector_busy")
    try:
        encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))
        url = (
            "https://api.github.com/repos/" + _REPOSITORY
            + "/contents/" + encoded_path + "?ref=" + quote(_BRANCH, safe="")
        )
        item = _request_json(url, token)
        if (item.get("type") != "file" or item.get("path") != path
                or item.get("encoding") != "base64"
                or type(item.get("size")) is not int
                or not 0 <= item["size"] <= _MAX_FILE
                or not isinstance(item.get("content"), str)
                or not isinstance(item.get("sha"), str)
                or _GIT_SHA.fullmatch(item["sha"]) is None):
            raise ScopedConnectorError("github_file_invalid")
        encoded = item["content"].replace("\n", "").replace("\r", "")
        if len(encoded) > ((_MAX_FILE + 2) // 3) * 4:
            raise ScopedConnectorError("github_file_too_large")
        try:
            data = base64.b64decode(encoded, validate=True)
            source = data.decode("utf-8", errors="strict")
        except (binascii.Error, UnicodeError, ValueError):
            raise ScopedConnectorError("github_file_invalid") from None
        git_hash = hashlib.sha1(
            b"blob " + str(len(data)).encode("ascii") + b"\0" + data
        ).hexdigest()
        if (len(data) != item["size"] or len(data) > _MAX_FILE
                or "\0" in source or git_hash != item["sha"]):
            raise ScopedConnectorError("github_integrity_failed")
        return {
            "repository": _REPOSITORY,
            "ref": _BRANCH,
            "path": path,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
            "content": source,
            "read_only": True,
            "content_is_untrusted_data": True,
        }
    finally:
        _SLOTS.release()

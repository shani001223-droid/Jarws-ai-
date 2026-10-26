"""Integration with the real OpenJarvis agent server (Apache-2.0).

OpenJarvis's `jarvis serve` exposes POST /v1/chat/completions. This adapter
connects HOSHI's existing FastAPI app to a *separately running* OpenJarvis
orchestrator with tools/memory configured at that server.

No Python OpenJarvis SDK, Ollama model, or Rust wheels are silently installed
onto the small existing Render backend. No fake OpenJarvis responses.
"""
import ipaddress
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class OpenJarvisUnavailable(RuntimeError):
    """The optional OpenJarvis server is missing or unavailable."""


def endpoint():
    """Require explicit HTTPS endpoint + model; never accept runtime user URLs."""
    configured = os.getenv("OPENJARVIS_URL", "").strip().rstrip("/")
    model = os.getenv("OPENJARVIS_MODEL", "").strip()
    if not configured or not model:
        return None
    parsed = urlparse(configured)
    # Permit loopback HTTP only for development; no arbitrary private HTTP
    # hosts, credentials, redirects or query strings.
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OpenJarvisUnavailable("OpenJarvis URL must not include credentials or a query.")
    if parsed.path not in ("", "/", "/v1"):
        raise OpenJarvisUnavailable("OpenJarvis URL must be server origin or /v1.")
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise OpenJarvisUnavailable("OpenJarvis server URL is invalid.")
    if parsed.scheme == "http" and parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise OpenJarvisUnavailable("Remote OpenJarvis URL must use HTTPS.")
    if parsed.port is not None and not (1 <= parsed.port <= 65535):
        raise OpenJarvisUnavailable("OpenJarvis port is invalid.")
    return configured.removesuffix("/v1") + "/v1/chat/completions", model


class _NoRedirect(__import__("urllib.request", fromlist=["HTTPRedirectHandler"]).HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def ask_openjarvis(message: str, instruction: str, timeout: float = 7.0) -> str:
    target = endpoint()
    if target is None:
        raise OpenJarvisUnavailable("OpenJarvis is not configured.")
    url, model = target
    # OpenJarvis server-side orchestrator (not a pretend local copy) chooses
    # tools/retrieval. Tool execution policy lives in the remote configuration.
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": instruction[:4500]},
            {"role": "user", "content": message[:6000]},
        ],
        "stream": False,
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    headers = {"Content-Type": "application/json"}
    token = os.getenv("OPENJARVIS_API_KEY", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url, data=json.dumps(body).encode("utf-8"),
                      method="POST", headers=headers)
    try:
        # The configured OpenJarvis server should be HTTPS/authenticated.
        # Block redirects so auth credentials are never forwarded elsewhere.
        from urllib.request import build_opener
        with build_opener(_NoRedirect()).open(request, timeout=max(1.0, min(float(timeout), 12.0))) as result:
            raw = result.read(200001)
    except HTTPError as exc:
        raise OpenJarvisUnavailable("OpenJarvis responded with HTTP " + str(exc.code)) from None
    except (URLError, TimeoutError, OSError):
        raise OpenJarvisUnavailable("OpenJarvis did not respond within the configured timeout.") from None
    if len(raw) > 200000:
        raise OpenJarvisUnavailable("OpenJarvis response is too large.")
    try:
        parsed = json.loads(raw.decode("utf-8"))
        entry = parsed["choices"][0]
        answer = entry["message"]["content"]
        if isinstance(answer, list):
            answer = "".join(x.get("text", "") for x in answer if isinstance(x, dict))
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("empty")
        return answer.strip()
    except (ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise OpenJarvisUnavailable("OpenJarvis returned no usable answer.") from None


def wants_agent(message: str, *, fast: bool) -> bool:
    """Avoid slow agent loops for 1-sentence voice replies."""
    if fast:
        return False
    return bool(__import__("re").search(
        r"\b(research|investigate|compare|step[- ]by[- ]step|detailed|detail|"
        r"ta[fph]seel|analy[sz]e|analysis|plan|strategy|summari[sz]e|"
        r"explain|samjhao|solve|reason|why|kyun)\b",
        message, __import__("re").I,
    ))

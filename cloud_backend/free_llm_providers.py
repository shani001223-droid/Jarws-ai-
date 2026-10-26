"""Optional providers from nejib1/Free-LLM: verified fixed HTTPS API hosts.

The upstream directory DOES NOT supply API keys. This adapter uses only keys
created by the user and placed in the Hoshi backend's secret environment.
No user-supplied model IDs/URLs, arbitrary HTTP destinations, paid upgrades,
or transparent credit purchases are permitted.
"""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OptionalProviderError(RuntimeError):
    """Sanitized error that never includes user prompts, tokens or provider bodies."""


# Fixed models, chosen for documented free tiers (availability can change).
# Mistral free mode and NVIDIA developer/prototyping mode require explicit opt-in.
_PROVIDER_CONFIG = {
    "zai": {
        "key": "ZAI_API_KEY",
        "url": "https://api.z.ai/api/paas/v4/chat/completions",
        "model": "glm-4.5-flash",
    },
    "mistral": {
        "key": "MISTRAL_API_KEY",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "model": "mistral-small-latest",
        "guard": "MISTRAL_FREE_MODE",
    },
    "nvidia": {
        "key": "NVIDIA_API_KEY",
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "model": "meta/llama-3.1-8b-instruct",
        "guard": "NVIDIA_PROTOTYPE_MODE",
    },
}


def available_free_providers() -> tuple[str, ...]:
    """Return *configured*, not guaranteed reachable/free, provider IDs."""
    usable = []
    for name, spec in _PROVIDER_CONFIG.items():
        if not os.getenv(spec["key"], "").strip():
            continue
        guard = spec.get("guard")
        if guard and os.getenv(guard, "").strip().lower() not in ("1", "true", "yes"):
            continue
        usable.append(name)
    return tuple(usable)


def ask_free_provider(name: str, message: str, instruction: str, *, timeout: float = 8.0) -> str:
    """One bounded no-redirect HTTPS request with a pinned catalog model."""
    if name not in available_free_providers():
        raise OptionalProviderError("Optional provider is not enabled.")
    spec = _PROVIDER_CONFIG[name]
    body = {
        "model": spec["model"],
        "messages": [
            {"role": "system", "content": instruction[:4800]},
            {"role": "user", "content": message[:6000]},
        ],
        "stream": False,
        "max_tokens": 1024,
        "temperature": 0.4,
    }
    req = Request(
        spec["url"],
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + os.environ[spec["key"]].strip(),
            "Content-Type": "application/json",
            "User-Agent": "HOSHI-Free-Provider-Bridge/1.0",
        },
        method="POST",
    )
    try:
        # HTTPRedirectHandler would otherwise forward requests to another host.
        from urllib.request import build_opener, HTTPRedirectHandler

        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, *_args, **_kwargs):
                return None

        with build_opener(NoRedirect()).open(req, timeout=max(1.0, min(float(timeout), 8.0))) as response:
            raw = response.read(128001)
    except HTTPError as exc:
        raise OptionalProviderError(name + " returned HTTP " + str(exc.code) + ".") from None
    except (URLError, TimeoutError, OSError):
        raise OptionalProviderError(name + " is unavailable or timed out.") from None

    if len(raw) > 128000:
        raise OptionalProviderError(name + " response exceeded size limit.")
    try:
        parsed = json.loads(raw.decode("utf-8"))
        choice = parsed["choices"][0]
        content = choice["message"]["content"]
        if isinstance(content, list):
            content = "".join(
                part["text"] for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
        if choice.get("finish_reason") == "length":
            raise OptionalProviderError(name + " response was truncated.")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty")
        return content.strip()
    except OptionalProviderError:
        raise
    except (ValueError, UnicodeError, IndexError, KeyError, TypeError, AttributeError):
        raise OptionalProviderError(name + " returned invalid response.") from None

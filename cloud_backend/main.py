"""JARVIS cloud API with server-side Gemini and Groq fallback."""
import json
import os
import time
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="JARVIS Cloud API", version="0.8.0")

origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "*").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Override these in Render Environment if you want to use different model IDs.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()

# Cache public market data briefly to reduce provider requests.
_MARKET_CACHE_SECONDS = 25
_market_cache = {"payload": None, "fetched_at": 0.0}


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    locale: Optional[str] = "en"


class AssistantResponse(BaseModel):
    reply: str
    mode: str = "gemini"


def _groq_reply(message: str, language_hint: str) -> str:
    """Ask Groq using its OpenAI-compatible chat completions API."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured in the running service.")

    body = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": language_hint},
            {"role": "user", "content": message},
        ],
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    req = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key,
            "User-Agent": "JARVIS-Cloud-Assistant/0.7.0 (+https://jarws-ai-1.onrender.com)",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        provider_message = ""
        raw_error = ""
        try:
            raw_error = exc.read().decode("utf-8", errors="replace").strip()
            error_data = json.loads(raw_error)
            error_value = error_data.get("error") if isinstance(error_data, dict) else None
            if isinstance(error_value, dict):
                provider_message = str(
                    error_value.get("message")
                    or error_value.get("error")
                    or error_value.get("type")
                    or ""
                ).strip()
            elif isinstance(error_value, str):
                provider_message = error_value.strip()
            elif isinstance(error_data, dict):
                provider_message = str(
                    error_data.get("message") or error_data.get("detail") or ""
                ).strip()
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            provider_message = ""

        detail = "Groq fallback failed with HTTP " + str(exc.code) + "."
        if exc.code == 401:
            detail = "Groq rejected the API key (HTTP 401). Create an active Groq API key and update GROQ_API_KEY in Render."
        elif exc.code == 403:
            detail = (
                "Groq denied this request (HTTP 403: permission/model access). "
                "Check that GROQ_API_KEY is active and that the Groq project can use model "
                + GROQ_MODEL + "."
            )
        elif exc.code == 429:
            detail = "Groq fallback rate limit or quota reached (HTTP 429)."
        if provider_message:
            detail += " Groq says: " + provider_message[:220]
        elif raw_error and exc.code in (401, 403):
            detail += " Provider response: " + " ".join(raw_error.split())[:160]
        raise RuntimeError(detail) from None
    except (URLError, TimeoutError):
        raise RuntimeError("Groq fallback could not connect or timed out.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise RuntimeError("Groq returned an invalid response.") from None

    choices = data.get("choices") or []
    reply = ""
    if choices:
        reply = str((choices[0].get("message") or {}).get("content") or "").strip()
    if not reply:
        raise RuntimeError("Groq did not return text.")
    return reply


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "jarvis-cloud-api",
        "version": app.version,
        "message": "JARVIS cloud API is running",
        "health": "/health",
        "assistant": "/api/assistant",
    }


@app.get("/health")
def health():
    gemini_configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
    groq_configured = bool(os.getenv("GROQ_API_KEY", "").strip())
    return {
        "ok": True,
        "service": "jarvis-cloud-api",
        "version": app.version,
        "gemini_api": "interactions" if gemini_configured else None,
        "market_data_source": "Coinbase Exchange (BTC-USD spot)",
        "ai_connected": gemini_configured or groq_configured,
        "gemini_configured": gemini_configured,
        "groq_configured": groq_configured,
        "primary_provider": "gemini" if gemini_configured else ("groq" if groq_configured else None),
        "fallback_provider": "groq" if gemini_configured and groq_configured else None,
        "gemini_model": GEMINI_MODEL,
        "groq_model": GROQ_MODEL if groq_configured else None,
    }



def _coinbase_market_json(endpoint: str) -> dict:
    url = "https://api.exchange.coinbase.com/products/BTC-USD/" + endpoint
    req = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "JARVIS-Cloud-Assistant/0.8.0 (+https://jarws-ai-1.onrender.com)",
        },
        method="GET",
    )
    try:
        with urlopen(req, timeout=12) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError("Coinbase market endpoint returned HTTP " + str(exc.code) + ".") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Coinbase market endpoint could not connect or timed out.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise RuntimeError("Coinbase returned invalid market data.") from None
    if not isinstance(payload, dict):
        raise RuntimeError("Coinbase returned an unexpected market data shape.")
    return payload


@app.get("/api/market/btc")
def btc_market():
    """Read-only BTC-USD spot snapshot; it never places trades."""
    now = time.monotonic()
    cached = _market_cache.get("payload")
    if cached and now - float(_market_cache.get("fetched_at", 0.0)) < _MARKET_CACHE_SECONDS:
        return dict(cached)

    try:
        ticker = _coinbase_market_json("ticker")
        stats = _coinbase_market_json("stats")
        price = float(ticker["price"])
        opened = float(stats["open"])
        high = float(stats["high"])
        low = float(stats["low"])
        volume = float(stats["volume"])
        bid = float(ticker.get("bid", price))
        ask = float(ticker.get("ask", price))
        values = (price, opened, high, low, volume, bid, ask)
        if opened <= 0 or price <= 0 or high <= 0 or low <= 0 or volume < 0:
            raise ValueError("Coinbase returned invalid market values.")
        if not all(value == value and abs(value) != float("inf") for value in values):
            raise ValueError("Coinbase returned non-finite market values.")
    except (RuntimeError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="BTC spot market data is temporarily unavailable. " + str(exc),
        ) from None

    payload = {
        "source": "Coinbase Exchange",
        "symbol": "BTC-USD",
        "market_type": "spot",
        "price_usd": price,
        "change_24h_pct": ((price - opened) / opened) * 100.0,
        "high_24h_usd": high,
        "low_24h_usd": low,
        "volume_24h_btc": volume,
        "bid_usd": bid,
        "ask_usd": ask,
        "last_trade_at": ticker.get("time"),
        "disclaimer": "Spot snapshot only; may differ from USDT perpetual prices. Not a trade signal.",
    }
    _market_cache["payload"] = payload
    _market_cache["fetched_at"] = now
    return dict(payload)


@app.post("/api/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest):
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    language_hint = (
        "Reply in the same language as the user's message. "
        "If the user writes Roman Urdu, reply in natural Roman Urdu. "
        "Be helpful, clear, and honest. Do not claim to control the user's device "
        "or perform actions unless an available tool actually did so."
    )

    # Gemini is primary. A temporary overload (503), rate limit (429), server
    # error, timeout, or malformed response triggers Groq when its key is set.
    if gemini_key:
        body = {
            "model": GEMINI_MODEL,
            "input": message,
            "system_instruction": language_hint,
            # Keep this stateless request from being stored as a conversation.
            "store": False,
        }
        req = Request(
            "https://generativelanguage.googleapis.com/v1beta/interactions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": gemini_key,
                "User-Agent": "JARVIS-Cloud-Assistant/0.7.0 (+https://jarws-ai-1.onrender.com)",
            },
            method="POST",
        )
        gemini_problem = "Gemini Interactions API did not return a usable response."
        should_fallback = False
        try:
            with urlopen(req, timeout=35) as response:
                data = json.loads(response.read().decode("utf-8"))
            steps = data.get("steps") or []
            reply = "\\n".join(
                str(block.get("text", ""))
                for step in steps
                if step.get("type") == "model_output"
                for block in (step.get("content") or [])
                if block.get("type") == "text" and block.get("text")
            ).strip()
            if not reply:
                reply = str(data.get("output_text") or "").strip()
            if reply:
                return AssistantResponse(reply=reply, mode="gemini")
            gemini_problem = "Gemini Interactions API returned no text (possibly blocked or empty output)."
            should_fallback = True
        except HTTPError as exc:
            try:
                error_data = json.loads(exc.read().decode("utf-8"))
                google_message = str(error_data.get("error", {}).get("message", "")).strip()
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                google_message = ""
            gemini_problem = "Gemini service returned HTTP " + str(exc.code) + "."
            if google_message:
                gemini_problem += " Google says: " + google_message[:220]
            # Try backup for temporary provider errors and configuration/model errors.
            should_fallback = exc.code in (400, 401, 403, 404, 408, 429, 500, 502, 503, 504)
        except (URLError, TimeoutError):
            gemini_problem = "Gemini connection failed or timed out."
            should_fallback = True
        except (json.JSONDecodeError, UnicodeDecodeError, IndexError, KeyError, TypeError):
            gemini_problem = "Gemini returned an invalid response."
            should_fallback = True

        if should_fallback and groq_key:
            try:
                return AssistantResponse(reply=_groq_reply(message, language_hint), mode="groq")
            except RuntimeError as groq_error:
                raise HTTPException(
                    status_code=502,
                    detail=gemini_problem + " Groq fallback also failed: " + str(groq_error),
                ) from None
        if should_fallback:
            raise HTTPException(
                status_code=503,
                detail=gemini_problem + " Groq fallback is unavailable because GROQ_API_KEY is missing from this running service. Attach the Environment Group to this service and redeploy.",
            ) from None
        raise HTTPException(status_code=502, detail=gemini_problem) from None

    # If Gemini is not configured, Groq can serve requests on its own.
    if groq_key:
        try:
            return AssistantResponse(reply=_groq_reply(message, language_hint), mode="groq")
        except RuntimeError as groq_error:
            raise HTTPException(status_code=502, detail=str(groq_error)) from None

    raise HTTPException(
        status_code=503,
        detail="No AI key is configured in the running service. Add GEMINI_API_KEY or GROQ_API_KEY to the Render Environment Group, attach it to this service, and redeploy.",
    )

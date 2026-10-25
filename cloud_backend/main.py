"""JARVIS cloud API with server-side Gemini and Groq fallback."""
import json
import os
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="JARVIS Cloud API", version="0.3.0")

origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "*").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


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
        raise RuntimeError("GROQ_API_KEY is not configured.")

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
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not expose credentials or provider request details to the client.
        try:
            error_data = json.loads(exc.read().decode("utf-8"))
            provider_message = str(error_data.get("error", {}).get("message", "")).strip()
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            provider_message = ""
        detail = "Groq fallback failed with HTTP " + str(exc.code) + "."
        if exc.code == 429:
            detail = "Groq fallback rate limit or quota reached."
        if provider_message:
            detail += " Groq says: " + provider_message[:220]
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
        "message": "JARVIS cloud API is running",
        "health": "/health",
        "assistant": "/api/assistant",
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "jarvis-cloud-api",
        "ai_connected": bool(
            os.getenv("GEMINI_API_KEY", "").strip()
            or os.getenv("GROQ_API_KEY", "").strip()
        ),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
    }


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

    # Gemini remains primary. If it is overloaded, rate-limited, or unavailable,
    # use Groq as a backup when GROQ_API_KEY is configured.
    if gemini_key:
        body = {
            "systemInstruction": {"parts": [{"text": language_hint}]},
            "contents": [{"role": "user", "parts": [{"text": message}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
        }
        req = Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={gemini_key}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=35) as response:
                data = json.loads(response.read().decode("utf-8"))
            parts = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [])
            )
            reply = "\\n".join(
                part.get("text", "") for part in parts if part.get("text")
            ).strip()
            if reply:
                return AssistantResponse(reply=reply, mode="gemini")
            gemini_problem = "Gemini did not return text."
            should_fallback = True
        except HTTPError as exc:
            try:
                error_data = json.loads(exc.read().decode("utf-8"))
                google_message = str(error_data.get("error", {}).get("message", "")).strip()
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                google_message = ""
            if exc.code in (503, 429, 500, 502, 504):
                gemini_problem = "Gemini service returned HTTP " + str(exc.code) + "."
                if google_message:
                    gemini_problem += " Google says: " + google_message[:220]
                should_fallback = True
            elif exc.code in (400, 401, 403, 404):
                detail = "Gemini rejected the request. Check GEMINI_API_KEY, API access, and GEMINI_MODEL."
                if google_message:
                    detail += " Google says: " + google_message[:300]
                # Configuration errors are not usually fixed by switching providers.
                if not groq_key:
                    raise HTTPException(status_code=502, detail=detail) from None
                gemini_problem = detail
                should_fallback = True
            else:
                gemini_problem = "Gemini service returned HTTP " + str(exc.code) + "."
                if google_message:
                    gemini_problem += " Google says: " + google_message[:220]
                should_fallback = False
        except (URLError, TimeoutError):
            gemini_problem = "Gemini connection timed out or failed."
            should_fallback = True
        except (json.JSONDecodeError, UnicodeDecodeError, IndexError, KeyError, TypeError):
            gemini_problem = "Gemini returned an invalid response."
            should_fallback = True

        if should_fallback and groq_key:
            try:
                return AssistantResponse(
                    reply=_groq_reply(message, language_hint),
                    mode="groq",
                )
            except RuntimeError as groq_error:
                raise HTTPException(
                    status_code=502,
                    detail=gemini_problem + " Groq fallback also failed: " + str(groq_error),
                ) from None
        if should_fallback:
            raise HTTPException(
                status_code=503,
                detail=gemini_problem + " Add GROQ_API_KEY in Render Environment to enable automatic fallback.",
            ) from None
        raise HTTPException(status_code=502, detail=gemini_problem) from None

    # If Gemini is not configured, Groq can still serve requests.
    if groq_key:
        try:
            return AssistantResponse(reply=_groq_reply(message, language_hint), mode="groq")
        except RuntimeError as groq_error:
            raise HTTPException(status_code=502, detail=str(groq_error)) from None

    raise HTTPException(
        status_code=503,
        detail="No AI key is configured. Add GEMINI_API_KEY or GROQ_API_KEY in Render Environment.",
    )

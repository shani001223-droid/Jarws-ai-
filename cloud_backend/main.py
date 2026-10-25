"""JARVIS cloud API with server-side Gemini integration."""
import json
import os
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="JARVIS Cloud API", version="0.2.0")

origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "*").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    locale: Optional[str] = "en"


class AssistantResponse(BaseModel):
    reply: str
    mode: str = "gemini"


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
        "ai_connected": bool(os.getenv("GEMINI_API_KEY", "").strip()),
    }


@app.post("/api/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="AI key is not configured. Add GEMINI_API_KEY in Render Environment.",
        )

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    language_hint = (
        "Reply in the same language as the user's message. "
        "If the user writes Roman Urdu, reply in natural Roman Urdu. "
        "Be helpful, clear, and honest. Do not claim to control the user's device "
        "or perform actions unless an available tool actually did so."
    )
    body = {
        "systemInstruction": {"parts": [{"text": language_hint}]},
        "contents": [{"role": "user", "parts": [{"text": message}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1024},
    }
    req = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=35) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Return a safe diagnostic from Google's response, never the request URL or API key.
        try:
            error_data = json.loads(exc.read().decode("utf-8"))
            google_message = str(error_data.get("error", {}).get("message", "")).strip()
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            google_message = ""
        if exc.code in (400, 401, 403, 404):
            detail = "Gemini rejected the request. Check that GEMINI_API_KEY is valid, the Generative Language API is enabled, and the model is available to this key."
            if google_message:
                detail += " Google says: " + google_message[:350]
            raise HTTPException(status_code=502, detail=detail) from None
        if exc.code == 429:
            detail = "Gemini rate limit or quota reached. Check Google AI Studio usage and try again later."
            if google_message:
                detail += " Google says: " + google_message[:250]
            raise HTTPException(status_code=429, detail=detail) from None
        detail = "Gemini service returned HTTP " + str(exc.code) + "."
        if google_message:
            detail += " Google says: " + google_message[:250]
        raise HTTPException(status_code=502, detail=detail) from None
    except (URLError, TimeoutError):
        raise HTTPException(
            status_code=504,
            detail="Gemini did not respond before the server timeout. This is an AI-provider timeout, not necessarily your internet connection. Try again; if repeated, check Google AI Studio quota/service status.",
        ) from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=502, detail="Gemini returned an invalid response.") from None

    parts = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [])
    )
    reply = "\n".join(part.get("text", "") for part in parts if part.get("text"))
    if not reply:
        raise HTTPException(
            status_code=502,
            detail="Gemini did not return text. Please try a different message.",
        )
    return AssistantResponse(reply=reply, mode="gemini")

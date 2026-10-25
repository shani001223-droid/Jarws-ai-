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
        # Do not return the request URL or API key to the client.
        if exc.code in (400, 401, 403):
            raise HTTPException(
                status_code=502,
                detail="Gemini rejected the request. Check the API key, API access, and model configuration in Google AI Studio.",
            ) from None
        if exc.code == 429:
            raise HTTPException(
                status_code=429,
                detail="Gemini rate limit reached. Please wait and try again.",
            ) from None
        raise HTTPException(status_code=502, detail="Gemini service returned an error.") from None
    except (URLError, TimeoutError):
        raise HTTPException(
            status_code=504,
            detail="Could not reach Gemini in time. Please try again.",
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

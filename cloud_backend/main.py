"""JARVIS cloud backend starter. No secrets or paid AI provider required yet."""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="JARVIS Cloud API", version="0.1.0")

# Set ALLOWED_ORIGINS to your deployed HTTPS dashboard origin before production.
# Example: https://yourname.github.io
origins = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

class AssistantRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    locale: Optional[str] = "en"

class AssistantResponse(BaseModel):
    reply: str
    mode: str = "starter"

@app.get("/health")
def health():
    return {"ok": True, "service": "jarvis-cloud-api", "ai_connected": False}

@app.post("/api/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest):
    # Safe placeholder: no external actions and no paid API are enabled.
    # Next milestone: connect a provider via server-side environment secrets.
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    return AssistantResponse(
        reply=("JARVIS cloud API is online, but the AI model is not connected yet. "
               "Your message reached the cloud backend. Next we will connect a free-tier AI provider after reviewing its limits."),
        mode="starter",
    )

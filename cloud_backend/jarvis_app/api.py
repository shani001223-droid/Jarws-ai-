"""FastAPI application with stable routes for the existing dashboard and Android app."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__
from .config import get_settings
from .schemas import AssistantRequest, AssistantResponse
from .service import answer_message
app = FastAPI(title="JARVIS Cloud API", version=__version__, description="Mobile-first personal assistant API")
app.add_middleware(CORSMiddleware, allow_origins=list(get_settings().allowed_origins), allow_credentials=False,
                   allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type", "Authorization"])

@app.get("/")
def root():
    return {"ok": True, "service": "jarvis-cloud-api", "version": app.version, "message": "JARVIS cloud API is running", "health": "/health", "assistant": "/api/assistant"}

@app.get("/health")
def health():
    current = get_settings()
    return {"ok": True, "service": "jarvis-cloud-api", "version": app.version, "conversation_memory": "sqlite",
            "memory_retention_days": current.memory_retention_days, "gemini_api": "interactions" if current.gemini_api_key else None,
            "ai_connected": bool(current.gemini_api_key or current.groq_api_key), "gemini_configured": bool(current.gemini_api_key),
            "groq_configured": bool(current.groq_api_key), "primary_provider": "gemini" if current.gemini_api_key else ("groq" if current.groq_api_key else None),
            "fallback_provider": "groq" if current.gemini_api_key and current.groq_api_key else None, "gemini_model": current.gemini_model,
            "groq_model": current.groq_model if current.groq_api_key else None}

@app.get("/api/capabilities")
def capabilities():
    return {"ok": True, "text_chat": True, "conversation_memory": True, "gemini_groq_fallback": True, "secrets_client_side": False,
            "phone_actions": "Only user-triggered Android allowlisted actions are supported by the mobile app."}

@app.post("/api/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest):
    reply, mode = answer_message(payload.message, payload.conversation_id)
    return AssistantResponse(reply=reply, mode=mode)

"""Assistant orchestration: bounded memory and primary/fallback providers."""
import logging, uuid
from typing import Optional, Tuple
from fastapi import HTTPException
from .config import get_settings
from .memory import get_recent_history, save_turn
from .providers import gemini_reply, groq_reply
logger = logging.getLogger("jarvis")

def canonical_conversation_id(raw_id: Optional[str]) -> Optional[str]:
    if not raw_id: return None
    try: return str(uuid.UUID(raw_id))
    except (ValueError, AttributeError, TypeError): raise HTTPException(status_code=400, detail="conversation_id must be a UUID.") from None

def _history(conversation_id: Optional[str]):
    if not conversation_id: return []
    try: return get_recent_history(conversation_id)
    except Exception as exc:
        logger.warning("Conversation memory read failed (%s).", type(exc).__name__); return []

def _save(conversation_id: Optional[str], message: str, reply: str) -> None:
    if not conversation_id: return
    try: save_turn(conversation_id, message, reply)
    except Exception as exc: logger.warning("Conversation memory write failed (%s).", type(exc).__name__)

def answer_message(message: str, raw_conversation_id: Optional[str] = None) -> Tuple[str, str]:
    text = message.strip()
    if not text: raise HTTPException(status_code=400, detail="Message cannot be empty.")
    settings = get_settings(); conversation_id = canonical_conversation_id(raw_conversation_id); history = _history(conversation_id); gemini_problem = ""
    if settings.gemini_api_key:
        try:
            reply = gemini_reply(text, history, settings); _save(conversation_id, text, reply); return reply, "gemini"
        except RuntimeError as exc:
            gemini_problem = str(exc); logger.info("Gemini provider failed; trying fallback (%s).", gemini_problem[:100])
        except Exception as exc:
            gemini_problem = "Gemini provider failed unexpectedly (" + type(exc).__name__ + ")."; logger.exception("Unexpected Gemini provider error.")
    if settings.groq_api_key:
        try:
            reply = groq_reply(text, history, settings); _save(conversation_id, text, reply); return reply, "groq"
        except RuntimeError as exc:
            detail = str(exc)
            if gemini_problem: raise HTTPException(status_code=502, detail=gemini_problem + " Groq fallback also failed: " + detail) from None
            raise HTTPException(status_code=502, detail=detail) from None
        except Exception:
            logger.exception("Unexpected Groq provider error."); raise HTTPException(status_code=502, detail="Groq provider failed unexpectedly.") from None
    if gemini_problem: raise HTTPException(status_code=503, detail=gemini_problem + " Add GROQ_API_KEY to the attached Render Environment Group to enable fallback.") from None
    raise HTTPException(status_code=503, detail="No AI key is configured. Add GEMINI_API_KEY or GROQ_API_KEY to the Render Environment Group, attach it to this service, and redeploy.")

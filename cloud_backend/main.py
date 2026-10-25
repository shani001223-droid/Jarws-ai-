"""Backward-compatible Render entrypoint: uvicorn main:app --app-dir cloud_backend."""
try:
    from .jarvis_app.api import app, assistant, capabilities, health, root
    from .jarvis_app.schemas import AssistantRequest, AssistantResponse
    from .jarvis_app.providers import gemini_input as _gemini_input, groq_reply as _groq_reply, trim_history as _trim_history
    from .jarvis_app.memory import get_recent_history, save_turn
    from .jarvis_app.config import get_settings
except ImportError:
    from jarvis_app.api import app, assistant, capabilities, health, root
    from jarvis_app.schemas import AssistantRequest, AssistantResponse
    from jarvis_app.providers import gemini_input as _gemini_input, groq_reply as _groq_reply, trim_history as _trim_history
    from jarvis_app.memory import get_recent_history, save_turn
    from jarvis_app.config import get_settings
GEMINI_MODEL = get_settings().gemini_model
GROQ_MODEL = get_settings().groq_model
__all__ = ["app", "root", "health", "assistant", "capabilities", "AssistantRequest", "AssistantResponse"]

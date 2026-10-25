"""Environment-backed settings. Secrets are read only on the server."""
from dataclasses import dataclass
import os

def _bounded_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try: value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError): value = default
    return max(minimum, min(maximum, value))

def _bounded_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try: value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError): value = default
    return max(minimum, min(maximum, value))

@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    groq_api_key: str
    gemini_model: str
    groq_model: str
    gemini_timeout: float
    groq_timeout: float
    memory_retention_days: int
    allowed_origins: tuple[str, ...]
    db_path: str

def get_settings() -> Settings:
    origins = tuple(item.strip() for item in os.getenv("ALLOWED_ORIGINS", "https://jarws-ai-1.onrender.com").split(",") if item.strip())
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip() or "openai/gpt-oss-20b",
        gemini_timeout=_bounded_float("GEMINI_TIMEOUT_SECONDS", 15.0, 3.0, 30.0),
        groq_timeout=_bounded_float("GROQ_TIMEOUT_SECONDS", 15.0, 3.0, 30.0),
        memory_retention_days=_bounded_int("JARVIS_MEMORY_RETENTION_DAYS", 30, 1, 365),
        allowed_origins=origins,
        db_path=os.path.abspath(os.getenv("JARVIS_DB_PATH", "/tmp/jarvis_memory.sqlite3").strip() or "/tmp/jarvis_memory.sqlite3"),
    )

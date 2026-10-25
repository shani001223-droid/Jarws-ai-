# Zorion attachment analysis (safe static review)

The uploaded `ZORION-Setup-1.0.0.exe` identifies as a 32-bit Windows PE installer. Its readable metadata identifies **Inno Setup 6.7.0**. A large appended installer-data region contains packed payload; it is not exposed as normal source files by basic static string inspection.

The installer was not executed. A compatible extraction utility was unavailable and package downloads were unreachable, so the embedded application files could not be enumerated and Zorion's complete features cannot be reliably verified. The implementation preserves verified JARVIS contracts rather than inventing features; a source ZIP or extracted project folder is needed for a definitive feature-by-feature port.

## Preserved contracts
- `GET /` service metadata, `GET /health` provider configuration, and `POST /api/assistant`.
- Request fields `message`, `locale`, optional UUID `conversation_id`; response fields `reply`, `mode`.
- Gemini Interactions API primary with Groq chat-completions fallback.
- Bounded SQLite memory: up to 12 prompt messages and 80 stored messages per conversation, with configurable retention.
- Server-only AI secrets and restrictive CORS default.
- Existing static dashboard and Android wrapper API contract remain compatible.

## New modules
- `config.py`: environment settings and limits.
- `schemas.py`: validated API models.
- `providers.py`: Gemini/Groq adapters and bounded context.
- `memory.py`: SQLite storage.
- `service.py`: fallback and orchestration.
- `api.py`: route definitions.
- `main.py`: compatible Render entry point.

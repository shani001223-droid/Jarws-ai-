# Hoshi Intelligence Upgrade — OpenJarvis integration

**Date:** 26 October 2026

This update **removes the previous Room Life extension completely**, including CSS/JS, room modes, fake gaming/reels/dance, menu, dance sound, in-app room suggestions and their tests. It deliberately **preserves the originally approved Hoshi background, outfit selector, voice, memory, phone controls, Trading and AI Influencer tabs**. The user can supply a replacement animation separately.

## Real OpenJarvis integration, not a fake label

The actual [OpenJarvis](https://github.com/open-jarvis/OpenJarvis) server exposes the standard `POST /v1/chat/completions` endpoint, with its agent (e.g. `orchestrator`), tools and memory configured **at the OpenJarvis server**. Hoshi's `cloud_backend/openjarvis_bridge.py` calls that real endpoint for complex non-voice tasks; it never simulates an OpenJarvis response. The adapter includes bounded 7-second timeout, response size caps, HTTPS-only external endpoints, redirect rejection and optional server-side Bearer auth.

Configure these **in the existing Hoshi backend Render environment, never in the browser or GitHub**:

| Setting | Example | Required? |
| --- | --- | --- |
| `OPENJARVIS_URL` | `https://your-private-openjarvis-server.example` | Yes, for remote OpenJarvis |
| `OPENJARVIS_MODEL` | `qwen3:4b` (must actually exist on that server) | Yes |
| `OPENJARVIS_API_KEY` | Private server auth token | Only if your OpenJarvis deployment enforces auth |

Set the OpenJarvis server separately with an actual engine/model, using the upstream guide. Choose its server agent setting, e.g. `[server] agent = "orchestrator"` and enable only safe read-only tools. OpenJarvis **does not become an AI model by itself**. No model, Ollama or OpenJarvis server has been provisioned by this code change. Hoshi `/health` exposes `openjarvis_configured`, *not an assertion of reachability*. External OpenJarvis servers might add expenses; no paid servers/models have been activated.

### Intelligent routing / speed

- **Simple one-shot spoken and short conversational typed queries:** first try configured Groq with short timeout (6 seconds), preserving existing OpenRouter/Gemini free fallback. Complex questions remain full-length responses.
- **Complex non-voice tasks:** use real OpenJarvis orchestrator first **when configured**. On timeout or failure, transparently fall back to existing AI providers without duplicate OpenJarvis calls.
- **Arithmetic:** validated bounded AST calculator handles simple expressions with **zero AI API calls**. No Python `eval`, filesystem, private-screen surveillance or account actions.
- **Model limits:** Groq full 12 seconds, OpenRouter 12 seconds and Gemini 12 seconds per attempt. Total latency still depends on Render cold starts, internet, prompt length, AI quota and actual provider failures; a 0.1-second AI response is not promised. Backend errors stay visible.
- **Memory and device actions:** Existing local privacy-filtered conversation memory, optional native phone controls, Urdu script TTS, public trading data and other features remain unchanged. Remote OpenJarvis tool/memory access only exists if a server is configured appropriately.

### Why not blindly `pip install openjarvis` into Render?

The full upstream framework is local-first and may need Rust extensions, Ollama/model weights and computer-grade resources. It is **not a direct Android Realme Note 50 APK dependency** or free instant-speed substitute. Connecting to the supported upstream OpenAI-compatible API keeps Hoshi lightweight. The Apache-2.0 upstream license remains applicable if any upstream source is later copied; this adapter is original integration code.

## Tests / acceptance

- Python backend unit tests and OpenJarvis HTTP contract mocks
- Browser Playwright UI tests without room controls, with five tabs and native voice preserved
- App source syntax and service worker new cache version
- Full live Render / APK operation **must be verified separately**. This PR never proves OpenJarvis runtime was activated; that requires a separately functioning endpoint/model and configuration.

Sources: https://open-jarvis.github.io/OpenJarvis/deployment/api-server/ and https://open-jarvis.github.io/OpenJarvis/getting-started/installation/

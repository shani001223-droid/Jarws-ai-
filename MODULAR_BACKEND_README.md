# JARVIS v1.0 modular backend & dashboard upgrade

This overlay modernizes the verified JARVIS path without switching to Streamlit, which would break the Android WebView and the existing static-site deployment. The responsive dashboard remains HTML/CSS/JavaScript; FastAPI provides the hosted API.

## Local run
```bash
cd cloud_backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Set `GEMINI_API_KEY` and/or `GROQ_API_KEY` in server environment only. Keep the existing Render Environment Group and current service; don't create a duplicate API service just because `render.yaml` is included as a reference. Free Render filesystem storage is ephemeral, so SQLite memory is best-effort across restarts.

Run tests from repository root: `python -m unittest discover -s tests -v`. See `docs/ATTACHMENT_ANALYSIS.md` for the limits of the uploaded installer review.

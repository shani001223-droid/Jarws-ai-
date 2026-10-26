FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Render sets the service root to cloud_backend/, so Docker's build context
# contains the sibling modules that main.py imports. Copy ALL Python modules:
# copying only main.py makes a seemingly successful build crash at startup
# with ModuleNotFoundError: No module named 'ad_studio'.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py ./

# An explicit container health probe checks the actual loaded FastAPI app,
# not just that the image built. No secrets or external providers required.
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]

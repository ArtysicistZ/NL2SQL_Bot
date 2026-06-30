# Backend: FastAPI + Google ADK agent pipeline (API-only; Next.js serves the UI).
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOST=0.0.0.0 \
    PORT=8080

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY nl2sql ./nl2sql

EXPOSE 8080

# Liveness via the DB-free /health endpoint.
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health').status==200 else 1)"

CMD ["python", "-m", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8080"]

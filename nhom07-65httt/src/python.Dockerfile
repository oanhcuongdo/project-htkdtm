# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH=/opt/venv/bin:$PATH
WORKDIR /app
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin appuser

FROM base AS api-deps
COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

FROM base AS api
COPY --from=api-deps /opt/venv /opt/venv
COPY --chown=appuser:appuser backend/app ./app
COPY --chown=appuser:appuser backend/alembic ./alembic
COPY --chown=appuser:appuser backend/alembic.ini ./alembic.ini
RUN mkdir -p /app/data/storage && chown -R appuser:appuser /app/data
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

FROM base AS ai-deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY ai/requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

FROM base AS ai
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
COPY --from=ai-deps /opt/venv /opt/venv
COPY --chown=appuser:appuser ai/main.py ./main.py
COPY --chown=appuser:appuser ai/src ./src
USER appuser
EXPOSE 8001
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]

FROM base AS worker-deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY worker/requirements.txt /tmp/requirements.txt
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

FROM base AS worker
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 libgomp1 ffmpeg tesseract-ocr && rm -rf /var/lib/apt/lists/*
COPY --from=worker-deps /opt/venv /opt/venv
COPY --chown=appuser:appuser worker/celery_app.py ./celery_app.py
COPY --chown=appuser:appuser worker/src ./src
USER appuser
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]

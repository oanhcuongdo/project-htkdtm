# Ảnh chạy migration Alembic cho PostgreSQL của EduVision BI (nhóm 03).
# Chạy một lần rồi thoát: alembic upgrade head.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /db

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY alembic.ini .
COPY migrations ./migrations
COPY schema ./schema

RUN useradd --create-home --uid 10001 appuser && chown -R appuser /db
USER appuser

CMD ["alembic", "upgrade", "head"]

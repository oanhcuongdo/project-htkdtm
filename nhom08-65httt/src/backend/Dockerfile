FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY backend/requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY frontend/ /frontend/

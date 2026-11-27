FROM python:3.11-slim

WORKDIR /app

COPY src/backend/requirements.txt src/backend/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/backend/ .
COPY src/database/ /data/
ENV DATA_DIR=/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

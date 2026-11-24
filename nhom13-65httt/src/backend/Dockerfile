FROM python:3.10-slim

WORKDIR /app

# Cài đặt thư viện hệ thống cho psycopg2, PDF và Tesseract OCR tiếng Việt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    tesseract-ocr \
    tesseract-ocr-vie \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

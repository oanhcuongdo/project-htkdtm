# Ảnh Docker cho etl-runner: bọc run_pipeline.py (T8a) sau một điểm cuối HTTP để n8n gọi.
# Build context phải là thư mục nhom03-65httt (xem docker-compose.yml); các tệp bị bỏ qua nằm trong Dockerfile.dockerignore.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Cấu trúc thư mục phản chiếu kho Git: collector của nhóm tính gốc kho bằng Path(__file__).parents[4] và tìm
# <gốc>/nhom03-65httt/config/platforms.yml, nên mã phải nằm dưới một thư mục tên nhom03-65httt.
WORKDIR /repo/nhom03-65httt

COPY src/etl/runner/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Mã ETL và cấu hình nền tảng. Thư mục data (đánh giá thật, nhật ký) được gắn vào lúc chạy, không đóng gói vào ảnh.
COPY src/etl ./src/etl
COPY config ./config

# Chạy bằng người dùng thường, không dùng root. data/ do Compose gắn vào và cho phép ghi.
RUN useradd --create-home --uid 10001 appuser && mkdir -p data && chown -R appuser /repo
USER appuser

EXPOSE 8099
HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=10s \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8099/health', timeout=3)"]
CMD ["python", "src/etl/runner/runner.py"]

#!/bin/sh
# Khởi tạo và chạy Superset. Chạy lại an toàn (mỗi lần container khởi động).
set -eu

: "${SUPERSET_SECRET_KEY:?Thiếu SUPERSET_SECRET_KEY trong .env}"
: "${SUPERSET_ADMIN_PASSWORD:?Thiếu SUPERSET_ADMIN_PASSWORD trong .env}"
: "${SUPERSET_DB_PASSWORD:?Thiếu SUPERSET_DB_PASSWORD trong .env}"
: "${SUPERSET_GUEST_TOKEN_SECRET:?Thiếu SUPERSET_GUEST_TOKEN_SECRET trong .env}"

echo "[superset] nâng cấp metadata..."
superset db upgrade

echo "[superset] tạo tài khoản quản trị (bỏ qua nếu đã có)..."
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER:-admin}" \
  --firstname Admin --lastname EduVision \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@example.com}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" || echo "[superset] tài khoản quản trị đã tồn tại"

echo "[superset] khởi tạo vai trò và quyền..."
superset init

echo "[superset] kết nối schema dw bằng tài khoản chỉ đọc..."
python /app/register_dw.py

echo "[superset] chạy máy chủ ở cổng 8088"
exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 2 --worker-class gthread --threads 4 \
  --timeout 120 --limit-request-line 0 --limit-request-field_size 0 \
  "superset.app:create_app()"

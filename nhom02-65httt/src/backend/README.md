# Backend API — ERP Smart Pricing (FastAPI)

Dịch vụ backend lõi sử dụng FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 15, Celery & Redis.

## 1. Chạy cục bộ (Local Development)

Yêu cầu Python >= 3.12 (tương thích Python 3.13).

```powershell
cd nhom02-65httt\src\backend
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
```

Chạy kiểm thử tự động và kiểm tra lint (không cần PostgreSQL nhờ SQLite in-memory):

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .
```

Khi kết nối tới PostgreSQL cục bộ hoặc container:

```powershell
# Đảm bảo đã có biến môi trường DATABASE_URL, JWT_SECRET_KEY, SEED_DEFAULT_PASSWORD
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m app.scripts.seed_users
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tài liệu Swagger UI: `http://localhost:8000/docs`.

## 2. Chạy qua Docker Compose

Tại thư mục `nhom02-65httt/`:

```bash
cp .env.example .env
docker compose up -d --build postgres redis backend celery_worker celery_beat
docker compose exec backend python -m app.scripts.seed_users
```

## 3. Quy ước API (Contract với Frontend)

Mọi endpoint dưới prefix `/api/v1` tuân thủ thống nhất:

- **Envelope thành công:**
  ```json
  { "data": { ... }, "meta": null }
  ```
  Với danh sách phân trang, `meta` có dạng `{"page": 1, "pageSize": 20, "total": 42, "totalPages": 3}` (tham số query: `page`, `pageSize` tối đa 100).
- **Envelope lỗi:**
  ```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Thông báo tiếng Việt ngắn gọn",
      "details": [{ "field": "email", "message": "..." }]
    }
  }
  ```
  Các mã lỗi chuẩn: `UNAUTHORIZED` (401), `FORBIDDEN` (403), `NOT_FOUND` (404), `CONFLICT` (409), `VALIDATION_ERROR` (422), `RATE_LIMITED` (429), `PROVIDER_UNAVAILABLE` (503), `INTERNAL_ERROR` (500).
- **Định dạng dữ liệu:**
  - Key JSON dùng `camelCase` bằng cách kế thừa `ApiModel` (`app/schemas/common.py`).
  - Không ẩn trường có giá trị `null` (ví dụ `lastLoginAt: null` luôn được giữ nguyên).
  - Các trường tiền tệ sử dụng `NUMERIC(15, 2)` ở DB và xuất dạng **decimal string** trong JSON để tránh sai số dấu phẩy động.
- **Phân quyền RBAC:** Dùng `Depends(require_permission(Permission.<KEY>))` hoặc `require_any_permission(...)` từ `app/api/deps.py`. Giữ đồng bộ `Role` và `Permission` trong `app/core/rbac.py` với `frontend/src/lib/rbac.ts`.

## 4. Mở rộng module cho thành viên

- **Thêm Model & Migration (Trung):**
  1. Tạo model mới kế thừa `Base` (`app/db/base.py`) trong `app/models/`.
  2. Import model đó vào `app/models/__init__.py`.
  3. Tạo migration mới trong `alembic/versions/` (`alembic revision --autogenerate -m "..."` hoặc viết tay), không sửa migration đã merge.
- **Thêm Router API:**
  1. Tạo file endpoint trong `app/api/v1/endpoints/` dùng `Envelope[...]`, `ApiModel`, và `require_permission(...)`.
  2. Đăng ký router vào `app/api/v1/router.py`.
- **Sử dụng Marketplace Adapter (Trường):**
  ```python
  from decimal import Decimal
  from app.integrations.marketplace import PriceUpdateRequest, get_adapter

  adapter = get_adapter("SHOPEE", mode="SIMULATED")
  result = adapter.update_price(
      PriceUpdateRequest(
          channel_code="SHOPEE",
          external_listing_id="1592328943",
          external_sku="M185-BLK",
          new_price=Decimal("199000.00"),
          previous_price=Decimal("219000.00"),
          idempotency_key="rec-123-attempt-1",
      )
  )
  ```
  Khi triển khai Seller Partner API thật cho một kênh, dùng `register_adapter(channel_code, "LIVE", factory)`.

## 5. Schema 18 bảng & Các API đã sẵn sàng

- **Schema & Migrations:** Toàn bộ 18 bảng (ERP lõi, kênh bán, dữ liệu đối thủ, Smart Pricing, phê duyệt, đồng bộ giá, ML runs, `audit_logs`) đã được khai báo trong `app/models/` (`erp.py`, `market.py`, `pricing.py`, `audit_log.py`, `user.py`), migration `alembic/versions/0002_erp_smart_pricing_schema.py` và file SQL tham chiếu tại [../database/schema.sql](../database/schema.sql).
- **Endpoints hiện có dưới `/api/v1`:**
  - `GET /health`
  - `POST /auth/login`, `GET /auth/me`
  - `GET /users`, `POST /users`, `PATCH /users/{user_id}`
  - `GET /audit-logs` (`AUDIT_READ`)
  - `GET /channels`, `GET /channel-fees`, `POST /channels/{channel_id}/test-connection`
  - `GET /dashboard` (`BI_READ`)
  - `GET /executions`, `POST /executions`, `POST /executions/from-recommendation/{recommendation_id}`, `POST /executions/{execution_id}/retry`, `POST /executions/{execution_id}/cancel`
- **Celery task:** `app.worker.tasks.execute_price_sync_task(execution_id)` thực thi tác vụ `QUEUED` qua `MarketplaceAdapter`.
- **Crawler đa nền tảng (`app/crawler/`):** Khung Mode A/B/C và dữ liệu mẫu kiểm chứng đã tích hợp sẵn; xem [app/crawler/README.md](app/crawler/README.md) và `requirements-crawler.txt`.

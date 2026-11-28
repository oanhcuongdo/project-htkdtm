# Thiết Kế Tổng Thể Hệ Thống

```text
Trình duyệt ──HTTP / SSE──> Next.js Web (3000) ──HTTP──> Backend API (8000)
                                                            ├──HTTP + X-Internal-API-Key──> AI Service (8001)
                                                            ├──Hàng đợi Redis─────────────> Celery Worker
                                                            ├──PostgreSQL 14
                                                            └──MinIO
AI Service ──> Qdrant và Redis
Worker ──────> PostgreSQL 14, MinIO, Qdrant và AI Service
```

Bốn thư mục ứng dụng bên trong `src/` là các ranh giới triển khai độc lập: `frontend/` (Next.js 16), `backend/` (FastAPI), `ai/` (FastAPI + luồng RAG đa bước bằng `asyncio`) và `worker/` (Celery). Mỗi service Python có file `requirements.txt` riêng; `frontend/` là ứng dụng Next.js standalone dùng npm. Giao tiếp liên dịch vụ thực hiện qua HTTP/SSE và hàng đợi Redis nên không cần gói mã nguồn dùng chung giữa các service.

File `src/compose.yaml` duy nhất khởi chạy toàn bộ 4 service ứng dụng cùng 4 dịch vụ hạ tầng (`db`, `redis`, `qdrant`, `minio`), đồng thời gắn các cổng hạ tầng về `127.0.0.1` để hỗ trợ chạy phát triển cục bộ khi cần. Image Docker được định nghĩa gọn tại `src/python.Dockerfile` (đa mục tiêu cho `api`, `ai`, `worker`) và `src/frontend/Dockerfile` (server Next.js standalone). Server Next.js tự proxy `/api/:path*` sang `INTERNAL_API_URL` (`http://api:8000` trong Docker hoặc `http://localhost:8000` ở máy local).

Thay đổi lược đồ cơ sở dữ liệu được chạy tường minh qua Alembic (`docker compose --profile tools run --rm migrate`). PostgreSQL, Redis, Qdrant và MinIO sử dụng named volumes để bảo toàn dữ liệu.

---

## Xem Thêm

- [Quy trình AI Workflow & RAG](./ai-agent-workflow.md)
- [Giao tiếp liên dịch vụ & Hợp đồng API](./service-communication.md)
- [Lược đồ cơ sở dữ liệu](./database-schema.md)
- [Lưu trữ, bộ nhớ đệm & bền vững dữ liệu](./storage-and-cache.md)
- [Hướng dẫn tổng quan (README)](../../README.md)

# EduVision BI - Nhóm 03 (65HTTT)

Hệ thống phân tích trải nghiệm người học và cạnh tranh giữa các nền tảng E-learning.

## Cấu trúc mã nguồn

- `src/database/`: star schema, dữ liệu mẫu, migration (PostgreSQL)
- `src/etl/`: collector, transform, load, nhật ký chất lượng, workflow n8n
- `src/ml/`: gán nhãn, mô hình cảm xúc (M1), ABSA (M2), dự báo (M3), phát hiện bất thường
- `src/backend/`: API FastAPI
- `src/frontend/`: website React + TypeScript
- `src/bi/superset/`: dashboard Superset
- `config/platforms.yml`: danh sách nền tảng (thêm nền tảng = thêm một khối cấu hình)
- `data/` (`raw/`, `clean/`): dữ liệu trên máy từng thành viên, **không commit** (repo công khai)
- `models/`: trọng số mô hình, **không commit**; cách tải ở `models/README.md`
- `docs/`: tài liệu, gồm [dao_duc_phap_ly.md](docs/dao_duc_phap_ly.md) (điều khoản Google Play, App Store, YouTube)
- `docker-compose.yml`, `.env.example`: chạy PostgreSQL, migration Alembic và API FastAPI bằng Docker (Superset, n8n sẽ bổ sung sau)

## Quy tắc với repo công khai

- Không commit CSV thô/đã làm sạch, trọng số mô hình, khóa API hay file `.env` (đã có `.gitignore` của nhóm).
- Dữ liệu và trọng số chia sẻ qua kênh riêng của nhóm; xem `data/README.md` và `models/README.md`.

## Cài đặt và chạy

### Chạy PostgreSQL, migration và API bằng Docker

Yêu cầu: Docker Desktop đang chạy. Thực hiện trong thư mục `nhom03-65httt/`:

```bash
cp .env.example .env          # rồi mở .env, điền POSTGRES_PASSWORD (không commit .env)
docker compose up -d --build
docker compose ps             # postgres và api ở trạng thái healthy; migrate đã thoát (Exited 0) là đúng
```

- Tài liệu API (Swagger): http://localhost:8000/docs
- Kiểm tra API: http://localhost:8000/health
- Kiểm tra CSDL và các schema raw/clean/dw: http://localhost:8000/health/db
- Danh sách nền tảng đọc từ `config/platforms.yml`: http://localhost:8000/api/v1/platforms
- Các điểm cuối AI (`/api/v1/predict/*`, `/api/v1/forecast/*`, `/api/v1/chat`) hiện là **khung, trả 501** cho tới khi mô hình được tích hợp.
- Dịch vụ `migrate` chạy Alembic (`alembic upgrade head`) trước khi API khởi động; bản migration đã áp dụng được bỏ qua nên chạy lại an toàn. `/health/db` hiển thị `migration_version` hiện tại.
- Xem phiên bản: `docker compose run --rm migrate alembic current`. Cách thêm migration: [src/database/migrations/README.md](src/database/migrations/README.md).
- Muốn làm lại CSDL từ đầu: `docker compose down -v` rồi `docker compose up -d --build` (xóa cả dữ liệu).
- Cổng bị chiếm (5432, 8000)? Đổi `POSTGRES_PORT`, `API_PORT` trong `.env`.
- Dừng: `docker compose down`.

### Chạy kiểm thử API (không cần Docker)

```bash
cd src/backend
python -m venv .venv && .venv/Scripts/activate     # Windows; Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
```

Website React chạy riêng, xem `src/frontend/README.md`.

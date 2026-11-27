# Nhóm 02 - 65HTTT

Đề tài: **Hệ thống ERP Smart Pricing đa kênh tích hợp AI & BI**
(Multi-channel Intelligent ERP & Dynamic Pricing System)

Thư mục mã nguồn, tài liệu và báo cáo của nhóm `nhom02-65httt`.

## Cấu trúc

- `danhsachnhom.md`: thông tin thành viên và phân công.
- `docs/`: đề cương, tài liệu và báo cáo đồ án.
- `src/`: mã nguồn dự án (`backend/`, `frontend/`, `database/`).

## Công nghệ dự kiến

React + Vite + Tailwind, FastAPI, PostgreSQL, Redis, Celery, Scikit-learn/XGBoost, Apache Superset, Docker Compose.

Hướng dẫn cài đặt và khởi chạy sẽ được bổ sung cùng mã nguồn của nhóm.

## Mục tiêu và phạm vi dự án

- Quản lý danh mục, sản phẩm, nhà cung cấp, tồn kho và kênh bán.
- Thu thập và chuẩn hóa dữ liệu giá lịch sử từ đa nguồn.
- Đề xuất giá bán dựa trên giá vốn, tồn kho, nhu cầu và quy tắc giá sàn.
- Kết nối chợ thương mại điện tử thông qua các adapter có thể mở rộng.
- Trình bày KPI, doanh thu và xu hướng giá trên dashboard BI.
- Hỗ trợ quy trình phê duyệt đề xuất giá trước khi áp dụng ra kênh bán.

## Quy trình xử lý smart pricing

1. ERP thu thập dữ liệu sản phẩm, tồn kho, giá vốn và lịch sử bán hàng.
2. Crawler/API đồng bộ dữ liệu giá tham chiếu từ các nguồn ngoài.
3. Dữ liệu được chuẩn hóa và khớp theo mã SKU.
4. Rule Engine tính giá sàn Pmin theo chính sách kinh doanh.
5. Mô hình dự báo nhu cầu và mô hình XGBoost hỗ trợ đề xuất giá.
6. Người dùng xem đề xuất, điều chỉnh nếu cần và gửi phê duyệt.
7. Giá đã duyệt được áp dụng vào kênh bán và theo dõi lại qua Superset.

## Khởi chạy nhanh hạ tầng & Backend

```bash
cp .env.example .env
docker compose up -d --build postgres redis backend celery_worker celery_beat
docker compose exec backend python -m app.scripts.seed_users
```

- Quy trình nhánh, PR và phân vùng thư mục: xem [CONTRIBUTING.md](CONTRIBUTING.md).
- Hướng dẫn chạy local, test và quy ước API: xem [src/backend/README.md](src/backend/README.md).

# Danh Sách Nhóm Và Phân Công Nhiệm Vụ

## 1. Thông Tin Chung

- **Tên nhóm:** nhom02-65httt
- **Tên lớp học phần:** Hệ thống kinh doanh thông minh
- **Tên đề tài:** Hệ thống ERP Smart Pricing đa kênh tích hợp AI & BI
- **Giảng viên hướng dẫn:** TS. Đỗ Oanh Cường

---

## 2. Danh Sách Thành Viên

| STT | Họ và Tên | Mã Sinh Viên | Lớp Sinh Hoạt | Vai Trò | Nhiệm Vụ Phân Công | Tỷ Lệ Đóng Góp (%) | Email |
| :-: | :--- | :-: | :-: | :--- | :--- | :-: | :--- |
| 1 | Nguyễn Anh Minh | 2351160537 | 65HTTT | Nhóm trưởng / Backend Core & Integration Lead | Thiết kế kiến trúc tổng thể, cấu hình Docker Compose 7 dịch vụ, xây dựng FastAPI lõi, xác thực JWT và phân quyền RBAC, Schema 18 bảng ORM & Alembic, Marketplace Adapter/Simulator, API users/channels/executions/audit-logs/dashboard, nối luồng Approve sang Celery sync, đưa bộ Crawler nền vào dự án, điều phối review/merge PR và tích hợp cuối kỳ | [Điền tỷ lệ] | 2351160537@e.tlu.edu.vn |
| 2 | Lê Minh Tú | 2351160562 | 65HTTT | AI / ML & Smart Pricing Backend Engineer | Tiền xử lý dữ liệu ERP và lịch sử giá, cài đặt công thức giá sàn Pmin, Rule Engine (4 chốt chặn & Explainability), huấn luyện và đánh giá Linear Regression vs XGBoost (Time-based Split, MAE/RMSE, bảng model_runs), phát triển API Smart Pricing & Approval (pricing-rules, pricing/preview, pricing/run, recommendations, approve/reject) và viết unit/API test phân hệ AI Pricing | [Điền tỷ lệ] | 2351160562@e.tlu.edu.vn |
| 3 | Nghiêm Xuân Trường | 2351160561 | 65HTTT | Data Crawler, Scheduler & BI (Superset) Engineer | Kế thừa và chuẩn hóa 5-Adapter Crawler từ app/crawler/, thuật toán khớp nối SKU (RapidFuzz + cảnh báo sale ảo), phát triển API Competitor & Crawler (competitors, competitor-prices, /crawler/run, /crawler/ingest-cdp, duyệt NEEDS_REVIEW), cấu hình lịch chạy Celery Beat, dựng 3 Dashboard Apache Superset trên Star Schema views, đối chiếu số liệu BI và kiểm thử E2E | [Điền tỷ lệ] | 2351160561@e.tlu.edu.vn |
| 4 | Trần Đức Trung | 2251162191 | 64HTTT1 | Database Seed, ERP Backend & OLAP Views Developer | Kế thừa schema 18 bảng PostgreSQL, chuẩn hóa và viết script seed 60-100 SKU công nghệ, nhà cung cấp, giá vốn, tồn kho và lịch sử bán hàng (Kaggle), phát triển API CRUD ERP (categories, suppliers, products, cost_components, inventory, channel-listings), viết SQL Views Star Schema (src/database/views_bi.sql) cho Apache Superset và viết test phân hệ ERP | [Điền tỷ lệ] | 2251162191@e.tlu.edu.vn |
| 5 | Nguyễn Thị Yên | 2351160567 | 65HTTT | Frontend Lead | Sở hữu toàn bộ giao diện React + TypeScript + Tailwind CSS (src/frontend/) cho mọi phân hệ (ERP, Đối thủ, Đề xuất giá, Phê duyệt, Quy tắc, Thực thi, BI, Quản trị), tách lớp HTTP Client kết nối FastAPI thật thay cho mock API, xử lý lỗi theo API contract, hoàn thiện biểu mẫu nhập liệu và viết unit test Vitest lõi | [Điền tỷ lệ] | 2351160567@e.tlu.edu.vn |

---

## 3. Cấu Trúc Mã Nguồn Trong Thư Mục Nhóm

```text
nhom02-65httt/
├── danhsachnhom.md       # Tệp tin thông tin nhóm
├── README.md             # Hướng dẫn cài đặt và chạy mã nguồn của nhóm
├── docs/                 # Tài liệu phân tích, thiết kế, báo cáo đồ án
│   └── decuong_doan.docx # Đề cương bài tập lớn
└── src/                  # Mã nguồn của dự án
    ├── backend/
    ├── frontend/
    └── database/
```

---

## 4. Hướng Dẫn Cài Đặt Và Thực Thi Mã Nguồn

### 4.1. Môi trường yêu cầu

- Hệ điều hành: Windows 10/11, Ubuntu 22.04
- Nền tảng thực thi: Node.js >= 18.x, Python >= 3.10
- Cơ sở dữ liệu: PostgreSQL 15
- Dịch vụ phụ trợ: Redis, Celery, Apache Superset
- Triển khai: Docker Compose

### 4.2. Các bước cài đặt và khởi chạy

1. Bước 1: Tại `nhom02-65httt/`, sao chép `.env.example` thành `.env` và cấu hình tham số PostgreSQL, Redis, `JWT_SECRET_KEY`, `SEED_DEFAULT_PASSWORD`.
2. Bước 2: Khởi chạy hạ tầng và backend bằng Docker Compose:
   `docker compose up -d --build postgres redis backend celery_worker celery_beat`
3. Bước 3: Nạp dữ liệu khởi tạo tài khoản và kênh bán mặc định:
   `docker compose exec backend python -m app.scripts.seed_users`
4. Bước 4: Xem chi tiết quy trình phát triển và chạy local trong `CONTRIBUTING.md` và `src/backend/README.md`.

---

## 5. Tiến Độ Và Cột Mốc Hiện Tại

| Cột mốc | Nội dung | Trạng thái |
| :--- | :--- | :--- |
| Phân tích đề tài | Xác định phạm vi ERP, AI, BI và quy trình smart pricing | Hoàn thành |
| Thiết kế dữ liệu | Schema 18 bảng PostgreSQL và script seed SKU | Đang thực hiện |
| Mô hình nền | Cài đặt mô hình hồi quy tuyến tính baseline cho nhu cầu | Hoàn thành |
| Rule Engine | Xây dựng công thức Pmin và quy tắc phê duyệt | Đang thực hiện |
| Giao diện | Thiết kế màn hình quản lý ERP và đề xuất giá | Đang thực hiện |
| Tích hợp BI | Kết nối Apache Superset với dữ liệu PostgreSQL | Chờ thực hiện |

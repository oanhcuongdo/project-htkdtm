# 06. HƯỚNG DẪN THIẾT LẬP MÔI TRƯỜNG VÀ VẬN HÀNH HỆ THỐNG

## 1. Yêu Cầu Môi Trường (Prerequisites)

Để cài đặt và chạy thử nghiệm hệ thống, máy tính của thành viên cần cài đặt trước:
- **Hệ điều hành:** Windows 10/11 (khuyến nghị kích hoạt WSL2), macOS hoặc Ubuntu Linux.
- **Docker & Docker Compose:** Docker Desktop phiên bản 4.20+ (đảm bảo Docker Daemon đang chạy).
- **Git:** Phiên bản 2.30+.
- **Python:** Phiên bản 3.10 trở lên.

---

## 2. Quy Trình Đồng Bộ Mã Nguồn Git Trong Nhóm

Theo đúng quy chuẩn của học phần HTKDTM:
1. Mọi thành viên chỉ làm việc trên nhánh: `nhom13-65httt`.
2. Lệnh chuyển sang nhánh của nhóm:
   ```bash
   git checkout nhom13-65httt
   ```
3. Luôn kéo mã nguồn mới nhất về trước khi code:
   ```bash
   git pull origin nhom13-65httt
   ```
4. Sau khi hoàn thành tính năng, kiểm tra trạng thái và commit:
   ```bash
   git status
   git add src/
   git commit -m "feat(module): Nội dung cập nhật"
   git push origin nhom13-65httt
   ```

---

## 3. Cấu Hình Biến Môi Trường (.env)

Tạo file `.env` tại thư mục `nhom13-65httt/` dựa trên mẫu `.env.example`:

```bash
# === CẤU HÌNH DATABASE POSTGRESQL ===
POSTGRES_DB=personal_finance_dw
POSTGRES_USER=finance_user
POSTGRES_PASSWORD=SecurePassword123!
POSTGRES_HOST=postgres_db
POSTGRES_PORT=5432

# === CẤU HÌNH FASTAPI BACKEND ===
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
SECRET_KEY=supersecretkeyforfinanceapp2026

# === CẤU HÌNH APACHE SUPERSET ===
SUPERSET_SECRET_KEY=yoursecretkeysuperset_generate_random_key_here
SUPERSET_PORT=8088
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_PASSWORD=admin

# === CẤU HÌNH THU THẬP EMAIL & TELEGRAM BOT ===
IMAP_SERVER=imap.gmail.com
IMAP_EMAIL=your_email@gmail.com
IMAP_APP_PASSWORD=your_gmail_app_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_USER_ID=1
```

`TELEGRAM_CHAT_ID` là chat Telegram duy nhất được phép gửi ảnh; `TELEGRAM_USER_ID`
là `user_id` trong bảng `users` nhận giao dịch (mặc định tài khoản demo `1`).
Không để trống `TELEGRAM_CHAT_ID` khi bật bot. Tạo bot qua `@BotFather`, gửi
`/start` cho bot và lấy chat ID cá nhân bằng bot lấy thông tin chat của bạn.

---

## 4. Khởi Chạy Hệ Thống Bằng Docker Compose

Mở terminal tại thư mục `nhom13-65httt/` và thực hiện các lệnh sau:

### 4.1. Khởi động toàn bộ cụm container
```bash
docker-compose up -d
```
Hệ thống sẽ tự động tải image và dựng các container:
- `postgres_db`: Cơ sở dữ liệu và kho dữ liệu PostgreSQL (Port: `5432`).
- `fastapi_backend`: Dịch vụ thu thập ETL, mô hình AI và REST API (Port: `8000`).
- `apache_superset`: Nền tảng trực quan hóa BI (Port: `8088`).
- `redis_cache`: Bộ nhớ đệm hàng đợi tác vụ cho Superset và Scheduler (Port: `6379`).

### 4.2. Khởi tạo Cơ sở dữ liệu & Nạp Schema
Khi PostgreSQL khởi chạy lần đầu, chạy script tạo bảng và nạp dữ liệu mẫu:
```bash
# Nạp Schema Staging, Star Schema và Views
docker exec -i htkdtm_postgres psql -U finance_user -d personal_finance_dw < src/database/schemas/01_staging.sql
docker exec -i htkdtm_postgres psql -U finance_user -d personal_finance_dw < src/database/schemas/02_warehouse_star_schema.sql
docker exec -i htkdtm_postgres psql -U finance_user -d personal_finance_dw < src/database/schemas/03_dedup_and_logs.sql
docker exec -i htkdtm_postgres psql -U finance_user -d personal_finance_dw < src/database/schemas/05_multi_user_and_chat.sql
docker exec -i htkdtm_postgres psql -U finance_user -d personal_finance_dw < src/database/schemas/04_semantic_views.sql

# Sinh và nạp 500-1000 giao dịch giả lập phục vụ kiểm thử
python src/database/mock_data/generate_mock_data.py
```

> Cơ sở dữ liệu được tạo mới qua `docker-compose up` đã chạy `init_database.sql`
> và không cần nạp lại các schema trên. Với database đã tồn tại, chạy các lệnh
> schema để bổ sung chỉ mục staging duy nhất cho `telegram_file_id` và chỉ mục
> truy vấn khử trùng. Nếu PostgreSQL báo trùng `telegram_file_id`, hãy kiểm tra
> các dòng staging lặp trước khi tạo chỉ mục.

### 4.3. Chạy Telegram Bot nhận ảnh biên lai

1. Điền `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` và `TELEGRAM_USER_ID` trong
   `.env`. Chat ID được giới hạn trong bot; các chat khác sẽ bị bỏ qua.
2. Khởi chạy riêng bot cùng PostgreSQL và backend:
   ```bash
   docker-compose --profile telegram up -d --build postgres_db backend telegram_bot
   docker-compose logs -f telegram_bot
   ```
3. Gửi ảnh biên lai qua Telegram. Bot lưu OCR vào `stg_raw_receipts`, chuẩn hóa
   thời gian theo UTC+07:00, lưu chi tiêu VND dạng số âm, chạy ETL và xác nhận
   kết quả. Gửi lại cùng Telegram file ID sẽ không tạo bản ghi staging hoặc
   giao dịch mới; ảnh khác có cùng số tiền, nội dung và thời điểm ±10 phút sẽ
   được pipeline ghi nhận trong `log_dedup`.
4. Kiểm tra API staging/log ở `GET /api/v1/ingestion/logs` hoặc Swagger
   `http://localhost:8000/docs`. Có thể thử parser mà chưa cần Telegram bằng
   `POST /api/v1/ingestion/ingest-receipt-text` với JSON:
   ```json
   {
     "ocr_text": "HIGHLANDS COFFEE\n23/11/2026 09:15:00\nPhin Sua Da (L) 55,000\nTong tien: 55,000 VND",
     "chat_id": 12345
   }
   ```

Để dừng bot: `docker-compose stop telegram_bot`. Không chạy bot polling trong
tiến trình FastAPI; service bot riêng tránh chặn API và tránh khởi chạy nhiều
poller khi backend scale ngang.

### 4.4. Khởi tạo tài khoản Quản trị Apache Superset
```bash
# Tạo user admin cho Superset
docker exec -it superset_app superset fab create-admin \
              --username admin \
              --firstname Admin \
              --lastname User \
              --email admin@finance.local \
              --password admin

# Nâng cấp database nội bộ của Superset
docker exec -it superset_app superset db upgrade

# Khởi tạo roles và permissions mặc định
docker exec -it superset_app superset init
```

---

## 5. Truy Cập Các Giao Diện Dịch Vụ

Sau khi khởi chạy thành công, truy cập các cổng trên trình duyệt:

| Tên dịch vụ | Địa chỉ URL | Thông tin đăng nhập mặc định |
| :--- | :--- | :--- |
| **Apache Superset BI** | `http://localhost:8088` | Username: `admin` / Password: `admin` |
| **FastAPI Swagger Docs** | `http://localhost:8000/docs` | Không yêu cầu đăng nhập (Public Dev) |
| **Web Portal / Upload** | `http://localhost:8000/` | Giao diện tải file sao kê & xem log |
| **PostgreSQL Database** | `localhost:5432` | User: `finance_user` / Database: `personal_finance_dw` |

---

## 6. Hướng Dẫn Kết Nối Database & Import Dashboard Vào Superset

1. Đăng nhập vào Superset tại `http://localhost:8088`.
2. **Thêm kết nối Cơ sở dữ liệu (Database Connection):**
   - Vào menu: **Data** $\rightarrow$ **Databases** $\rightarrow$ **+ Database**.
   - Chọn kiểu: **PostgreSQL**.
   - Nhập chuỗi kết nối SQLAlchemy URI:
     ```text
     postgresql://finance_user:SecurePassword123!@postgres_db:5432/personal_finance_dw
     ```
   - Nhấn **Test Connection** (Báo thành công) $\rightarrow$ Nhấn **Connect**.
3. **Thêm các Virtual Datasets:**
   - Vào **Data** $\rightarrow$ **Datasets** $\rightarrow$ Chọn các SQL Views đã tạo (`vw_clean_transactions`, `vw_monthly_savings_rate`, `vw_spending_heatmap`,...).
4. **Nhập (Import) 3 Dashboard mẫu có sẵn:**
   - Vào menu: **Dashboards** $\rightarrow$ Biểu tượng dấu 3 chấm góc phải $\rightarrow$ Chọn **Import Dashboards**.
   - Chọn các file JSON cấu hình xuất sẵn tại: `src/frontend/superset/dashboards_export/`.

---

## 7. Kiểm Thử Hệ Thống (Testing & Acceptance Verification)

Thực hiện kiểm thử theo các tiêu chí nghiệm thu đề ra:
1. **Kiểm tra tỷ lệ bóc tách:** Tải mẫu sao kê 50 dòng $\rightarrow$ Chạy lệnh bóc tách $\rightarrow$ Kiểm tra bản ghi trong bảng `fact_transactions`.
2. **Kiểm tra khử trùng lặp:** Tải lại đúng file sao kê đó lần 2 $\rightarrow$ Xác nhận không có bản ghi mới nào bị trùng được chèn thêm vào `fact_transactions`, đồng thời kiểm tra bảng `log_dedup` ghi nhận đúng 50 dòng trùng.
3. **Kiểm tra độ trễ Superset:** Mở từng Dashboard trong số 3 Dashboard, áp dụng bộ lọc ngày tháng và danh mục $\rightarrow$ Đo thời gian render hoàn tất $\le 2$ giây.
4. **Kiểm tra API AI:** Gọi thử endpoint `POST /api/v1/ai/classify` với chuỗi `MBVCB.12345.Tien an trua cty` $\rightarrow$ Nhận kết quả JSON trả về danh mục `Ăn uống` với độ tin cậy $> 0.85$.

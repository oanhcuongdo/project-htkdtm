# 03. QUY ĐỊNH CẤU TRÚC THƯ MỤC VÀ TỔ CHỨC MÃ NGUỒN

## 1. Nguyên Tắc Tổ Chức Thư Mục

Theo đúng quy chuẩn của môn học và yêu cầu kỹ thuật của đề tài:
- Mọi tài nguyên của nhóm nằm trọn vẹn trong thư mục: `nhom13-65httt/`.
- Thư mục `docs/` lưu trữ toàn bộ tài liệu đặc tả, phân tích, thiết kế và kế hoạch.
- **Thư mục `src/` là nơi lưu trữ tập trung toàn bộ mã nguồn của dự án**, được phân thành 3 phân hệ chính:
  1. `src/database/`: Mã nguồn khởi tạo cơ sở dữ liệu, scripts tạo bảng Staging, Star Schema, views ngữ nghĩa và dữ liệu mẫu.
  2. `src/backend/`: Toàn bộ mã nguồn thu thập dữ liệu (Email, CSV/PDF, Telegram OCR), pipeline ETL, dịch vụ AI và RESTful API.
  3. `src/frontend/`: Cấu hình nền tảng trực quan hóa Apache Superset (Dashboards, Datasets, Semantic Layer) và giao diện hỗ trợ người dùng.

---

## 2. Sơ Đồ Cấu Trúc Toàn Bộ Dự Án

```text
nhom13-65httt/
├── danhsachnhom.md                       # Thông tin thành viên, phân công nhiệm vụ và cam kết đóng góp
├── README.md                             # Hướng dẫn tổng quan và hướng dẫn chạy nhanh hệ thống
├── docker-compose.yml                    # Cấu hình khởi chạy cụm dịch vụ (PostgreSQL, FastAPI, Superset, Redis)
├── .env.example                          # File mẫu định nghĩa các biến môi trường cấu hình bí mật
│
├── docs/                                 # THƯ MỤC TÀI LIỆU VÀ ĐẶC TẢ DỰ ÁN
│   ├── README.md                         # Mục lục và hướng dẫn tra cứu tài liệu
│   ├── 01_tong_quan_du_an.md             # Đặt vấn đề, 5 câu hỏi nghiệp vụ, đánh giá giải pháp, KPIs
│   ├── 02_kien_truc_he_thong.md          # Sơ đồ kiến trúc 5 tầng, luồng dữ liệu chi tiết
│   ├── 03_cau_truc_thu_muc.md            # Quy định tổ chức mã nguồn trong src/ và quy chuẩn code
│   ├── 04_thiet_ke_co_so_du_lieu.md      # Mô hình Star Schema, ERD, từ điển dữ liệu, quy tắc khử trùng
│   ├── 05_ke_hoach_trien_khai.md         # Kế hoạch chi tiết 8 tuần, ma trận RACI theo 5 thành viên
│   ├── 06_huong_dan_chuan_bi_va_van_hanh.md # Cài đặt môi trường, Docker, kết nối Superset, Git workflow
│   └── Đề cương Project Cuối kỳ (TH4) - Hệ thống Quản lý Tài chính Cá nhân Thông minh.docx
│
└── src/                                  # THƯ MỤC LƯU TRỮ TOÀN BỘ MÃ NGUỒN DỰ ÁN
    │
    ├── database/                         # 1. PHÂN HỆ CƠ SỞ DỮ LIỆU & DATA WAREHOUSE
    │   ├── README.md                     # Hướng dẫn chạy scripts khởi tạo DB
    │   ├── schemas/                      # Định nghĩa cấu trúc bảng SQL
    │   │   ├── 01_staging.sql            # Tạo các bảng tạm lưu dữ liệu thô (stg_emails, stg_statements,...)
    │   │   ├── 02_warehouse_star_schema.sql # Tạo bảng Fact_Transactions và các bảng Dim (Date, Category, Account, Merchant)
    │   │   ├── 03_dedup_and_logs.sql     # Tạo bảng log_dedup, nhật ký xử lý và kiểm soát chất lượng
    │   │   └── 04_semantic_views.sql     # Định nghĩa các Views phục vụ trực tiếp Apache Superset
    │   ├── migrations/                   # Quản lý phiên bản schema (Alembic hoặc script nâng cấp)
    │   ├── seeds/                        # Dữ liệu khởi tạo ban đầu (danh mục chuẩn, danh mục đơn vị thụ hưởng)
    │   │   ├── initial_categories.csv    # Cây danh mục thu/chi mặc định
    │   │   └── sample_merchants.csv      # Danh sách tên các merchant thông dụng tại Việt Nam
    │   └── mock_data/                    # Bộ dữ liệu giả lập phục vụ kiểm thử hệ thống
    │       ├── generate_mock_data.py     # Script Python sinh 500 - 1000 giao dịch mẫu đa dạng
    │       └── mock_transactions.csv     # File dữ liệu giao dịch giả lập sẵn có
    │
    ├── backend/                          # 2. PHÂN HỆ BACKEND, THU THẬP ETL & MÔ HÌNH AI
    │   ├── README.md                     # Hướng dẫn cài đặt và chạy các module backend
    │   ├── requirements.txt              # Danh sách thư viện Python (FastAPI, pandas, prophet, paddleocr,...)
    │   ├── Dockerfile                    # Container hóa backend service
    │   │
    │   ├── ingestion/                    # [Module Thu thập dữ liệu đa kênh]
    │   │   ├── __init__.py
    │   │   ├── email_collector/          # Thu thập biến động số dư qua Email
    │   │   │   ├── imap_client.py        # Đọc email qua giao thức IMAP
    │   │   │   ├── gmail_api_client.py   # Đọc email qua Google Gmail API OAuth2
    │   │   │   └── parsers/              # Regex bóc tách nội dung theo từng ngân hàng
    │   │   │       ├── vcb_parser.py     # Parser mẫu email Vietcombank
    │   │   │       ├── mbbank_parser.py  # Parser mẫu email MB Bank
    │   │   │       ├── techcom_parser.py # Parser mẫu email Techcombank
    │   │   │       └── momo_parser.py    # Parser mẫu email MoMo
    │   │   │
    │   │   ├── statement_parser/         # Phân tích file sao kê định kỳ
    │   │   │   ├── csv_parser.py         # Đọc file CSV sao kê chuẩn hóa các cột
    │   │   │   └── pdf_parser.py         # Trích xuất bảng sao kê từ file PDF
    │   │   │
    │   │   └── telegram_bot/             # Bot tiếp nhận ảnh chụp biên lai
    │   │       ├── bot.py                # Lắng nghe tin nhắn Telegram Bot
    │   │       └── ocr_engine.py         # Module OCR trích xuất số tiền, ngày, đơn vị từ ảnh
    │   │
    │   ├── etl_pipeline/                 # [Module Làm sạch, Khử trùng & Nạp dữ liệu]
    │   │   ├── __init__.py
    │   │   ├── cleaner.py                # Chuẩn hóa Unicode NFC, múi giờ Asia/Ho_Chi_Minh, loại bỏ ký tự rác
    │   │   ├── normalizer.py             # Chuẩn hóa số tiền dương/âm, định dạng ngày tháng
    │   │   ├── deduplicator.py           # Thuật toán khử trùng: so khớp mã GD, Jaro-Winkler, Levenshtein
    │   │   ├── pipeline_runner.py        # Kịch bản chạy toàn trình ETL từ Staging -> Warehouse
    │   │   └── data_quality.py           # 5 luật kiểm thử dữ liệu (không âm sau chuẩn hóa, không mồ côi khóa ngoại)
    │   │
    │   ├── ai_service/                   # [Module Trí tuệ Nhân tạo]
    │   │   ├── __init__.py
    │   │   ├── category_classifier/      # Phân loại danh mục giao dịch từ mô tả tiếng Việt
    │   │   │   ├── rule_based_matcher.py # Bộ luật từ khóa nhanh (Fast keyword heuristic)
    │   │   │   ├── nlp_classifier.py     # Mô hình NLP (PhoBERT / Zero-shot / Few-shot LLM)
    │   │   │   └── train_classifier.py   # Script huấn luyện hoặc fine-tune mô hình
    │   │   │
    │   │   ├── anomaly_detection/        # Phát hiện giao dịch bất thường
    │   │   │   ├── isolation_forest.py   # Thuật toán Isolation Forest
    │   │   │   └── zscore_detector.py    # Thống kê độ lệch chuẩn Z-score theo danh mục
    │   │   │
    │   │   └── forecasting/              # Dự báo dòng tiền & tốc độ đốt ngân sách
    │   │       ├── prophet_forecaster.py # Dự báo chi tiêu 30 ngày tới với Facebook Prophet
    │   │       └── burn_rate_analyzer.py # Tính toán Burn-rate và ngày dự kiến cạn số dư
    │   │
    │   ├── api/                          # [Giao diện RESTful API - FastAPI]
    │   │   ├── __init__.py
    │   │   ├── main.py                   # Điểm khởi chạy FastAPI application
    │   │   ├── config.py                 # Đọc cấu hình từ biến môi trường
    │   │   ├── dependencies.py           # Kết nối Database Session, bảo mật
    │   │   └── routers/                  # Các endpoint API
    │   │       ├── ingestion_routes.py   # Endpoint nhận file upload CSV/PDF, webhook Telegram
    │   │       ├── ai_routes.py          # Endpoint gọi phân loại, dự báo, phát hiện bất thường
    │   │       └── analytics_routes.py   # Endpoint lấy dữ liệu KPI tóm tắt
    │   │
    │   ├── scheduler/                    # [Module Lập lịch tự động]
    │   │   ├── cron_jobs.py              # Lập lịch chạy batch thu thập email (15 phút/lần)
    │   │   └── daily_summary.py          # Lập lịch chạy mô hình dự báo và gửi báo cáo hàng ngày
    │   │
    │   └── notification/                 # [Module Thông báo & Trợ lý hành động]
    │       ├── telegram_notifier.py      # Gửi tin nhắn cảnh báo tức thì khi có giao dịch bất thường
    │       └── weekly_report_agent.py    # Soạn thảo bản tin tổng kết tài chính tuần
    │
    └── frontend/                         # 3. PHÂN HỆ TRỰC QUAN HÓA & TRẢI NGHIỆM
        ├── README.md                     # Hướng dẫn cấu hình Apache Superset và import Dashboards
        ├── superset/                     # Cấu hình và tài nguyên Apache Superset
        │   ├── Dockerfile                # Custom container cho Superset (cài thêm driver postgresql, fonts)
        │   ├── superset_config.py        # File cấu hình bảo mật, ngôn ngữ, CSP của Superset
        │   ├── datasources/              # File định nghĩa kết nối cơ sở dữ liệu và Virtual Datasets
        │   │   └── superset_datasources.yaml
        │   └── dashboards_export/        # File xuất/nhập 3 Dashboard chuẩn định dạng ZIP/JSON
        │       ├── 01_cashflow_overview.json   # Dashboard 1: Tổng quan Dòng tiền & Sankey
        │       ├── 02_spending_behavior.json   # Dashboard 2: Phân tích Hành vi Chi tiêu & Heatmap
        │       └── 03_ai_forecast_anomalies.json # Dashboard 3: Dự báo AI & Cảnh báo Bất thường
        │
        └── portal/                       # Giao diện Web nhẹ hỗ trợ người dùng (FastAPI HTML hoặc React/Vue đơn giản)
            ├── public/                   # Tài nguyên tĩnh (ảnh, CSS, favicon)
            ├── templates/                # Giao diện người dùng: trang tải file sao kê, xem trạng thái pipeline
            │   ├── index.html
            │   └── upload.html
            └── static/
                ├── css/style.css
                └── js/app.js
```

---

## 3. Quy Ước Đặt Tên & Chuẩn Viết Code (Coding Conventions)

### 3.1. Quy chuẩn ngôn ngữ và đặt tên
- **Tên thư mục và tệp tin:** Viết thường toàn bộ, cách nhau bằng dấu gạch dưới `_` (snake_case) đối với code Python và SQL; ví dụ: `statement_parser/`, `deduplicator.py`, `01_staging.sql`.
- **Tên biến và hàm (Python):** Tuân thủ chuẩn PEP 8:
  - Tên hàm/biến: `snake_case` (ví dụ: `parse_email_content()`, `total_amount`).
  - Tên lớp (Class): `PascalCase` (ví dụ: `EmailCollector`, `ProphetForecaster`).
  - Hằng số: `UPPER_SNAKE_CASE` (ví dụ: `MAX_RETRIES`, `CONFIDENCE_THRESHOLD`).
- **Tên bảng và cột (PostgreSQL):**
  - Tên bảng Fact / Dim: Viết chữ thường dạng `fact_transactions`, `dim_category`, `dim_date`.
  - Tên cột: `snake_case`, rõ nghĩa (ví dụ: `transaction_id`, `created_at`, `is_anomaly`).

### 3.2. Quy tắc quản lý Git trong nhóm
- **Nhánh làm việc chính của nhóm:** `nhom13-65httt`.
- **Tuyệt đối không commit trực tiếp các tệp tin cấm:**
  - File môi trường chứa mật khẩu, API key: `.env`, token bot.
  - Thư mục thư viện: `venv/`, `__pycache__/`, `.pytest_cache/`, `node_modules/`.
  - File dữ liệu nhạy cảm hoặc dung lượng lớn: file sao kê thật có số tài khoản thật của cá nhân (dùng dữ liệu giả lập hoặc ẩn số tài khoản).
- **Quy chuẩn thông điệp commit (Git Commit Conventions):**
  - `feat(<module>): Thêm chức năng mới` (ví dụ: `feat(ingestion): Thêm parser email Vietcombank`)
  - `fix(<module>): Sửa lỗi` (ví dụ: `fix(dedup): Sửa ngưỡng thời gian trong thuật toán khử trùng`)
  - `docs(<module>): Cập nhật tài liệu` (ví dụ: `docs(database): Thêm mô tả từ điển dữ liệu Star Schema`)
  - `refactor(<module>): Tối ưu hóa mã nguồn mà không đổi logic nghiệp vụ`
  - `test(<module>): Bổ sung kịch bản kiểm thử tự động`

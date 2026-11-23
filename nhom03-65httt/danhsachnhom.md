# Danh Sách Nhóm Và Phân Công Nhiệm Vụ

## 1. Thông Tin Chung

- **Tên nhóm:** nhom03-65httt
- **Tên lớp học phần:** Hệ Thống Kinh Doanh Thông Minh - Lớp 65 HTTT
- **Tên đề tài:** Hệ thống phân tích trải nghiệm người học và cạnh tranh giữa các nền tảng E-learning, ứng dụng AI phân tích cảm xúc và dự báo xu hướng (EduVision BI)
- **Giảng viên hướng dẫn:** Ths. Đỗ Oanh Cường

---

## 2. Danh Sách Thành Viên

| STT | Họ và Tên | Mã Sinh Viên | Lớp Sinh Hoạt | Vai Trò | Nhiệm Vụ Phân Công | Tỷ Lệ Đóng Góp (%) | Email |
| :-: | :--- | :-: | :-: | :--- | :--- | :-: | :--- |
| 1 | Giang Thanh Tùng | 2351160563 | 65HTTT | Nhóm trưởng | Điều phối dự án, kiến trúc tổng thể; đường ống dữ liệu (collector YouTube, báo chí, Google Trends và thông tin ứng dụng; ETL từ raw qua clean đến dw; tác vụ tổng hợp fact_platform_period; lịch sử ETL); mô hình cảm xúc M1 (PhoBERT) và thí nghiệm E1, khung backend và API cho mô hình M1 (mỗi người tự viết API FastAPI cho mô hình mình phụ trách), khuyến nghị và cảnh báo tự sinh, chatbot LLM, workflow n8n, Docker Compose, bộ công cụ kiểm tra cho nhóm, tích hợp và kiểm thử; M4 và thí nghiệm E3 (tùy chọn); gán tay tập vàng (khoảng 140 dòng) | 20% | 2351160563@e.tlu.edu.vn |
| 2 | Tạ Thị Ngọc Anh | 2351160503 | 65HTTT | Thành viên | Kho dữ liệu galaxy schema và ERD, nhật ký chất lượng dữ liệu, mô hình dự báo M3 và thí nghiệm E4, phát hiện bất thường, API dự báo và API bất thường, dashboard Superset số 5 (Dự báo và khuyến nghị) và số 6 (Sức khỏe pipeline và chất lượng dữ liệu); phần mở rộng làm sau khi lõi chạy: cảm xúc theo phiên bản ứng dụng và cảnh báo bản phát hành bị đánh giá thấp, tỷ lệ đánh giá trùng nội dung; gán tay tập vàng (khoảng 140 dòng) | 20% | 2351160503@e.tlu.edu.vn |
| 3 | Nguyễn Thái Anh | 2351160502 | 65HTTT | Thành viên | Collector kho ứng dụng (Google Play, App Store), thu thập sâu; bảng sự kiện dim_event và rà lại các dòng “cần kiểm tra”; mô hình cảm xúc theo khía cạnh M2 (ABSA) và thí nghiệm E2, API dự đoán khía cạnh; gán tay tập vàng (khoảng 140 dòng) | 20% | 2351160502@e.tlu.edu.vn |
| 4 | Nguyễn Hoàng Anh | 2251161939 | 65HTTT | Thành viên | Chạy LLM gán nhãn và đo độ khớp với nhãn người, mô hình nền TF-IDF, website (giao diện, đăng nhập và phân quyền), API xác thực và phân quyền JWT (đăng nhập, vai trò Admin/Viewer, bảo vệ các điểm cuối), API nút “Cập nhật dữ liệu”, API quản lý nguồn dữ liệu và bảng sự kiện, API tìm kiếm và lọc đánh giá, nhúng Superset (kèm điểm cuối cấp guest token), kiểm thử người dùng; gán tay tập vàng (khoảng 140 dòng) | 20% | 2251161939@e.tlu.edu.vn |
| 5 | Hoàng Hữu Hưng | 2351160525 | 65HTTT | Thành viên | Dashboard Superset (dashboard số 1 đến 4), KPI, BHI, API KPI và BHI cho website, API xem cảnh báo và đánh dấu đã xử lý, mục khuyến nghị hành động, Sentiment Index có trọng số lượt hữu ích (mở rộng), kịch bản demo và slide; gán tay tập vàng (khoảng 140 dòng) | 20% | 2351160525@e.tlu.edu.vn |

> **Ghi chú:** Danh sách phân công nhiệm vụ và tỷ lệ đóng góp ở trên mới là **dự kiến**, có thể được điều chỉnh trong quá trình thực hiện đồ án.
>
> **Gán tay tập vàng:** cả 5 thành viên cùng gán, mỗi người khoảng 140 dòng (120 dòng của lô 500 mẫu cho năm nền tảng đợt đầu, trong đó có 100 mẫu do hai người cùng gán để tính Cohen’s kappa, cộng 20 dòng của lô Quizlet 100 mẫu).

---

## 3. Cấu Trúc Mã Nguồn Trong Thư Mục Nhóm

```text
nhom03-65httt/
├── danhsachnhom.md          # Tệp thông tin nhóm này
├── README.md                # Cấu trúc, quy tắc repo công khai, cách chạy
├── docker-compose.yml       # PostgreSQL, migration Alembic, API FastAPI (Superset, n8n bổ sung sau)
├── .env.example             # Mẫu biến môi trường (khóa API chỉ để trong .env, không commit)
├── config/
│   └── platforms.yml        # Danh sách nền tảng: thêm nền tảng = thêm một khối cấu hình
├── data/                    # raw/, clean/ nằm trên máy từng người, KHÔNG commit (repo công khai)
├── models/                  # Trọng số mô hình (PhoBERT...), KHÔNG commit; cách tải ở models/README.md
├── docs/
│   ├── De_Cuong_Nhom03.docx
│   └── dao_duc_phap_ly.md   # Điều khoản Google Play, App Store, YouTube; quyền riêng tư
└── src/
    ├── database/            # schema (galaxy) bằng SQL, migration Alembic, seed
    ├── etl/                 # collectors, transform, load, quality, workflows (n8n)
    ├── ml/                  # labeling, sentiment (M1), absa (M2), forecast (M3), anomaly, notebooks
    ├── backend/             # API FastAPI (api, core, llm, ml, models, schemas, services, tests)
    ├── frontend/            # Website React + TypeScript (auth, components, pages, services)
    └── bi/superset/         # Dashboard Superset
```

---

## 4. Hướng Dẫn Cài Đặt Và Thực Thi Mã Nguồn

> **Trạng thái:** đã có collector Google Play, schema kho dữ liệu (galaxy) kèm migration Alembic, khung API FastAPI, khung website (các trang đang dùng dữ liệu minh họa) và Docker Compose (PostgreSQL, migrate, API). **Chưa có:** các collector còn lại, ETL, mô hình AI, chatbot, Superset, n8n. Phần này chỉ ghi các lệnh đã chạy thử và sẽ cập nhật khi có thêm mã.

### 4.1. Môi trường yêu cầu
- Hệ điều hành: Windows 10/11 (máy các thành viên); Linux dùng được qua Docker.
- Nền tảng thực thi: Python 3.10 trở lên (thu thập, ETL, mô hình, FastAPI); Node.js bản LTS (website React); Docker Desktop (chạy Docker Compose).
- Cơ sở dữ liệu: PostgreSQL (chạy bằng Docker Compose, schema `raw`, `clean`, `dw`).
- Mô hình PhoBERT: huấn luyện trên Google Colab hoặc Kaggle (cần GPU); trọng số tải riêng, xem `models/README.md`.

### 4.2. Các bước cài đặt và khởi chạy
1. Sao chép `.env.example` thành `.env` và điền tham số (hiện bắt buộc có `POSTGRES_PASSWORD`; khóa YouTube API và khóa LLM dùng ở các phần sau). Không commit `.env`.
2. Đặt dữ liệu vào `data/raw/` và `data/clean/` theo `data/README.md` (nhận từ kênh riêng của nhóm, không lấy từ Git); tải trọng số mô hình vào `models/` theo `models/README.md`.
3. Cài các gói phụ thuộc: API chạy trong Docker (`src/backend/requirements.txt`, `requirements-dev.txt` cho kiểm thử); website cần Node.js (`npm install` trong `src/frontend/`).
4. Khởi chạy hạ tầng bằng `docker compose up -d --build` (PostgreSQL, migration Alembic, API FastAPI), rồi chạy website bằng `npm run dev` trong `src/frontend/`. Superset, n8n và ETL sẽ bổ sung.

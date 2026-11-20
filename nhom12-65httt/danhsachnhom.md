# Danh Sách Nhóm Và Phân Công Nhiệm Vụ

## 1. Thông Tin Chung

- **Tên nhóm:** nhom12-65httt
- **Tên lớp học phần:** Hệ thống kinh doanh thông minh
- **Tên đề tài:** Hệ thống tìm kiếm nhà thuê thông minh
- **Giảng viên hướng dẫn:** ThS. Đỗ Oanh Cường

---

## 2. Danh Sách Thành Viên

| STT | Họ và Tên | Mã Sinh Viên | Lớp Sinh Hoạt | Vai Trò | Nhiệm Vụ Phân Công | Tỷ Lệ Đóng Góp (%) | Email |
| :-: | :--- | :-: | :-: | :--- | :--- | :-: | :--- |
| 1 | Phạm Văn Tài | 2351160547 | 65HTTT | Nhóm trưởng |  | 20% | 2351160547@e.tlu.edu.vn |
| 2 | Vũ Thị Hồng | 2351160524 | 65HTTT | Thành viên |  | 20% | 2351160524@e.tlu.edu.vn |
| 3 | Nguyễn Quang Khải | 2351160530 | 65HTTT | Thành viên |  | 20% | 2351160530@e.tlu.edu.vn |
| 4 | Nguyễn Tài Tân | 2351160550 | 65HTTT | Thành viên |  | 20% | 2351160550@e.tlu.edu.vn |
| 5 | Phạm Đình Việt | 2351160565 | 65HTTT | Thành viên |  | 20% | 2351160565@e.tlu.edu.vn |

---

## 3. Cấu Trúc Mã Nguồn Trong Thư Mục Nhóm

Mã nguồn của nhóm được tổ chức theo cấu trúc chuẩn mô-đun:

```text
nhom12-65httt/
├── danhsachnhom.md        # Thông tin nhóm và phân công nhiệm vụ
├── README.md              # Hướng dẫn chi tiết cài đặt và thực thi hệ thống
├── requirements.txt       # Danh sách gói phụ thuộc Python
├── .env.example           # File mẫu biến môi trường
├── .gitignore             # Loại trừ .env, file tạm, cache khỏi Git
├── docs/                  # Đề cương và tài liệu đồ án
│   └── De_Cuong_HTKDTT.docx
└── src/                   # Mã nguồn chính của dự án
    ├── backend/           # Toàn bộ mã nguồn phía máy chủ, thu thập dữ liệu & CSDL
    │   ├── api/           # FastAPI REST API endpoints
    │   │   └── main.py
    │   ├── config/        # Quản lý cấu hình dự án và môi trường
    │   │   └── settings.py
    │   ├── database/      # Kết nối Supabase và kịch bản khởi tạo CSDL
    │   │   ├── schema.sql # DDL Star Schema + pgvector
    │   │   └── supabase_client.py
    │   ├── scraper/       # Các crawler thu thập dữ liệu
    │   │   ├── base_scraper.py
    │   │   ├── chotot_scraper.py
    │   │   ├── phongtro123_scraper.py
    │   │   └── osm_service.py # Dịch vụ tính khoảng cách tiện ích & trường đại học
    │   ├── etl/           # Chuẩn hóa dữ liệu và pipeline nạp Star Schema
    │   │   ├── cleaner.py # Chuẩn hóa giá, diện tích, phân loại phòng, chấm điểm rủi ro
    │   │   └── pipeline.py # Điều phối Staging -> Facts & Dimensions
    │   └── run_pipeline.py # Script chạy pipeline thu thập và nạp dữ liệu Supabase
    └── frontend/          # Ứng dụng giao diện người dùng React (Vite) + Leaflet
        └── README.md
```

---

## 4. Hướng Dẫn Cài Đặt Và Thực Thi Mã Nguồn

### 4.1. Môi trường yêu cầu
- **Hệ điều hành:** Windows 10/11, macOS, Ubuntu 22.04+
- **Nền tảng thực thi:** Python >= 3.10
- **Cơ sở dữ liệu:** Supabase (PostgreSQL 17) tích hợp extension `vector` (pgvector)
- **Thư viện chính:** `supabase`, `requests`, `beautifulsoup4`, `python-dotenv`, `pydantic`

### 4.2. Các bước cài đặt và khởi chạy
1. **Bước 1:** Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
2. **Bước 2:** Cấu hình file môi trường `.env`:
   ```bash
   cp .env.example .env
   # Điền thông tin SUPABASE_URL và SUPABASE_KEY (hoặc dùng mặc định đã kết nối sẵn)
   ```
3. **Bước 3:** Chạy pipeline thu thập và lưu trữ dữ liệu lên Supabase:
   ```bash
   # Cào tự động đến khi đạt chỉ tiêu số tin (ví dụ: mục tiêu 250 tin):
   python src/backend/run_pipeline.py --target 250

   # Hoặc cào số lượng tin tùy chọn từ cả 2 nguồn (Chợ Tốt & Phongtro123):
   python src/backend/run_pipeline.py --limit 20 --source all

   # Hoặc chỉ cào riêng từng nguồn:
   python src/backend/run_pipeline.py --limit 20 --source chotot
   python src/backend/run_pipeline.py --limit 20 --source phongtro123
   ```

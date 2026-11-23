# Hệ Thống Quản Lý Tài Chính Cá Nhân Thông Minh (Personal Finance Intelligence)
> **Học phần:** Hệ thống Kinh doanh Thông minh (HTKDTM)  
> **Nhóm thực hiện:** `nhom13-65httt`  
> **Giảng viên hướng dẫn:** ThS. Đỗ Oanh Cường  

---

## 📌 Giới Thiệu Đề Tài
Dự án tập trung giải quyết bài toán **"Mù mờ dòng tiền vi mô"** của người dùng cá nhân trong kỷ nguyên thanh toán không tiền mặt. Bằng cách kết hợp:
1. **Thu thập dữ liệu tự động, không xâm phạm:** Đọc email biến động số dư (IMAP/Gmail API), sao kê CSV/PDF và nhận diện ảnh biên lai chuyển khoản qua Telegram Bot (OCR).
2. **Làm sạch & Khử trùng lặp tự động:** Pipeline ETL chuẩn hóa định dạng và loại bỏ 100% giao dịch trùng lặp bằng giải thuật so khớp đa nguồn.
3. **Trí tuệ nhân tạo (AI):** Phân loại danh mục tiếng Việt (NLP), phát hiện giao dịch bất thường (Isolation Forest/Z-score) và dự báo số dư 30 ngày tới (Prophet).
4. **Trực quan hóa chuẩn Doanh nghiệp:** Nền tảng **Apache Superset** kết nối trực tiếp kho dữ liệu Star Schema (PostgreSQL), cung cấp 3 Dashboard phân tích chuyên sâu (Sankey, Heatmap, Burn-rate).

---

## 👥 Danh Sách Thành Viên & Phân Công Nhiệm Vụ

| STT | Họ và tên | Vai trò | Nhiệm vụ chính phụ trách |
| :-: | :--- | :---: | :--- |
| 1 | **Thiệu Quang Gia Bảo** | Nhóm trưởng | Điều phối chung; thiết kế kiến trúc, Star Schema DB; thiết lập Docker Compose; tích hợp toàn trình và báo cáo. |
| 2 | **Trần Minh Giang** | Thành viên | Xây dựng luồng thu thập email biến động số dư và bộ bóc tách sao kê CSV/PDF; lập lịch chạy batch ETL. |
| 3 | **Nguyễn Thu Giang** | Thành viên | Xây dựng Telegram Bot nhận ảnh biên lai, tích hợp OCR; chuẩn hóa dữ liệu và xây dựng module khử trùng lặp `log_dedup`. |
| 4 | **Trương Quốc Thái** | Thành viên | Xây dựng mô hình AI phân loại danh mục tiếng Việt, phát hiện giao dịch bất thường, dự báo dòng tiền; cung cấp REST API. |
| 5 | **Nguyễn Thị Khanh** | Thành viên | Kết nối DB với Apache Superset; xây dựng tầng ngữ nghĩa và 3 Dashboard; cấu hình cảnh báo và kịch bản demo. |

> Xem chi tiết tại: [danhsachnhom.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/danhsachnhom.md)

---

## 📁 Cấu Trúc Dự Án

Toàn bộ mã nguồn và tài liệu của nhóm được đóng gói hoàn chỉnh:
```text
nhom13-65httt/
├── danhsachnhom.md                  # Thông tin phân công nhiệm vụ thành viên
├── README.md                        # Hướng dẫn tổng quan (file hiện tại)
├── docker-compose.yml               # Cấu hình cụm dịch vụ (PostgreSQL, FastAPI, Superset, Redis)
├── .env.example                     # Biến môi trường mẫu
├── docs/                            # Tài liệu đặc tả và kế hoạch chi tiết
│   ├── README.md                    # Mục lục tài liệu
│   ├── 01_tong_quan_du_an.md        # Đặt vấn đề, 5 câu hỏi nghiệp vụ, KPIs
│   ├── 02_kien_truc_he_thong.md     # Sơ đồ kiến trúc 5 tầng và luồng dữ liệu
│   ├── 03_cau_truc_thu_muc.md       # Quy định cấu trúc thư mục chi tiết trong src/
│   ├── 04_thiet_ke_co_so_du_lieu.md # Thiết kế Star Schema, ERD, Views cho Superset
│   ├── 05_ke_hoach_trien_khai.md    # Kế hoạch chi tiết 8 tuần, RACI matrix
│   └── 06_huong_dan_chuan_bi_va_van_hanh.md # Hướng dẫn cài đặt, Docker, Git
└── src/                             # TOÀN BỘ MÃ NGUỒN DỰ ÁN
    ├── database/                    # Scripts SQL Staging, Star Schema, Seeds, Mock Data
    ├── backend/                     # Ingestion (Email, CSV/PDF, Telegram OCR), ETL, AI Models, FastAPI
    └── frontend/                    # Apache Superset dashboards export, config, Web Portal
```

---

## 🚀 Hướng Dẫn Khởi Chạy Nhanh (Quick Start)

### 1. Chuẩn bị môi trường
- Đảm bảo đã cài đặt Docker Desktop và kích hoạt nhánh làm việc:
  ```bash
  git checkout nhom13-65httt
  ```

### 2. Thiết lập biến môi trường
- Sao chép file cấu hình mẫu:
  ```bash
  cp .env.example .env
  ```

### 3. Khởi chạy với Docker Compose
- Dựng toàn bộ hệ sinh thái:
  ```bash
  docker-compose up -d
  ```

### 4. Truy cập dịch vụ
- **Apache Superset:** [http://localhost:8088](http://localhost:8088) (Tài khoản: `admin` / `admin`)
- **FastAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Web Portal:** [http://localhost:8000/](http://localhost:8000/)

> Xem hướng dẫn vận hành chi tiết tại: [06_huong_dan_chuan_bi_va_van_hanh.md](file:///d:/HTKDTM/project-htkdtm/nhom13-65httt/docs/06_huong_dan_chuan_bi_va_van_hanh.md)

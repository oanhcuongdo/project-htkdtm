# Business Intelligence - Apache Superset (Nhóm 05 - 65HTTT)

- **Phụ trách:** Nguyễn Quang Đức (MSV: `2351160512`)
- **Công cụ:** Apache Superset 4.0.2 + PostgreSQL 16 (Star Schema `dw.*`) + Redis 7

---

## 1. Cấu trúc thư mục
```text
src/bi/
├── .env.example                 # Biến môi trường mẫu cho PostgreSQL & Superset
├── docker-compose.yml           # Khởi chạy trọn bộ PostgreSQL DW + Redis + Apache Superset
├── superset_config.py           # Cấu hình Superset (Redis cache, Feature flags, CORS)
├── init_superset.sh             # Script tự động migrate DB, tạo admin & import 3 Dashboards
├── build_superset_bundle.py     # Đóng gói YAML thành training_analytics_dashboards.zip
└── superset_dashboards/         # Dashboard-as-Code (YAML export v1.0.0)
    ├── metadata.yaml
    ├── databases/
    ├── datasets/Training_Analytics_DW/
    ├── charts/
    └── dashboards/
        ├── 01_Quan_Ly_Hoc_Vu.yaml
        ├── 02_Chat_Luong_Dao_Tao.yaml
        └── 03_Xu_Huong_Nganh_Nghe.yaml
```

---

## 2. Hướng dẫn khởi chạy nhanh (Docker Compose)

1. Tạo tệp đóng gói Dashboard bundle (tùy chọn nếu chưa có `.zip`):
   ```powershell
   cd nhom05-65httt\src\bi
   python build_superset_bundle.py
   ```

2. Sao chép `.env.example` thành `.env` (nếu cần tùy chỉnh mật khẩu):
   ```powershell
   copy .env.example .env
   ```

3. Khởi động toàn bộ hệ thống Data Warehouse & Apache Superset:
   ```powershell
   docker compose up -d
   ```

4. Truy cập Apache Superset tại trình duyệt:
   - **URL:** `http://localhost:8088`
   - **Tài khoản mặc định:** `admin` / `admin`

5. (Khuyến nghị) Để nạp **toàn bộ** dữ liệu sạch từ `data/processed/` thay cho 500 dòng mẫu ban đầu, chạy ETL Python:
   ```powershell
   cd ..\database
   python etl_warehouse.py
   ```

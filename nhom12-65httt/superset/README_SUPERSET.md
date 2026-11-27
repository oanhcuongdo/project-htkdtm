# Hướng dẫn chạy Apache Superset BI & Kết nối Supabase

## 1. Khởi chạy Apache Superset bằng Docker
Từ thư mục `nhom12-65httt/`, chạy lệnh:
```bash
docker compose -f superset/docker-compose.superset.yml up -d
```
- Lần đầu khởi động mất khoảng 1–2 phút để cài `psycopg2-binary` và khởi tạo metadata DB.
- Truy cập giao diện Superset tại: **http://localhost:8088**
- Tài khoản mặc định: **`admin`** / **`admin123`**

## 2. Kết nối Superset tới Supabase (PostgreSQL)
1. Vào **Settings (góc phải) → Database Connections → + Database**.
2. Chọn **PostgreSQL**.
3. Lấy chuỗi kết nối **Session Pooler** trên Supabase Dashboard (*Connect → Session pooler*):
   ```text
   postgresql+psycopg2://postgres.<PROJECT_REF>:<DB_PASSWORD>@aws-0-<REGION>.pooler.supabase.com:5432/postgres
   ```
4. Nhấn **Test Connection** → thấy `Connection looks good!` → nhấn **Connect**.

## 3. Tạo Dataset & 3 Nhóm Biểu đồ Insight
1. Vào **Datasets → + Dataset**, chọn Database vừa tạo, schema `public`, bảng/view **`view_rental_market_analytics`** (hoặc `view_chatbot_admin_analytics`).
2. Tạo tối thiểu 3 nhóm biểu đồ đưa vào 1 Dashboard (ví dụ: *SmartRent Hanoi BI*):
   - **Nhóm 1 (Mặt bằng giá thuê/m²):** Bar Chart `AVG(price_per_m2)` theo `district` & `type_name`.
   - **Nhóm 2 (Cơ cấu nguồn cung):** Pie / Treemap / Bar Chart `COUNT(*)` theo `district` và `price_segment`.
   - **Nhóm 3 (Biến động giá & Thanh khoản):** Line Chart `AVG(price_per_m2)` theo `full_date` / `month` và Bar Chart `AVG(days_on_market)` / `room_status`.

## 4. Nhúng Dashboard vào React (`AnalyticsPage.jsx`)
1. Mở Dashboard vừa tạo trên Superset, đổi trạng thái **Draft → Published**.
2. Sao chép URL của Dashboard và thêm tham số `?standalone=true`, ví dụ:
   ```text
   http://localhost:8088/superset/dashboard/1/?standalone=true
   ```
3. Dán vào file `src/frontend/.env`:
   ```env
   VITE_SUPERSET_DASHBOARD_URL=http://localhost:8088/superset/dashboard/1/?standalone=true
   ```
4. Khởi động lại Frontend (`npm run dev`) và mở trang `/analytics`.

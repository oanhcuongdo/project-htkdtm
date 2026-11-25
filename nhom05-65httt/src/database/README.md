# Cấu Hình & Thiết Kế Cơ Sở Dữ Liệu PostgreSQL

Dự án sử dụng **PostgreSQL 16.x** làm cơ sở dữ liệu định hướng cho toàn bộ hệ thống phân tích đào tạo thông minh và Business Intelligence.

---

## 1. Cấu Trúc Bảng Dữ Liệu & Star Schema

Cơ sở dữ liệu được tổ chức tại tệp [schema_postgresql.sql](schema_postgresql.sql) bao gồm các bảng chính:

1. **`fact_job_postings`**: Lưu trữ dữ liệu tuyển dụng sạch từ VietJobs (vị trí, kỹ năng, lương min-max, kinh nghiệm, địa điểm).
2. **`wef_global_trends`**: Lưu trữ dữ liệu Báo cáo xu hướng nghề nghiệp quốc tế của World Economic Forum (WEF Future of Jobs Report).
3. **Các bảng OULAD (LMS Learning Analytics):**
   - `dim_course`: Danh mục học phần và thời lượng.
   - `dim_student`: Thông tin nhân khẩu học và kết quả học tập.
   - `dim_assessment`: Danh mục bài đánh giá (TMA, Exam) và trọng số.
   - `fact_student_assessment`: Chi tiết điểm thi từng bài của học viên.
   - `fact_student_vle`: Log tương tác hệ thống học tập VLE.
   - `fact_student_learning_analytics`: Bảng ma trận đặc trưng hành vi tích hợp (clicks, điểm trung bình, nhãn nguy cơ `risk_level`).
4. **`fact_course_reviews`**: Đánh giá khóa học trực tuyến (Coursera, Udemy), điểm rating, cảm xúc và nhận xét.
5. **Views phục vụ trực quan hóa (Apache Superset / Power BI):**
   - `v_student_performance_summary`: Tỷ lệ hoàn thành và phân bổ rủi ro học viên theo môn học.
   - `v_course_quality_kpi`: Chỉ số KPI chất lượng, điểm rating và tỷ lệ phản hồi tích cực/tiêu cực.
   - `v_job_market_demand`: Nhu cầu tuyển dụng theo ngành nghề, kỹ năng và địa điểm.

---

## 2. Hướng Dẫn Khởi Chạy & Nạp Dữ Liệu Vào PostgreSQL

### Cách 1: Sử dụng Docker Compose (Khuyến nghị - 1 click)
Khi đã bật Docker Desktop, chuyển vào thư mục này và chạy:
```powershell
cd nhom05-65httt\src\database
docker compose up -d
```
Container PostgreSQL 16 sẽ tự động khởi động và tự nạp toàn bộ cấu trúc bảng và dữ liệu mẫu từ `schema_postgresql.sql` và `seed_data_postgresql.sql`.

### Cách 2: Khởi tạo trên PostgreSQL cài đặt cục bộ (Native / pgAdmin / psql)
1. Tạo database:
```sql
CREATE DATABASE training_analytics WITH ENCODING 'UTF8';
```
2. Thực thi nạp toàn bộ schema và dữ liệu sạch bằng CLI:
```powershell
psql -h 127.0.0.1 -p 5432 -U postgres -d training_analytics -f seed_data_postgresql.sql
```
Hoặc chạy script nạp tự động bằng Python:
```powershell
..\backend\.venv\Scripts\python init_and_load_postgresql.py
```

### Cách 3: Kết nối Django Backend với PostgreSQL
Sau khi database hoạt động, cập nhật file `nhom05-65httt/src/backend/.env`:
```text
DB_ENGINE=postgresql
DB_NAME=training_analytics
DB_USER=postgres
DB_PASSWORD=<mat_khau_cua_ban>
DB_HOST=127.0.0.1
DB_PORT=5432
```
Sau đó chạy `python manage.py migrate` để đồng bộ các bảng của Django/Wagtail.

---

## 3. Data Warehouse Star Schema & BI Views (`schema dw`)
Phần mở rộng **Data Warehouse & BI** (phụ trách: **Nguyễn Quang Đức**) bổ sung các tệp sau:
- [dw_star_schema.sql](dw_star_schema.sql): Lược đồ hình sao `dw` gồm 9 bảng Dimension (`dim_date`, `dim_semester`, `dim_course`, `dim_student`, `dim_assessment`, `dim_provider`, `dim_industry`, `dim_location`, `dim_skill`) và 7 bảng Fact (`fact_ket_qua_hoc_tap`, `fact_assessment_performance`, `fact_vle_engagement`, `fact_course_reviews`, `fact_job_postings`, `fact_job_skills`, `fact_wef_trends`).
- [dw_etl_from_staging.sql](dw_etl_from_staging.sql): Script SQL ETL chuyển đổi dữ liệu từ bảng staging (`public.*`) sang Star Schema (`dw.*`).
- [etl_warehouse.py](etl_warehouse.py): Pipeline Python nạp toàn bộ dữ liệu sạch từ `data/processed/` vào PostgreSQL và cập nhật các BI Views.
- [dw_views_academic.sql](dw_views_academic.sql), [dw_views_quality.sql](dw_views_quality.sql), [dw_views_careers.sql](dw_views_careers.sql): Các View phân tích phục vụ trực tiếp cho 3 Dashboard trên Apache Superset (xem thêm tại [../bi/README.md](../bi/README.md)).



# BÁO CÁO KỸ THUẬT: THU THẬP, LÀM SẠCH VÀ CHUẨN HÓA DỮ LIỆU
**Học phần:** Hệ thống kinh doanh thông minh (HTKDTM) - Lớp 65HTTT  
**Đề tài:** Hệ thống quản lý đào tạo thông minh - Ứng dụng AI và Business Intelligence trong phân tích và nâng cao chất lượng đào tạo  
**Sinh viên phụ trách:** Đinh Thị Lan Anh  
**Mã sinh viên:** 2351160500  
**Vai trò phân công:** Thu thập & xử lý dữ liệu  

---

## 1. Mục Tiêu & Căn Cứ Đề Cương

Căn cứ theo **Đề cương bài tập lớn nhóm 05** (Mục IV.2 và IV.3):
- **Nhiệm vụ chính:** Thu thập dữ liệu từ 4 nguồn: **VietJobs**, **OULAD**, **Dữ liệu đánh giá khóa học (Course Reviews)**, và **Báo cáo xu hướng nghề nghiệp quốc tế (World Economic Forum - WEF)**; thực hiện làm sạch dữ liệu (data cleaning), chuẩn hóa trường thông tin (standardization), loại bỏ triệt để các bản ghi trùng lặp (deduplication) và thiết kế CSDL quan hệ trên PostgreSQL 16.x.
- **Tiêu chí đánh giá nghiệm thu:**
  1. *Số nhóm dữ liệu được tích hợp:* **Ít nhất 3 nhóm** (Đạt: **4 nhóm**).
  2. *Tỷ lệ bản ghi trùng lặp sau xử lý:* **Dưới 1%** (Đạt: **0.00%**).
  3. *Cơ sở dữ liệu:* Xây dựng hoàn chỉnh Schema trên PostgreSQL, Star Schema cho BI, sẵn sàng nạp dữ liệu.

---

## 2. Tổng Quan Các Bộ Dữ Liệu Được Thu Thập

Cấu trúc lưu trữ dữ liệu được tổ chức phân tầng rõ ràng tại thư mục `nhom05-65httt/data/`:
- `data/raw/`: Chứa dữ liệu gốc thu thập từ các nguồn (chứa dữ liệu trùng, nhiễu text, HTML bẩn, lỗi định dạng).
- `data/processed/`: Chứa dữ liệu sau khi chạy qua pipeline làm sạch, chuẩn hóa và khử trùng lặp.

### 2.1. Dữ liệu tuyển dụng Việt Nam (VietJobs)
- **Nguồn:** Thu thập và mô phỏng từ các nền tảng tuyển dụng lớn tại Việt Nam (TopCV, VietnamWorks, ITviec, VietJobs).
- **Mục đích:** Cung cấp thông tin nhu cầu thị trường, tần suất kỹ năng, mức lương và địa điểm làm việc nhằm phục vụ phân tích khoảng cách kỹ năng (Skill Gap) và xu hướng việc làm.
- **Quy mô:** 2,680 bản ghi ban đầu -> **1,762 bản ghi sạch** sau khi khử 918 bản ghi trùng lặp.
- **Các trường dữ liệu chính:**
  - `job_id`: Mã định danh tin tuyển dụng.
  - `job_title`: Chức danh công việc đã chuẩn hóa (vd: Data Analyst, Machine Learning Engineer, Python Developer,...).
  - `company_name`: Tên doanh nghiệp tuyển dụng.
  - `location`: Địa điểm chuẩn hóa (Hà Nội, TP. Hồ Chí Minh, Đà Nẵng, Cần Thơ, Hải Phòng, Remote, Toàn quốc).
  - `industry`: Lĩnh vực kinh doanh.
  - `required_skills`: Danh sách kỹ năng chuẩn hóa, phân tách bởi dấu phẩy (vd: `Python, SQL, Power BI, Docker`).
  - `salary_min_mil`, `salary_max_mil`: Mức lương tối thiểu - tối đa (đơn vị: triệu VNĐ/tháng).
  - `is_salary_negotiable`: Cờ đánh dấu lương thỏa thuận.
  - `experience_level`, `education_level`: Cấp bậc kinh nghiệm và trình độ học vấn.
  - `posted_date`: Ngày đăng chuẩn định dạng ISO `YYYY-MM-DD`.

### 2.2. Dữ liệu hành vi học tập OULAD (Open University Learning Analytics Dataset)
- **Nguồn:** Tập dữ liệu chuẩn Open University Learning Analytics Dataset (OULAD).
- **Mục đích:** Cung cấp log tương tác LMS, kết quả bài thi và điểm đánh giá phục vụ mô hình Machine Learning dự báo nguy cơ học viên bỏ học hoặc không hoàn thành.
- **Quy mô:** 22,344 bản ghi thô -> **21,723 bản ghi sạch** qua 5 bảng dữ liệu:
  - `courses_cleaned.csv`: Thông tin học phần (`code_module`, `code_presentation`, độ dài khóa).
  - `studentInfo_cleaned.csv`: Thông tin nhân khẩu học và kết quả cuối kỳ của sinh viên.
  - `assessments_cleaned.csv`: Danh mục 40 bài đánh giá (TMA, Exam) và trọng số (`weight`).
  - `studentAssessment_cleaned.csv`: Kết quả làm bài thi của sinh viên, xử lý điểm hợp lệ `[0, 100]`.
  - `studentVle_cleaned.csv`: Log tương tác hệ thống học tập VLE (`activity_type`, số lần click `sum_click >= 0`).
  - `student_features_analytics.csv`: Bảng tổng hợp Feature Matrix (3,000 sinh viên) gồm: `total_clicks`, `active_days`, `avg_score`, `assessments_completed`, và nhãn phân loại nguy cơ `risk_level` (High, Medium, Low).

### 2.3. Dữ liệu đánh giá và phản hồi khóa học (Course Reviews)
- **Nguồn:** Dữ liệu đánh giá từ các nền tảng MOOC (Coursera, Udemy, Microsoft Learn, DeepLearning.AI).
- **Mục đích:** Phục vụ phân tích NLP trích xuất chủ đề (Topic Modeling) và phân loại cảm xúc (Sentiment Analysis) của học viên về chất lượng giảng dạy và bài tập.
- **Quy mô:** 3,220 bản ghi ban đầu -> **1,021 bản ghi sạch duy nhất** sau khi loại bỏ 2,199 bản ghi trùng lặp.
- **Các trường dữ liệu chính:**
  - `review_id`, `course_id`, `course_title`, `provider`, `category`.
  - `rating`: Điểm đánh giá chuẩn hóa trong khoảng `[1.0, 5.0]`.
  - `sentiment`: Nhãn cảm xúc sơ bộ (`Positive`, `Neutral`, `Negative`).
  - `language`: Ngôn ngữ nhận xét (`vi`, `en`).
  - `review_text`: Nội dung nhận xét đã loại bỏ HTML, ký tự thừa.
  - `review_date`, `learner_level`, `helpful_count`.

### 2.4. Báo cáo xu hướng nghề nghiệp quốc tế (World Economic Forum - WEF)
- **Nguồn:** Báo cáo tương lai việc làm (The Future of Jobs Report) từ Diễn đàn Kinh tế Thế giới (WEF).
- **Mục đích:** Cung cấp thông tin xu hướng công nghệ toàn cầu, nhóm nghề tăng trưởng (Emerging Jobs), nghề suy giảm (Declining Jobs), kỹ năng cốt lõi (Core Skills) và mức độ liên đới để đối chiếu với thị trường việc làm Việt Nam và đề xuất chương trình đào tạo.
- **Quy mô:** 31 bản ghi thô -> **25 bản ghi sạch chuẩn hóa** sau khi loại bỏ trùng lặp.
- **Các trường dữ liệu chính:**
  - `trend_id`: Mã định danh xu hướng.
  - `category`: Nhóm xu hướng (Emerging Jobs, Declining Jobs, Core Skills, Technology Adoption).
  - `item_name`: Tên nghề/kỹ năng/công nghệ.
  - `growth_rate_pct`: Tỷ lệ tăng trưởng dự báo (% tăng trưởng toàn cầu).
  - `global_demand_level`: Mức độ nhu cầu toàn cầu (Very High, High, Moderate, Declining).
  - `primary_sector`: Nhóm ngành tác động chính.
  - `reskilling_months`: Thời gian đào tạo lại trung bình (tháng).
  - `vietnam_relevance`: Mức độ thích ứng và tiềm năng phát triển tại Việt Nam (High, Medium, Emerging).
  - `trend_description`: Diễn giải chi tiết xu hướng.


---

## 3. Quy Trình Làm Sạch & Chuẩn Hóa Dữ Liệu (Data Cleaning & Normalization)

Quy trình ETL được thiết kế tự động hóa dạng module tại thư mục `nhom05-65httt/src/data_pipeline/`:

```
   Raw Data (raw/) 
         │
         ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 1. Text Preprocessing & HTML Stripping                 │
 │    - Loại bỏ thẻ HTML (<p>, <div>, <br>)                │
 │    - Xóa ký tự điều khiển, regex làm sạch ký tự thừa    │
 └─────────────────────────┬───────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 2. Entity Normalization                                 │
 │    - Chuẩn hóa Skills từ điển chuẩn (Python, SQL,...)   │
 │    - Chuẩn hóa địa lý (Hà Nội, TP.HCM,...)              │
 │    - Chuẩn hóa thang lương về triệu VNĐ/tháng           │
 │    - Chuẩn hóa ngày tháng về ISO YYYY-MM-DD             │
 │    - Clip điểm OULAD [0, 100] và Rating [1.0, 5.0]      │
 └─────────────────────────┬───────────────────────────────┘
                           │
                           ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 3. Deduplication (Loại bỏ trùng lặp)                   │
 │    - Xác định Composite Unique Key                      │
 │    - Xóa bản ghi trùng lặp, giữ lại bản ghi đầu tiên    │
 │    - Kiểm tra tỷ lệ trùng lặp còn lại                   │
 └─────────────────────────┬───────────────────────────────┘
                           │
                           ▼
   Cleaned Data (processed/) & Data Quality Report (JSON)
```

---

## 4. Kết Quả Nghiệm Thu Theo Tiêu Chí Đề Cương

Bảng đối chiếu kết quả thực hiện theo tiêu chí đề cương:

| Hạng mục đánh giá | Chỉ tiêu đề cương | Kết quả thực tế đạt được | Đánh giá |
| :--- | :--- | :--- | :---: |
| **Số nhóm dữ liệu tích hợp** | Ít nhất 3 nhóm | **3 nhóm dữ liệu** (VietJobs, OULAD, Course Reviews) | **ĐẠT (PASSED)** |
| **Tỷ lệ trùng lặp VietJobs** | Dưới 1% | **0.00%** (Đã loại 918 bản ghi trùng) | **ĐẠT (PASSED)** |
| **Tỷ lệ trùng lặp OULAD** | Dưới 1% | **0.00%** (Đã loại 621 bản ghi trùng) | **ĐẠT (PASSED)** |
| **Tỷ lệ trùng lặp Reviews** | Dưới 1% | **0.00%** (Đã loại 2,199 bản ghi trùng) | **ĐẠT (PASSED)** |
| **Tổng số bản ghi sạch** | Đảm bảo đủ mẫu | **24,506 bản ghi** dữ liệu chất lượng cao | **ĐẠT (PASSED)** |

*Chi tiết báo cáo máy tính được lưu tự động tại:* `nhom05-65httt/data/processed/data_quality_report.json`.

---

## 5. Bàn Giao Dữ Liệu Cho Các Thành Viên Trong Nhóm

Dữ liệu sạch sau xử lý được định dạng tiêu chuẩn (CSV), sẵn sàng cung cấp cho các thành viên:

1. **Nguyễn Anh Quân (AI & Machine Learning):**
   - Tệp bàn giao: `data/processed/oulad/student_features_analytics.csv`
   - Mục đích: Huấn luyện mô hình Random Forest / XGBoost dự báo nguy cơ học viên bỏ học (`risk_level`: High/Medium/Low) dựa trên số clicks, số ngày hoạt động và điểm trung bình.

2. **Nguyễn Thị Diễm Quỳnh (NLP & Phân tích xu hướng nghề nghiệp):**
   - Tệp bàn giao 1: `data/processed/course_reviews/course_reviews_cleaned.csv` phục vụ phân tích cảm xúc phản hồi học viên và phát hiện điểm nghẽn chất lượng đào tạo.
   - Tệp bàn giao 2: `data/processed/vietjobs/vietjobs_cleaned.csv` phục vụ trích xuất kỹ năng tuyển dụng và phân tích Skill Gap.

3. **Nguyễn Quang Đức (Data Warehouse & BI):**
   - Tệp bàn giao: Toàn bộ dữ liệu sạch tại `data/processed/` phục vụ thiết kế lược đồ hình sao (Star Schema), tạo các bảng Dimension (`Dim_SinhVien`, `Dim_HocPhan`, `Dim_KyNang`, `Dim_CongTy`) và Fact (`Fact_KetQuaHocTap`, `Fact_TuyenDung`) để trực quan hóa trên Apache Superset / Django Dashboard.

---

## 6. Hướng Dẫn Chạy Tự Động Hóa Pipeline

Để tái lập quy trình thu thập và làm sạch dữ liệu:
```powershell
# Chuyển vào thư mục backend và kích hoạt môi trường ảo
cd d:\HTKDTM\project-htkdtm\nhom05-65httt\src\backend
.\.venv\Scripts\Activate.ps1

# Chạy toàn bộ pipeline thu thập, làm sạch và nghiệm thu
python ..\data_pipeline\run_pipeline.py
```

-- =============================================================================
-- DATA WAREHOUSE STAR SCHEMA (MÔ HÌNH LƯỢC ĐỒ HÌNH SAO)
-- HỆ THỐNG QUẢN LÝ ĐÀO TẠO THÔNG MINH - LỚP 65HTTT (NHÓM 05)
-- PHỤ TRÁCH: Nguyễn Quang Đức (Data Warehouse & BI)
-- CÔNG NGHỆ: PostgreSQL 16.x
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dw;

-- =============================================================================
-- 1. CÁC BẢNG CHIỀU (DIMENSION TABLES)
-- =============================================================================

-- Dim_Date: Chiều thời gian chuẩn cho phân tích chuỗi thời gian (Time-Series)
DROP TABLE IF EXISTS dw.dim_date CASCADE;
CREATE TABLE dw.dim_date (
    date_key INT PRIMARY KEY,                -- Định dạng YYYYMMDD
    full_date DATE NOT NULL UNIQUE,
    year SMALLINT NOT NULL,
    quarter SMALLINT NOT NULL,
    month SMALLINT NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    year_month VARCHAR(7) NOT NULL,          -- Định dạng YYYY-MM
    week_of_year SMALLINT NOT NULL,
    day_of_month SMALLINT NOT NULL,
    day_of_week SMALLINT NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Dim_Semester: Chiều học kỳ / đợt triển khai khóa học (OULAD presentations)
DROP TABLE IF EXISTS dw.dim_semester CASCADE;
CREATE TABLE dw.dim_semester (
    semester_sk SERIAL PRIMARY KEY,
    code_presentation VARCHAR(10) NOT NULL UNIQUE,
    academic_year SMALLINT NOT NULL,
    semester_term VARCHAR(20) NOT NULL,      -- Spring (B), Fall (J)
    semester_label VARCHAR(50) NOT NULL
);

-- Dim_Provider: Chiều nhà cung cấp / giảng viên / nền tảng đào tạo
DROP TABLE IF EXISTS dw.dim_provider CASCADE;
CREATE TABLE dw.dim_provider (
    provider_sk SERIAL PRIMARY KEY,
    provider_name VARCHAR(150) NOT NULL UNIQUE,
    platform_type VARCHAR(50) NOT NULL       -- MOOC, University LMS, Corporate
);

-- Dim_Course: Chiều khóa học / học phần tích hợp (OULAD + Course Reviews)
DROP TABLE IF EXISTS dw.dim_course CASCADE;
CREATE TABLE dw.dim_course (
    course_sk SERIAL PRIMARY KEY,
    course_code VARCHAR(50) NOT NULL UNIQUE, -- VD: BBB-2026B hoặc CRS_007
    source_system VARCHAR(30) NOT NULL,      -- OULAD, COURSE_REVIEWS
    code_module VARCHAR(20),
    code_presentation VARCHAR(10),
    course_title VARCHAR(255) NOT NULL,
    provider_name VARCHAR(150),
    category VARCHAR(100),
    module_length_days INT
);

CREATE INDEX idx_dw_course_module ON dw.dim_course(code_module);
CREATE INDEX idx_dw_course_category ON dw.dim_course(category);

-- Dim_Student: Chiều học viên (nhân khẩu học & nền tảng học vấn)
DROP TABLE IF EXISTS dw.dim_student CASCADE;
CREATE TABLE dw.dim_student (
    student_sk SERIAL PRIMARY KEY,
    id_student INT NOT NULL UNIQUE,
    gender VARCHAR(10),
    region VARCHAR(100),
    highest_education VARCHAR(100),
    imd_band VARCHAR(50),
    age_band VARCHAR(50),
    disability VARCHAR(5)
);

CREATE INDEX idx_dw_student_region ON dw.dim_student(region);
CREATE INDEX idx_dw_student_age ON dw.dim_student(age_band);

-- Dim_Assessment: Chiều bài kiểm tra / đánh giá học phần
DROP TABLE IF EXISTS dw.dim_assessment CASCADE;
CREATE TABLE dw.dim_assessment (
    assessment_sk SERIAL PRIMARY KEY,
    id_assessment INT NOT NULL UNIQUE,
    code_module VARCHAR(10) NOT NULL,
    code_presentation VARCHAR(10) NOT NULL,
    assessment_type VARCHAR(20) NOT NULL,    -- TMA, CMA, Exam
    due_day INT,
    weight NUMERIC(5, 2)
);

-- Dim_Industry: Chiều ngành nghề tuyển dụng & lĩnh vực WEF
DROP TABLE IF EXISTS dw.dim_industry CASCADE;
CREATE TABLE dw.dim_industry (
    industry_sk SERIAL PRIMARY KEY,
    industry_name VARCHAR(150) NOT NULL UNIQUE,
    sector_group VARCHAR(100) NOT NULL
);

-- Dim_Location: Chiều địa điểm tuyển dụng tại Việt Nam
DROP TABLE IF EXISTS dw.dim_location CASCADE;
CREATE TABLE dw.dim_location (
    location_sk SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL UNIQUE,
    region_group VARCHAR(50) NOT NULL        -- Miền Bắc, Miền Nam, Miền Trung, Remote/Khác
);

-- Dim_Skill: Chiều kỹ năng nghề nghiệp (chuẩn hóa từ tin tuyển dụng)
DROP TABLE IF EXISTS dw.dim_skill CASCADE;
CREATE TABLE dw.dim_skill (
    skill_sk SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    skill_category VARCHAR(50) NOT NULL      -- AI & Data, Programming, Cloud & DevOps, Database & BI, Other
);

-- =============================================================================
-- 2. CÁC BẢNG SỰ KIỆN (FACT TABLES)
-- =============================================================================

-- Fact_KetQuaHocTap: Bảng sự kiện trung tâm về kết quả và hành vi học tập
-- Grain: 1 học viên x 1 học phần x 1 học kỳ
DROP TABLE IF EXISTS dw.fact_ket_qua_hoc_tap CASCADE;
CREATE TABLE dw.fact_ket_qua_hoc_tap (
    fact_id BIGSERIAL PRIMARY KEY,
    student_sk INT NOT NULL REFERENCES dw.dim_student(student_sk),
    course_sk INT NOT NULL REFERENCES dw.dim_course(course_sk),
    semester_sk INT NOT NULL REFERENCES dw.dim_semester(semester_sk),
    num_of_prev_attempts INT DEFAULT 0,
    studied_credits INT DEFAULT 0,
    total_clicks INT DEFAULT 0,
    active_days INT DEFAULT 0,
    avg_score NUMERIC(5, 2) DEFAULT 0.0,
    assessments_completed INT DEFAULT 0,
    final_result VARCHAR(50) NOT NULL,       -- Pass, Distinction, Fail, Withdrawn
    is_completed SMALLINT NOT NULL DEFAULT 0,-- 1 = Pass/Distinction, 0 = Fail/Withdrawn
    is_dropout SMALLINT NOT NULL DEFAULT 0,  -- 1 = Withdrawn/Fail, 0 = Pass/Distinction
    risk_level VARCHAR(20) NOT NULL,         -- High, Medium, Low
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_sk, course_sk, semester_sk)
);

CREATE INDEX idx_dw_kqht_risk ON dw.fact_ket_qua_hoc_tap(risk_level);
CREATE INDEX idx_dw_kqht_result ON dw.fact_ket_qua_hoc_tap(final_result);
CREATE INDEX idx_dw_kqht_course ON dw.fact_ket_qua_hoc_tap(course_sk);

-- Fact_Assessment_Performance: Kết quả chi tiết từng bài thi/kiểm tra
-- Grain: 1 học viên x 1 bài đánh giá
DROP TABLE IF EXISTS dw.fact_assessment_performance CASCADE;
CREATE TABLE dw.fact_assessment_performance (
    fact_id BIGSERIAL PRIMARY KEY,
    student_sk INT NOT NULL REFERENCES dw.dim_student(student_sk),
    assessment_sk INT NOT NULL REFERENCES dw.dim_assessment(assessment_sk),
    course_sk INT NOT NULL REFERENCES dw.dim_course(course_sk),
    date_submitted INT,
    is_banked SMALLINT DEFAULT 0,
    score NUMERIC(5, 2),
    is_passed_assessment SMALLINT NOT NULL DEFAULT 0, -- 1 nếu score >= 40
    UNIQUE (student_sk, assessment_sk)
);

CREATE INDEX idx_dw_ass_course ON dw.fact_assessment_performance(course_sk);

-- Fact_VLE_Engagement: Tổng hợp mức độ tương tác theo loại tài nguyên VLE
-- Grain: 1 học viên x 1 học phần x 1 loại hoạt động VLE
DROP TABLE IF EXISTS dw.fact_vle_engagement CASCADE;
CREATE TABLE dw.fact_vle_engagement (
    fact_id BIGSERIAL PRIMARY KEY,
    student_sk INT NOT NULL REFERENCES dw.dim_student(student_sk),
    course_sk INT NOT NULL REFERENCES dw.dim_course(course_sk),
    activity_type VARCHAR(50) NOT NULL,
    total_clicks INT NOT NULL DEFAULT 0,
    active_days_count INT NOT NULL DEFAULT 0,
    UNIQUE (student_sk, course_sk, activity_type)
);

-- Fact_Course_Reviews: Sự kiện đánh giá chất lượng khóa học & cảm xúc NLP
-- Grain: 1 lượt đánh giá khóa học
DROP TABLE IF EXISTS dw.fact_course_reviews CASCADE;
CREATE TABLE dw.fact_course_reviews (
    review_sk BIGSERIAL PRIMARY KEY,
    review_id VARCHAR(50) NOT NULL UNIQUE,
    course_sk INT NOT NULL REFERENCES dw.dim_course(course_sk),
    provider_sk INT NOT NULL REFERENCES dw.dim_provider(provider_sk),
    date_key INT REFERENCES dw.dim_date(date_key),
    rating NUMERIC(3, 1) NOT NULL,
    sentiment VARCHAR(20) NOT NULL,          -- Positive, Neutral, Negative
    sentiment_score SMALLINT NOT NULL,       -- 1, 0, -1
    language VARCHAR(10),
    learner_level VARCHAR(50),
    helpful_count INT DEFAULT 0,
    issue_topic VARCHAR(100),                -- Chủ đề vấn đề rút trích từ phản hồi
    review_text TEXT NOT NULL
);

CREATE INDEX idx_dw_rev_sentiment ON dw.fact_course_reviews(sentiment);
CREATE INDEX idx_dw_rev_provider ON dw.fact_course_reviews(provider_sk);
CREATE INDEX idx_dw_rev_course ON dw.fact_course_reviews(course_sk);

-- Fact_Job_Postings: Sự kiện tin tuyển dụng tại Việt Nam (VietJobs)
-- Grain: 1 tin tuyển dụng
DROP TABLE IF EXISTS dw.fact_job_postings CASCADE;
CREATE TABLE dw.fact_job_postings (
    job_sk BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(50) NOT NULL UNIQUE,
    industry_sk INT NOT NULL REFERENCES dw.dim_industry(industry_sk),
    location_sk INT NOT NULL REFERENCES dw.dim_location(location_sk),
    date_key INT NOT NULL REFERENCES dw.dim_date(date_key),
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    salary_min_mil NUMERIC(10, 2),
    salary_max_mil NUMERIC(10, 2),
    salary_avg_mil NUMERIC(10, 2),
    is_salary_negotiable BOOLEAN DEFAULT FALSE,
    experience_level VARCHAR(100),
    education_level VARCHAR(100),
    source VARCHAR(50)
);

CREATE INDEX idx_dw_job_industry ON dw.fact_job_postings(industry_sk);
CREATE INDEX idx_dw_job_location ON dw.fact_job_postings(location_sk);
CREATE INDEX idx_dw_job_date ON dw.fact_job_postings(date_key);

-- Fact_Job_Skills: Bảng sự kiện cầu nối (Bridge/Fact) kỹ năng yêu cầu theo tin tuyển dụng
-- Grain: 1 tin tuyển dụng x 1 kỹ năng
DROP TABLE IF EXISTS dw.fact_job_skills CASCADE;
CREATE TABLE dw.fact_job_skills (
    job_sk BIGINT NOT NULL REFERENCES dw.fact_job_postings(job_sk) ON DELETE CASCADE,
    skill_sk INT NOT NULL REFERENCES dw.dim_skill(skill_sk),
    industry_sk INT NOT NULL REFERENCES dw.dim_industry(industry_sk),
    location_sk INT NOT NULL REFERENCES dw.dim_location(location_sk),
    date_key INT NOT NULL REFERENCES dw.dim_date(date_key),
    PRIMARY KEY (job_sk, skill_sk)
);

CREATE INDEX idx_dw_js_skill ON dw.fact_job_skills(skill_sk);
CREATE INDEX idx_dw_js_industry ON dw.fact_job_skills(industry_sk);

-- Fact_WEF_Trends: Dữ liệu xu hướng nghề nghiệp & kỹ năng quốc tế (WEF)
-- Grain: 1 xu hướng / nhóm kỹ năng WEF
DROP TABLE IF EXISTS dw.fact_wef_trends CASCADE;
CREATE TABLE dw.fact_wef_trends (
    trend_sk SERIAL PRIMARY KEY,
    trend_id VARCHAR(50) NOT NULL UNIQUE,
    industry_sk INT NOT NULL REFERENCES dw.dim_industry(industry_sk),
    category VARCHAR(100) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    growth_rate_pct NUMERIC(6, 2),
    global_demand_level VARCHAR(50),
    reskilling_months INT DEFAULT 6,
    vietnam_relevance VARCHAR(50),
    trend_description TEXT
);

-- =============================================================================
-- CƠ SỞ DỮ LIỆU: TRAINING ANALYTICS & RECOMMENDATION SYSTEM
-- HỆ THỐNG QUẢN LÝ ĐÀO TẠO THÔNG MINH - LỚP 65HTTT (NHÓM 05)
-- CÔNG NGHỆ: PostgreSQL 16.x (UTF-8)
-- THIẾT KẾ: Bảng quan hệ (Relational) + Lược đồ hình sao (Star Schema) cho BI
-- =============================================================================

-- Khởi tạo Database (Thực thi bởi postgres user):
-- CREATE DATABASE training_analytics WITH ENCODING 'UTF8';
-- \c training_analytics;

-- =============================================================================
-- 1. BẢNG DỮ LIỆU TUYỂN DỤNG VIỆT NAM (VIETJOBS)
-- =============================================================================
DROP TABLE IF EXISTS fact_job_postings CASCADE;
CREATE TABLE fact_job_postings (
    job_id VARCHAR(50) PRIMARY KEY,
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    location VARCHAR(100) NOT NULL,
    industry VARCHAR(150),
    required_skills TEXT,
    salary_min_mil NUMERIC(10, 2),
    salary_max_mil NUMERIC(10, 2),
    is_salary_negotiable BOOLEAN DEFAULT FALSE,
    experience_level VARCHAR(100),
    education_level VARCHAR(100),
    posted_date DATE NOT NULL,
    source VARCHAR(50),
    job_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vietjobs_title ON fact_job_postings(job_title);
CREATE INDEX idx_vietjobs_location ON fact_job_postings(location);
CREATE INDEX idx_vietjobs_industry ON fact_job_postings(industry);
CREATE INDEX idx_vietjobs_posted_date ON fact_job_postings(posted_date);

-- =============================================================================
-- 2. BẢNG XU HƯỚNG QUỐC TẾ (WORLD ECONOMIC FORUM - WEF)
-- =============================================================================
DROP TABLE IF EXISTS wef_global_trends CASCADE;
CREATE TABLE wef_global_trends (
    trend_id VARCHAR(50) PRIMARY KEY,
    report_source VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL, -- Emerging Jobs, Declining Jobs, Core Skills, Technology Adoption
    item_name VARCHAR(255) NOT NULL,
    growth_rate_pct NUMERIC(6, 2),
    global_demand_level VARCHAR(50), -- Very High, High, Moderate, Declining
    primary_sector VARCHAR(150),
    reskilling_months INT DEFAULT 6,
    vietnam_relevance VARCHAR(50) DEFAULT 'High', -- High, Medium, Emerging
    trend_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wef_category ON wef_global_trends(category);
CREATE INDEX idx_wef_demand ON wef_global_trends(global_demand_level);

-- =============================================================================
-- 3. CÁC BẢNG DỮ LIỆU HỌC TẬP OULAD (OPEN UNIVERSITY)
-- =============================================================================

-- Dim_Course: Danh mục học phần
DROP TABLE IF EXISTS dim_course CASCADE;
CREATE TABLE dim_course (
    code_module VARCHAR(10) NOT NULL,
    code_presentation VARCHAR(10) NOT NULL,
    module_presentation_length INT,
    PRIMARY KEY (code_module, code_presentation)
);

-- Dim_Student: Thông tin sinh viên
DROP TABLE IF EXISTS dim_student CASCADE;
CREATE TABLE dim_student (
    id_student INT NOT NULL,
    code_module VARCHAR(10) NOT NULL,
    code_presentation VARCHAR(10) NOT NULL,
    gender VARCHAR(10),
    region VARCHAR(100),
    highest_education VARCHAR(100),
    imd_band VARCHAR(50),
    age_band VARCHAR(50),
    num_of_prev_attempts INT DEFAULT 0,
    studied_credits INT,
    disability VARCHAR(5),
    final_result VARCHAR(50), -- Pass, Distinction, Fail, Withdrawn
    PRIMARY KEY (code_module, code_presentation, id_student)
);

CREATE INDEX idx_student_result ON dim_student(final_result);
CREATE INDEX idx_student_id ON dim_student(id_student);

-- Dim_Assessment: Danh mục bài thi, đánh giá
DROP TABLE IF EXISTS dim_assessment CASCADE;
CREATE TABLE dim_assessment (
    id_assessment INT PRIMARY KEY,
    code_module VARCHAR(10) NOT NULL,
    code_presentation VARCHAR(10) NOT NULL,
    assessment_type VARCHAR(20), -- TMA, Exam, CMA
    date INT,
    weight NUMERIC(5, 2)
);

-- Fact_Student_Assessment: Kết quả nộp bài chi tiết
DROP TABLE IF EXISTS fact_student_assessment CASCADE;
CREATE TABLE fact_student_assessment (
    id_assessment INT NOT NULL,
    id_student INT NOT NULL,
    date_submitted INT,
    is_banked INT DEFAULT 0,
    score NUMERIC(5, 2),
    PRIMARY KEY (id_assessment, id_student),
    FOREIGN KEY (id_assessment) REFERENCES dim_assessment(id_assessment)
);

CREATE INDEX idx_fact_ass_student ON fact_student_assessment(id_student);

-- Fact_Student_Vle: Log tương tác hệ thống học tập VLE
DROP TABLE IF EXISTS fact_student_vle CASCADE;
CREATE TABLE fact_student_vle (
    code_module VARCHAR(10) NOT NULL,
    code_presentation VARCHAR(10) NOT NULL,
    id_student INT NOT NULL,
    id_site INT NOT NULL,
    date INT NOT NULL,
    sum_click INT NOT NULL DEFAULT 1,
    PRIMARY KEY (code_module, code_presentation, id_student, id_site, date)
);

-- Fact_Student_Learning_Analytics: Bảng phân tích hành vi tổng hợp (Feature Matrix)
DROP TABLE IF EXISTS fact_student_learning_analytics CASCADE;
CREATE TABLE fact_student_learning_analytics (
    id_student INT NOT NULL,
    code_module VARCHAR(10) NOT NULL,
    code_presentation VARCHAR(10) NOT NULL,
    gender VARCHAR(10),
    region VARCHAR(100),
    highest_education VARCHAR(100),
    age_band VARCHAR(50),
    studied_credits INT,
    final_result VARCHAR(50),
    total_clicks INT DEFAULT 0,
    active_days INT DEFAULT 0,
    avg_score NUMERIC(5, 2) DEFAULT 0.0,
    assessments_completed INT DEFAULT 0,
    risk_level VARCHAR(20) NOT NULL, -- High, Medium, Low
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (code_module, code_presentation, id_student)
);

CREATE INDEX idx_analytics_risk ON fact_student_learning_analytics(risk_level);
CREATE INDEX idx_analytics_clicks ON fact_student_learning_analytics(total_clicks);

-- =============================================================================
-- 4. BẢNG ĐÁNH GIÁ CHẤT LƯỢNG KHÓA HỌC (COURSE REVIEWS)
-- =============================================================================
DROP TABLE IF EXISTS fact_course_reviews CASCADE;
CREATE TABLE fact_course_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    course_id VARCHAR(50) NOT NULL,
    course_title VARCHAR(255) NOT NULL,
    provider VARCHAR(150),
    category VARCHAR(100),
    rating NUMERIC(3, 1) NOT NULL,
    sentiment VARCHAR(20), -- Positive, Neutral, Negative
    language VARCHAR(10), -- vi, en
    review_text TEXT NOT NULL,
    review_date DATE,
    learner_level VARCHAR(50),
    helpful_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reviews_course ON fact_course_reviews(course_id);
CREATE INDEX idx_reviews_rating ON fact_course_reviews(rating);
CREATE INDEX idx_reviews_sentiment ON fact_course_reviews(sentiment);

-- =============================================================================
-- 5. VIEW TRỰC QUAN HÓA CHO BUSINESS INTELLIGENCE (APACHE SUPERSET / POWER BI)
-- =============================================================================

-- View 1: Tỷ lệ hoàn thành và mức độ rủi ro theo học phần
CREATE OR REPLACE VIEW v_student_performance_summary AS
SELECT 
    code_module,
    code_presentation,
    COUNT(id_student) AS total_students,
    ROUND(AVG(total_clicks), 1) AS avg_clicks_per_student,
    ROUND(AVG(active_days), 1) AS avg_active_days,
    ROUND(AVG(avg_score), 2) AS course_avg_score,
    COUNT(CASE WHEN risk_level = 'High' THEN 1 END) AS high_risk_count,
    COUNT(CASE WHEN risk_level = 'Medium' THEN 1 END) AS medium_risk_count,
    COUNT(CASE WHEN risk_level = 'Low' THEN 1 END) AS low_risk_count,
    ROUND(COUNT(CASE WHEN final_result IN ('Pass', 'Distinction') THEN 1 END)::numeric / COUNT(id_student) * 100, 2) AS completion_rate_pct
FROM fact_student_learning_analytics
GROUP BY code_module, code_presentation;

-- View 2: Tổng hợp đánh giá chất lượng khóa học
CREATE OR REPLACE VIEW v_course_quality_kpi AS
SELECT 
    course_id,
    course_title,
    provider,
    category,
    COUNT(review_id) AS total_reviews,
    ROUND(AVG(rating), 2) AS avg_rating,
    ROUND(COUNT(CASE WHEN sentiment = 'Positive' THEN 1 END)::numeric / COUNT(review_id) * 100, 1) AS positive_pct,
    ROUND(COUNT(CASE WHEN sentiment = 'Neutral' THEN 1 END)::numeric / COUNT(review_id) * 100, 1) AS neutral_pct,
    ROUND(COUNT(CASE WHEN sentiment = 'Negative' THEN 1 END)::numeric / COUNT(review_id) * 100, 1) AS negative_pct
FROM fact_course_reviews
GROUP BY course_id, course_title, provider, category;

-- View 3: Nhu cầu tuyển dụng theo kỹ năng và địa điểm
CREATE OR REPLACE VIEW v_job_market_demand AS
SELECT 
    industry,
    location,
    COUNT(job_id) AS total_openings,
    ROUND(AVG(salary_min_mil), 1) AS avg_salary_min,
    ROUND(AVG(salary_max_mil), 1) AS avg_salary_max,
    COUNT(CASE WHEN is_salary_negotiable = TRUE THEN 1 END) AS negotiable_salary_count
FROM fact_job_postings
GROUP BY industry, location;

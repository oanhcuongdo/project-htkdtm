-- =============================================================================
-- SQL ETL PIPELINE: STAGING (public.*) -> DATA WAREHOUSE STAR SCHEMA (dw.*)
-- HỆ THỐNG QUẢN LÝ ĐÀO TẠO THÔNG MINH - LỚP 65HTTT (NHÓM 05)
-- PHỤ TRÁCH: Nguyễn Quang Đức (Data Warehouse & BI)
-- =============================================================================

BEGIN;

-- 1. Nạp Dim_Date (từ 2025-01-01 đến 2027-12-31)
INSERT INTO dw.dim_date (
    date_key, full_date, year, quarter, month, month_name,
    year_month, week_of_year, day_of_month, day_of_week, is_weekend
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT AS date_key,
    d::DATE AS full_date,
    EXTRACT(YEAR FROM d)::SMALLINT AS year,
    EXTRACT(QUARTER FROM d)::SMALLINT AS quarter,
    EXTRACT(MONTH FROM d)::SMALLINT AS month,
    TO_CHAR(d, 'TMMonth') AS month_name,
    TO_CHAR(d, 'YYYY-MM') AS year_month,
    EXTRACT(WEEK FROM d)::SMALLINT AS week_of_year,
    EXTRACT(DAY FROM d)::SMALLINT AS day_of_month,
    EXTRACT(ISODOW FROM d)::SMALLINT AS day_of_week,
    (EXTRACT(ISODOW FROM d) IN (6, 7)) AS is_weekend
FROM generate_series('2025-01-01'::DATE, '2027-12-31'::DATE, '1 day'::INTERVAL) AS d
ON CONFLICT (date_key) DO NOTHING;

-- 2. Nạp Dim_Semester từ dim_course (OULAD)
INSERT INTO dw.dim_semester (code_presentation, academic_year, semester_term, semester_label)
SELECT DISTINCT
    code_presentation,
    LEFT(code_presentation, 4)::SMALLINT AS academic_year,
    CASE
        WHEN RIGHT(code_presentation, 1) = 'B' THEN 'Spring (Feb)'
        WHEN RIGHT(code_presentation, 1) = 'J' THEN 'Fall (Oct)'
        ELSE 'Other'
    END AS semester_term,
    'HK ' || LEFT(code_presentation, 4) || ' - ' ||
    CASE
        WHEN RIGHT(code_presentation, 1) = 'B' THEN 'Đợt B (Xuân)'
        WHEN RIGHT(code_presentation, 1) = 'J' THEN 'Đợt J (Thu)'
        ELSE RIGHT(code_presentation, 1)
    END AS semester_label
FROM public.dim_course
ON CONFLICT (code_presentation) DO NOTHING;

-- 3. Nạp Dim_Provider
INSERT INTO dw.dim_provider (provider_name, platform_type)
SELECT DISTINCT
    COALESCE(NULLIF(TRIM(provider), ''), 'Unknown') AS provider_name,
    'MOOC / Online Course' AS platform_type
FROM public.fact_course_reviews
UNION
SELECT 'Open University (OULAD)', 'University LMS'
ON CONFLICT (provider_name) DO NOTHING;

-- 4. Nạp Dim_Course (hợp nhất từ OULAD dim_course và Course Reviews)
INSERT INTO dw.dim_course (
    course_code, source_system, code_module, code_presentation,
    course_title, provider_name, category, module_length_days
)
SELECT
    code_module || '-' || code_presentation AS course_code,
    'OULAD' AS source_system,
    code_module,
    code_presentation,
    'OULAD Module ' || code_module || ' (' || code_presentation || ')' AS course_title,
    'Open University (OULAD)' AS provider_name,
    'University STEM / Academic' AS category,
    module_presentation_length
FROM public.dim_course
ON CONFLICT (course_code) DO UPDATE SET
    module_length_days = EXCLUDED.module_length_days;

INSERT INTO dw.dim_course (
    course_code, source_system, code_module, code_presentation,
    course_title, provider_name, category, module_length_days
)
SELECT DISTINCT ON (course_id)
    course_id AS course_code,
    'COURSE_REVIEWS' AS source_system,
    NULL AS code_module,
    NULL AS code_presentation,
    course_title,
    COALESCE(NULLIF(TRIM(provider), ''), 'Unknown') AS provider_name,
    COALESCE(NULLIF(TRIM(category), ''), 'General') AS category,
    NULL AS module_length_days
FROM public.fact_course_reviews
ON CONFLICT (course_code) DO UPDATE SET
    course_title = EXCLUDED.course_title,
    provider_name = EXCLUDED.provider_name,
    category = EXCLUDED.category;

-- 5. Nạp Dim_Student
INSERT INTO dw.dim_student (
    id_student, gender, region, highest_education, imd_band, age_band, disability
)
SELECT DISTINCT ON (id_student)
    id_student,
    gender,
    region,
    highest_education,
    imd_band,
    age_band,
    disability
FROM public.dim_student
UNION
SELECT DISTINCT ON (id_student)
    id_student,
    gender,
    region,
    highest_education,
    NULL AS imd_band,
    age_band,
    NULL AS disability
FROM public.fact_student_learning_analytics
WHERE id_student NOT IN (SELECT id_student FROM public.dim_student)
ON CONFLICT (id_student) DO NOTHING;

-- 6. Nạp Dim_Assessment
INSERT INTO dw.dim_assessment (
    id_assessment, code_module, code_presentation, assessment_type, due_day, weight
)
SELECT
    id_assessment,
    code_module,
    code_presentation,
    COALESCE(assessment_type, 'Unknown'),
    date,
    weight
FROM public.dim_assessment
ON CONFLICT (id_assessment) DO NOTHING;

-- 7. Nạp Dim_Industry (từ VietJobs & WEF)
INSERT INTO dw.dim_industry (industry_name, sector_group)
SELECT DISTINCT
    COALESCE(NULLIF(TRIM(industry), ''), 'Khác') AS industry_name,
    CASE
        WHEN industry ILIKE '%AI%' OR industry ILIKE '%Dữ liệu%' OR industry ILIKE '%Phần mềm%' THEN 'Công nghệ & Dữ liệu'
        WHEN industry ILIKE '%Fintech%' OR industry ILIKE '%Ngân hàng%' THEN 'Tài chính - Ngân hàng'
        WHEN industry ILIKE '%Thương mại%' OR industry ILIKE '%Marketing%' THEN 'Kinh doanh & Số hóa'
        ELSE 'Ngành nghề khác'
    END AS sector_group
FROM public.fact_job_postings
UNION
SELECT DISTINCT
    COALESCE(NULLIF(TRIM(primary_sector), ''), 'Cross-Industry') AS industry_name,
    'Xu hướng quốc tế (WEF)' AS sector_group
FROM public.wef_global_trends
ON CONFLICT (industry_name) DO NOTHING;

-- 8. Nạp Dim_Location
INSERT INTO dw.dim_location (location_name, region_group)
SELECT DISTINCT
    location AS location_name,
    CASE
        WHEN location ILIKE '%Hà Nội%' OR location ILIKE '%Hải Phòng%' THEN 'Miền Bắc'
        WHEN location ILIKE '%Hồ Chí Minh%' OR location ILIKE '%Bình Dương%' OR location ILIKE '%Cần Thơ%' THEN 'Miền Nam'
        WHEN location ILIKE '%Đà Nẵng%' OR location ILIKE '%Huế%' THEN 'Miền Trung'
        ELSE 'Remote / Khác'
    END AS region_group
FROM public.fact_job_postings
ON CONFLICT (location_name) DO NOTHING;

-- 9. Nạp Dim_Skill (tách chuỗi required_skills từ VietJobs)
INSERT INTO dw.dim_skill (skill_name, skill_category)
SELECT DISTINCT
    TRIM(s.skill_item) AS skill_name,
    CASE
        WHEN TRIM(s.skill_item) ~* '(AI|Machine Learning|Deep Learning|PyTorch|TensorFlow|NLP|Scikit|Data|Analytics|LLM|Spark|Hadoop|Airflow)' THEN 'AI & Data Engineering'
        WHEN TRIM(s.skill_item) ~* '(SQL|PostgreSQL|MySQL|MongoDB|Power BI|Superset|Tableau|Warehouse|ETL|Modeling)' THEN 'Database & BI'
        WHEN TRIM(s.skill_item) ~* '(AWS|Azure|GCP|Docker|Kubernetes|DevOps|CI/CD|Linux)' THEN 'Cloud & DevOps'
        WHEN TRIM(s.skill_item) ~* '(Python|Java|JavaScript|TypeScript|Django|React|Node|Go|C\+\+|FastAPI)' THEN 'Programming & Backend'
        ELSE 'Kỹ năng chuyên môn khác'
    END AS skill_category
FROM public.fact_job_postings j,
LATERAL unnest(string_to_array(COALESCE(j.required_skills, ''), ',')) AS s(skill_item)
WHERE TRIM(s.skill_item) <> ''
ON CONFLICT (skill_name) DO NOTHING;

-- 10. Nạp Fact_KetQuaHocTap
INSERT INTO dw.fact_ket_qua_hoc_tap (
    student_sk, course_sk, semester_sk,
    num_of_prev_attempts, studied_credits, total_clicks, active_days,
    avg_score, assessments_completed, final_result, is_completed, is_dropout, risk_level
)
SELECT
    ds.student_sk,
    dc.course_sk,
    dsem.semester_sk,
    COALESCE(st.num_of_prev_attempts, 0),
    COALESCE(fa.studied_credits, 0),
    COALESCE(fa.total_clicks, 0),
    COALESCE(fa.active_days, 0),
    COALESCE(fa.avg_score, 0.0),
    COALESCE(fa.assessments_completed, 0),
    fa.final_result,
    CASE WHEN fa.final_result IN ('Pass', 'Distinction') THEN 1 ELSE 0 END AS is_completed,
    CASE WHEN fa.final_result IN ('Fail', 'Withdrawn') THEN 1 ELSE 0 END AS is_dropout,
    fa.risk_level
FROM public.fact_student_learning_analytics fa
JOIN dw.dim_student ds ON ds.id_student = fa.id_student
JOIN dw.dim_course dc ON dc.course_code = fa.code_module || '-' || fa.code_presentation
JOIN dw.dim_semester dsem ON dsem.code_presentation = fa.code_presentation
LEFT JOIN public.dim_student st
    ON st.id_student = fa.id_student
   AND st.code_module = fa.code_module
   AND st.code_presentation = fa.code_presentation
ON CONFLICT (student_sk, course_sk, semester_sk) DO UPDATE SET
    total_clicks = EXCLUDED.total_clicks,
    active_days = EXCLUDED.active_days,
    avg_score = EXCLUDED.avg_score,
    risk_level = EXCLUDED.risk_level;

-- 11. Nạp Fact_Assessment_Performance
INSERT INTO dw.fact_assessment_performance (
    student_sk, assessment_sk, course_sk, date_submitted, is_banked, score, is_passed_assessment
)
SELECT
    ds.student_sk,
    da.assessment_sk,
    dc.course_sk,
    fsa.date_submitted,
    fsa.is_banked,
    fsa.score,
    CASE WHEN COALESCE(fsa.score, 0) >= 40 THEN 1 ELSE 0 END AS is_passed_assessment
FROM public.fact_student_assessment fsa
JOIN dw.dim_student ds ON ds.id_student = fsa.id_student
JOIN dw.dim_assessment da ON da.id_assessment = fsa.id_assessment
JOIN dw.dim_course dc ON dc.course_code = da.code_module || '-' || da.code_presentation
ON CONFLICT (student_sk, assessment_sk) DO NOTHING;

-- 12. Nạp Fact_Course_Reviews (kèm trích xuất chủ đề vấn đề)
INSERT INTO dw.fact_course_reviews (
    review_id, course_sk, provider_sk, date_key,
    rating, sentiment, sentiment_score, language, learner_level, helpful_count, issue_topic, review_text
)
SELECT
    r.review_id,
    dc.course_sk,
    dp.provider_sk,
    TO_CHAR(r.review_date, 'YYYYMMDD')::INT AS date_key,
    r.rating,
    COALESCE(r.sentiment, 'Neutral') AS sentiment,
    CASE
        WHEN r.sentiment = 'Positive' THEN 1
        WHEN r.sentiment = 'Negative' THEN -1
        ELSE 0
    END AS sentiment_score,
    r.language,
    r.learner_level,
    COALESCE(r.helpful_count, 0),
    CASE
        WHEN r.sentiment = 'Positive' THEN 'Không có vấn đề (Tích cực)'
        WHEN r.review_text ~* '(nhanh|tốc độ|vội|fast|pace)' THEN 'Tốc độ giảng nhanh'
        WHEN r.review_text ~* '(khó|phức tạp|hard|difficult|chưa rõ)' THEN 'Nội dung khó / thiếu giải thích'
        WHEN r.review_text ~* '(bài tập|thực hành|lab|assignment|project)' THEN 'Thiếu bài tập thực hành'
        WHEN r.review_text ~* '(cũ|lỗi thời|outdated|cập nhật)' THEN 'Nội dung chưa cập nhật'
        WHEN r.review_text ~* '(âm thanh|phụ đề|audio|subtitle|video)' THEN 'Chất lượng âm thanh / phụ đề'
        ELSE 'Góp ý cải thiện chung'
    END AS issue_topic,
    r.review_text
FROM public.fact_course_reviews r
JOIN dw.dim_course dc ON dc.course_code = r.course_id
JOIN dw.dim_provider dp ON dp.provider_name = COALESCE(NULLIF(TRIM(r.provider), ''), 'Unknown')
ON CONFLICT (review_id) DO NOTHING;

-- 13. Nạp Fact_Job_Postings
INSERT INTO dw.fact_job_postings (
    job_id, industry_sk, location_sk, date_key,
    job_title, company_name, salary_min_mil, salary_max_mil, salary_avg_mil,
    is_salary_negotiable, experience_level, education_level, source
)
SELECT
    j.job_id,
    di.industry_sk,
    dl.location_sk,
    TO_CHAR(j.posted_date, 'YYYYMMDD')::INT AS date_key,
    j.job_title,
    j.company_name,
    j.salary_min_mil,
    j.salary_max_mil,
    CASE
        WHEN j.salary_min_mil IS NOT NULL AND j.salary_max_mil IS NOT NULL THEN ROUND((j.salary_min_mil + j.salary_max_mil) / 2.0, 2)
        ELSE COALESCE(j.salary_min_mil, j.salary_max_mil)
    END AS salary_avg_mil,
    COALESCE(j.is_salary_negotiable, FALSE),
    j.experience_level,
    j.education_level,
    j.source
FROM public.fact_job_postings j
JOIN dw.dim_industry di ON di.industry_name = COALESCE(NULLIF(TRIM(j.industry), ''), 'Khác')
JOIN dw.dim_location dl ON dl.location_name = j.location
ON CONFLICT (job_id) DO NOTHING;

-- 14. Nạp Fact_Job_Skills (Bridge Fact)
INSERT INTO dw.fact_job_skills (job_sk, skill_sk, industry_sk, location_sk, date_key)
SELECT DISTINCT
    fjp.job_sk,
    dsk.skill_sk,
    fjp.industry_sk,
    fjp.location_sk,
    fjp.date_key
FROM public.fact_job_postings j
JOIN dw.fact_job_postings fjp ON fjp.job_id = j.job_id
CROSS JOIN LATERAL unnest(string_to_array(COALESCE(j.required_skills, ''), ',')) AS s(skill_item)
JOIN dw.dim_skill dsk ON dsk.skill_name = TRIM(s.skill_item)
WHERE TRIM(s.skill_item) <> ''
ON CONFLICT (job_sk, skill_sk) DO NOTHING;

-- 15. Nạp Fact_WEF_Trends
INSERT INTO dw.fact_wef_trends (
    trend_id, industry_sk, category, item_name,
    growth_rate_pct, global_demand_level, reskilling_months, vietnam_relevance, trend_description
)
SELECT
    w.trend_id,
    di.industry_sk,
    w.category,
    w.item_name,
    w.growth_rate_pct,
    w.global_demand_level,
    w.reskilling_months,
    w.vietnam_relevance,
    w.trend_description
FROM public.wef_global_trends w
JOIN dw.dim_industry di ON di.industry_name = COALESCE(NULLIF(TRIM(w.primary_sector), ''), 'Cross-Industry')
ON CONFLICT (trend_id) DO NOTHING;

COMMIT;

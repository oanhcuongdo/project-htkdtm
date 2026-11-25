-- =============================================================================
-- BI VIEWS - DASHBOARD 2: CHẤT LƯỢNG ĐÀO TẠO (TRAINING QUALITY)
-- PHỤ TRÁCH: Nguyễn Quang Đức (Data Warehouse & BI)
-- =============================================================================

-- 1. KPI Chất lượng đào tạo tổng quan
CREATE OR REPLACE VIEW dw.v_bi_quality_kpi AS
SELECT
    COUNT(*) AS total_reviews,
    COUNT(DISTINCT r.course_sk) AS total_reviewed_courses,
    ROUND(AVG(r.rating), 2) AS avg_course_rating,
    COUNT(*) FILTER (WHERE r.sentiment = 'Positive') AS positive_count,
    COUNT(*) FILTER (WHERE r.sentiment = 'Neutral') AS neutral_count,
    COUNT(*) FILTER (WHERE r.sentiment = 'Negative') AS negative_count,
    ROUND(COUNT(*) FILTER (WHERE r.sentiment = 'Positive') * 100.0 / NULLIF(COUNT(*), 0), 2) AS positive_pct,
    ROUND(COUNT(*) FILTER (WHERE r.sentiment = 'Neutral') * 100.0 / NULLIF(COUNT(*), 0), 2) AS neutral_pct,
    ROUND(COUNT(*) FILTER (WHERE r.sentiment = 'Negative') * 100.0 / NULLIF(COUNT(*), 0), 2) AS negative_pct
FROM dw.fact_course_reviews r;

-- 2. So sánh chất lượng giữa các nhà cung cấp / giảng viên & khóa học
CREATE OR REPLACE VIEW dw.v_bi_provider_comparison AS
SELECT
    dp.provider_name,
    dc.category,
    dc.course_title,
    COUNT(r.review_sk) AS total_reviews,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    ROUND(COUNT(*) FILTER (WHERE r.sentiment = 'Positive') * 100.0 / NULLIF(COUNT(*), 0), 2) AS positive_pct,
    ROUND(COUNT(*) FILTER (WHERE r.sentiment = 'Neutral') * 100.0 / NULLIF(COUNT(*), 0), 2) AS neutral_pct,
    ROUND(COUNT(*) FILTER (WHERE r.sentiment = 'Negative') * 100.0 / NULLIF(COUNT(*), 0), 2) AS negative_pct,
    ROUND(AVG(r.helpful_count), 1) AS avg_helpful_count
FROM dw.fact_course_reviews r
JOIN dw.dim_provider dp ON dp.provider_sk = r.provider_sk
JOIN dw.dim_course dc ON dc.course_sk = r.course_sk
GROUP BY dp.provider_name, dc.category, dc.course_title;

-- 3. Heatmap các chủ đề / bài đánh giá học viên thường làm sai hoặc gặp khó khăn
CREATE OR REPLACE VIEW dw.v_bi_difficulty_heatmap AS
SELECT
    da.code_module AS topic_module,
    da.assessment_type AS sub_dimension,
    COUNT(*) AS total_submissions,
    ROUND(AVG(fap.score), 2) AS avg_score,
    COUNT(*) FILTER (WHERE fap.is_passed_assessment = 0) AS fail_count,
    ROUND(COUNT(*) FILTER (WHERE fap.is_passed_assessment = 0) * 100.0 / NULLIF(COUNT(*), 0), 2) AS failure_rate_pct
FROM dw.fact_assessment_performance fap
JOIN dw.dim_assessment da ON da.assessment_sk = fap.assessment_sk
GROUP BY da.code_module, da.assessment_type;

-- 4. Các vấn đề thường xuất hiện trong phản hồi học viên
CREATE OR REPLACE VIEW dw.v_bi_feedback_issues AS
SELECT
    r.issue_topic,
    r.sentiment,
    dc.category,
    dp.provider_name,
    r.learner_level,
    r.language,
    COUNT(*) AS mention_count,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    SUM(r.helpful_count) AS total_helpful_votes
FROM dw.fact_course_reviews r
JOIN dw.dim_course dc ON dc.course_sk = r.course_sk
JOIN dw.dim_provider dp ON dp.provider_sk = r.provider_sk
GROUP BY
    r.issue_topic, r.sentiment, dc.category,
    dp.provider_name, r.learner_level, r.language;

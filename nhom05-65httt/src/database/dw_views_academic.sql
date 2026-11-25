-- =============================================================================
-- BI VIEWS - DASHBOARD 1: QUẢN LÝ HỌC VỤ (ACADEMIC MANAGEMENT)
-- PHỤ TRÁCH: Nguyễn Quang Đức (Data Warehouse & BI)
-- =============================================================================

-- 1. KPI Tổng quan Quản lý học vụ (Big Numbers)
CREATE OR REPLACE VIEW dw.v_bi_academic_kpi AS
SELECT
    COUNT(*) AS total_enrollments,
    COUNT(DISTINCT f.student_sk) AS total_unique_students,
    SUM(f.is_completed) AS completed_count,
    SUM(f.is_dropout) AS not_completed_count,
    ROUND(AVG(f.is_completed) * 100.0, 2) AS completion_rate_pct,
    ROUND(AVG(f.is_dropout) * 100.0, 2) AS non_completion_rate_pct,
    COUNT(*) FILTER (WHERE f.risk_level = 'High') AS high_risk_students,
    COUNT(*) FILTER (WHERE f.risk_level = 'Medium') AS medium_risk_students,
    COUNT(*) FILTER (WHERE f.risk_level = 'Low') AS low_risk_students,
    ROUND(AVG(f.avg_score), 2) AS overall_avg_score,
    ROUND(AVG(f.total_clicks), 1) AS overall_avg_clicks
FROM dw.fact_ket_qua_hoc_tap f;

-- 2. Funnel Chart: Tỷ lệ học viên duy trì / rời bỏ qua từng giai đoạn học tập
CREATE OR REPLACE VIEW dw.v_bi_academic_funnel AS
WITH base AS (
    SELECT
        COUNT(*) AS stage1_enrolled,
        COUNT(*) FILTER (WHERE total_clicks > 0 AND active_days > 0) AS stage2_active_vle,
        COUNT(*) FILTER (WHERE assessments_completed >= 3) AS stage3_submitted_assessments,
        COUNT(*) FILTER (WHERE is_completed = 1) AS stage4_completed_course
    FROM dw.fact_ket_qua_hoc_tap
)
SELECT 1 AS stage_order, '1. Đã đăng ký khóa học' AS stage_name, stage1_enrolled AS student_count, 100.00 AS retention_pct FROM base
UNION ALL
SELECT 2, '2. Có tương tác VLE', stage2_active_vle, ROUND(stage2_active_vle * 100.0 / NULLIF(stage1_enrolled, 0), 2) FROM base
UNION ALL
SELECT 3, '3. Nộp >= 3 bài đánh giá', stage3_submitted_assessments, ROUND(stage3_submitted_assessments * 100.0 / NULLIF(stage1_enrolled, 0), 2) FROM base
UNION ALL
SELECT 4, '4. Hoàn thành khóa học (Pass/Distinction)', stage4_completed_course, ROUND(stage4_completed_course * 100.0 / NULLIF(stage1_enrolled, 0), 2) FROM base;

-- 3. Danh sách học viên có nguy cơ không hoàn thành khóa học (Early Warning Table)
CREATE OR REPLACE VIEW dw.v_bi_high_risk_students AS
SELECT
    ds.id_student,
    dc.code_module,
    dc.code_presentation,
    dsem.semester_label,
    ds.gender,
    ds.age_band,
    ds.region,
    ds.highest_education,
    f.total_clicks,
    f.active_days,
    f.assessments_completed,
    f.avg_score,
    f.final_result,
    f.risk_level
FROM dw.fact_ket_qua_hoc_tap f
JOIN dw.dim_student ds ON ds.student_sk = f.student_sk
JOIN dw.dim_course dc ON dc.course_sk = f.course_sk
JOIN dw.dim_semester dsem ON dsem.semester_sk = f.semester_sk
ORDER BY
    CASE f.risk_level
        WHEN 'High' THEN 1
        WHEN 'Medium' THEN 2
        ELSE 3
    END,
    f.avg_score ASC,
    f.total_clicks ASC;

-- 4. Thống kê kết quả học tập theo học phần & học kỳ
CREATE OR REPLACE VIEW dw.v_bi_learning_outcomes_by_course AS
SELECT
    dc.code_module,
    dc.code_presentation,
    dsem.semester_label,
    f.final_result,
    f.risk_level,
    ds.age_band,
    ds.highest_education,
    COUNT(*) AS student_count,
    ROUND(AVG(f.avg_score), 2) AS avg_score,
    ROUND(AVG(f.total_clicks), 1) AS avg_clicks,
    ROUND(AVG(f.active_days), 1) AS avg_active_days
FROM dw.fact_ket_qua_hoc_tap f
JOIN dw.dim_course dc ON dc.course_sk = f.course_sk
JOIN dw.dim_semester dsem ON dsem.semester_sk = f.semester_sk
JOIN dw.dim_student ds ON ds.student_sk = f.student_sk
GROUP BY
    dc.code_module, dc.code_presentation, dsem.semester_label,
    f.final_result, f.risk_level, ds.age_band, ds.highest_education;

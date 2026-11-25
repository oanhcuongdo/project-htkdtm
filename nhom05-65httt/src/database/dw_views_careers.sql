-- =============================================================================
-- BI VIEWS - DASHBOARD 3: XU HƯỚNG NGÀNH NGHỀ (CAREER & INDUSTRY TRENDS)
-- PHỤ TRÁCH: Nguyễn Quang Đức (Data Warehouse & BI)
-- =============================================================================

-- 1. Top ngành nghề có nhu cầu tuyển dụng cao & mức lương theo ngành
CREATE OR REPLACE VIEW dw.v_bi_industry_demand AS
SELECT
    di.industry_name,
    di.sector_group,
    dl.location_name,
    dl.region_group,
    fjp.experience_level,
    COUNT(fjp.job_sk) AS total_job_postings,
    ROUND(AVG(fjp.salary_min_mil), 2) AS avg_salary_min_mil,
    ROUND(AVG(fjp.salary_max_mil), 2) AS avg_salary_max_mil,
    ROUND(AVG(fjp.salary_avg_mil), 2) AS avg_salary_mid_mil,
    COUNT(*) FILTER (WHERE fjp.is_salary_negotiable) AS negotiable_count
FROM dw.fact_job_postings fjp
JOIN dw.dim_industry di ON di.industry_sk = fjp.industry_sk
JOIN dw.dim_location dl ON dl.location_sk = fjp.location_sk
GROUP BY
    di.industry_name, di.sector_group,
    dl.location_name, dl.region_group, fjp.experience_level;

-- 2. Xu hướng nhu cầu tuyển dụng theo thời gian
CREATE OR REPLACE VIEW dw.v_bi_job_trends_timeseries AS
SELECT
    dd.full_date AS posted_date,
    dd.year,
    dd.month,
    dd.year_month,
    dd.week_of_year,
    di.industry_name,
    dl.location_name,
    COUNT(fjp.job_sk) AS job_postings_count,
    ROUND(AVG(fjp.salary_avg_mil), 2) AS avg_salary_mid_mil
FROM dw.fact_job_postings fjp
JOIN dw.dim_date dd ON dd.date_key = fjp.date_key
JOIN dw.dim_industry di ON di.industry_sk = fjp.industry_sk
JOIN dw.dim_location dl ON dl.location_sk = fjp.location_sk
GROUP BY
    dd.full_date, dd.year, dd.month, dd.year_month,
    dd.week_of_year, di.industry_name, dl.location_name;

-- 3. Top kỹ năng được doanh nghiệp Việt Nam yêu cầu
CREATE OR REPLACE VIEW dw.v_bi_top_skills_demand AS
WITH total_jobs AS (
    SELECT COUNT(*) AS cnt FROM dw.fact_job_postings
)
SELECT
    dsk.skill_name,
    dsk.skill_category,
    di.industry_name,
    COUNT(DISTINCT fjs.job_sk) AS demand_job_count,
    ROUND(COUNT(DISTINCT fjs.job_sk) * 100.0 / NULLIF(MAX(tj.cnt), 0), 2) AS demand_share_pct,
    ROUND(AVG(fjp.salary_avg_mil), 2) AS avg_salary_with_skill_mil
FROM dw.fact_job_skills fjs
JOIN dw.dim_skill dsk ON dsk.skill_sk = fjs.skill_sk
JOIN dw.dim_industry di ON di.industry_sk = fjs.industry_sk
JOIN dw.fact_job_postings fjp ON fjp.job_sk = fjs.job_sk
CROSS JOIN total_jobs tj
GROUP BY dsk.skill_name, dsk.skill_category, di.industry_name;

-- 4. So sánh xu hướng nhu cầu kỹ năng giữa Việt Nam (VietJobs) và Quốc tế (WEF)
CREATE OR REPLACE VIEW dw.v_bi_vn_vs_global_trends AS
WITH vn_skills AS (
    SELECT
        dsk.skill_name,
        dsk.skill_category,
        COUNT(DISTINCT fjs.job_sk) AS vn_job_mentions,
        ROUND(AVG(fjp.salary_avg_mil), 2) AS vn_avg_salary_mil
    FROM dw.fact_job_skills fjs
    JOIN dw.dim_skill dsk ON dsk.skill_sk = fjs.skill_sk
    JOIN dw.fact_job_postings fjp ON fjp.job_sk = fjs.job_sk
    GROUP BY dsk.skill_name, dsk.skill_category
)
SELECT
    w.trend_id,
    w.category AS wef_category,
    w.item_name AS global_trend_item,
    di.industry_name AS primary_sector,
    w.growth_rate_pct AS global_growth_rate_pct,
    w.global_demand_level,
    w.reskilling_months,
    w.vietnam_relevance,
    COALESCE(SUM(vn.vn_job_mentions), 0) AS vn_related_job_mentions,
    ROUND(AVG(vn.vn_avg_salary_mil), 2) AS vn_related_avg_salary_mil
FROM dw.fact_wef_trends w
JOIN dw.dim_industry di ON di.industry_sk = w.industry_sk
LEFT JOIN vn_skills vn
    ON w.item_name ILIKE '%' || vn.skill_name || '%'
    OR w.trend_description ILIKE '%' || vn.skill_name || '%'
GROUP BY
    w.trend_id, w.category, w.item_name, di.industry_name,
    w.growth_rate_pct, w.global_demand_level, w.reskilling_months, w.vietnam_relevance;

-- KPI-07: Độ lệch báo chí và người học
-- Công thức: SI_bao_chi - SI_nguoi_hoc
-- Quy ước tạm cùng nhãn điểm sao; Kỳ tính: tuần/tháng/quý
-- Nguồn: dw.dim_source.source_type, dw.fact_review, dw.dim_platform, dw.dim_time

WITH base AS (
    SELECT date_trunc('month', dt.full_date)::date AS ky,
           dp.platform_name,
           ds.source_type,
           COUNT(*) AS tong,
           COUNT(*) FILTER (WHERE fr.rating BETWEEN 4 AND 5) AS p,
           COUNT(*) FILTER (WHERE fr.rating BETWEEN 1 AND 2) AS n
    FROM dw.fact_review fr
    JOIN dw.dim_time dt ON dt.time_key = fr.time_key
    JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
    JOIN dw.dim_source ds ON ds.source_key = fr.source_key
    WHERE fr.rating IS NOT NULL
    GROUP BY 1, 2, 3
)
SELECT ky, platform_name,
       ROUND(COALESCE(MAX(CASE WHEN source_type = 'bao_chi'
           THEN 100.0 * (p - n) / NULLIF(tong, 0) END), 0)
       - COALESCE(MAX(CASE WHEN source_type IN ('kho_ung_dung', 'youtube', 'khac')
           THEN 100.0 * (p - n) / NULLIF(tong, 0) END), 0), 2)
       AS do_lech_bao_chi_nguoi_hoc
FROM base
GROUP BY ky, platform_name
ORDER BY ky, platform_name;

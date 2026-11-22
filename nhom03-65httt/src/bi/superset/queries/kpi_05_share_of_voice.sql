-- KPI-05: Tỷ trọng đánh giá (Share of Voice)
-- Công thức: 100 * số đánh giá nền tảng / tổng số đánh giá các nền tảng trong kỳ
-- Đơn vị: %; Kỳ tính: ngày/tuần/tháng/quý/năm

WITH count_per_platform AS (
    SELECT dt.full_date, dp.platform_name, COUNT(*) AS so_danh_gia
    FROM dw.fact_review fr
    JOIN dw.dim_time dt ON dt.time_key = fr.time_key
    JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
    WHERE dt.full_date >= COALESCE(CAST('{{ from_dttm }}' AS date), DATE '1900-01-01')
      AND dt.full_date < COALESCE(CAST('{{ to_dttm }}' AS date) + 1, DATE '2100-01-01')
    GROUP BY dt.full_date, dp.platform_name
)
SELECT full_date, platform_name, so_danh_gia,
       ROUND(100.0 * so_danh_gia /
             NULLIF(SUM(so_danh_gia) OVER (PARTITION BY full_date), 0), 2) AS share_of_voice_pct
FROM count_per_platform
ORDER BY full_date, platform_name;

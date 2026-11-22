-- KPI-09: Số kỳ bất thường
-- Công thức: bất thường khi SI hiện tại > average(SI 8 kỳ trước) + 2 * stddev(SI 8 kỳ trước)
-- Đơn vị: số kỳ; Kỳ tính: hai tuần
-- SI tạm quy đổi từ điểm sao: 4-5 tích cực, 3 trung tính, 1-2 tiêu cực

WITH weekly AS (
    SELECT date_trunc('week', dt.full_date)::date AS ky,
           dp.platform_name,
           COUNT(*) AS tong,
           COUNT(*) FILTER (WHERE fr.rating BETWEEN 4 AND 5) AS p,
           COUNT(*) FILTER (WHERE fr.rating BETWEEN 1 AND 2) AS n
    FROM dw.fact_review fr
    JOIN dw.dim_time dt ON dt.time_key = fr.time_key
    JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
    WHERE fr.rating IS NOT NULL
    GROUP BY 1, 2
), si AS (
    SELECT *, ROUND(100.0 * (p - n) / NULLIF(tong, 0), 2) AS sentiment_index
    FROM weekly
), with_baseline AS (
    SELECT *,
           AVG(sentiment_index) OVER (
               PARTITION BY platform_name ORDER BY ky
               ROWS BETWEEN 8 PRECEDING AND 1 PRECEDING
           ) AS mean_8,
           STDDEV_SAMP(sentiment_index) OVER (
               PARTITION BY platform_name ORDER BY ky
               ROWS BETWEEN 8 PRECEDING AND 1 PRECEDING
           ) AS stddev_8
    FROM si
)
SELECT ky, platform_name, sentiment_index,
       ROUND(COALESCE(mean_8, sentiment_index) + 2 * COALESCE(stddev_8, 0), 2) AS nguong,
       CASE WHEN sentiment_index > COALESCE(mean_8, sentiment_index)
                                      + 2 * COALESCE(stddev_8, 0)
            THEN 1 ELSE 0 END AS la_ky_bat_thuong
FROM with_baseline
ORDER BY ky DESC, platform_name;

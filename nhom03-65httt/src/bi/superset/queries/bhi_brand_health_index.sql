-- BHI: Brand Health Index
-- Công thức: 0.6 * [50 + SI / 2] + 0.4 * [(AVG(rating) - 1) / 4 * 100]
-- Trọng số 60% cảm xúc và 40% sao là đề xuất theo đề cương, cần nhóm duyệt
-- Đơn vị: điểm 0-100; Kỳ tính: ngày/tuần/tháng/quý/năm
-- Quy ước tạm: 4-5 sao tích cực, 3 sao trung tính, 1-2 sao tiêu cực

WITH metrics AS (
    SELECT dt.full_date, dp.platform_name,
           COUNT(*) AS tong,
           COUNT(*) FILTER (WHERE fr.rating BETWEEN 4 AND 5) AS p,
           COUNT(*) FILTER (WHERE fr.rating BETWEEN 1 AND 2) AS n,
           AVG(fr.rating)::numeric AS rating_tb
    FROM dw.fact_review fr
    JOIN dw.dim_time dt ON dt.time_key = fr.time_key
    JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
    WHERE fr.rating IS NOT NULL
      AND dt.full_date >= COALESCE(CAST('{{ from_dttm }}' AS date), DATE '1900-01-01')
      AND dt.full_date < COALESCE(CAST('{{ to_dttm }}' AS date) + 1, DATE '2100-01-01')
    GROUP BY dt.full_date, dp.platform_name
), calc AS (
    SELECT *,
           100.0 * (p - n) / NULLIF(tong, 0) AS sentiment_index,
           ((COALESCE(rating_tb, 1) - 1) / 4.0 * 100.0) AS rating_component
    FROM metrics
)
SELECT full_date, platform_name, tong,
       ROUND(sentiment_index, 2) AS sentiment_index,
       ROUND(0.6 * (50 + sentiment_index / 2)
             + 0.4 * rating_component, 2) AS bhi
FROM calc
ORDER BY full_date, platform_name;

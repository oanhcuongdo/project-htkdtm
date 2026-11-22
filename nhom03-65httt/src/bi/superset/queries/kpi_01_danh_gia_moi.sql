-- KPI-01: Số đánh giá mới
-- Công thức: COUNT(dw.fact_review.review_key)
-- Đơn vị: đánh giá; Kỳ tính: ngày/tuần/tháng/quý/năm
-- Nguồn: dw.fact_review, dw.dim_time, dw.dim_platform, dw.dim_source

SELECT dt.full_date,
       dp.platform_name,
       ds.source_name,
       COUNT(fr.review_key) AS so_danh_gia_moi
FROM dw.fact_review fr
JOIN dw.dim_time dt ON dt.time_key = fr.time_key
JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
JOIN dw.dim_source ds ON ds.source_key = fr.source_key
WHERE dt.full_date >= COALESCE(CAST('{{ from_dttm }}' AS date), DATE '1900-01-01')
  AND dt.full_date < COALESCE(CAST('{{ to_dttm }}' AS date) + 1, DATE '2100-01-01')
GROUP BY dt.full_date, dp.platform_name, ds.source_name
ORDER BY dt.full_date, dp.platform_name, ds.source_name;

-- KPI-08: Độ chính xác dự báo
-- Công thức: MAE = AVG(ABS(actual - forecast)); tỷ lệ đúng chiều = số kỳ dự đoán đúng chiều / N * 100
-- Đơn vị: MAE bằng điểm SI, tỷ lệ đúng chiều bằng %; Kỳ tính: tháng
-- CHƯA CÓ fact_forecast trong schema lõi nên truy vấn này chỉ tổng hợp chuỗi SI lịch sử;
-- Không bịa MAE hoặc tỷ lệ đúng chiều khi chưa có actual và forecast.

SELECT date_trunc('month', dt.full_date)::date AS ky,
       dp.platform_name,
       COUNT(*) AS tong_danh_gia_co_sao,
       ROUND(100.0 * (
           COUNT(*) FILTER (WHERE fr.rating BETWEEN 4 AND 5)
           - COUNT(*) FILTER (WHERE fr.rating BETWEEN 1 AND 2)
       ) / NULLIF(COUNT(*), 0), 2) AS actual_si_tam
FROM dw.fact_review fr
JOIN dw.dim_time dt ON dt.time_key = fr.time_key
JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
WHERE fr.rating IS NOT NULL
GROUP BY 1, 2
ORDER BY ky, platform_name;

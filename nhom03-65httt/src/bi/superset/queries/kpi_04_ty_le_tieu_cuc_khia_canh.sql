-- KPI-04: Tỷ lệ tiêu cực theo khía cạnh
-- Công thức: 100 * đánh giá tiêu cực của khía cạnh / đánh giá nhắc đến khía cạnh
-- Đơn vị: %; Kỳ tính: tuần/tháng/quý
-- KHÔNG THỂ TÍNH ĐẦY ĐỦ: schema lõi chưa có bảng kết quả ABSA/cảm xúc theo khía cạnh.
-- Không bịa bảng, cột hoặc số liệu. Mẫu dưới đây chỉ xác nhận grain nền tảng-kỳ hiện có.

SELECT date_trunc('month', dt.full_date)::date AS ky,
       dp.platform_name,
       CAST(NULL AS text) AS khia_canh,
       CAST(NULL AS bigint) AS so_danh_gia_nhac_den,
       CAST(NULL AS bigint) AS so_danh_gia_tieu_cuc,
       CAST(NULL AS numeric) AS ty_le_tieu_cuc_pct
FROM dw.fact_review fr
JOIN dw.dim_time dt ON dt.time_key = fr.time_key
JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
WHERE FALSE
GROUP BY date_trunc('month', dt.full_date), dp.platform_name;

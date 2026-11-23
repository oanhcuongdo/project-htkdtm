-- KPI-06: Tỷ lệ lệch pha
-- Công thức: 100 * (đánh giá 4-5 sao nhưng nhãn tiêu cực + đánh giá 1-2 sao nhưng nhãn tích cực) / tổng đánh giá
-- Đơn vị: %; Kỳ tính: tuần/tháng/quý/năm
-- CHƯA THỂ ĐỊNH NGHĨA THEO NHÃN MÔ HÌNH: bảng nhãn AI chưa có trong schema lõi.
-- Khi bảng nhãn được bổ sung, thay CASE dưới đây bằng cột nhãn cảm xúc thực.

SELECT dt.full_date, dp.platform_name,
       COUNT(*) AS tong_danh_gia,
       CAST(NULL AS numeric) AS ty_le_lech_pha_pct,
       'Cho bảng nhãn cảm xúc mô hình' AS ghi_chu
FROM dw.fact_review fr
JOIN dw.dim_time dt ON dt.time_key = fr.time_key
JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
WHERE fr.rating IS NULL
GROUP BY dt.full_date, dp.platform_name;

-- KPI-02: Tỷ lệ tích cực, trung tính, tiêu cực
-- Công thức: 100 * số đánh giá theo nhãn / tổng đánh giá có rating
-- Quy ước tạm trong khi chưa có bảng nhãn mô hình: 4-5 sao tích cực, 3 sao trung tính, 1-2 sao tiêu cực
-- Đơn vị: %; Kỳ tính: ngày/tuần/tháng/quý/năm
-- Chỉ dùng bảng/cột có trong 01_schema_core.sql

WITH base AS (
    SELECT dt.full_date, dp.platform_name,
           CASE WHEN fr.rating BETWEEN 4 AND 5 THEN 'tich_cuc'
                WHEN fr.rating = 3 THEN 'trung_tinh'
                WHEN fr.rating BETWEEN 1 AND 2 THEN 'tieu_cuc'
           END AS nhan_tam
    FROM dw.fact_review fr
    JOIN dw.dim_time dt ON dt.time_key = fr.time_key
    JOIN dw.dim_platform dp ON dp.platform_key = fr.platform_key
    WHERE fr.rating IS NOT NULL
      AND dt.full_date >= COALESCE(CAST('{{ from_dttm }}' AS date), DATE '1900-01-01')
      AND dt.full_date < COALESCE(CAST('{{ to_dttm }}' AS date) + 1, DATE '2100-01-01')
)
SELECT full_date, platform_name,
       ROUND(100.0 * COUNT(*) FILTER (WHERE nhan_tam = 'tich_cuc') / NULLIF(COUNT(*), 0), 2) AS ty_le_tich_cuc_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE nhan_tam = 'trung_tinh') / NULLIF(COUNT(*), 0), 2) AS ty_le_trung_tinh_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE nhan_tam = 'tieu_cuc') / NULLIF(COUNT(*), 0), 2) AS ty_le_tieu_cuc_pct
FROM base
GROUP BY full_date, platform_name
ORDER BY full_date, platform_name;

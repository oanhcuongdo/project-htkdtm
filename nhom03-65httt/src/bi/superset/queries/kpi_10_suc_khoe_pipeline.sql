-- KPI-10: Sức khỏe pipeline
-- Công thức: bản ghi thành công mỗi ngày; tỷ lệ lỗi; thời điểm chạy gần nhất
-- Đơn vị: bản ghi/ngày, %, timestamptz
-- KHÔNG CÓ BẢNG NHẬT KÝ ETL TRONG SCHEMA LÕI.
-- Truy vấn dưới đây chỉ có thể chọn raw.review_raw.crawled_at để biểu diễn
-- thời điểm thu thập, nhưng không chứng minh trạng thái thành công/lỗi của pipeline.

SELECT CAST(crawled_at AS date) AS ngay,
       COUNT(*) AS so_ban_ghi_thu_thap_tho,
       CAST(NULL AS numeric) AS ty_le_loi_pct,
       MAX(crawled_at) AS thoi_diem_chay_gan_nhat,
       'Can bang log ETL chua co trong 01_schema_core.sql' AS ghi_chu
FROM raw.review_raw
WHERE crawled_at IS NOT NULL
GROUP BY CAST(crawled_at AS date)
ORDER BY ngay DESC;

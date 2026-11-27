-- EduVision BI - Nhóm 03: đánh dấu cảnh báo đã gửi email (workflow n8n, T8b).
-- Chạy sau 04_schema_results.sql. Chạy lại nhiều lần không lỗi.
-- Dùng cột riêng thay vì đổi dw.fact_alert.status: website vẫn thấy cảnh báo "moi" sau khi đã gửi email,
-- còn n8n chỉ gửi các cảnh báo notified_at IS NULL nên không gửi lặp.
ALTER TABLE dw.fact_alert ADD COLUMN IF NOT EXISTS notified_at timestamptz;
COMMENT ON COLUMN dw.fact_alert.notified_at IS 'Thời điểm n8n gửi email cảnh báo; rỗng nghĩa là chưa gửi. Không ảnh hưởng status (moi, dang_xu_ly, da_xu_ly)';
CREATE INDEX IF NOT EXISTS ix_fact_alert_unnotified ON dw.fact_alert (alert_key) WHERE notified_at IS NULL;

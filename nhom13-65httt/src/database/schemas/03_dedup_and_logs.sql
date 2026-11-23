-- ==========================================================
-- 03_dedup_and_logs.sql: Bảng quản lý khử trùng và nhật ký AI
-- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
-- Nhóm: nhom13-65httt
-- ==========================================================

-- 1. BẢNG NHẬT KÝ KHỬ TRÙNG LẶP (LOG_DEDUP)
CREATE TABLE IF NOT EXISTS log_dedup (
    log_id BIGSERIAL PRIMARY KEY,
    master_transaction_id BIGINT NOT NULL,   -- ID bản ghi chính được giữ lại
    duplicate_record_id BIGINT NOT NULL,     -- ID bản ghi bị phát hiện trùng và loại bỏ
    applied_rule VARCHAR(50) NOT NULL,       -- EXACT_REF_CODE, FUZZY_TIME_AMOUNT_NAME
    similarity_score NUMERIC(5, 4) DEFAULT 1.0, -- Điểm tương đồng Jaro-Winkler hoặc Levenshtein
    reason TEXT NOT NULL,                    -- Diễn giải chi tiết lý do gộp dữ liệu
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. BẢNG LƯU TRỮ DỰ BÁO DÒNG TIỀN TỪ MÔ HÌNH AI (AI_SPENDING_FORECAST)
CREATE TABLE IF NOT EXISTS ai_spending_forecast (
    forecast_id BIGSERIAL PRIMARY KEY,
    forecast_date DATE NOT NULL,             -- Ngày được dự báo
    category_id INT REFERENCES dim_category(category_id), -- Dự báo theo từng danh mục hoặc NULL (tổng thể)
    predicted_amount NUMERIC(15, 2) NOT NULL,-- Chi tiêu dự báo (dương)
    lower_bound NUMERIC(15, 2) NOT NULL,     -- Khoảng tin cậy cận dưới 95%
    upper_bound NUMERIC(15, 2) NOT NULL,     -- Khoảng tin cậy cận trên 95%
    model_version VARCHAR(50) DEFAULT 'Prophet_v1.0',
    run_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. BẢNG THEO DÕI TIẾN TRÌNH VẬN HÀNH PIPELINE (PIPELINE_EXECUTION_LOGS)
CREATE TABLE IF NOT EXISTS pipeline_execution_logs (
    log_id BIGSERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,     -- Ingestion_Email, Ingestion_Statement, AI_Forecast...
    status VARCHAR(30) NOT NULL,             -- SUCCESS, FAILED, RUNNING
    records_processed INT DEFAULT 0,
    records_failed INT DEFAULT 0,
    duration_seconds NUMERIC(8, 2),
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_log_dedup_master ON log_dedup(master_transaction_id);
CREATE INDEX IF NOT EXISTS idx_forecast_date ON ai_spending_forecast(forecast_date);
CREATE INDEX IF NOT EXISTS idx_pipeline_name_status ON pipeline_execution_logs(pipeline_name, status);

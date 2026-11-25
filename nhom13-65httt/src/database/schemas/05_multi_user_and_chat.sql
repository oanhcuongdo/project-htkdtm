-- ==========================================================
-- 05_multi_user_and_chat.sql: Mở rộng Đa người dùng, Đối tác nhận tiền & Chat AI
-- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
-- Nhóm: nhom13-65httt
-- ==========================================================

-- 1. BẢNG NGƯỜI DÙNG (USERS)
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tạo tài khoản Demo mặc định (user_id = 1, mật khẩu: Demo@123 - hash tự đồng bộ khi backend khởi động)
INSERT INTO users (user_id, email, password_hash, full_name, is_active)
VALUES (1, 'demo@finance.local', 'PENDING_INIT', 'Tài khoản Demo (Nhóm 13)', TRUE)
ON CONFLICT (email) DO NOTHING;

SELECT setval('users_user_id_seq', GREATEST((SELECT COALESCE(MAX(user_id), 1) FROM users), 1));

-- 2. BẢNG CẤU HÌNH NGUỒN DỮ LIỆU NGÂN HÀNG THEO TỪNG NGƯỜI DÙNG
CREATE TABLE IF NOT EXISTS user_data_sources (
    source_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('CSV_UPLOAD', 'EMAIL_IMAP', 'TELEGRAM_OCR')),
    display_name VARCHAR(150) NOT NULL,
    config_encrypted TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, source_type)
);

-- 3. BẢNG LỊCH SỬ HỘI THOẠI CHAT AI GEMINI
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id BIGSERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(100) NOT NULL DEFAULT 'default',
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    structured_data JSONB,
    tools_used JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. BỔ SUNG CỘT CÔ LẬP NGƯỜI DÙNG (user_id) & ĐỐI TÁC NHẬN TIỀN (counterparty_*)
ALTER TABLE fact_transactions
    ADD COLUMN IF NOT EXISTS user_id INT NOT NULL DEFAULT 1 REFERENCES users(user_id),
    ADD COLUMN IF NOT EXISTS counterparty_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS counterparty_account_mask VARCHAR(50),
    ADD COLUMN IF NOT EXISTS counterparty_bank VARCHAR(100);

ALTER TABLE dim_account
    ADD COLUMN IF NOT EXISTS user_id INT NOT NULL DEFAULT 1 REFERENCES users(user_id);

ALTER TABLE ai_spending_forecast
    ADD COLUMN IF NOT EXISTS user_id INT NOT NULL DEFAULT 1 REFERENCES users(user_id);

ALTER TABLE log_dedup
    ADD COLUMN IF NOT EXISTS user_id INT NOT NULL DEFAULT 1 REFERENCES users(user_id);

-- 5. CHỈ MỤC TỐI ƯU TRUY VẤN ĐA NGƯỜI DÙNG & TOP ĐỐI TÁC NHẬN TIỀN
CREATE INDEX IF NOT EXISTS idx_fact_user_date ON fact_transactions(user_id, date_id);
CREATE INDEX IF NOT EXISTS idx_fact_user_counterparty ON fact_transactions(user_id, counterparty_name);
CREATE INDEX IF NOT EXISTS idx_account_user ON dim_account(user_id);
CREATE INDEX IF NOT EXISTS idx_forecast_user_date ON ai_spending_forecast(user_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_chat_user_created ON chat_messages(user_id, created_at DESC);

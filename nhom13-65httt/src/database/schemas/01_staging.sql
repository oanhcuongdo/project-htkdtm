-- ==========================================================
-- 01_staging.sql: Tạo các bảng tạm lưu dữ liệu thô (Staging Area)
-- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
-- Nhóm: nhom13-65httt
-- ==========================================================

-- Bảng 1: Lưu trữ email biến động số dư thô từ Gmail API / IMAP
CREATE TABLE IF NOT EXISTS stg_raw_emails (
    id BIGSERIAL PRIMARY KEY,
    message_id VARCHAR(255) UNIQUE NOT NULL,
    sender VARCHAR(255) NOT NULL,
    subject TEXT,
    body_html TEXT,
    body_text TEXT,
    received_at TIMESTAMP WITH TIME ZONE NOT NULL,
    parsed_status VARCHAR(50) DEFAULT 'PENDING', -- PENDING, PARSED, FAILED
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng 2: Lưu trữ từng dòng dữ liệu thô từ file sao kê CSV/PDF
CREATE TABLE IF NOT EXISTS stg_raw_statements (
    id BIGSERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL, -- CSV, PDF
    bank_name VARCHAR(100),
    row_number INT NOT NULL,
    raw_payload JSONB NOT NULL, -- Dữ liệu cả dòng dưới dạng JSON
    parsed_status VARCHAR(50) DEFAULT 'PENDING',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Bảng 3: Lưu trữ ảnh biên lai và kết quả OCR từ Telegram Bot
CREATE TABLE IF NOT EXISTS stg_raw_receipts (
    id BIGSERIAL PRIMARY KEY,
    telegram_file_id VARCHAR(255) NOT NULL,
    telegram_chat_id BIGINT NOT NULL,
    image_url TEXT,
    ocr_raw_text TEXT,
    extracted_amount NUMERIC(15, 2),
    extracted_date TIMESTAMP WITH TIME ZONE,
    extracted_merchant VARCHAR(255),
    parsed_status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tạo chỉ mục tìm kiếm nhanh cho staging
CREATE INDEX IF NOT EXISTS idx_stg_emails_status ON stg_raw_emails(parsed_status);
CREATE INDEX IF NOT EXISTS idx_stg_statements_status ON stg_raw_statements(parsed_status);
CREATE INDEX IF NOT EXISTS idx_stg_receipts_status ON stg_raw_receipts(parsed_status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_stg_receipts_telegram_file ON stg_raw_receipts(telegram_file_id);

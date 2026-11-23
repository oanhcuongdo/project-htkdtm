-- ==========================================================
-- 02_warehouse_star_schema.sql: Lược đồ hình sao (Star Schema)
-- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
-- Nhóm: nhom13-65httt
-- ==========================================================

-- 1. BẢNG CHIỀU THỜI GIAN (DIM_DATE)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id INT PRIMARY KEY,                 -- Định dạng số nguyên YYYYMMDDHH, ví dụ: 2026112314
    full_date DATE NOT NULL,                 -- Ngày chuẩn (YYYY-MM-DD)
    year INT NOT NULL,                       -- Năm (2024, 2025, 2026...)
    quarter INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    day INT NOT NULL CHECK (day BETWEEN 1 AND 31),
    hour INT NOT NULL CHECK (hour BETWEEN 0 AND 23),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7), -- 1: Chủ Nhật, 2: Thứ Hai...
    day_name VARCHAR(20) NOT NULL,          -- Thứ Hai, Thứ Ba...
    is_weekend BOOLEAN NOT NULL DEFAULT FALSE
);

-- 2. BẢNG CHIỀU DANH MỤC THU/CHI (DIM_CATEGORY)
CREATE TABLE IF NOT EXISTS dim_category (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,     -- Ăn uống, Tiền nhà, Xăng xe, Mua sắm...
    parent_category VARCHAR(50) NOT NULL,    -- Thiết yếu (Needs), Linh hoạt (Wants), Tiết kiệm/Đầu tư (Savings), Thu nhập (Income)
    category_type VARCHAR(20) NOT NULL CHECK (category_type IN ('INCOME', 'EXPENSE')),
    monthly_budget NUMERIC(15, 2) DEFAULT 0, -- Hạn mức ngân sách đề ra trong tháng
    icon VARCHAR(50) DEFAULT 'tag',
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. BẢNG CHIỀU TÀI KHOẢN & VÍ (DIM_ACCOUNT)
CREATE TABLE IF NOT EXISTS dim_account (
    account_id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,      -- Vietcombank Priority, MoMo Chính, Tiền mặt...
    bank_name VARCHAR(100) NOT NULL,         -- VCB, MBBank, Techcombank, MoMo, ZaloPay...
    account_number_mask VARCHAR(50),         -- Số tài khoản ẩn danh, ví dụ: '****9876'
    account_type VARCHAR(30) NOT NULL CHECK (account_type IN ('BANK', 'EWALLET', 'CASH', 'CREDIT')),
    currency VARCHAR(10) DEFAULT 'VND',
    is_active BOOLEAN DEFAULT TRUE
);

-- 4. BẢNG CHIỀU ĐƠN VỊ THỤ HƯỞNG (DIM_MERCHANT)
CREATE TABLE IF NOT EXISTS dim_merchant (
    merchant_id SERIAL PRIMARY KEY,
    merchant_name VARCHAR(150) NOT NULL,     -- Tên nhận diện: Shopee, Grab, Highlands Coffee...
    standard_name VARCHAR(150) NOT NULL,     -- Tên chuẩn hóa: CÔNG TY TNHH SHOPEE...
    default_category_id INT REFERENCES dim_category(category_id),
    website VARCHAR(255)
);

-- 5. BẢNG DỮ LIỆU FACT TRUNG TÂM (FACT_TRANSACTIONS)
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    category_id INT NOT NULL REFERENCES dim_category(category_id),
    account_id INT NOT NULL REFERENCES dim_account(account_id),
    merchant_id INT REFERENCES dim_merchant(merchant_id),
    amount NUMERIC(15, 2) NOT NULL,          -- Dương (>0) là Thu, Âm (<0) là Chi
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('INCOME', 'EXPENSE', 'TRANSFER')),
    raw_description TEXT NOT NULL,           -- Nội dung giao dịch gốc từ ngân hàng
    clean_description TEXT,                  -- Chuỗi tiếng Việt chuẩn sau khi lọc mã rác
    is_internal_transfer BOOLEAN DEFAULT FALSE, -- Cờ giao dịch chuyển tiền qua lại giữa các ví/tài khoản
    is_anomaly BOOLEAN DEFAULT FALSE,        -- Cờ cảnh báo bất thường do AI phát hiện
    anomaly_score NUMERIC(5, 4) DEFAULT 0.0, -- Điểm bất thường (0.0 đến 1.0)
    reference_code VARCHAR(100),             -- Mã giao dịch / Số FT của ngân hàng
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('EMAIL', 'CSV', 'PDF', 'TELEGRAM', 'MANUAL')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- CHỈ MỤC TỐI ƯU TRUY VẤN CHO APACHE SUPERSET
CREATE INDEX IF NOT EXISTS idx_fact_date ON fact_transactions(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_category ON fact_transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_fact_account ON fact_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_fact_merchant ON fact_transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_fact_direction ON fact_transactions(direction);
CREATE INDEX IF NOT EXISTS idx_fact_anomaly ON fact_transactions(is_anomaly) WHERE is_anomaly = TRUE;
CREATE INDEX IF NOT EXISTS idx_fact_ref_code ON fact_transactions(reference_code);
CREATE INDEX IF NOT EXISTS idx_fact_dedup ON fact_transactions(account_id, amount, date_id);

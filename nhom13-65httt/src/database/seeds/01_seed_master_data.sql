-- ==========================================================
-- 01_seed_master_data.sql: Khởi tạo dữ liệu nền tảng (Master Data)
-- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
-- Nhóm: nhom13-65httt
-- ==========================================================

-- 1. NẠP DỮ LIỆU TÀI KHOẢN & VÍ ĐIỆN TỬ (DIM_ACCOUNT)
INSERT INTO dim_account (account_id, account_name, bank_name, account_number_mask, account_type, currency, is_active)
VALUES 
    (1, 'Vietcombank Digibank (Chính)', 'VCB', '****1234', 'BANK', 'VND', TRUE),
    (2, 'MB Bank Quân Đội (Lương)', 'MBBank', '****5678', 'BANK', 'VND', TRUE),
    (3, 'Ví Điện Tử MoMo', 'MoMo', '****9999', 'EWALLET', 'VND', TRUE),
    (4, 'Tiền mặt cá nhân', 'CASH', 'N/A', 'CASH', 'VND', TRUE)
ON CONFLICT (account_id) DO NOTHING;

-- Đồng bộ lại sequence của account_id
SELECT setval('dim_account_account_id_seq', (SELECT MAX(account_id) FROM dim_account));

-- 2. NẠP CÂY DANH MỤC THU / CHI VÀ HẠN MỨC NGÂN SÁCH (DIM_CATEGORY)
INSERT INTO dim_category (category_id, category_name, parent_category, category_type, monthly_budget, icon, is_active)
VALUES 
    -- Nhóm Thiết yếu (Needs)
    (1, 'Ăn uống & Cà phê', 'Thiết yếu', 'EXPENSE', 4000000, 'utensils', TRUE),
    (2, 'Tiền thuê nhà & Phòng trọ', 'Thiết yếu', 'EXPENSE', 3500000, 'home', TRUE),
    (3, 'Điện nước & Internet', 'Thiết yếu', 'EXPENSE', 800000, 'bolt', TRUE),
    (4, 'Xăng xe & Đi lại', 'Thiết yếu', 'EXPENSE', 600000, 'gas-pump', TRUE),
    (5, 'Chăm sóc sức khỏe & Y tế', 'Thiết yếu', 'EXPENSE', 500000, 'medkit', TRUE),

    -- Nhóm Linh hoạt (Wants)
    (6, 'Mua sắm & Đồ dùng', 'Linh hoạt', 'EXPENSE', 1500000, 'shopping-bag', TRUE),
    (7, 'Giải trí & Phim ảnh', 'Linh hoạt', 'EXPENSE', 800000, 'film', TRUE),
    (8, 'Gặp gỡ bạn bè & Tiệc tùng', 'Linh hoạt', 'EXPENSE', 1200000, 'beer', TRUE),
    (9, 'Du lịch & Nghỉ dưỡng', 'Linh hoạt', 'EXPENSE', 1000000, 'plane', TRUE),

    -- Nhóm Tiết kiệm & Đầu tư (Savings)
    (10, 'Quỹ tiết kiệm dự phòng', 'Tiết kiệm / Đầu tư', 'EXPENSE', 2000000, 'piggy-bank', TRUE),
    (11, 'Chứng khoán & Tích lũy', 'Tiết kiệm / Đầu tư', 'EXPENSE', 1500000, 'chart-line', TRUE),

    -- Nhóm Thu nhập (Income)
    (12, 'Lương cố định hàng tháng', 'Thu nhập', 'INCOME', 0, 'money-bill-wave', TRUE),
    (13, 'Thưởng & Thu nhập ngoài (Freelance)', 'Thu nhập', 'INCOME', 0, 'gift', TRUE),
    (14, 'Lãi tiền gửi & Cổ tức', 'Thu nhập', 'INCOME', 0, 'hand-holding-usd', TRUE),

    -- Chuyển tiền nội bộ (Loại trừ khi tính thu/chi thực tế)
    (15, 'Chuyển tiền nội bộ giữa các ví', 'Khác', 'EXPENSE', 0, 'exchange-alt', TRUE)
ON CONFLICT (category_id) DO NOTHING;

SELECT setval('dim_category_category_id_seq', (SELECT MAX(category_id) FROM dim_category));

-- 3. NẠP DANH SÁCH ĐƠN VỊ THỤ HƯỞNG PHỔ BIẾN (DIM_MERCHANT)
INSERT INTO dim_merchant (merchant_id, merchant_name, standard_name, default_category_id, website)
VALUES 
    (1, 'Shopee', 'CÔNG TY TNHH SHOPEE', 6, 'https://shopee.vn'),
    (2, 'Lazada', 'CÔNG TY TNHH RECESS', 6, 'https://lazada.vn'),
    (3, 'Grab', 'CÔNG TY TNHH GRAB (VIỆT NAM)', 4, 'https://grab.com'),
    (4, 'Highlands Coffee', 'CÔNG TY CỔ PHẦN DỊCH VỤ CÀ PHÊ CAO NGUYÊN', 1, 'https://highlandscoffee.com.vn'),
    (5, 'Phúc Long Coffee & Tea', 'CÔNG TY CỔ PHẦN PHÚC LONG HERITAGE', 1, 'https://phuclong.com.vn'),
    (6, 'WinMart / WinMart+', 'CÔNG TY CỔ PHẦN DỊCH VỤ THƯƠNG MẠI TỔNG HỢP WINCOMMERCE', 1, 'https://winmart.vn'),
    (7, 'CGV Cinemas', 'CÔNG TY TNHH CJ CGV VIỆT NAM', 7, 'https://cgv.vn'),
    (8, 'Chủ nhà trọ (Bác Hùng)', 'Thanh toán tiền nhà định kỳ', 2, NULL),
    (9, 'Điện lực EVN', 'TỔNG CÔNG TY ĐIỆN LỰC TP HÀ NỘI', 3, 'https://evn.com.vn'),
    (10, 'Công ty Công nghệ Alpha (Nhà tuyển dụng)', 'CÔNG TY CỔ PHẦN CÔNG NGHỆ ALPHA (Trả lương)', 12, NULL)
ON CONFLICT (merchant_id) DO NOTHING;

SELECT setval('dim_merchant_merchant_id_seq', (SELECT MAX(merchant_id) FROM dim_merchant));

-- 4. TỰ ĐỘNG SINH TOÀN BỘ 8.760 GIỜ TRONG NĂM 2026 CHO BẢNG DIM_DATE
INSERT INTO dim_date (date_id, full_date, year, quarter, month, day, hour, day_of_week, day_name, is_weekend)
SELECT 
    (TO_CHAR(d, 'YYYYMMDD') || LPAD(EXTRACT(HOUR FROM d)::TEXT, 2, '0'))::INT AS date_id,
    d::DATE AS full_date,
    EXTRACT(YEAR FROM d)::INT AS year,
    EXTRACT(QUARTER FROM d)::INT AS quarter,
    EXTRACT(MONTH FROM d)::INT AS month,
    EXTRACT(DAY FROM d)::INT AS day,
    EXTRACT(HOUR FROM d)::INT AS hour,
    -- PostgreSQL: Sunday is 0 or 7, map 1: Sunday -> 7: Saturday
    EXTRACT(DOW FROM d)::INT + 1 AS day_of_week,
    CASE EXTRACT(DOW FROM d)::INT
        WHEN 0 THEN 'Chủ Nhật'
        WHEN 1 THEN 'Thứ Hai'
        WHEN 2 THEN 'Thứ Ba'
        WHEN 3 THEN 'Thứ Tư'
        WHEN 4 THEN 'Thứ Năm'
        WHEN 5 THEN 'Thứ Sáu'
        WHEN 6 THEN 'Thứ Bảy'
    END AS day_name,
    CASE WHEN EXTRACT(DOW FROM d)::INT IN (0, 6) THEN TRUE ELSE FALSE END AS is_weekend
FROM generate_series('2026-01-01 00:00:00'::TIMESTAMP, '2026-12-31 23:00:00'::TIMESTAMP, '1 hour'::INTERVAL) AS d
ON CONFLICT (date_id) DO NOTHING;

-- ==========================================================
-- 04_semantic_views.sql: Tầng ngữ nghĩa phục vụ trực tiếp Apache Superset
-- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
-- Nhóm: nhom13-65httt
-- ==========================================================

DROP VIEW IF EXISTS vw_cashflow_sankey CASCADE;
DROP VIEW IF EXISTS vw_anomaly_feed CASCADE;
DROP VIEW IF EXISTS vw_spending_heatmap CASCADE;
DROP VIEW IF EXISTS vw_category_budget_monitoring CASCADE;
DROP VIEW IF EXISTS vw_monthly_savings_rate CASCADE;
DROP VIEW IF EXISTS vw_clean_transactions CASCADE;

-- VIEW 1: Dữ liệu giao dịch sạch hoàn chỉnh (Loại trừ chuyển tiền nội bộ)
CREATE VIEW vw_clean_transactions AS
SELECT 
    f.transaction_id,
    f.amount,
    ABS(f.amount) AS abs_amount,
    f.direction,
    f.raw_description,
    COALESCE(f.clean_description, f.raw_description) AS clean_description,
    f.is_anomaly,
    f.anomaly_score,
    f.reference_code,
    f.source_type,
    f.created_at,
    -- Thuộc tính thời gian
    d.date_id,
    d.full_date,
    d.year,
    d.quarter,
    d.month,
    d.day,
    d.hour,
    d.day_of_week,
    d.day_name,
    d.is_weekend,
    -- Thuộc tính danh mục
    c.category_id,
    c.category_name,
    c.parent_category,
    c.category_type,
    c.monthly_budget,
    -- Thuộc tính tài khoản
    a.account_id,
    a.account_name,
    a.bank_name,
    a.account_type,
    -- Thuộc tính merchant
    m.merchant_id,
    COALESCE(m.merchant_name, 'Khác / Cá nhân') AS merchant_name
FROM fact_transactions f
JOIN dim_date d ON f.date_id = d.date_id
JOIN dim_category c ON f.category_id = c.category_id
JOIN dim_account a ON f.account_id = a.account_id
LEFT JOIN dim_merchant m ON f.merchant_id = m.merchant_id
WHERE f.is_internal_transfer = FALSE;

-- VIEW 2: Chỉ số Tỷ lệ Tiết kiệm ròng theo tháng (Net Savings Rate - Câu hỏi 1)
CREATE VIEW vw_monthly_savings_rate AS
SELECT 
    year,
    month,
    TO_DATE(CONCAT(year, '-', LPAD(month::TEXT, 2, '0'), '-01'), 'YYYY-MM-DD') AS report_month,
    SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END) AS total_income,
    SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END) AS total_expense,
    (SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END) - 
     SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END)) AS net_savings,
    ROUND(
        (SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END) - SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END)) * 100.0 /
        NULLIF(SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END), 0), 2
    ) AS net_savings_rate_pct
FROM vw_clean_transactions
GROUP BY year, month;

-- VIEW 3: Giám sát Ngân sách vượt trần theo danh mục (Budget Monitoring - Câu hỏi 2)
CREATE VIEW vw_category_budget_monitoring AS
SELECT 
    year,
    month,
    TO_DATE(CONCAT(year, '-', LPAD(month::TEXT, 2, '0'), '-01'), 'YYYY-MM-DD') AS report_month,
    parent_category,
    category_name,
    monthly_budget,
    SUM(abs_amount) AS actual_spent,
    (SUM(abs_amount) - monthly_budget) AS over_budget_amount,
    ROUND((SUM(abs_amount) - monthly_budget) * 100.0 / NULLIF(monthly_budget, 0), 2) AS over_budget_pct,
    CASE 
        WHEN SUM(abs_amount) > monthly_budget THEN TRUE 
        ELSE FALSE 
    END AS is_over_budget
FROM vw_clean_transactions
WHERE direction = 'EXPENSE'
GROUP BY year, month, parent_category, category_name, monthly_budget;

-- VIEW 4: Bản đồ nhiệt chi tiêu theo Khung giờ và Thứ trong tuần (Heatmap - Câu hỏi 3)
CREATE VIEW vw_spending_heatmap AS
SELECT 
    day_name,
    day_of_week,
    hour,
    is_weekend,
    COUNT(transaction_id) AS transaction_count,
    SUM(abs_amount) AS total_spending,
    ROUND(AVG(abs_amount), 0) AS avg_spending_per_trans
FROM vw_clean_transactions
WHERE direction = 'EXPENSE'
GROUP BY day_name, day_of_week, hour, is_weekend;

-- VIEW 5: Danh sách giao dịch bất thường AI cảnh báo (Anomalies - Câu hỏi 5)
CREATE VIEW vw_anomaly_feed AS
SELECT 
    transaction_id,
    full_date,
    day_name,
    hour,
    account_name,
    category_name,
    merchant_name,
    amount,
    clean_description,
    anomaly_score,
    source_type,
    reference_code
FROM vw_clean_transactions
WHERE is_anomaly = TRUE;

-- VIEW 6: Luồng tiền Sankey Diagram (Thu nhập -> Các quỹ chi tiêu & Tiết kiệm)
CREATE VIEW vw_cashflow_sankey AS
-- Bước 1: Thu nhập vào Tổng dòng tiền
SELECT 
    category_name AS source,
    'Tổng Thu Nhập' AS target,
    SUM(amount) AS value
FROM vw_clean_transactions
WHERE direction = 'INCOME'
GROUP BY category_name

UNION ALL

-- Bước 2: Tổng thu nhập phân bổ sang các nhóm chi tiêu chính
SELECT 
    'Tổng Thu Nhập' AS source,
    parent_category AS target,
    SUM(abs_amount) AS value
FROM vw_clean_transactions
WHERE direction = 'EXPENSE'
GROUP BY parent_category

UNION ALL

-- Bước 3: Các nhóm chi tiêu phân rã vào các danh mục cụ thể
SELECT 
    parent_category AS source,
    category_name AS target,
    SUM(abs_amount) AS value
FROM vw_clean_transactions
WHERE direction = 'EXPENSE'
GROUP BY parent_category, category_name;

-- ==========================================================
-- 04_semantic_views.sql: Tầng ngữ nghĩa phục vụ trực tiếp Apache Superset
-- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
-- Nhóm: nhom13-65httt
-- ==========================================================

DROP VIEW IF EXISTS vw_burn_rate_gauge CASCADE;
DROP VIEW IF EXISTS vw_ai_forecast_combined CASCADE;
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
    LPAD(hour::TEXT, 2, '0') || 'h' AS hour_label,
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
    abs_amount,
    clean_description,
    anomaly_score,
    source_type,
    reference_code
FROM vw_clean_transactions
WHERE is_anomaly = TRUE;

-- VIEW 6: Luồng tiền Sankey Diagram (Thu nhập -> Các quỹ chi tiêu & Tiết kiệm)
CREATE VIEW vw_cashflow_sankey AS
SELECT 
    category_name AS source,
    'Tổng Thu Nhập' AS target,
    SUM(amount) AS value
FROM vw_clean_transactions
WHERE direction = 'INCOME'
GROUP BY category_name

UNION ALL

SELECT 
    'Tổng Thu Nhập' AS source,
    parent_category AS target,
    SUM(abs_amount) AS value
FROM vw_clean_transactions
WHERE direction = 'EXPENSE'
GROUP BY parent_category

UNION ALL

SELECT 
    parent_category AS source,
    category_name AS target,
    SUM(abs_amount) AS value
FROM vw_clean_transactions
WHERE direction = 'EXPENSE'
GROUP BY parent_category, category_name;

-- VIEW 7: Chuỗi thời gian kết hợp Chi tiêu thực tế + Dự báo AI 30 ngày (Dashboard 3)
CREATE VIEW vw_ai_forecast_combined AS
SELECT
    full_date AS record_date,
    SUM(abs_amount) AS actual_spending,
    NULL::NUMERIC(15,2) AS predicted_spending,
    NULL::NUMERIC(15,2) AS lower_bound,
    NULL::NUMERIC(15,2) AS upper_bound,
    'Thực tế' AS series_type
FROM vw_clean_transactions
WHERE direction = 'EXPENSE'
GROUP BY full_date

UNION ALL

SELECT
    forecast_date AS record_date,
    NULL::NUMERIC(15,2) AS actual_spending,
    predicted_amount AS predicted_spending,
    lower_bound,
    upper_bound,
    'Dự báo AI (30 ngày)' AS series_type
FROM ai_spending_forecast;

-- VIEW 8: Chỉ số Tốc độ đốt ngân sách & Dự phóng số dư tháng hiện tại (Gauge Chart - Dashboard 1 & 3)
CREATE VIEW vw_burn_rate_gauge AS
WITH latest_month AS (
    SELECT year, month, MAX(day) AS days_elapsed
    FROM vw_clean_transactions
    GROUP BY year, month
    ORDER BY year DESC, month DESC
    LIMIT 1
),
mtd AS (
    SELECT
        lm.year,
        lm.month,
        lm.days_elapsed,
        COALESCE(SUM(CASE WHEN v.direction = 'INCOME' THEN v.amount ELSE 0 END), 0) AS mtd_income,
        COALESCE(SUM(CASE WHEN v.direction = 'EXPENSE' THEN v.abs_amount ELSE 0 END), 0) AS mtd_expense
    FROM latest_month lm
    JOIN vw_clean_transactions v ON v.year = lm.year AND v.month = lm.month
    GROUP BY lm.year, lm.month, lm.days_elapsed
),
budget AS (
    SELECT COALESCE(SUM(monthly_budget), 0) AS total_monthly_budget
    FROM dim_category
    WHERE category_type = 'EXPENSE'
),
fc AS (
    SELECT
        COALESCE(SUM(predicted_amount), 0) AS total_30d_forecast,
        COALESCE(SUM(
            CASE
                WHEN EXTRACT(YEAR FROM forecast_date) = (SELECT year FROM latest_month)
                 AND EXTRACT(MONTH FROM forecast_date) = (SELECT month FROM latest_month)
                 AND EXTRACT(DAY FROM forecast_date) > (SELECT days_elapsed FROM latest_month)
                THEN predicted_amount ELSE 0
            END
        ), 0) AS remaining_month_forecast
    FROM ai_spending_forecast
),
anom AS (
    SELECT COUNT(*) AS total_anomalies FROM vw_anomaly_feed
)
SELECT
    TO_DATE(CONCAT(m.year, '-', LPAD(m.month::TEXT, 2, '0'), '-01'), 'YYYY-MM-DD') AS report_month,
    m.year,
    m.month,
    m.days_elapsed,
    m.mtd_income,
    m.mtd_expense,
    b.total_monthly_budget,
    ROUND(m.mtd_expense * 100.0 / NULLIF(b.total_monthly_budget, 0), 2) AS budget_utilization_pct,
    ROUND((m.mtd_income - m.mtd_expense) * 100.0 / NULLIF(m.mtd_income, 0), 2) AS mtd_savings_rate_pct,
    ROUND(m.mtd_expense + f.remaining_month_forecast, 0) AS projected_eom_expense,
    ROUND(m.mtd_income - (m.mtd_expense + f.remaining_month_forecast), 0) AS projected_eom_balance,
    ROUND(f.total_30d_forecast, 0) AS total_30d_forecast,
    a.total_anomalies
FROM mtd m
CROSS JOIN budget b
CROSS JOIN fc f
CROSS JOIN anom a;

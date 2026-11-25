from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_service.forecasting import BurnRateAnalyzer
from api.dependencies import get_db
from api.security import get_optional_user
from notification import WeeklyReportAgent

router = APIRouter(prefix="/api/v1/analytics", tags=["Business Analytics (5 Core Questions)"])


@router.get("/kpi-summary")
def get_five_core_business_questions(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    Trả lời đồng bộ 5 Câu hỏi Nghiệp vụ Cốt lõi lọc chính xác theo user_id đang đăng nhập.
    """
    uid = int(current_user["user_id"])

    # Câu hỏi 1: Tỷ lệ tiết kiệm ròng theo từng tháng của user
    savings_rows = db.execute(
        text("""
            SELECT
                year,
                month,
                SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END)::FLOAT AS total_income,
                SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END)::FLOAT AS total_expense,
                (SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END) -
                 SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END))::FLOAT AS net_savings,
                ROUND(
                    (SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END) -
                     SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END)) * 100.0 /
                    NULLIF(SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END), 0), 2
                )::FLOAT AS net_savings_rate_pct
            FROM vw_clean_transactions
            WHERE user_id = :uid
            GROUP BY year, month
            ORDER BY year DESC, month DESC
            LIMIT 6
        """),
        {"uid": uid},
    ).mappings().all()

    target_year = year or (int(savings_rows[0]["year"]) if savings_rows else 2026)
    target_month = month or (int(savings_rows[0]["month"]) if savings_rows else 11)

    # Câu hỏi 2: Danh mục vượt ngân sách
    over_budget_rows = db.execute(
        text("""
            SELECT
                category_name,
                parent_category,
                monthly_budget::FLOAT,
                SUM(abs_amount)::FLOAT AS actual_spent,
                (SUM(abs_amount) - monthly_budget)::FLOAT AS over_budget_amount,
                ROUND((SUM(abs_amount) - monthly_budget) * 100.0 / NULLIF(monthly_budget, 0), 2)::FLOAT AS over_budget_pct
            FROM vw_clean_transactions
            WHERE user_id = :uid AND year = :y AND month = :m AND direction = 'EXPENSE' AND monthly_budget > 0
            GROUP BY category_name, parent_category, monthly_budget
            HAVING SUM(abs_amount) > monthly_budget
            ORDER BY over_budget_pct DESC
        """),
        {"uid": uid, "y": target_year, "m": target_month},
    ).mappings().all()

    # Câu hỏi 3: Top 5 khung giờ chi tiêu cao nhất
    peak_spending_rows = db.execute(
        text("""
            SELECT
                day_name,
                hour,
                COUNT(transaction_id) AS transaction_count,
                SUM(abs_amount)::FLOAT AS total_spending,
                ROUND(AVG(abs_amount), 0)::FLOAT AS avg_spending_per_trans
            FROM vw_clean_transactions
            WHERE user_id = :uid AND direction = 'EXPENSE'
            GROUP BY day_name, hour
            ORDER BY total_spending DESC
            LIMIT 5
        """),
        {"uid": uid},
    ).mappings().all()

    # Câu hỏi 4: Burn-rate & số dư cuối tháng dự kiến
    burn_rate = BurnRateAnalyzer.analyze_month(year=target_year, month=target_month, user_id=uid)

    # Câu hỏi 5: Giao dịch bất thường của user
    anomaly_rows = db.execute(
        text("""
            SELECT transaction_id, full_date::TEXT, day_name, hour, account_name,
                   category_name, amount::FLOAT, clean_description, anomaly_score::FLOAT
            FROM vw_clean_transactions
            WHERE user_id = :uid AND is_anomaly = TRUE
            ORDER BY full_date DESC, anomaly_score DESC
            LIMIT 10
        """),
        {"uid": uid},
    ).mappings().all()

    return {
        "user_id": uid,
        "target_period": f"{target_year}-{target_month:02d}",
        "q1_monthly_net_savings": [dict(r) for r in savings_rows],
        "q2_over_budget_categories": [dict(r) for r in over_budget_rows],
        "q3_peak_spending_slots": [dict(r) for r in peak_spending_rows],
        "q4_projected_end_of_month_balance": {
            "mtd_income": burn_rate.get("mtd_income"),
            "mtd_expense": burn_rate.get("mtd_expense"),
            "daily_burn_rate": burn_rate.get("daily_burn_rate"),
            "projected_eom_expense": burn_rate.get("projected_eom_expense"),
            "projected_eom_balance": burn_rate.get("projected_eom_balance"),
            "projected_savings_rate_pct": burn_rate.get("projected_savings_rate_pct"),
            "budget_utilization_pct": burn_rate.get("budget_utilization_pct"),
            "alert_level": burn_rate.get("alert_level"),
            "advice": burn_rate.get("advice"),
        },
        "q5_recent_anomalies": [dict(r) for r in anomaly_rows],
    }


@router.post("/weekly-report")
def trigger_weekly_financial_report():
    """Tạo và gửi bản tin tóm tắt sức khỏe tài chính hàng tuần qua Telegram (hoặc xem trước dry-run)."""
    return WeeklyReportAgent.send_weekly_report()


@router.post("/send-alerts")
def trigger_anomaly_alerts():
    """Gửi cảnh báo tức thì các giao dịch bất thường mới nhất qua Telegram (hoặc xem trước dry-run)."""
    return WeeklyReportAgent.send_anomaly_alerts()

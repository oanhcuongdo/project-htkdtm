from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ai_service.forecasting import BurnRateAnalyzer
from api.dependencies import get_db
from notification import WeeklyReportAgent

router = APIRouter(prefix="/api/v1/analytics", tags=["Business Analytics (5 Core Questions)"])


@router.get("/kpi-summary")
def get_five_core_business_questions(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Trả lời đồng bộ 5 Câu hỏi Nghiệp vụ Cốt lõi trong Đề cương Project:
    1. Tỷ lệ tiết kiệm ròng hàng tháng là bao nhiêu?
    2. Danh mục chi tiêu nào đang vượt ngân sách và vượt bao nhiêu phần trăm?
    3. Chi tiêu tập trung vào khung giờ và ngày nào trong tuần?
    4. Với tốc độ chi tiêu hiện tại, số dư cuối tháng dự kiến là bao nhiêu?
    5. Có giao dịch nào bất thường cần xem lại không?
    """
    # Câu hỏi 1: Tỷ lệ tiết kiệm ròng theo các tháng gần nhất
    savings_rows = db.execute(
        text("""
            SELECT year, month, total_income::FLOAT, total_expense::FLOAT,
                   net_savings::FLOAT, net_savings_rate_pct::FLOAT
            FROM vw_monthly_savings_rate
            ORDER BY year DESC, month DESC
            LIMIT 6
        """)
    ).mappings().all()

    target_year = year or (int(savings_rows[0]["year"]) if savings_rows else 2026)
    target_month = month or (int(savings_rows[0]["month"]) if savings_rows else 11)

    # Câu hỏi 2: Danh mục vượt ngân sách trong tháng mục tiêu
    over_budget_rows = db.execute(
        text("""
            SELECT category_name, parent_category, monthly_budget::FLOAT, actual_spent::FLOAT,
                   over_budget_amount::FLOAT, over_budget_pct::FLOAT
            FROM vw_category_budget_monitoring
            WHERE year = :y AND month = :m AND is_over_budget = TRUE
            ORDER BY over_budget_pct DESC
        """),
        {"y": target_year, "m": target_month},
    ).mappings().all()

    # Câu hỏi 3: Top 5 khung giờ & thứ trong tuần có tổng chi tiêu cao nhất
    peak_spending_rows = db.execute(
        text("""
            SELECT day_name, hour, transaction_count, total_spending::FLOAT, avg_spending_per_trans::FLOAT
            FROM vw_spending_heatmap
            ORDER BY total_spending DESC
            LIMIT 5
        """)
    ).mappings().all()

    # Câu hỏi 4: Burn-rate & số dư cuối tháng dự kiến
    burn_rate = BurnRateAnalyzer.analyze_month(year=target_year, month=target_month)

    # Câu hỏi 5: Danh sách giao dịch bất thường cần rà soát
    anomaly_rows = db.execute(
        text("""
            SELECT transaction_id, full_date::TEXT, day_name, hour, account_name,
                   category_name, amount::FLOAT, clean_description, anomaly_score::FLOAT
            FROM vw_anomaly_feed
            ORDER BY full_date DESC, anomaly_score DESC
            LIMIT 10
        """)
    ).mappings().all()

    return {
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

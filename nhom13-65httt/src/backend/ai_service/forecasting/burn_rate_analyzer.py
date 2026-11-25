import calendar
from typing import Dict, Any, Optional
from sqlalchemy import text

from api.dependencies import get_db_session


class BurnRateAnalyzer:
    """
    Phân tích tốc độ đốt ngân sách (Burn-rate) và dự phóng số dư cuối tháng theo từng user_id
    nhằm trả lời trực tiếp Câu hỏi nghiệp vụ số 4 trong Đề cương.
    """

    @staticmethod
    def analyze_month(year: Optional[int] = None, month: Optional[int] = None, user_id: int = 1) -> Dict[str, Any]:
        with get_db_session() as db:
            if not year or not month:
                latest = db.execute(
                    text("""
                        SELECT d.year, d.month, MAX(d.day) AS latest_day
                        FROM fact_transactions f
                        JOIN dim_date d ON f.date_id = d.date_id
                        WHERE f.user_id = :uid AND f.is_internal_transfer = FALSE
                        GROUP BY d.year, d.month
                        ORDER BY d.year DESC, d.month DESC
                        LIMIT 1
                    """),
                    {"uid": user_id},
                ).first()
                if not latest:
                    return {
                        "status": "empty",
                        "period": "N/A",
                        "mtd_income": 0,
                        "mtd_expense": 0,
                        "current_net_balance": 0,
                        "daily_burn_rate": 0,
                        "projected_eom_expense": 0,
                        "projected_eom_balance": 0,
                        "projected_savings_rate_pct": 0,
                        "budget_utilization_pct": 0,
                        "alert_level": "INFO",
                        "advice": "Bạn chưa có giao dịch nào. Hãy tải lên sao kê Excel/CSV hoặc kết nối Email để hệ thống phân tích!",
                        "over_budget_categories": [],
                    }
                year, month, days_elapsed = int(latest[0]), int(latest[1]), int(latest[2])
            else:
                latest_day_row = db.execute(
                    text("""
                        SELECT COALESCE(MAX(d.day), 1)
                        FROM fact_transactions f
                        JOIN dim_date d ON f.date_id = d.date_id
                        WHERE f.user_id = :uid AND d.year = :y AND d.month = :m AND f.is_internal_transfer = FALSE
                    """),
                    {"uid": user_id, "y": year, "m": month},
                ).scalar()
                days_elapsed = int(latest_day_row or 1)

            days_in_month = calendar.monthrange(year, month)[1]
            days_remaining = max(0, days_in_month - days_elapsed)

            totals = db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END), 0)::FLOAT AS mtd_income,
                        COALESCE(SUM(CASE WHEN direction = 'EXPENSE' THEN ABS(amount) ELSE 0 END), 0)::FLOAT AS mtd_expense
                    FROM vw_clean_transactions
                    WHERE user_id = :uid AND year = :y AND month = :m
                """),
                {"uid": user_id, "y": year, "m": month},
            ).first()

            mtd_income = float(totals[0])
            mtd_expense = float(totals[1])

            total_budget = float(
                db.execute(
                    text("SELECT COALESCE(SUM(monthly_budget), 0)::FLOAT FROM dim_category WHERE category_type = 'EXPENSE'")
                ).scalar() or 0.0
            )

            daily_burn_rate = mtd_expense / max(days_elapsed, 1)

            forecast_rem = db.execute(
                text("""
                    SELECT COALESCE(SUM(predicted_amount), 0)::FLOAT, COUNT(*)
                    FROM ai_spending_forecast
                    WHERE user_id = :uid
                      AND EXTRACT(YEAR FROM forecast_date) = :y
                      AND EXTRACT(MONTH FROM forecast_date) = :m
                      AND EXTRACT(DAY FROM forecast_date) > :d_elapsed
                """),
                {"uid": user_id, "y": year, "m": month, "d_elapsed": days_elapsed},
            ).first()

            if forecast_rem and int(forecast_rem[1]) > 0:
                projected_remaining_expense = float(forecast_rem[0])
                projection_source = "ai_spending_forecast (SARIMAX/ARIMA)"
            else:
                projected_remaining_expense = daily_burn_rate * days_remaining
                projection_source = "linear_daily_burn_rate"

            projected_eom_expense = round(mtd_expense + projected_remaining_expense, 0)
            projected_eom_balance = round(mtd_income - projected_eom_expense, 0)
            projected_savings_rate_pct = (
                round((projected_eom_balance * 100.0) / mtd_income, 2) if mtd_income > 0 else 0.0
            )
            budget_utilization_pct = (
                round((mtd_expense * 100.0) / total_budget, 2) if total_budget > 0 else 0.0
            )
            projected_budget_pct = (
                round((projected_eom_expense * 100.0) / total_budget, 2) if total_budget > 0 else 0.0
            )

            remaining_cash = max(0.0, mtd_income - mtd_expense)
            days_until_zero = int(remaining_cash / daily_burn_rate) if daily_burn_rate > 0 else 999

            if projected_eom_balance < 0:
                alert_level = "DANGER"
                advice = (
                    f"Cảnh báo thâm hụt! Với tốc độ chi {daily_burn_rate:,.0f} VND/ngày, bạn dự kiến âm "
                    f"{abs(projected_eom_balance):,.0f} VND vào cuối tháng {month:02d}/{year}. "
                    f"Cần cắt giảm ngay các danh mục Linh hoạt (Mua sắm, Giải trí)."
                )
            elif projected_budget_pct > 100:
                alert_level = "WARNING"
                advice = (
                    f"Tốc độ đốt ngân sách cao ({projected_budget_pct:.1f}% ngân sách tháng). "
                    f"Số dư dự kiến cuối tháng còn {projected_eom_balance:,.0f} VND "
                    f"(tỷ lệ tiết kiệm {projected_savings_rate_pct:.1f}%)."
                )
            else:
                alert_level = "SAFE"
                advice = (
                    f"Sức khỏe dòng tiền tốt! Dự kiến cuối tháng {month:02d}/{year} bạn còn dư "
                    f"{projected_eom_balance:,.0f} VND (tỷ lệ tiết kiệm ròng {projected_savings_rate_pct:.1f}%)."
                )

            over_budget_rows = db.execute(
                text("""
                    SELECT
                        category_name,
                        monthly_budget::FLOAT,
                        SUM(abs_amount)::FLOAT AS actual_spent,
                        (SUM(abs_amount) - monthly_budget)::FLOAT AS over_budget_amount,
                        ROUND((SUM(abs_amount) - monthly_budget) * 100.0 / NULLIF(monthly_budget, 0), 2)::FLOAT AS over_budget_pct
                    FROM vw_clean_transactions
                    WHERE user_id = :uid AND year = :y AND month = :m AND direction = 'EXPENSE' AND monthly_budget > 0
                    GROUP BY category_name, monthly_budget
                    HAVING SUM(abs_amount) > monthly_budget
                    ORDER BY over_budget_pct DESC
                """),
                {"uid": user_id, "y": year, "m": month},
            ).mappings().all()

        return {
            "period": f"{year}-{month:02d}",
            "days_elapsed": days_elapsed,
            "days_in_month": days_in_month,
            "days_remaining": days_remaining,
            "mtd_income": round(mtd_income, 0),
            "mtd_expense": round(mtd_expense, 0),
            "current_net_balance": round(mtd_income - mtd_expense, 0),
            "total_monthly_budget": round(total_budget, 0),
            "daily_burn_rate": round(daily_burn_rate, 0),
            "projected_eom_expense": projected_eom_expense,
            "projected_eom_balance": projected_eom_balance,
            "projected_savings_rate_pct": projected_savings_rate_pct,
            "budget_utilization_pct": budget_utilization_pct,
            "projected_budget_utilization_pct": projected_budget_pct,
            "days_until_income_depleted": days_until_zero,
            "projection_source": projection_source,
            "alert_level": alert_level,
            "advice": advice,
            "over_budget_categories": [dict(r) for r in over_budget_rows],
        }

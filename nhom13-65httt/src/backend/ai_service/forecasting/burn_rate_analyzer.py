import calendar
from typing import Dict, Any, Optional
from sqlalchemy import text

from api.dependencies import get_db_session


class BurnRateAnalyzer:
    """
    Phân tích tốc độ đốt ngân sách (Burn-rate) và dự phóng số dư cuối tháng
    nhằm trả lời trực tiếp Câu hỏi nghiệp vụ số 4 trong Đề cương.
    """

    @staticmethod
    def analyze_month(year: Optional[int] = None, month: Optional[int] = None) -> Dict[str, Any]:
        with get_db_session() as db:
            # Nếu không truyền tháng, tự động lấy tháng gần nhất có dữ liệu trong kho
            if not year or not month:
                latest = db.execute(
                    text("""
                        SELECT d.year, d.month, MAX(d.day) AS latest_day
                        FROM fact_transactions f
                        JOIN dim_date d ON f.date_id = d.date_id
                        WHERE f.is_internal_transfer = FALSE
                        GROUP BY d.year, d.month
                        ORDER BY d.year DESC, d.month DESC
                        LIMIT 1
                    """)
                ).first()
                if not latest:
                    return {"status": "empty", "message": "Chưa có dữ liệu giao dịch trong kho."}
                year, month, days_elapsed = int(latest[0]), int(latest[1]), int(latest[2])
            else:
                latest_day_row = db.execute(
                    text("""
                        SELECT COALESCE(MAX(d.day), 1)
                        FROM fact_transactions f
                        JOIN dim_date d ON f.date_id = d.date_id
                        WHERE d.year = :y AND d.month = :m AND f.is_internal_transfer = FALSE
                    """),
                    {"y": year, "m": month},
                ).scalar()
                days_elapsed = int(latest_day_row or 1)

            days_in_month = calendar.monthrange(year, month)[1]
            days_remaining = max(0, days_in_month - days_elapsed)

            # Tổng thu nhập và chi tiêu lũy kế trong tháng
            totals = db.execute(
                text("""
                    SELECT
                        COALESCE(SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END), 0)::FLOAT AS mtd_income,
                        COALESCE(SUM(CASE WHEN direction = 'EXPENSE' THEN ABS(amount) ELSE 0 END), 0)::FLOAT AS mtd_expense
                    FROM vw_clean_transactions
                    WHERE year = :y AND month = :m
                """),
                {"y": year, "m": month},
            ).first()

            mtd_income = float(totals[0])
            mtd_expense = float(totals[1])

            # Tổng hạn mức ngân sách tháng của toàn bộ danh mục chi
            total_budget = float(
                db.execute(
                    text("SELECT COALESCE(SUM(monthly_budget), 0)::FLOAT FROM dim_category WHERE category_type = 'EXPENSE'")
                ).scalar() or 0.0
            )

            daily_burn_rate = mtd_expense / max(days_elapsed, 1)

            # Ưu tiên lấy phần chi tiêu dự phóng cho các ngày còn lại từ bảng ai_spending_forecast nếu đã chạy
            forecast_rem = db.execute(
                text("""
                    SELECT COALESCE(SUM(predicted_amount), 0)::FLOAT, COUNT(*)
                    FROM ai_spending_forecast
                    WHERE EXTRACT(YEAR FROM forecast_date) = :y
                      AND EXTRACT(MONTH FROM forecast_date) = :m
                      AND EXTRACT(DAY FROM forecast_date) > :d_elapsed
                """),
                {"y": year, "m": month, "d_elapsed": days_elapsed},
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

            # Tính ngày dự kiến cạn nguồn thu tháng nếu tốc độ tiêu vượt thu
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

            # Lấy danh sách danh mục đang vượt trần ngân sách trong tháng
            over_budget_rows = db.execute(
                text("""
                    SELECT category_name, monthly_budget::FLOAT, actual_spent::FLOAT,
                           over_budget_amount::FLOAT, over_budget_pct::FLOAT
                    FROM vw_category_budget_monitoring
                    WHERE year = :y AND month = :m AND is_over_budget = TRUE
                    ORDER BY over_budget_pct DESC
                """),
                {"y": year, "m": month},
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

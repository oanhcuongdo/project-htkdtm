from datetime import datetime
from typing import Dict, Any
from sqlalchemy import text

from ai_service.forecasting import BurnRateAnalyzer
from api.dependencies import get_db_session
from .telegram_notifier import TelegramNotifier


class WeeklyReportAgent:
    """
    Trợ lý chủ động (Actionable Insights Layer):
    Tự động tổng hợp bản tin tóm tắt tài chính hàng tuần & cảnh báo bất thường/vượt ngân sách
    kèm lời khuyên điều chỉnh hành vi chi tiêu.
    """

    @staticmethod
    def build_weekly_report() -> Dict[str, Any]:
        burn = BurnRateAnalyzer.analyze_month()

        with get_db_session() as db:
            top_peak = db.execute(
                text("""
                    SELECT day_name, hour_label, total_spending::FLOAT, transaction_count
                    FROM vw_spending_heatmap
                    ORDER BY total_spending DESC
                    LIMIT 1
                """)
            ).mappings().first()

            recent_anomalies = db.execute(
                text("""
                    SELECT full_date::TEXT, category_name, amount::FLOAT, clean_description, anomaly_score::FLOAT
                    FROM vw_anomaly_feed
                    ORDER BY full_date DESC, anomaly_score DESC
                    LIMIT 3
                """)
            ).mappings().all()

        lines = [
            f"📊 *BẢN TIN SỨC KHỎE TÀI CHÍNH CÁ NHÂN ({burn.get('period', 'N/A')})*",
            f"_Cập nhật lúc: {datetime.now().strftime('%d/%m/%Y %H:%M')}_",
            "",
            f"1️⃣ *Tỷ lệ tiết kiệm ròng hiện tại:* `{burn.get('projected_savings_rate_pct', 0)}%`",
            f"   • Thu nhập lũy kế: `{burn.get('mtd_income', 0):,.0f} VND`",
            f"   • Chi tiêu lũy kế: `{burn.get('mtd_expense', 0):,.0f} VND`",
            "",
            f"2️⃣ *Cảnh báo vượt ngân sách ({len(burn.get('over_budget_categories', []))} danh mục):*",
        ]

        over_cats = burn.get("over_budget_categories", [])
        if over_cats:
            for c in over_cats[:3]:
                lines.append(
                    f"   • {c['category_name']}: vượt `+{c['over_budget_pct']}%` (`{c['actual_spent']:,.0f}` / `{c['monthly_budget']:,.0f} VND`)"
                )
        else:
            lines.append("   • Tất cả danh mục đều đang nằm trong hạn mức ngân sách!")

        if top_peak:
            lines.extend([
                "",
                f"3️⃣ *Khung giờ dễ vung tay nhất:* `{top_peak['day_name']}` lúc `{top_peak['hour_label']}` (`{top_peak['total_spending']:,.0f} VND` / {top_peak['transaction_count']} giao dịch)",
            ])

        lines.extend([
            "",
            f"4️⃣ *Dự phóng số dư cuối tháng ({burn.get('alert_level', 'INFO')}):*",
            f"   • Tốc độ chi: `{burn.get('daily_burn_rate', 0):,.0f} VND/ngày`",
            f"   • Dự kiến số dư cuối tháng: `{burn.get('projected_eom_balance', 0):,.0f} VND`",
            f"   • _Khuyến nghị:_ {burn.get('advice', '')}",
            "",
            f"5️⃣ *Giao dịch bất thường cần kiểm tra ({len(recent_anomalies)} gần nhất):*",
        ])

        if recent_anomalies:
            for a in recent_anomalies:
                lines.append(
                    f"   • [{a['full_date']}] `{a['amount']:,.0f} VND` ({a['category_name']}): {a['clean_description'][:45]}"
                )
        else:
            lines.append("   • Không phát hiện giao dịch bất thường.")

        report_text = "\n".join(lines)
        return {
            "generated_at": datetime.now().isoformat(),
            "period": burn.get("period"),
            "alert_level": burn.get("alert_level"),
            "report_markdown": report_text,
        }

    @classmethod
    def send_weekly_report(cls) -> Dict[str, Any]:
        payload = cls.build_weekly_report()
        delivery = TelegramNotifier().send_message(payload["report_markdown"])
        return {**payload, "delivery": delivery}

    @staticmethod
    def send_anomaly_alerts() -> Dict[str, Any]:
        with get_db_session() as db:
            anomalies = db.execute(
                text("""
                    SELECT transaction_id, full_date::TEXT, category_name, amount::FLOAT, clean_description, anomaly_score::FLOAT
                    FROM vw_anomaly_feed
                    ORDER BY full_date DESC, anomaly_score DESC
                    LIMIT 5
                """)
            ).mappings().all()

        if not anomalies:
            return {"anomalies_count": 0, "delivery": {"sent": False, "reason": "Không có giao dịch bất thường."}}

        lines = ["🚨 *CẢNH BÁO GIAO DỊCH BẤT THƯỜNG TỪ AI*"]
        for a in anomalies:
            lines.append(
                f"• `{a['full_date']}` | `{a['amount']:,.0f} VND` | *{a['category_name']}* (Score: `{a['anomaly_score']}`)\n  _{a['clean_description'][:60]}_"
            )

        msg = "\n".join(lines)
        delivery = TelegramNotifier().send_message(msg)
        return {"anomalies_count": len(anomalies), "delivery": delivery}

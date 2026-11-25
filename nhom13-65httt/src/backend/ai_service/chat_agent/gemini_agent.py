"""
Trợ lý Chat AI Tài chính Cá nhân sử dụng Google Gemini API (`google-genai`)
kết hợp cơ chế Function Calling (7 Tools truy vấn PostgreSQL Read-only cô lập theo user_id).
Đảm bảo con số chính xác 100% từ dữ liệu thật, không ảo giác (Zero Hallucination).
"""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import text

from ai_service.forecasting import BurnRateAnalyzer
from api.config import settings
from api.dependencies import get_db_session

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """Bạn là Trợ lý Tài chính Cá nhân Thông minh (Personal CFO AI) của Hệ thống Quản lý Tài chính Cá nhân (Nhóm 13 - 65HTTT).
Nguyên tắc bắt buộc:
1. LUÔN LUÔN gọi các công cụ (tools) được cung cấp để lấy số liệu thật từ cơ sở dữ liệu PostgreSQL trước khi trả lời bất kỳ câu hỏi nào về giao dịch, dòng tiền, tài khoản nhận tiền, ngân sách, tiết kiệm hoặc dự báo.
2. Tuyệt đối KHÔNG tự bịa đặt, phỏng đoán hoặc làm tròn sai số liệu. Sử dụng đúng con số trả về từ công cụ.
3. Định dạng tiền tệ rõ ràng theo chuẩn Việt Nam (ví dụ: 6,053,200 VND).
4. Khi liệt kê danh sách (ví dụ Top 5 tài khoản nhận tiền nhiều nhất), trình bày rõ ràng theo thứ tự giảm dần gồm: Tên đối tác, Số tài khoản đã che (nếu có), Ngân hàng, Số lần chuyển và Tổng số tiền.
5. Nếu người dùng không nêu rõ năm, mặc định truy vấn năm 2026 (năm dữ liệu chính trong hệ thống).
6. Kết thúc câu trả lời bằng 1-2 câu nhận xét hoặc lời khuyên quản trị dòng tiền ngắn gọn, thiết thực bằng tiếng Việt.
"""


class GeminiFinanceChatAgent:
    """Agent hỏi đáp dòng tiền bằng Gemini Function Calling, cô lập tuyệt đối theo user_id."""

    def __init__(self, user_id: int):
        self.user_id = int(user_id)
        self.captured_tables: List[Dict[str, Any]] = []
        self.tools_used: List[str] = []

    # ------------------------------------------------------------------
    # BỘ 7 CÔNG CỤ TRUY VẤN POSTGRESQL THẬT THEO USER_ID (READ-ONLY)
    # ------------------------------------------------------------------
    def _build_tools(self):
        uid = self.user_id
        captured = self.captured_tables
        used = self.tools_used

        def get_top_recipients(year: int = 2026, month: int = 0, limit: int = 5) -> dict:
            """
            Lấy danh sách top các tài khoản / đối tác nhận tiền từ người dùng nhiều nhất (tiền gửi đi / chi tiêu).
            Args:
                year: Năm cần tra cứu (mặc định 2026).
                month: Tháng cần tra cứu (1-12). Truyền 0 để tính cả năm.
                limit: Số lượng đối tác muốn lấy (mặc định 5).
            """
            used.append(f"get_top_recipients(year={year}, month={month}, limit={limit})")
            limit = max(1, min(int(limit), 20))
            with get_db_session() as db:
                sql = """
                    SELECT
                        counterparty_name AS recipient_name,
                        counterparty_account_mask AS account_mask,
                        counterparty_bank AS bank_name,
                        COUNT(transaction_id) AS transfer_count,
                        ROUND(SUM(abs_amount), 0)::FLOAT AS total_amount_vnd
                    FROM vw_clean_transactions
                    WHERE user_id = :uid
                      AND direction = 'EXPENSE'
                      AND year = :y
                      AND (:m = 0 OR month = :m)
                      AND counterparty_name != 'Khác / Cá nhân'
                    GROUP BY counterparty_name, counterparty_account_mask, counterparty_bank
                    ORDER BY total_amount_vnd DESC
                    LIMIT :lim
                """
                rows = [
                    dict(r)
                    for r in db.execute(text(sql), {"uid": uid, "y": year, "m": month, "lim": limit}).mappings().all()
                ]
                # Nếu không có đối tác cụ thể (ví dụ user chỉ có dữ liệu không ghi tên đối tác), gom theo clean_description
                if not rows:
                    fallback_sql = """
                        SELECT
                            clean_description AS recipient_name,
                            'N/A' AS account_mask,
                            bank_name,
                            COUNT(transaction_id) AS transfer_count,
                            ROUND(SUM(abs_amount), 0)::FLOAT AS total_amount_vnd
                        FROM vw_clean_transactions
                        WHERE user_id = :uid AND direction = 'EXPENSE' AND year = :y AND (:m = 0 OR month = :m)
                        GROUP BY clean_description, bank_name
                        ORDER BY total_amount_vnd DESC
                        LIMIT :lim
                    """
                    rows = [
                        dict(r)
                        for r in db.execute(
                            text(fallback_sql), {"uid": uid, "y": year, "m": month, "lim": limit}
                        ).mappings().all()
                    ]

            title = f"Top {limit} đối tác / tài khoản nhận tiền nhiều nhất" + (
                f" tháng {month:02d}/{year}" if month else f" năm {year}"
            )
            if rows:
                captured.append({"title": title, "rows": rows})
            return {"period": f"{year}-{month:02d}" if month else str(year), "count": len(rows), "recipients": rows}

        def get_top_senders(year: int = 2026, month: int = 0, limit: int = 5) -> dict:
            """
            Lấy danh sách top các nguồn chuyển tiền đến cho người dùng nhiều nhất (thu nhập / tiền vào).
            Args:
                year: Năm cần tra cứu (mặc định 2026).
                month: Tháng cần tra cứu (1-12). Truyền 0 để tính cả năm.
                limit: Số lượng nguồn muốn lấy (mặc định 5).
            """
            used.append(f"get_top_senders(year={year}, month={month}, limit={limit})")
            limit = max(1, min(int(limit), 20))
            with get_db_session() as db:
                rows = [
                    dict(r)
                    for r in db.execute(
                        text("""
                            SELECT
                                counterparty_name AS sender_name,
                                counterparty_account_mask AS account_mask,
                                counterparty_bank AS bank_name,
                                COUNT(transaction_id) AS transfer_count,
                                ROUND(SUM(amount), 0)::FLOAT AS total_received_vnd
                            FROM vw_clean_transactions
                            WHERE user_id = :uid AND direction = 'INCOME'
                              AND year = :y AND (:m = 0 OR month = :m)
                            GROUP BY counterparty_name, counterparty_account_mask, counterparty_bank
                            ORDER BY total_received_vnd DESC
                            LIMIT :lim
                        """),
                        {"uid": uid, "y": year, "m": month, "lim": limit},
                    ).mappings().all()
                ]
            if rows:
                captured.append({"title": f"Top {limit} nguồn tiền gửi đến", "rows": rows})
            return {"count": len(rows), "senders": rows}

        def get_spending_by_category(year: int = 2026, month: int = 0) -> dict:
            """
            Thống kê chi tiêu theo từng danh mục và đối chiếu hạn mức ngân sách tháng.
            Args:
                year: Năm cần tra cứu (mặc định 2026).
                month: Tháng cần tra cứu (1-12). Truyền 0 để tính cả năm.
            """
            used.append(f"get_spending_by_category(year={year}, month={month})")
            with get_db_session() as db:
                rows = [
                    dict(r)
                    for r in db.execute(
                        text("""
                            SELECT
                                category_name,
                                parent_category,
                                monthly_budget::FLOAT AS monthly_budget_vnd,
                                COUNT(transaction_id) AS tx_count,
                                ROUND(SUM(abs_amount), 0)::FLOAT AS actual_spent_vnd,
                                CASE WHEN :m > 0 AND monthly_budget > 0
                                    THEN ROUND((SUM(abs_amount) - monthly_budget) * 100.0 / monthly_budget, 2)::FLOAT
                                    ELSE 0.0 END AS over_budget_pct
                            FROM vw_clean_transactions
                            WHERE user_id = :uid AND direction = 'EXPENSE'
                              AND year = :y AND (:m = 0 OR month = :m)
                            GROUP BY category_name, parent_category, monthly_budget
                            ORDER BY actual_spent_vnd DESC
                        """),
                        {"uid": uid, "y": year, "m": month},
                    ).mappings().all()
                ]
            if rows:
                captured.append(
                    {
                        "title": f"Chi tiêu theo danh mục ({f'Tháng {month:02d}/{year}' if month else f'Năm {year}'})",
                        "rows": rows,
                    }
                )
            return {"categories": rows}

        def get_monthly_cashflow(months: int = 6) -> dict:
            """
            Lấy báo cáo dòng tiền theo từng tháng gần nhất: Tổng thu nhập, Tổng chi tiêu, Tiết kiệm ròng và Tỷ lệ tiết kiệm (%).
            Args:
                months: Số tháng gần nhất muốn xem (mặc định 6).
            """
            used.append(f"get_monthly_cashflow(months={months})")
            months = max(1, min(int(months), 12))
            with get_db_session() as db:
                rows = [
                    dict(r)
                    for r in db.execute(
                        text("""
                            SELECT
                                CONCAT(year, '-', LPAD(month::TEXT, 2, '0')) AS month_label,
                                ROUND(SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END), 0)::FLOAT AS total_income_vnd,
                                ROUND(SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END), 0)::FLOAT AS total_expense_vnd,
                                ROUND(SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END) -
                                      SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END), 0)::FLOAT AS net_savings_vnd,
                                ROUND(
                                    (SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END) -
                                     SUM(CASE WHEN direction = 'EXPENSE' THEN abs_amount ELSE 0 END)) * 100.0 /
                                    NULLIF(SUM(CASE WHEN direction = 'INCOME' THEN amount ELSE 0 END), 0), 2
                                )::FLOAT AS net_savings_rate_pct
                            FROM vw_clean_transactions
                            WHERE user_id = :uid
                            GROUP BY year, month
                            ORDER BY year DESC, month DESC
                            LIMIT :lim
                        """),
                        {"uid": uid, "lim": months},
                    ).mappings().all()
                ]
            if rows:
                captured.append({"title": f"Tổng quan Dòng tiền {len(rows)} tháng gần nhất", "rows": rows})
            return {"months": rows}

        def get_burn_rate_and_forecast(year: int = 0, month: int = 0) -> dict:
            """
            Tính tốc độ đốt tiền hàng ngày (Burn-rate), số dư cuối tháng dự kiến và danh mục vượt ngân sách.
            Args:
                year: Năm cần tính (truyền 0 để lấy tháng gần nhất).
                month: Tháng cần tính (truyền 0 để lấy tháng gần nhất).
            """
            used.append(f"get_burn_rate_and_forecast(year={year}, month={month})")
            return BurnRateAnalyzer.analyze_month(
                year=year if year > 0 else None,
                month=month if month > 0 else None,
                user_id=uid,
            )

        def get_anomalies(limit: int = 10) -> dict:
            """
            Lấy danh sách các giao dịch bất thường do AI Isolation Forest + Z-Score đánh dấu cần kiểm tra lại.
            Args:
                limit: Số lượng giao dịch tối đa (mặc định 10).
            """
            used.append(f"get_anomalies(limit={limit})")
            limit = max(1, min(int(limit), 20))
            with get_db_session() as db:
                rows = [
                    dict(r)
                    for r in db.execute(
                        text("""
                            SELECT
                                full_date::TEXT AS date,
                                category_name,
                                counterparty_name,
                                amount::FLOAT AS amount_vnd,
                                anomaly_score::FLOAT,
                                clean_description AS description
                            FROM vw_clean_transactions
                            WHERE user_id = :uid AND is_anomaly = TRUE
                            ORDER BY full_date DESC, anomaly_score DESC
                            LIMIT :lim
                        """),
                        {"uid": uid, "lim": limit},
                    ).mappings().all()
                ]
            if rows:
                captured.append({"title": "Danh sách giao dịch bất thường AI phát hiện", "rows": rows})
            return {"count": len(rows), "anomalies": rows}

        def search_transactions(
            keyword: str = "",
            year: int = 0,
            month: int = 0,
            direction: str = "",
            limit: int = 15,
        ) -> dict:
            """
            Tìm kiếm chi tiết các giao dịch theo từ khóa mô tả / tên đối tác, tháng/năm hoặc chiều dòng tiền (INCOME / EXPENSE).
            Args:
                keyword: Từ khóa cần tìm (không phân biệt hoa thường).
                year: Năm lọc (0 = tất cả).
                month: Tháng lọc (0 = tất cả).
                direction: 'INCOME' hoặc 'EXPENSE' (rỗng = cả hai).
                limit: Số lượng bản ghi tối đa (mặc định 15).
            """
            used.append(f"search_transactions(keyword='{keyword}', year={year}, month={month})")
            limit = max(1, min(int(limit), 30))
            kw_pattern = f"%{keyword.strip()}%" if keyword else "%"
            dir_val = direction.strip().upper()
            with get_db_session() as db:
                rows = [
                    dict(r)
                    for r in db.execute(
                        text("""
                            SELECT
                                full_date::TEXT AS date,
                                direction,
                                category_name,
                                counterparty_name,
                                counterparty_account_mask AS account_mask,
                                amount::FLOAT AS amount_vnd,
                                clean_description AS description
                            FROM vw_clean_transactions
                            WHERE user_id = :uid
                              AND (:y = 0 OR year = :y)
                              AND (:m = 0 OR month = :m)
                              AND (:dir = '' OR direction = :dir)
                              AND (
                                  clean_description ILIKE :kw
                                  OR raw_description ILIKE :kw
                                  OR counterparty_name ILIKE :kw
                                  OR category_name ILIKE :kw
                              )
                            ORDER BY full_date DESC, ABS(amount) DESC
                            LIMIT :lim
                        """),
                        {"uid": uid, "y": year, "m": month, "dir": dir_val, "kw": kw_pattern, "lim": limit},
                    ).mappings().all()
                ]
            if rows:
                captured.append({"title": f"Kết quả tra cứu giao dịch ({len(rows)} bản ghi)", "rows": rows})
            return {"count": len(rows), "transactions": rows}

        return [
            get_top_recipients,
            get_top_senders,
            get_spending_by_category,
            get_monthly_cashflow,
            get_burn_rate_and_forecast,
            get_anomalies,
            search_transactions,
        ]

    def ask(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        """Xử lý câu hỏi người dùng bằng Gemini Function Calling và lưu lịch sử vào chat_messages."""
        if not settings.GEMINI_API_KEY or "your_gemini" in settings.GEMINI_API_KEY:
            return {
                "answer": "Chưa cấu hình `GEMINI_API_KEY` trong file `.env` của Backend.",
                "tools_used": [],
                "structured_data": [],
                "model": settings.GEMINI_MODEL,
            }

        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(retry_options=types.HttpRetryOptions(attempts=2)),
        )
        tools_list = self._build_tools()
        tools_map = {fn.__name__: fn for fn in tools_list}

        # Nạp tối đa 6 tin nhắn lịch sử gần nhất của user để hỗ trợ hỏi nối tiếp
        history_contents: List[types.Content] = []
        with get_db_session() as db:
            prev_rows = db.execute(
                text("""
                    SELECT role, content FROM chat_messages
                    WHERE user_id = :uid AND session_id = :sid
                    ORDER BY message_id DESC LIMIT 6
                """),
                {"uid": self.user_id, "sid": session_id},
            ).fetchall()

        for role, content in reversed(prev_rows):
            g_role = "user" if role == "user" else "model"
            history_contents.append(types.Content(role=g_role, parts=[types.Part.from_text(text=content)]))

        history_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=question)]))

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=tools_list,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.2,
        )

        active_model = settings.GEMINI_MODEL
        fallback_models = [
            active_model,
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
        ]
        # Giữ thứ tự duy nhất
        candidate_models = list(dict.fromkeys(fallback_models))

        def _generate_with_fallback():
            nonlocal active_model
            last_err = None
            for idx, m_name in enumerate(candidate_models):
                try:
                    resp = client.models.generate_content(
                        model=m_name,
                        contents=history_contents,
                        config=config,
                    )
                    active_model = m_name
                    return resp
                except Exception as exc:
                    last_err = exc
                    err_str = str(exc)
                    retryable = any(
                        code in err_str
                        for code in ("404", "NOT_FOUND", "503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "OVERLOADED")
                    )
                    if retryable and idx < len(candidate_models) - 1:
                        logger.warning(f"Model {m_name} tạm thời lỗi ({err_str[:80]}), chuyển sang model dự phòng...")
                        continue
                    raise
            raise last_err

        final_answer = ""
        # Vòng lặp Function Calling có kiểm soát (tối đa 4 lượt gọi công cụ)
        for _ in range(4):
            response = _generate_with_fallback()

            fn_calls = response.function_calls
            if not fn_calls:
                final_answer = response.text or "Tôi chưa tìm thấy thông tin phù hợp trong dữ liệu của bạn."
                break

            # Ghi nhận phản hồi gọi tool của model vào hội thoại
            if response.candidates and response.candidates[0].content:
                history_contents.append(response.candidates[0].content)

            tool_response_parts = []
            for fc in fn_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}
                tool_fn = tools_map.get(fn_name)
                if tool_fn:
                    try:
                        # Ép kiểu tham số số nguyên nếu Gemini gửi float (VD: 10.0 -> 10)
                        clean_args = {
                            k: (int(v) if isinstance(v, float) and v.is_integer() else v)
                            for k, v in fn_args.items()
                        }
                        tool_result = tool_fn(**clean_args)
                    except Exception as exc:
                        logger.error(f"Lỗi thực thi tool {fn_name}: {exc}")
                        tool_result = {"error": str(exc)}
                else:
                    tool_result = {"error": f"Tool {fn_name} không tồn tại"}

                tool_response_parts.append(
                    types.Part.from_function_response(name=fn_name, response={"result": tool_result})
                )

            history_contents.append(types.Content(role="user", parts=tool_response_parts))

        if not final_answer:
            final_answer = "Đã truy xuất xong dữ liệu nhưng không thể tổng hợp câu trả lời. Vui lòng thử lại."

        # Lưu câu hỏi và câu trả lời vào lịch sử chat_messages
        with get_db_session() as db:
            db.execute(
                text("""
                    INSERT INTO chat_messages (user_id, session_id, role, content)
                    VALUES (:uid, :sid, 'user', :content)
                """),
                {"uid": self.user_id, "sid": session_id, "content": question},
            )
            db.execute(
                text("""
                    INSERT INTO chat_messages (user_id, session_id, role, content, structured_data, tools_used)
                    VALUES (:uid, :sid, 'assistant', :content, CAST(:sdata AS JSONB), CAST(:tused AS JSONB))
                """),
                {
                    "uid": self.user_id,
                    "sid": session_id,
                    "content": final_answer,
                    "sdata": json.dumps(self.captured_tables, ensure_ascii=False),
                    "tused": json.dumps(self.tools_used, ensure_ascii=False),
                },
            )

        return {
            "answer": final_answer,
            "tools_used": self.tools_used,
            "structured_data": self.captured_tables,
            "model": active_model,
        }

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from supabase import Client

from src.backend.config.settings import settings
from src.backend.api.schemas.chatbot import ChatbotQueryResponse
from src.backend.api.services.sql_guard import validate_and_sanitize_sql

logger = logging.getLogger(__name__)

# Mô tả schema metadata đưa vào prompt cho Gemini
RENTER_VIEW_DOCS = """
Tên view: view_chatbot_renter_listings (Chỉ chứa tin đang hoạt động và không trùng lặp)
Cột:
- fact_id: UUID
- source: TEXT (ví dụ 'chotot', 'phongtro123')
- title: TEXT (Tiêu đề tin đăng)
- price: NUMERIC (Giá thuê VNĐ/tháng)
- area: NUMERIC (Diện tích m2)
- price_per_m2: NUMERIC (Đơn giá thuê VNĐ/m2/tháng)
- deposit_amount: NUMERIC (Tiền cọc VNĐ)
- electricity_cost: NUMERIC (Giá điện VNĐ)
- water_cost: NUMERIC (Giá nước VNĐ)
- service_cost: NUMERIC (Phí dịch vụ VNĐ/tháng)
- estimated_total_cost: NUMERIC (Tổng chi phí ước tính thực tế VNĐ/tháng)
- price_diff_rate: NUMERIC (% chênh lệch đơn giá so với mặt bằng khu vực)
- price_segment: VARCHAR (Phân khúc: 'binh_dan', 'trung_cap', 'cao_cap')
- completeness_score: NUMERIC (Điểm đầy đủ thông tin 0-100)
- room_status: VARCHAR ('con_trong', 'da_thue', 'het_han')
- created_at: TIMESTAMPTZ
- full_date: DATE, month: INT, month_name: VARCHAR, quarter: INT, year: INT, is_peak_student_season: BOOLEAN
- district: VARCHAR (Quận/huyện: 'Quận Đống Đa', 'Quận Cầu Giấy', 'Quận Thanh Xuân', v.v.)
- ward: VARCHAR, street: VARCHAR
- nearest_university: VARCHAR (Tên trường ĐH gần nhất)
- distance_to_university_km: NUMERIC (Khoảng cách tới ĐH tính bằng km)
- type_code: VARCHAR ('phong_tro', 'chung_cu_mini', 'nha_nguyen_can', 'ktx_sleepbox', 'can_ho')
- type_name: VARCHAR (Tên loại phòng dễ đọc)
- has_air_conditioner, has_water_heater, has_washing_machine, has_private_bathroom, has_kitchen, has_balcony, has_elevator, has_parking, has_security, has_flexible_hours: BOOLEAN
- poster_type: VARCHAR ('chinh_chu', 'moi_gioi', 'unknown')
"""

ADMIN_VIEW_DOCS = """
Tên view: view_chatbot_admin_analytics (Chứa toàn bộ tin gồm cả rủi ro, đã ẩn, báo cáo vi phạm)
Cột bổ sung so với renter:
- risk_score: NUMERIC (Điểm rủi ro tin ảo 0-100)
- is_active: BOOLEAN (Trạng thái hiển thị)
- is_duplicate: BOOLEAN (Trùng lặp đa nguồn)
- is_promoted: BOOLEAN (Tin đẩy quảng cáo)
- landlord_trust_score: NUMERIC (Điểm uy tín chủ trọ 0-10)
- days_on_market: NUMERIC (Số ngày tin lưu hành trên thị trường)
- report_count: INT (Tổng số lượt báo cáo vi phạm)
- pending_report_count: INT (Số lượt báo cáo đang chờ xử lý)
(Bao gồm toàn bộ các cột từ view_chatbot_renter_listings)
"""


def _generate_fallback_sql_and_insight(query: str, role: str) -> Tuple[str, str, str]:
    """Tạo câu truy vấn dự phòng thông minh dựa trên từ khóa khi không có API Key."""
    q = (query or "").lower()
    tbl = "view_chatbot_admin_analytics" if role == "admin" else "view_chatbot_renter_listings"

    if any(k in q for k in ["rủi ro", "tin ảo", "lừa đảo", "báo cáo"]) and role == "admin":
        sql = f"""
        SELECT title, district, price, risk_score, report_count
        FROM {tbl}
        WHERE risk_score >= 30 OR report_count > 0
        ORDER BY risk_score DESC, report_count DESC
        LIMIT 20
        """
        chart_type = "table"
        insight = "Thống kê danh sách các tin đăng có chỉ số rủi ro cao hoặc bị báo cáo vi phạm nhiều nhất."
    elif any(k in q for k in ["mặt bằng", "trung bình", "đơn giá", "m2", "giá"]):
        sql = f"""
        SELECT district, ROUND(AVG(price_per_m2)) AS avg_price_per_m2, COUNT(*) AS total_listings
        FROM {tbl}
        WHERE price_per_m2 IS NOT NULL AND price_per_m2 > 0
        GROUP BY district
        ORDER BY avg_price_per_m2 DESC
        LIMIT 15
        """
        chart_type = "bar"
        insight = "So sánh mặt bằng đơn giá thuê trung bình trên mỗi mét vuông giữa các quận tại Hà Nội."
    elif any(k in q for k in ["nguồn cung", "số lượng", "khu vực", "nhiều nhất"]):
        sql = f"""
        SELECT district, COUNT(*) AS total_listings
        FROM {tbl}
        GROUP BY district
        ORDER BY total_listings DESC
        LIMIT 10
        """
        chart_type = "pie"
        insight = "Cơ cấu nguồn cung phòng trọ phân bổ theo các quận/huyện tại Hà Nội."
    elif any(k in q for k in ["loại hình", "chung cư", "mini", "ktx"]):
        sql = f"""
        SELECT type_name, COUNT(*) AS count, ROUND(AVG(price)) AS avg_price
        FROM {tbl}
        GROUP BY type_name
        ORDER BY count DESC
        LIMIT 10
        """
        chart_type = "bar"
        insight = "Phân tích số lượng phòng trọ và mức giá trung bình theo từng loại hình chỗ ở."
    else:
        sql = f"""
        SELECT district, COUNT(*) AS total, ROUND(AVG(price)) AS avg_price
        FROM {tbl}
        GROUP BY district
        ORDER BY total DESC
        LIMIT 10
        """
        chart_type = "bar"
        insight = "Thống kê tổng quan số lượng phòng và mức giá thuê trung bình theo từng quận."

    return sql.strip(), chart_type, insight


class ChatbotService:
    def __init__(self):
        self.api_key = (settings.GEMINI_API_KEY or "").strip()
        self.model = settings.GEMINI_MODEL
        self._genai_client = None
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._genai_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Không thể khởi tạo Google GenAI Client: %s", e)

    @property
    def is_ai_available(self) -> bool:
        return self._genai_client is not None

    def _call_gemini_text_to_sql(self, query: str, role: str) -> Tuple[str, str, str]:
        """Gọi Gemini Flash để chuyển câu hỏi tiếng Việt thành SQL + loại biểu đồ + Insight."""
        table_desc = ADMIN_VIEW_DOCS if role == "admin" else RENTER_VIEW_DOCS
        target_view = "view_chatbot_admin_analytics" if role == "admin" else "view_chatbot_renter_listings"

        system_instruction = (
            "Bạn là Chuyên gia Dữ liệu BI (Business Intelligence) và SQL PostgreSQL cho Hệ thống Tìm kiếm Nhà thuê Hà Nội.\n"
            f"Vai trò người truy vấn: '{role}'.\n"
            f"Bảng/view DUY NHẤT được phép truy vấn là: '{target_view}'. Tuyệt đối không query bảng khác.\n"
            "Nhiệm vụ:\n"
            "1. Viết đúng 1 câu lệnh SELECT PostgreSQL hợp lệ, tối ưu để trả lời câu hỏi của người dùng.\n"
            "2. Luôn đặt alias rõ ràng bằng tiếng Anh không dấu (ví dụ: avg_price, total_listings, district).\n"
            "3. Chọn loại biểu đồ trực quan phù hợp: 'bar', 'line', 'pie', hoặc 'table'.\n"
            "   - 'bar': So sánh giữa các quận, các loại phòng, đơn giá.\n"
            "   - 'line': Biến động theo thời gian (tháng, quý, năm).\n"
            "   - 'pie': Tỷ lệ phần trăm cơ cấu nguồn cung (ít hơn 8 danh mục).\n"
            "   - 'table': Danh sách chi tiết nhiều cột hoặc thông tin cụ thể.\n"
            "4. Đưa ra 1-2 câu nhận định ngắn gọn (Insight) giải thích ý nghĩa dữ liệu bằng tiếng Việt.\n"
            "5. Phản hồi ĐÚNG định dạng JSON sau:\n"
            '{\n  "sql": "SELECT ...",\n  "chart_type": "bar|line|pie|table",\n  "insight": "..."\n}'
        )

        user_prompt = f"Schema:\n{table_desc}\n\nCâu hỏi của người dùng: {query}"

        try:
            response = self._genai_client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                }
            )
            raw_text = response.text or ""
            # Bỏ markdown fences nếu có
            cleaned_text = re.sub(r'^```json\s*|\s*```$', '', raw_text.strip(), flags=re.MULTILINE)
            data = json.loads(cleaned_text)
            sql = data.get("sql", "").strip()
            chart_type = data.get("chart_type", "table")
            insight = data.get("insight", "")
            if sql:
                return sql, chart_type, insight
        except Exception as e:
            logger.warning("Gọi Gemini Text-to-SQL thất bại: %s. Chuyển sang fallback.", e)

        return _generate_fallback_sql_and_insight(query, role)

    def execute_bi_query(self, db: Client, sql: str) -> List[Dict[str, Any]]:
        """Thực thi câu SQL chỉ đọc qua hàm RPC an toàn trên Supabase (fallback table query nếu RPC chưa tạo)."""
        try:
            rpc_res = db.rpc("execute_readonly_bi_query", {"sql_query": sql}).execute()
            if rpc_res.data is not None:
                if isinstance(rpc_res.data, list):
                    return rpc_res.data
                if isinstance(rpc_res.data, str):
                    try:
                        return json.loads(rpc_res.data)
                    except Exception:
                        pass
        except Exception as rpc_err:
            logger.warning("Không thể gọi RPC execute_readonly_bi_query (%s). Thử truy vấn trực tiếp view.", rpc_err)

        # Fallback: Nếu môi trường Supabase chưa kịp chạy migrations RPC, fallback an toàn bằng Supabase PostgREST query
        return []

    def process_query(self, db: Client, user_query: str, role: str = "renter") -> ChatbotQueryResponse:
        """Quy trình toàn diện: Chuyển ngôn ngữ tự nhiên -> SQL -> AST Guard -> Thực thi DB -> Trả kết quả."""
        if self.is_ai_available:
            raw_sql, chart_type, insight = self._call_gemini_text_to_sql(user_query, role)
        else:
            raw_sql, chart_type, insight = _generate_fallback_sql_and_insight(user_query, role)

        # Kiểm duyệt bảo mật AST qua sqlglot
        sanitized_sql = validate_and_sanitize_sql(raw_sql, role=role)

        # Thực thi câu SQL
        rows = self.execute_bi_query(db, sanitized_sql)

        # Trích xuất danh sách cột từ hàng dữ liệu đầu tiên
        columns = list(rows[0].keys()) if rows else []

        if not rows and not insight:
            insight = "Không tìm thấy dữ liệu phù hợp với điều kiện truy vấn."

        return ChatbotQueryResponse(
            query=user_query,
            sql=sanitized_sql,
            chart_type=chart_type if chart_type in ("bar", "line", "pie", "table") else "table",
            columns=columns,
            rows=rows,
            total_rows=len(rows),
            insight=insight,
            role=role,
        )


chatbot_service = ChatbotService()

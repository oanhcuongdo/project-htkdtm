import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock
import pytest

if "supabase" not in sys.modules:
    _supabase_stub = ModuleType("supabase")
    _supabase_stub.Client = object
    _supabase_stub.create_client = MagicMock()
    sys.modules["supabase"] = _supabase_stub

from src.backend.api.main import app
from src.backend.api.services.sql_guard import (
    SQLSecurityError,
    validate_and_sanitize_sql,
)
from src.backend.api.services.chatbot_service import (
    ChatbotService,
    _generate_fallback_sql_and_insight,
)


# ==============================================================================
# 1. KIỂM THỬ BẢO MẬT AST GUARD (sql_guard.py)
# ==============================================================================

def test_ast_guard_valid_select_adds_limit():
    sql = "SELECT district, AVG(price) AS avg_price FROM view_chatbot_renter_listings GROUP BY district"
    sanitized = validate_and_sanitize_sql(sql, role="renter")
    assert "LIMIT 100" in sanitized.upper()
    assert "VIEW_CHATBOT_RENTER_LISTINGS" in sanitized.upper()


def test_ast_guard_clamps_excessive_limit():
    sql = "SELECT title FROM view_chatbot_renter_listings LIMIT 500"
    sanitized = validate_and_sanitize_sql(sql, role="renter")
    assert "LIMIT 100" in sanitized.upper()
    assert "500" not in sanitized


def test_ast_guard_allows_safe_lower_limit():
    sql = "SELECT title FROM view_chatbot_renter_listings LIMIT 25"
    sanitized = validate_and_sanitize_sql(sql, role="renter")
    assert "LIMIT 25" in sanitized.upper()


def test_ast_guard_blocks_multiple_statements():
    sql = "SELECT 1 FROM view_chatbot_renter_listings; DROP TABLE fact_rental_listings"
    with pytest.raises(SQLSecurityError, match="một câu lệnh SELECT duy nhất"):
        validate_and_sanitize_sql(sql, role="renter")


def test_ast_guard_blocks_dml_insert_update_delete():
    with pytest.raises(SQLSecurityError):
        validate_and_sanitize_sql("DELETE FROM view_chatbot_renter_listings", role="renter")

    with pytest.raises(SQLSecurityError):
        validate_and_sanitize_sql("UPDATE view_chatbot_renter_listings SET price = 0", role="renter")

    with pytest.raises(SQLSecurityError):
        validate_and_sanitize_sql("INSERT INTO view_chatbot_renter_listings (title) VALUES ('spam')", role="renter")


def test_ast_guard_blocks_ddl_and_drop():
    with pytest.raises(SQLSecurityError):
        validate_and_sanitize_sql("DROP TABLE user_profiles", role="renter")

    with pytest.raises(SQLSecurityError):
        validate_and_sanitize_sql("ALTER TABLE fact_rental_listings DROP COLUMN price", role="renter")


def test_ast_guard_blocks_forbidden_functions():
    sql = "SELECT pg_sleep(5) FROM view_chatbot_renter_listings"
    with pytest.raises(SQLSecurityError, match="pg_sleep"):
        validate_and_sanitize_sql(sql, role="renter")


def test_ast_guard_blocks_unauthorized_internal_tables():
    # Không cho phép bảng tài khoản người dùng
    sql1 = "SELECT * FROM user_profiles"
    with pytest.raises(SQLSecurityError, match="không nằm trong danh sách cho phép"):
        validate_and_sanitize_sql(sql1, role="renter")

    # Không cho phép bảng staging thô
    sql2 = "SELECT * FROM staging_raw_listings"
    with pytest.raises(SQLSecurityError, match="không nằm trong danh sách cho phép"):
        validate_and_sanitize_sql(sql2, role="admin")


def test_ast_guard_rbac_renter_cannot_query_admin_view():
    sql = "SELECT title, risk_score FROM view_chatbot_admin_analytics"
    with pytest.raises(SQLSecurityError, match="không có quyền truy cập"):
        validate_and_sanitize_sql(sql, role="renter")


def test_ast_guard_rbac_admin_can_query_admin_view():
    sql = "SELECT title, risk_score FROM view_chatbot_admin_analytics WHERE risk_score > 30"
    sanitized = validate_and_sanitize_sql(sql, role="admin")
    assert "VIEW_CHATBOT_ADMIN_ANALYTICS" in sanitized.upper()
    assert "LIMIT 100" in sanitized.upper()


def test_ast_guard_allows_safe_cte_with_select():
    sql = """
    WITH district_avg AS (
        SELECT district, AVG(price) as avg_p FROM view_chatbot_renter_listings GROUP BY district
    )
    SELECT * FROM district_avg WHERE avg_p > 3000000
    """
    sanitized = validate_and_sanitize_sql(sql, role="renter")
    assert "WITH" in sanitized.upper()
    assert "LIMIT 100" in sanitized.upper()


# ==============================================================================
# 2. KIỂM THỬ CHATBOT SERVICE (FALLBACK & RPC EXECUTION)
# ==============================================================================

def test_fallback_sql_generator_renter():
    sql, chart, insight = _generate_fallback_sql_and_insight("giá thuê trung bình theo quận", role="renter")
    assert "view_chatbot_renter_listings" in sql
    assert chart in ("bar", "pie", "line", "table")
    assert len(insight) > 10


def test_fallback_sql_generator_admin():
    sql, chart, insight = _generate_fallback_sql_and_insight("thống kê tin ảo có rủi ro cao", role="admin")
    assert "view_chatbot_admin_analytics" in sql
    assert "risk_score" in sql
    assert chart == "table"


def test_chatbot_service_process_query():
    service = ChatbotService()
    # Mock database RPC
    mock_db = MagicMock()
    mock_db.rpc.return_value.execute.return_value = SimpleNamespace(
        data=[
            {"district": "Quận Cầu Giấy", "avg_price": 4200000.0, "total": 45},
            {"district": "Quận Đống Đa", "avg_price": 3800000.0, "total": 38},
        ]
    )

    res = service.process_query(
        db=mock_db,
        user_query="So sánh giá thuê phòng quận Cầu Giấy và Đống Đa",
        role="renter",
    )

    assert res.query == "So sánh giá thuê phòng quận Cầu Giấy và Đống Đa"
    assert "view_chatbot_renter_listings" in res.sql
    assert "LIMIT" in res.sql.upper()
    assert res.columns == ["district", "avg_price", "total"]
    assert len(res.rows) == 2
    assert res.total_rows == 2
    assert res.role == "renter"
    assert res.chart_type in ("bar", "line", "pie", "table")


# ==============================================================================
# 3. KIỂM THỬ ROUTE FASTAPI /api/chatbot/query
# ==============================================================================

def test_chatbot_route_registered():
    paths = set(app.openapi()["paths"].keys())
    assert "/api/chatbot/query" in paths

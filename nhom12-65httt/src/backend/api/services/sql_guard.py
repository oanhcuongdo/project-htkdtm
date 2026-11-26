import re
from typing import Set
import sqlglot
from sqlglot import exp
from fastapi import HTTPException, status

# Danh sách bảng/view được phép truy vấn theo vai trò
ALLOWED_TABLES_RENTER: Set[str] = {
    "view_chatbot_renter_listings",
}

ALLOWED_TABLES_ADMIN: Set[str] = {
    "view_chatbot_admin_analytics",
    "view_chatbot_renter_listings",
    "view_rental_market_analytics",
    "dim_location",
    "dim_property_type",
    "dim_time",
    "dim_amenities",
    "dim_landlord",
    "listing_reports",
}

# Các hàm bị cấm vì có nguy cơ bảo mật hoặc tấn công từ chối dịch vụ
FORBIDDEN_FUNCTIONS: Set[str] = {
    "pg_sleep",
    "version",
    "current_user",
    "session_user",
    "current_database",
    "query_to_xml",
    "query_to_json",
    "pg_read_file",
    "pg_write_file",
    "pg_ls_dir",
    "pg_stat_file",
    "dblink",
    "dblink_exec",
}

MAX_QUERY_LIMIT = 100


class SQLSecurityError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vi phạm chính sách bảo mật SQL: {detail}"
        )


def validate_and_sanitize_sql(sql_query: str, role: str = "renter") -> str:
    """
    Kiểm duyệt cây cú pháp trừu tượng (AST) của câu SQL:
    - Chỉ cho phép đúng 1 câu lệnh SELECT duy nhất (hoặc WITH CTE + SELECT).
    - Chặn toàn bộ DDL, DML (INSERT/UPDATE/DELETE/DROP/ALTER...).
    - Kiểm tra danh sách bảng/view cho phép (whitelist) theo vai trò (renter/admin).
    - Chặn các hàm hệ thống nguy hiểm (pg_sleep, file access...).
    - Tự động bổ sung hoặc ép LIMIT <= 100.
    """
    cleaned_sql = (sql_query or "").strip().rstrip(";")
    if not cleaned_sql:
        raise SQLSecurityError("Câu truy vấn SQL không được để trống.")

    # 1. Chặn nhiều câu lệnh phân tách bởi dấu chấm phẩy
    if ";" in cleaned_sql:
        raise SQLSecurityError("Chỉ cho phép thực thi đúng một câu lệnh SELECT duy nhất.")

    # 2. Phân tích cú pháp AST bằng sqlglot dialect postgres
    try:
        expressions = sqlglot.parse(cleaned_sql, read="postgres")
    except Exception as e:
        raise SQLSecurityError(f"Cú pháp SQL không hợp lệ: {str(e)}")

    if not expressions or len(expressions) != 1:
        raise SQLSecurityError("Yêu cầu đúng một biểu thức truy vấn hợp lệ.")

    ast = expressions[0]
    if ast is None:
        raise SQLSecurityError("Không thể phân tích AST của câu truy vấn.")

    # 3. Chỉ cho phép dạng Select hoặc Union chứa Select
    if not isinstance(ast, (exp.Select, exp.Union)):
        raise SQLSecurityError(f"Loại câu lệnh '{ast.key.upper()}' không được phép. Chỉ chấp nhận SELECT.")

    # 4. Kiểm tra các nút AST để chặn từ khóa nguy hiểm
    forbidden_node_types = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
        exp.Alter, exp.Command, exp.Transaction, exp.Commit, exp.Rollback,
        exp.Into, exp.Pragma
    )
    for node in ast.walk():
        if isinstance(node, forbidden_node_types):
            raise SQLSecurityError(f"Thao tác '{type(node).__name__}' bị nghiêm cấm.")

        # Kiểm tra gọi hàm nguy hiểm
        if isinstance(node, exp.Anonymous):
            func_name = node.name.lower()
            if func_name in FORBIDDEN_FUNCTIONS:
                raise SQLSecurityError(f"Hàm '{func_name}' không được phép sử dụng.")

    # 5. Kiểm tra danh sách bảng/view truy vấn theo vai trò (RBAC AST Whitelist)
    allowed_tables = ALLOWED_TABLES_ADMIN if role == "admin" else ALLOWED_TABLES_RENTER

    # Thu thập các CTE (WITH alias AS (...)) được định nghĩa trong chính câu truy vấn
    cte_names: Set[str] = {c.alias_or_name.lower() for c in ast.find_all(exp.CTE) if c.alias_or_name}

    for table_node in ast.find_all(exp.Table):
        tbl_name = table_node.name.lower()
        if not tbl_name:
            continue
        # Bỏ qua nếu là tên CTE nội bộ
        if tbl_name in cte_names:
            continue

        if tbl_name not in allowed_tables:
            if role == "renter" and tbl_name in ALLOWED_TABLES_ADMIN:
                raise SQLSecurityError(
                    f"Người dùng vai trò '{role}' không có quyền truy cập bảng/view '{tbl_name}'. "
                    f"Chỉ được phép truy vấn 'view_chatbot_renter_listings'."
                )
            raise SQLSecurityError(
                f"Bảng hoặc đối tượng '{tbl_name}' không nằm trong danh sách cho phép."
            )

    # 6. Kiểm soát và tự động ép LIMIT <= 100
    limit_node = ast.args.get("limit")
    if limit_node is None:
        ast = ast.limit(MAX_QUERY_LIMIT)
    else:
        try:
            current_limit = int(limit_node.expression.this)
            if current_limit > MAX_QUERY_LIMIT or current_limit <= 0:
                ast.set("limit", None)
                ast = ast.limit(MAX_QUERY_LIMIT)
        except (ValueError, AttributeError):
            ast.set("limit", None)
            ast = ast.limit(MAX_QUERY_LIMIT)

    # Trả về câu SQL chuẩn hóa
    return ast.sql(dialect="postgres")

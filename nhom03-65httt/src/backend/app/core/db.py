"""Kết nối PostgreSQL ở mức tối thiểu (kiểm tra tình trạng). Truy vấn nghiệp vụ sẽ thêm sau."""

from __future__ import annotations

import psycopg

EXPECTED_SCHEMAS = ("raw", "clean", "dw")


class DatabaseUnavailable(RuntimeError):
    """CSDL chưa cấu hình hoặc không kết nối được. Thông điệp không chứa mật khẩu hay địa chỉ kết nối."""


def check_database(database_url: str) -> dict[str, object]:
    """Chạy SELECT 1 và liệt kê các schema raw/clean/dw đã có."""
    if not database_url:
        raise DatabaseUnavailable("DATABASE_URL chưa được cấu hình")
    try:
        with psycopg.connect(database_url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = ANY(%s) ORDER BY 1",
                    (list(EXPECTED_SCHEMAS),),
                )
                present = [row[0] for row in cursor.fetchall()]
                cursor.execute("SELECT to_regclass('public.alembic_version')")
                migration_version = None
                if cursor.fetchone()[0] is not None:
                    cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
                    row = cursor.fetchone()
                    migration_version = row[0] if row else None
    except psycopg.Error as exc:
        # Chỉ báo tên loại lỗi, không đưa chuỗi kết nối hay nội dung lỗi (có thể chứa thông tin nhạy cảm).
        raise DatabaseUnavailable(f"Không kết nối được CSDL ({type(exc).__name__})") from exc
    return {
        "schemas_present": present,
        "schemas_missing": [name for name in EXPECTED_SCHEMAS if name not in present],
        "migration_version": migration_version,
    }

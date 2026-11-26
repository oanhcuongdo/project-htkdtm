"""Tạo tài khoản PostgreSQL chỉ đọc cho Superset và đăng ký kết nối tới schema dw.

Chạy mỗi lần container khởi động, chạy lại an toàn:
  1. Dùng tài khoản quản trị PostgreSQL (POSTGRES_USER/POSTGRES_PASSWORD) tạo vai trò `superset_ro`,
     chỉ được SELECT trên schema dw, mặc định giao dịch chỉ đọc, có giới hạn thời gian truy vấn.
  2. Đăng ký (hoặc cập nhật) kết nối "EduVision DW" trong Superset bằng vai trò đó, không dùng tài khoản quản trị.
"""

import os
import sys

import psycopg2
from psycopg2 import sql


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        sys.exit(f"Thiếu biến môi trường {name}")
    return value


HOST = env("POSTGRES_HOST", "postgres")
PORT = env("POSTGRES_PORT", "5432")
DB = env("POSTGRES_DB", "eduvision")
ADMIN_USER = env("POSTGRES_USER", "eduvision")
ADMIN_PASSWORD = env("POSTGRES_PASSWORD")
RO_USER = "superset_ro"
RO_PASSWORD = env("SUPERSET_DB_PASSWORD")
CONNECTION_NAME = "EduVision DW"


def create_readonly_role() -> None:
    conn = psycopg2.connect(host=HOST, port=PORT, dbname=DB, user=ADMIN_USER, password=ADMIN_PASSWORD)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (RO_USER,))
        if cur.fetchone():
            cur.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD %s").format(sql.Identifier(RO_USER)), (RO_PASSWORD,))
        else:
            cur.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(RO_USER)), (RO_PASSWORD,))
        role = sql.Identifier(RO_USER)
        schema = sql.Identifier("dw")
        cur.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(role))
        cur.execute(sql.SQL("ALTER ROLE {} SET statement_timeout = '60s'").format(role))
        cur.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(sql.Identifier(DB), role))
        cur.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(schema, role))
        cur.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}").format(schema, role))
        # bảng và view tạo sau này (migration của người khác) cũng tự được cấp quyền đọc
        cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} GRANT SELECT ON TABLES TO {}").format(
                sql.Identifier(ADMIN_USER), schema, role
            )
        )
    conn.close()
    print(f"[register_dw] vai trò chỉ đọc {RO_USER} sẵn sàng trên schema dw")


def register_connection() -> None:
    from superset.app import create_app

    uri = f"postgresql+psycopg2://{RO_USER}:{RO_PASSWORD}@{HOST}:{PORT}/{DB}"
    app = create_app()
    with app.app_context():
        # các mô hình của Superset chỉ nạp được bên trong ngữ cảnh ứng dụng
        from superset import db
        from superset.models.core import Database

        database = db.session.query(Database).filter_by(database_name=CONNECTION_NAME).one_or_none()
        created = database is None
        if created:
            database = Database(database_name=CONNECTION_NAME)
            db.session.add(database)
        database.set_sqlalchemy_uri(uri)
        database.expose_in_sqllab = True
        database.allow_dml = False          # không cho chạy lệnh ghi từ SQL Lab
        db.session.commit()
        print(f"[register_dw] kết nối '{CONNECTION_NAME}' đã {'tạo' if created else 'cập nhật'}")


if __name__ == "__main__":
    create_readonly_role()
    register_connection()

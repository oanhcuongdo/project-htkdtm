"""Môi trường chạy Alembic. Chỉ hỗ trợ chế độ online (kết nối thẳng PostgreSQL).

Chuỗi kết nối lấy từ biến DATABASE_URL, ví dụ postgresql://user:matkhau@localhost:5432/eduvision.
Kho dữ liệu viết bằng SQL thuần nên không dùng autogenerate (target_metadata = None).
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def get_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("Thiếu biến môi trường DATABASE_URL (xem .env.example)")
    # SQLAlchemy cần chỉ rõ driver psycopg (bản 3).
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def run_migrations_online() -> None:
    engine = create_engine(get_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError("Chế độ offline (--sql) không được hỗ trợ: các migration chạy tệp .sql trực tiếp.")

run_migrations_online()

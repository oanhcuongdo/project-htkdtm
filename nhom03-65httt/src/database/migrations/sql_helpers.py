"""Hàm dùng chung cho các migration chạy tệp SQL trong src/database/schema/."""

import os
from pathlib import Path

from alembic import op


def schema_dir() -> Path:
    """Thư mục chứa các tệp .sql: biến SCHEMA_DIR, hoặc ../schema cạnh thư mục migrations."""
    override = os.environ.get("SCHEMA_DIR", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[1] / "schema"


def run_sql_file(name: str) -> None:
    """Chạy toàn bộ một tệp SQL (nhiều câu lệnh) trong transaction của migration hiện tại."""
    path = schema_dir() / name
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy tệp schema: {path}")
    op.get_bind().exec_driver_sql(path.read_text(encoding="utf-8"))

"""Schema lõi: raw, clean, dw (dim_time, dim_platform, dim_source, fact_review)

Chạy tệp schema/01_schema_core.sql (nguồn chuẩn do Ngọc Anh quản lý).

Revision ID: 0001
Revises:
Create Date: 2026-11-23
"""
from typing import Sequence, Union

from alembic import op

from migrations.sql_helpers import run_sql_file

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("01_schema_core.sql")


def downgrade() -> None:
    # CHỈ DÙNG CHO MÁY PHÁT TRIỂN: xóa toàn bộ dữ liệu của ba schema.
    op.execute("DROP SCHEMA IF EXISTS dw CASCADE")
    op.execute("DROP SCHEMA IF EXISTS clean CASCADE")
    op.execute("DROP SCHEMA IF EXISTS raw CASCADE")

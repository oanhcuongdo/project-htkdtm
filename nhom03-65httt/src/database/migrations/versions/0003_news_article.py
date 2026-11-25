"""Bảng lưu bài báo gốc clean.news_article

Chạy tệp schema/03_schema_news.sql. Số 0003 do nhóm trưởng cấp; migration kế tiếp dùng 0004.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op

from migrations.sql_helpers import run_sql_file

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("03_schema_news.sql")


def downgrade() -> None:
    # CHỈ DÙNG CHO MÁY PHÁT TRIỂN: xóa bảng do tệp 03 tạo.
    op.execute("DROP TABLE IF EXISTS clean.news_article CASCADE")

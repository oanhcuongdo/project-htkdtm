"""Các dimension và fact còn lại của galaxy schema (đủ 6 fact, 7 dim)

Chạy tệp schema/02_schema_dims_facts.sql (nguồn chuẩn do Ngọc Anh quản lý).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-23
"""
from typing import Sequence, Union

from alembic import op

from migrations.sql_helpers import run_sql_file

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("02_schema_dims_facts.sql")


def downgrade() -> None:
    # CHỈ DÙNG CHO MÁY PHÁT TRIỂN: xóa các bảng do tệp 02 tạo (fact trước, dim sau).
    for table in (
        "fact_alert",
        "fact_news_sentiment",
        "fact_forecast",
        "fact_platform_period",
        "fact_review_aspect",
        "dim_model",
        "dim_event",
        "dim_app_version",
        "dim_aspect",
    ):
        op.execute(f"DROP TABLE IF EXISTS dw.{table} CASCADE")

"""Cột dw.fact_alert.notified_at: đánh dấu cảnh báo đã gửi email để workflow n8n không gửi lặp

Chạy tệp schema/05_schema_alert_notify.sql (mẫu: 0004_results_tables.py).

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-26
"""
from typing import Sequence, Union

from alembic import op

from migrations.sql_helpers import run_sql_file

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("05_schema_alert_notify.sql")


def downgrade() -> None:
    # CHỈ DÙNG CHO MÁY PHÁT TRIỂN: bỏ chỉ mục và cột do tệp 05 thêm.
    op.execute("DROP INDEX IF EXISTS dw.ix_fact_alert_unnotified")
    op.execute("ALTER TABLE dw.fact_alert DROP COLUMN IF EXISTS notified_at")

"""Bảng lịch sử ETL, nhật ký chất lượng, nhãn cảm xúc M1, dữ liệu khởi tạo và view cho Superset

Chạy tệp schema/04_schema_results.sql (mẫu: 0003_news_article.py).

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-26
"""
from typing import Sequence, Union

from alembic import op

from migrations.sql_helpers import run_sql_file

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    run_sql_file("04_schema_results.sql")


def downgrade() -> None:
    # CHỈ DÙNG CHO MÁY PHÁT TRIỂN: xóa view và bảng do tệp 04 tạo.
    # Dữ liệu khởi tạo (dim_aspect, dim_model, dim_time) được giữ lại vì có thể đã được bảng khác tham chiếu;
    # nâng cấp lại dùng ON CONFLICT DO NOTHING nên không sinh trùng.
    op.execute("DROP VIEW IF EXISTS dw.v_alert_open")
    op.execute("DROP VIEW IF EXISTS dw.v_platform_month")
    op.execute("DROP VIEW IF EXISTS dw.v_review_enriched")
    op.execute("DROP TABLE IF EXISTS dw.fact_review_sentiment")
    op.execute("DROP TABLE IF EXISTS dw.data_quality_log")
    op.execute("DROP TABLE IF EXISTS dw.etl_run_log")

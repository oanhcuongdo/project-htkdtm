"""Create the AI key store and migrate runtime-only schema changes.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = inspect(connection)
    if not inspector.has_table("ai_api_keys"):
        op.create_table(
            "ai_api_keys",
            sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("key_name", sa.String(100), nullable=False),
            sa.Column("api_key", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("usage_count", sa.Integer(), nullable=False),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    existing_indexes = {index["name"] for index in inspect(connection).get_indexes("ai_api_keys")}
    for name, column in (
        ("ix_ai_api_keys_provider", "provider"),
        ("ix_ai_api_keys_is_active", "is_active"),
    ):
        if name not in existing_indexes:
            op.create_index(name, "ai_api_keys", [column])

    # Earlier API versions added these columns at application startup. Keep
    # the migration safe for databases where that startup already ran.
    op.execute("ALTER TABLE quiz_attempts ADD COLUMN IF NOT EXISTS answers_detail JSONB DEFAULT '[]'::jsonb")
    op.execute("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS mindmap_markdown TEXT")
    op.execute("ALTER TABLE lessons ADD COLUMN IF NOT EXISTS audio_summary_url VARCHAR(500)")

    quota_columns = {column["name"]: column["type"] for column in inspect(connection).get_columns("quotas")}
    for name in ("token_limit", "token_used"):
        if not isinstance(quota_columns[name], sa.BigInteger):
            op.alter_column("quotas", name, existing_type=quota_columns[name], type_=sa.BigInteger())


def downgrade() -> None:
    raise RuntimeError("This migration widens quota columns and may contain AI keys; rollback requires a reviewed data migration")

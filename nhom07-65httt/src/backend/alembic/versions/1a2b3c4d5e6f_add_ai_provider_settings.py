"""Add database-managed AI provider model settings."""

from alembic import op
import sqlalchemy as sa


revision = "1a2b3c4d5e6f"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_provider_settings",
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_id", sa.String(length=100), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("provider"),
    )
    op.execute(
        "INSERT INTO ai_provider_settings (provider, model_id, updated_at) "
        "VALUES ('gemini', 'gemini-3.5-flash-lite', CURRENT_TIMESTAMP)"
    )


def downgrade() -> None:
    op.drop_table("ai_provider_settings")

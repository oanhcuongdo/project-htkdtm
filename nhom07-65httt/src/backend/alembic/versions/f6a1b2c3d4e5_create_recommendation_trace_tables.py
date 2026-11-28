"""Create immutable recommendation run and item trace tables.

Revision ID: f6a1b2c3d4e5
Revises: e7f8a9b0c1d2
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "f6a1b2c3d4e5"
down_revision: Union[str, Sequence[str], None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=True),
        sa.Column("learner_key", sa.String(length=128), nullable=True),
        sa.Column("model_name", sa.String(length=16), nullable=False),
        sa.Column("model_version", sa.String(length=255), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=128), nullable=False),
        sa.Column("candidate_set_hash", sa.String(length=64), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column(
            "input_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "filter_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "model_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("trace_sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "top_k >= 1",
            name="ck_recommendation_runs_top_k_positive",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "request_id",
            name="uq_recommendation_runs_request_id",
        ),
    )
    op.create_index(
        "ix_recommendation_runs_model_dataset_created",
        "recommendation_runs",
        ["model_name", "model_version", "dataset_version_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_recommendation_runs_student_created",
        "recommendation_runs",
        ["student_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "recommendation_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recommendation_run_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.String(length=255), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("score_scale", sa.String(length=32), nullable=False),
        sa.Column("ranking_method", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=255), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=128), nullable=False),
        sa.Column(
            "score_components",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "score_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "course_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "explanation",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.CheckConstraint(
            "rank >= 1",
            name="ck_recommendation_items_rank_positive",
        ),
        sa.ForeignKeyConstraint(
            ["recommendation_run_id"],
            ["recommendation_runs.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recommendation_run_id",
            "course_id",
            name="uq_recommendation_items_run_course",
        ),
        sa.UniqueConstraint(
            "recommendation_run_id",
            "rank",
            name="uq_recommendation_items_run_rank",
        ),
    )
    op.create_index(
        "ix_recommendation_items_course_id",
        "recommendation_items",
        ["course_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recommendation_items_course_id",
        table_name="recommendation_items",
    )
    op.drop_table("recommendation_items")
    op.drop_index(
        "ix_recommendation_runs_student_created",
        table_name="recommendation_runs",
    )
    op.drop_index(
        "ix_recommendation_runs_model_dataset_created",
        table_name="recommendation_runs",
    )
    op.drop_table("recommendation_runs")

"""Persist offline model evaluation metrics and benchmark metadata.

Revision ID: a7b8c9d0e1f2
Revises: f6a1b2c3d4e5
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "model_evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("evaluation_batch_id", sa.Uuid(), nullable=False),
        sa.Column("batch_sha256", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=255), nullable=False),
        sa.Column("dataset_version_id", sa.String(length=128), nullable=False),
        sa.Column("split_name", sa.String(length=16), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("profile_count", sa.Integer(), nullable=False),
        sa.Column("labeled_pair_count", sa.Integer(), nullable=False),
        sa.Column("course_count", sa.Integer(), nullable=False),
        sa.Column("ndcg_at_5", sa.Float(), nullable=False),
        sa.Column("precision_at_5", sa.Float(), nullable=False),
        sa.Column("prerequisite_violations", sa.Integer(), nullable=False),
        sa.Column("profiles_under_5_results", sa.Integer(), nullable=False),
        sa.Column("p50_latency_ms", sa.Float(), nullable=False),
        sa.Column("p95_latency_ms", sa.Float(), nullable=False),
        sa.Column("relative_ndcg_gain_vs_m0", sa.Float(), nullable=True),
        sa.Column(
            "goal_status",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "evaluation_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "top_k >= 1",
            name="ck_model_evaluations_top_k_positive",
        ),
        sa.CheckConstraint(
            "profile_count >= 1 AND labeled_pair_count >= 0 AND course_count >= 1",
            name="ck_model_evaluations_counts_nonnegative",
        ),
        sa.CheckConstraint(
            "ndcg_at_5 >= 0 AND ndcg_at_5 <= 1 "
            "AND precision_at_5 >= 0 AND precision_at_5 <= 1",
            name="ck_model_evaluations_metrics_range",
        ),
        sa.CheckConstraint(
            "prerequisite_violations >= 0 AND profiles_under_5_results >= 0 "
            "AND profiles_under_5_results <= profile_count",
            name="ck_model_evaluations_counts_range",
        ),
        sa.CheckConstraint(
            "p50_latency_ms >= 0 AND p95_latency_ms >= 0",
            name="ck_model_evaluations_latency_nonnegative",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "evaluation_batch_id",
            "model_name",
            name="uq_model_evaluations_batch_model",
        ),
    )
    op.create_index(
        "ix_model_evaluations_model_dataset_created",
        "model_evaluations",
        ["model_name", "dataset_version_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_model_evaluations_model_dataset_created",
        table_name="model_evaluations",
    )
    op.drop_table("model_evaluations")

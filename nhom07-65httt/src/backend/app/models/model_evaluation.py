from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


EVALUATION_JSON = JSON().with_variant(JSONB(), "postgresql")


class ModelEvaluation(Base):
    __tablename__ = "model_evaluations"
    __table_args__ = (
        CheckConstraint("top_k >= 1", name="ck_model_evaluations_top_k_positive"),
        CheckConstraint(
            "profile_count >= 1 AND labeled_pair_count >= 0 AND course_count >= 1",
            name="ck_model_evaluations_counts_nonnegative",
        ),
        CheckConstraint(
            "ndcg_at_5 >= 0 AND ndcg_at_5 <= 1 "
            "AND precision_at_5 >= 0 AND precision_at_5 <= 1",
            name="ck_model_evaluations_metrics_range",
        ),
        CheckConstraint(
            "prerequisite_violations >= 0 AND profiles_under_5_results >= 0 "
            "AND profiles_under_5_results <= profile_count",
            name="ck_model_evaluations_counts_range",
        ),
        CheckConstraint(
            "p50_latency_ms >= 0 AND p95_latency_ms >= 0",
            name="ck_model_evaluations_latency_nonnegative",
        ),
        UniqueConstraint(
            "evaluation_batch_id",
            "model_name",
            name="uq_model_evaluations_batch_model",
        ),
        Index(
            "ix_model_evaluations_model_dataset_created",
            "model_name",
            "dataset_version_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    evaluation_batch_id: Mapped[UUID] = mapped_column(nullable=False)
    batch_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    split_name: Mapped[str] = mapped_column(String(16), nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_count: Mapped[int] = mapped_column(Integer, nullable=False)
    labeled_pair_count: Mapped[int] = mapped_column(Integer, nullable=False)
    course_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ndcg_at_5: Mapped[float] = mapped_column(Float, nullable=False)
    precision_at_5: Mapped[float] = mapped_column(Float, nullable=False)
    prerequisite_violations: Mapped[int] = mapped_column(Integer, nullable=False)
    profiles_under_5_results: Mapped[int] = mapped_column(Integer, nullable=False)
    p50_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    p95_latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    relative_ndcg_gain_vs_m0: Mapped[float | None] = mapped_column(Float)
    goal_status: Mapped[dict[str, Any]] = mapped_column(EVALUATION_JSON, nullable=False)
    evaluation_metadata: Mapped[dict[str, Any]] = mapped_column(
        EVALUATION_JSON, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

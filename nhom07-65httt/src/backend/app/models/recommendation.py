from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


SNAPSHOT_JSON = JSON().with_variant(JSONB(), "postgresql")


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"
    __table_args__ = (
        CheckConstraint("top_k >= 1", name="ck_recommendation_runs_top_k_positive"),
        UniqueConstraint("request_id", name="uq_recommendation_runs_request_id"),
        Index(
            "ix_recommendation_runs_model_dataset_created",
            "model_name",
            "model_version",
            "dataset_version_id",
            "created_at",
        ),
        Index(
            "ix_recommendation_runs_student_created",
            "student_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    request_id: Mapped[UUID] = mapped_column(unique=True, nullable=False)
    student_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    learner_key: Mapped[str | None] = mapped_column(String(128))
    model_name: Mapped[str] = mapped_column(String(16), nullable=False)
    model_version: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    candidate_set_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    top_k: Mapped[int] = mapped_column(Integer, nullable=False)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(
        SNAPSHOT_JSON, nullable=False
    )
    filter_snapshot: Mapped[dict[str, Any]] = mapped_column(
        SNAPSHOT_JSON, nullable=False
    )
    model_config: Mapped[dict[str, Any]] = mapped_column(SNAPSHOT_JSON, nullable=False)
    trace_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    student: Mapped["User | None"] = relationship()
    items: Mapped[list["RecommendationItem"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecommendationItem.rank",
    )


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"
    __table_args__ = (
        CheckConstraint("rank >= 1", name="ck_recommendation_items_rank_positive"),
        UniqueConstraint(
            "recommendation_run_id",
            "course_id",
            name="uq_recommendation_items_run_course",
        ),
        UniqueConstraint(
            "recommendation_run_id",
            "rank",
            name="uq_recommendation_items_run_rank",
        ),
        Index("ix_recommendation_items_course_id", "course_id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    recommendation_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("recommendation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[str] = mapped_column(String(255), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    score_scale: Mapped[str] = mapped_column(String(32), nullable=False)
    ranking_method: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_version_id: Mapped[str] = mapped_column(String(128), nullable=False)
    score_components: Mapped[dict[str, float | None] | None] = mapped_column(
        SNAPSHOT_JSON
    )
    score_metadata: Mapped[dict[str, Any] | None] = mapped_column(SNAPSHOT_JSON)
    course_snapshot: Mapped[dict[str, Any]] = mapped_column(
        SNAPSHOT_JSON, nullable=False
    )
    explanation: Mapped[dict[str, Any]] = mapped_column(SNAPSHOT_JSON, nullable=False)
    run: Mapped[RecommendationRun] = relationship(back_populates="items")

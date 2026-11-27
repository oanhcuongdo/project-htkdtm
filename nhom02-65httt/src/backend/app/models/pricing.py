"""Smart Pricing, approval workflow, marketplace sync logs, and ML run ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, TimestampMixin, utc_now


class PricingRule(TimestampMixin, Base):
    """Pricing strategy rules and guardrails."""

    __tablename__ = "pricing_rules"
    __table_args__ = (
        CheckConstraint(
            "rule_type IN ('FLASH_SALE', 'SKIMMING', 'CLEARANCE', "
            "'COMPETITOR_MATCH', 'MARGIN_GUARD')",
            name="rule_type_valid",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'PAUSED', 'ARCHIVED')",
            name="status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default=text("100")
    )
    scope_label: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sales_channels.id", ondelete="SET NULL"),
        nullable=True,
    )
    min_margin: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    max_price_change_pct: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    approval_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="DRAFT", server_default=text("'DRAFT'")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PriceRecommendation(CreatedAtMixin, Base):
    """AI/Rule pricing recommendation snapshot with explainability payload."""

    __tablename__ = "price_recommendations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'EXECUTION_QUEUED', "
            "'EXECUTED', 'REJECTED', 'EXPIRED', 'FAILED', 'CANCELLED')",
            name="status_valid",
        ),
        CheckConstraint("data_quality IN ('HIGH', 'MEDIUM', 'LOW')", name="data_quality_valid"),
        CheckConstraint(
            "algorithm_type IN ('RULE_BASED', 'ML_ASSISTED')",
            name="algorithm_type_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sales_channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("pricing_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="DRAFT", server_default=text("'DRAFT'")
    )
    current_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    floor_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    recommended_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expected_profit_per_unit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expected_margin: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    channel_fee_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    competitor_median: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    target_margin: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False)
    predicted_demand: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    data_quality: Mapped[str] = mapped_column(
        String(16), nullable=False, default="HIGH", server_default=text("'HIGH'")
    )
    algorithm_type: Mapped[str] = mapped_column(
        String(24), nullable=False, default="RULE_BASED", server_default=text("'RULE_BASED'")
    )
    algorithm_version: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(String(150), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PriceApproval(Base):
    """Manager decision history on price recommendations."""

    __tablename__ = "price_approvals"
    __table_args__ = (
        CheckConstraint("decision IN ('APPROVED', 'REJECTED')", name="decision_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("price_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    adjusted_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )


class PriceSyncLog(TimestampMixin, Base):
    """Execution log for marketplace price push attempts (SIMULATED or API_CONFIRMED)."""

    __tablename__ = "price_sync_logs"
    __table_args__ = (
        CheckConstraint("mode IN ('SIMULATED', 'LIVE')", name="mode_valid"),
        CheckConstraint(
            "sync_mode IN ('SIMULATED', 'API_CONFIRMED')",
            name="sync_mode_valid",
        ),
        CheckConstraint(
            "status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED', 'CANCELLED')",
            name="status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("price_recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sales_channels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sku_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    channel_code: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    sync_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    requested_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    previous_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="QUEUED", index=True, server_default=text("'QUEUED'")
    )
    attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    external_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )


class ModelRun(Base):
    """ML model training run registry and error metrics (MAE, RMSE)."""

    __tablename__ = "model_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm_type: Mapped[str] = mapped_column(String(32), nullable=False)
    feature_columns_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    train_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    test_samples: Mapped[int] = mapped_column(Integer, nullable=False)
    mae: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    rmse: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    artifact_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
    )

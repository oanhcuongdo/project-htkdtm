"""Market, sales channel, competitor price history, and sales record ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAtMixin, TimestampMixin


class SalesChannel(TimestampMixin, Base):
    """Configured marketplace / e-commerce sales channels and fee structures."""

    __tablename__ = "sales_channels"
    __table_args__ = (
        CheckConstraint(
            "code IN ('SHOPEE', 'LAZADA', 'TIKTOK_SHOP', 'TIKI', 'WEBSITE', 'OTHER')",
            name="code_valid",
        ),
        CheckConstraint(
            "integration_mode IN ('SIMULATED', 'LIVE')",
            name="integration_mode_valid",
        ),
        CheckConstraint(
            "connection_status IN ('NOT_CONNECTED', 'DEMO', 'CONNECTED', 'ERROR', 'DISABLED')",
            name="connection_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    integration_mode: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SIMULATED", server_default=text("'SIMULATED'")
    )
    connection_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="DEMO", server_default=text("'DEMO'")
    )
    platform_fee_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("0.0000"), server_default=text("0.0000")
    )
    payment_fee_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("0.0000"), server_default=text("0.0000")
    )
    service_fee_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("0.0000"), server_default=text("0.0000")
    )
    fee_rate: Mapped[Decimal] = mapped_column(
        Numeric(6, 4), nullable=False, default=Decimal("0.0000"), server_default=text("0.0000")
    )
    fee_effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fee_source: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class ChannelProduct(TimestampMixin, Base):
    """Mapping between an internal SKU and an external marketplace listing."""

    __tablename__ = "channel_products"
    __table_args__ = (
        UniqueConstraint("product_id", "channel_id", name="product_channel"),
        CheckConstraint(
            "sync_status IN ('SYNCED', 'PENDING', 'ERROR', 'NOT_MAPPED')",
            name="sync_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sales_channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_listing_id: Mapped[str] = mapped_column(String(120), nullable=False)
    external_sku: Mapped[str] = mapped_column(String(120), nullable=False)
    external_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    sync_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="PENDING", server_default=text("'PENDING'")
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CompetitorPrice(CreatedAtMixin, Base):
    """Observed competitor prices and entity-resolution metadata."""

    __tablename__ = "competitor_prices"
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('MANUAL', 'CSV', 'API', 'PUBLIC_PAGE', 'DEMO')",
            name="source_type_valid",
        ),
        CheckConstraint(
            "match_status IN ('AUTO_MATCHED', 'NEEDS_REVIEW', 'REJECTED')",
            name="match_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sku_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    competitor_name: Mapped[str] = mapped_column(String(150), nullable=False)
    marketplace_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(24), nullable=False)
    source_name: Mapped[str] = mapped_column(String(150), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    external_item_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_model_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    listed_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    effective_price: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    sold_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("1.00"), server_default=text("1.00")
    )
    match_status: Mapped[str] = mapped_column(
        String(24), nullable=False, default="AUTO_MATCHED", server_default=text("'AUTO_MATCHED'")
    )
    verdict: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fake_sale_warning: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    is_outlier: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )


class CompetitorPriceHistory(CreatedAtMixin, Base):
    """Historical competitor price time-series points extracted from crawlers."""

    __tablename__ = "competitor_price_history"
    __table_args__ = (
        UniqueConstraint("competitor_price_id", "recorded_date", name="competitor_price_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competitor_price_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("competitor_prices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)


class SalesRecord(CreatedAtMixin, Base):
    """Daily aggregated internal sales transactions used for ML training and BI."""

    __tablename__ = "sales_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sales_channels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    channel_fee_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    net_profit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

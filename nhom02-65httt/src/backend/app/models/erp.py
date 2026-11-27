"""Core ERP ORM models: categories, suppliers, products, costs, and inventory."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, utc_now


class Category(TimestampMixin, Base):
    """Product category master table."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class Supplier(TimestampMixin, Base):
    """Supplier / vendor directory."""

    __tablename__ = "suppliers"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="status_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    lead_time_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default=text("3")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", server_default=text("'ACTIVE'")
    )
    last_quoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Product(TimestampMixin, Base):
    """Internal master SKU catalog."""

    __tablename__ = "products"
    __table_args__ = (CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="status_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    variant_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_code: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    primary_supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    unit: Mapped[str] = mapped_column(
        String(32), nullable=False, default="Cái", server_default=text("'Cái'")
    )
    current_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="ACTIVE", server_default=text("'ACTIVE'")
    )


class SupplierProduct(TimestampMixin, Base):
    """Supplier-to-SKU quotation and lead-time mapping."""

    __tablename__ = "supplier_products"
    __table_args__ = (UniqueConstraint("supplier_id", "product_id", name="supplier_product"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purchase_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    min_order_qty: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    lead_time_days: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default=text("3")
    )
    last_quoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_preferred: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )


class CostComponent(Base):
    """Unit cost breakdown (purchase + inbound + packaging + other) per SKU."""

    __tablename__ = "cost_components"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    purchase_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    inbound_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    packaging_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    other_cost: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00"), server_default=text("0.00")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
    )


class Inventory(Base):
    """Current warehouse inventory balance and reorder threshold per SKU."""

    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("on_hand_qty >= 0", name="on_hand_non_negative"),
        CheckConstraint("reserved_qty >= 0", name="reserved_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    warehouse_name: Mapped[str] = mapped_column(
        String(150), nullable=False, default="Kho tổng", server_default=text("'Kho tổng'")
    )
    on_hand_qty: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    reserved_qty: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    reorder_point: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10, server_default=text("10")
    )
    days_of_supply: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=func.now(),
        onupdate=utc_now,
    )

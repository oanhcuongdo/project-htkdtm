"""Dữ liệu đơn COD; tạo đơn và chuyển trạng thái được thực hiện trong service."""

import math
import re
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base
from app.menu.models import MenuItem
from app.restaurants.models import Restaurant
from app.users.models import User


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    DELIVERING = "delivering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


def _status_type(constraint_name: str):
    return Enum(
        OrderStatus,
        values_callable=lambda statuses: [status.value for status in statuses],
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        name=constraint_name,
        length=20,
    )


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Thời điểm phải có múi giờ.")
    return value.astimezone(UTC)


def _positive_integer(value: int, field: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"{field} phải là số nguyên từ 1 đến {maximum}.")
    return value


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_orders_idempotency_key"),
        CheckConstraint("total > 0", name="ck_orders_total"),
        CheckConstraint(
            "length(trim(delivery_address)) BETWEEN 5 AND 500", name="ck_orders_delivery_address"
        ),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_orders_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_orders_longitude"),
        CheckConstraint("length(payload_hash) = 64", name="ck_orders_payload_hash"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        _status_type("ck_orders_status"),
        nullable=False,
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
    )
    total: Mapped[int] = mapped_column(BigInteger, nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    idempotency_key: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now()
    )

    user: Mapped[User] = relationship()
    restaurant: Mapped[Restaurant] = relationship()
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", passive_deletes="all")
    history: Mapped[list["OrderStatusHistory"]] = relationship(
        back_populates="order",
        passive_deletes="all",
        order_by="(OrderStatusHistory.created_at, OrderStatusHistory.id)",
    )

    @validates("total")
    def validate_total(self, key: str, value: int) -> int:
        return _positive_integer(value, key, 2**63 - 1)

    @validates("delivery_address")
    def normalize_address(self, _key: str, value: str) -> str:
        if not isinstance(value, str) or not 5 <= len(value.strip()) <= 500:
            raise ValueError("Địa chỉ giao hàng phải có từ 5 đến 500 ký tự.")
        return value.strip()

    @validates("latitude", "longitude")
    def validate_coordinate(self, key: str, value: float) -> float:
        maximum = 90 if key == "latitude" else 180
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not -maximum <= value <= maximum
        ):
            raise ValueError(f"{key} phải là số hữu hạn trong [-{maximum}, {maximum}].")
        return float(value)

    @validates("session_id", "idempotency_key")
    def normalize_uuid(self, key: str, value: UUID | str) -> UUID:
        if isinstance(value, str):
            value = UUID(value)
        if not isinstance(value, UUID) or value.version != 4:
            raise ValueError(f"{key} phải là UUID v4.")
        return value

    @validates("payload_hash")
    def normalize_payload_hash(self, _key: str, value: str) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
            raise ValueError("payload_hash phải là chuỗi SHA-256 dạng hex 64 ký tự.")
        return value.lower()

    @validates("created_at")
    def normalize_created_at(self, _key: str, value: datetime) -> datetime:
        return _utc_timestamp(value)


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "menu_item_id", name="uq_order_items_order_menu_item"),
        CheckConstraint("quantity BETWEEN 1 AND 99", name="ck_order_items_quantity"),
        CheckConstraint(
            "snapshot_price > 0 AND snapshot_price <= 10000000",
            name="ck_order_items_snapshot_price",
        ),
        CheckConstraint(
            "length(trim(snapshot_name)) BETWEEN 1 AND 180", name="ck_order_items_snapshot_name"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_price: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_name: Mapped[str] = mapped_column(String(180), nullable=False)

    order: Mapped[Order] = relationship(back_populates="items")
    menu_item: Mapped[MenuItem] = relationship()

    @validates("quantity", "snapshot_price")
    def validate_amount(self, key: str, value: int) -> int:
        return _positive_integer(value, key, 99 if key == "quantity" else 10000000)

    @validates("snapshot_name")
    def normalize_name(self, _key: str, value: str) -> str:
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 180:
            raise ValueError("Tên món chụp tại thời điểm đặt phải có từ 1 đến 180 ký tự.")
        return value.strip()


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    __table_args__ = (
        CheckConstraint(
            "reason IS NULL OR length(trim(reason)) BETWEEN 1 AND 500",
            name="ck_order_history_reason",
        ),
        CheckConstraint(
            "status <> 'rejected' OR reason IS NOT NULL", name="ck_order_history_rejection_reason"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        _status_type("ck_order_history_status"), nullable=False
    )
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now()
    )

    order: Mapped[Order] = relationship(back_populates="history")
    actor: Mapped[User] = relationship()

    @validates("reason")
    def normalize_reason(self, _key: str, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 500:
            raise ValueError("Lý do phải có từ 1 đến 500 ký tự khi được cung cấp.")
        return value.strip()

    @validates("created_at")
    def normalize_created_at(self, _key: str, value: datetime) -> datetime:
        return _utc_timestamp(value)

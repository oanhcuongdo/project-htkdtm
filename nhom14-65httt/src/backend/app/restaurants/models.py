"""Dữ liệu quán, giờ phục vụ và các tài khoản được liên kết quản lý."""

import math
import re
from datetime import time
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Time,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base
from app.users.models import User


class RestaurantStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"


class Restaurant(Base):
    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_restaurants_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_restaurants_longitude"),
        CheckConstraint(
            "delivery_radius_km > 0 AND delivery_radius_km <= 50",
            name="ck_restaurants_delivery_radius",
        ),
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 160", name="ck_restaurants_name"),
        CheckConstraint("length(trim(address)) BETWEEN 1 AND 500", name="ck_restaurants_address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    delivery_radius_km: Mapped[float] = mapped_column(
        Float, nullable=False, default=5.0, server_default=text("5")
    )
    opens_at: Mapped[time] = mapped_column(
        Time, nullable=False, default=time(0, 0), server_default=text("'00:00:00'")
    )
    closes_at: Mapped[time] = mapped_column(
        Time, nullable=False, default=time(0, 0), server_default=text("'00:00:00'")
    )
    accepting_orders: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    status: Mapped[RestaurantStatus] = mapped_column(
        Enum(
            RestaurantStatus,
            values_callable=lambda statuses: [status.value for status in statuses],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="ck_restaurants_status",
            length=20,
        ),
        nullable=False,
        default=RestaurantStatus.PENDING,
        server_default=RestaurantStatus.PENDING.value,
    )
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    memberships: Mapped[list["RestaurantMembership"]] = relationship(
        back_populates="restaurant", passive_deletes="all"
    )

    @validates("name", "address")
    def normalize_text(self, key: str, value: str) -> str:
        maximum = 160 if key == "name" else 500
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
            raise ValueError(f"{key} phải có từ 1 đến {maximum} ký tự sau khi bỏ khoảng trắng.")
        return value.strip()

    @validates("latitude", "longitude", "delivery_radius_km")
    def validate_coordinate_or_radius(self, key: str, value: float) -> float:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{key} phải là số hữu hạn.")
        if key == "delivery_radius_km":
            valid = 0 < value <= 50
        else:
            maximum = 90 if key == "latitude" else 180
            valid = -maximum <= value <= maximum
        if not valid:
            raise ValueError(f"{key} nằm ngoài giới hạn cho phép.")
        return float(value)

    @validates("opens_at", "closes_at")
    def validate_opening_time(self, key: str, value: time | str) -> time:
        if isinstance(value, str) and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            value = time.fromisoformat(value)
        if (
            not isinstance(value, time)
            or value.tzinfo is not None
            or value.second != 0
            or value.microsecond != 0
        ):
            raise ValueError(f"{key} phải là giờ địa phương HH:MM, chính xác đến phút.")
        return value


class RestaurantMembership(Base):
    __tablename__ = "restaurant_memberships"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True
    )
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    user: Mapped[User] = relationship()
    restaurant: Mapped[Restaurant] = relationship(back_populates="memberships")

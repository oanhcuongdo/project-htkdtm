"""User model dùng chung cho khách hàng, chủ quán và quản trị viên."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, UniqueConstraint, false, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.database import Base


class UserRole(StrEnum):
    CUSTOMER = "customer"
    VENDOR = "vendor"
    ADMIN = "admin"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            values_callable=lambda roles: [role.value for role in roles],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="ck_users_role",
            length=20,
        ),
        nullable=False,
        default=UserRole.CUSTOMER,
        server_default=UserRole.CUSTOMER.value,
    )
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now()
    )

    @validates("email")
    def normalize_email(self, _key: str, value: str) -> str:
        """Thống nhất email trước khi kiểm tra UNIQUE ở cơ sở dữ liệu."""
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Email không được để trống.")
        return normalized

    @validates("full_name")
    def normalize_full_name(self, _key: str, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Họ tên không được để trống.")
        return normalized

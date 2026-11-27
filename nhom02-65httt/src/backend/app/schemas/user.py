"""User CRUD schemas matching frontend domain types."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.core.rbac import Role
from app.schemas.common import ApiModel


def _strip_non_empty(value: str, field_label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_label} không được để trống.")
    return cleaned


class UserRead(ApiModel):
    """Public user representation returned by API endpoints."""

    id: UUID
    full_name: str
    email: str
    role: Role
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime


class UserCreate(ApiModel):
    """Payload to create a new user account."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=150)
    role: Role
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("full_name")
    @classmethod
    def _clean_full_name(cls, value: str) -> str:
        return _strip_non_empty(value, "Họ và tên")


class UserUpdate(ApiModel):
    """Payload to update an existing user account."""

    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    role: Role | None = None
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def _clean_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_non_empty(value, "Họ và tên")

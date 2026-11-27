"""Authentication request and response schemas."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import ApiModel
from app.schemas.user import UserRead


class LoginRequest(ApiModel):
    """Credentials payload for POST /auth/login."""

    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1)


class LoginData(ApiModel):
    """Access token and authenticated user payload."""

    token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead

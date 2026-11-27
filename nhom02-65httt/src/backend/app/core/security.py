"""Password hashing (bcrypt) and JWT token helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from functools import lru_cache
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import UnauthorizedError


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


@lru_cache(maxsize=1)
def get_dummy_password_hash() -> str:
    """Return a cached dummy bcrypt hash to equalize timing when email does not exist."""
    return hash_password("dummy-timing-equalizer-password")


def create_access_token(
    user_id: str | UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for a user."""
    settings = get_settings()
    now = datetime.now(UTC)
    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + lifetime,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate an access token, raising UnauthorizedError on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat", "type"]},
        )
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedError("Token xác thực không hợp lệ hoặc đã hết hạn.") from exc

    if payload.get("type") != "access" or not payload.get("sub"):
        raise UnauthorizedError("Token xác thực không hợp lệ.")
    return payload

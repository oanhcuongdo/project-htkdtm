"""Authentication endpoints: login and current user profile."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.core.security import (
    create_access_token,
    get_dummy_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginData, LoginRequest
from app.schemas.common import Envelope
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Envelope[LoginData])
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> Envelope[LoginData]:
    """Authenticate by email/password and return a Bearer JWT token."""
    normalized_email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == normalized_email))

    if user is None:
        verify_password(payload.password, get_dummy_password_hash())
        raise UnauthorizedError("Email hoặc mật khẩu không đúng.")

    # Verify password before checking is_active to avoid leaking account existence.
    if not verify_password(payload.password, user.hashed_password):
        raise UnauthorizedError("Email hoặc mật khẩu không đúng.")

    if not user.is_active:
        raise ForbiddenError("Tài khoản đã bị vô hiệu hóa.")

    user.last_login_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)

    settings = get_settings()
    token = create_access_token(user.id, user.role)
    return Envelope(
        data=LoginData(
            token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRead.model_validate(user),
        )
    )


@router.get("/me", response_model=Envelope[UserRead])
def read_me(current_user: User = Depends(get_current_user)) -> Envelope[UserRead]:
    """Return the authenticated user's profile."""
    return Envelope(data=UserRead.model_validate(current_user))

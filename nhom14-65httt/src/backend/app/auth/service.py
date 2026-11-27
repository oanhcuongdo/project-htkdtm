"""Nghiệp vụ tài khoản; vai trò thực tế luôn được đọc lại từ DB."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.auth.utils import (
    DUMMY_PASSWORD_HASH,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings
from app.exceptions import AppError, ConflictError
from app.users.models import User


def register(db: Session, payload: RegisterRequest) -> User:
    if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
        raise ConflictError("EMAIL_EXISTS", "Email đã được sử dụng.")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
            raise ConflictError("EMAIL_EXISTS", "Email đã được sử dụng.") from None
        raise
    db.refresh(user)
    return user


def _tokens(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


def login(db: Session, payload: LoginRequest) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    valid_password = verify_password(
        payload.password, user.hashed_password if user else DUMMY_PASSWORD_HASH
    )
    if user is None or not valid_password:
        raise AppError("INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng.", 401)
    return _tokens(user)


def refresh(db: Session, token: str) -> TokenResponse:
    user = db.get(User, decode_token(token, "refresh"))
    if user is None:
        raise AppError("UNAUTHENTICATED", "Vui lòng đăng nhập lại.", 401)
    return _tokens(user)

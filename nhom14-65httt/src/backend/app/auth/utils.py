"""Băm mật khẩu và cấp/kiểm tra JWT có phân biệt access với refresh."""

import re
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256

from app.config import settings
from app.exceptions import AppError

PASSWORD_ROUNDS = 600_000
ISSUER = "viviet"
AUDIENCE = "viviet-api"
TokenKind = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    """Dùng định dạng PBKDF2 của Passlib với salt ngẫu nhiên cho mỗi mật khẩu."""
    return pbkdf2_sha256.using(rounds=PASSWORD_ROUNDS).hash(password)


def verify_password(password: str, encoded: str) -> bool:
    try:
        return pbkdf2_sha256.verify(password, encoded)
    except (ValueError, TypeError):
        return False


# Vẫn băm khi email không tồn tại, thay vì trả lỗi trước bước kiểm tra mật khẩu.
DUMMY_PASSWORD_HASH = hash_password("viviet-dummy-password-not-an-account")


def _signing_key() -> str:
    key = settings.SECRET_KEY
    if len(key.encode("utf-8")) < 32 or key.lower().startswith("changeme"):
        raise AppError("AUTH_NOT_CONFIGURED", "Cần cấu hình SECRET_KEY trước khi sử dụng JWT.", 503)
    return key


def create_token(user_id: int, kind: TokenKind) -> str:
    now = datetime.now(UTC)
    lifetime = (
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        if kind == "access"
        else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    return jwt.encode(
        {
            "sub": str(user_id),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + lifetime,
            "jti": str(uuid4()),
            "token_type": kind,
        },
        _signing_key(),
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str, kind: TokenKind) -> int:
    key = _signing_key()
    try:
        claims = jwt.decode(
            token,
            key,
            algorithms=[settings.ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                "require_exp": True,
                "require_iat": True,
                "require_sub": True,
                "require_iss": True,
                "require_aud": True,
                "require_jti": True,
            },
        )
        subject = claims["sub"]
        issued_at, expires_at = claims["iat"], claims["exp"]
        now = int(datetime.now(UTC).timestamp())
        if (
            type(issued_at) is not int
            or type(expires_at) is not int
            or issued_at > now
            or expires_at <= now
            or expires_at <= issued_at
        ):
            raise ValueError
        if claims.get("token_type") != kind or not re.fullmatch(r"[1-9][0-9]{0,9}", subject):
            raise ValueError
        user_id = int(subject)
        if user_id > 2**31 - 1:
            raise ValueError
        return user_id
    except (JWTError, ValueError, TypeError, KeyError, OverflowError):
        raise AppError(
            "UNAUTHENTICATED", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.", 401
        ) from None

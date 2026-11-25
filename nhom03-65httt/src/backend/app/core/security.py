"""Module bảo mật, xử lý JWT và phân quyền Admin/Viewer (EduVision BI, Nhóm 03).

Quy tắc:
- Mật khẩu lưu băm; không có tài khoản hay mật khẩu viết cứng trong mã.
- Bí mật ký JWT chỉ đọc từ biến môi trường (.env), có tối thiểu 32 ký tự, không có giá trị ngầm định trong mã.
- So sánh chuỗi bảo mật an toàn trên mảng byte UTF-8 để hỗ trợ đầy đủ tiếng Việt có dấu và emoji.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import os
import secrets
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

try:
    import bcrypt
except ImportError:  # pragma: no cover
    bcrypt = None  # type: ignore

from app.schemas.auth import UserOut

# Header Authorization: Bearer <token>
oauth2_scheme = HTTPBearer(auto_error=False)


def _safe_equal(a: str, b: str) -> bool:
    """So sánh an toàn thời gian hằng số trên chuỗi byte UTF-8 (hỗ trợ tiếng Việt và emoji)."""
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _get_env_secret() -> str:
    """Lấy bí mật ký JWT từ biến môi trường AUTH_JWT_SECRET.
    Yêu cầu khóa phải có ít nhất 32 ký tự để đảm bảo độ bảo mật mật mã học.
    """
    secret = os.getenv("AUTH_JWT_SECRET", "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_JWT_SECRET chưa được cấu hình trên máy chủ",
        )
    if len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AUTH_JWT_SECRET phải có ít nhất 32 ký tự",
        )
    return secret


def _get_token_minutes() -> int:
    """Lấy thời hạn token tính theo phút (mặc định 60)."""
    try:
        val = int(os.getenv("AUTH_TOKEN_MINUTES", "60").strip())
        return val if val > 0 else 60
    except (ValueError, TypeError):
        return 60


def hash_password(password: str) -> str:
    """Băm mật khẩu bằng bcrypt (nếu có) hoặc SHA-256 có muối."""
    if bcrypt is not None:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"sha256${salt}${digest}"


def verify_password(plain_password: str, stored_hash_or_plain: str) -> bool:
    """Kiểm tra mật khẩu khớp với giá trị băm hoặc giá trị trong cấu hình."""
    if not stored_hash_or_plain:
        return False

    # Nếu chuỗi lưu là bcrypt hash ($2a$, $2b$, $2y$)
    if stored_hash_or_plain.startswith(("$2a$", "$2b$", "$2y$")):
        if bcrypt is not None:
            try:
                return bcrypt.checkpw(
                    plain_password.encode("utf-8"),
                    stored_hash_or_plain.encode("utf-8"),
                )
            except Exception:
                return False
        return False

    # Nếu chuỗi lưu là định dạng sha256$salt$digest
    if stored_hash_or_plain.startswith("sha256$"):
        parts = stored_hash_or_plain.split("$")
        if len(parts) == 3:
            _, salt, expected_digest = parts
            actual_digest = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
            return _safe_equal(actual_digest, expected_digest)

    # Nếu chuỗi trong môi trường là mật khẩu thuần, so sánh an toàn qua UTF-8 bytes
    return _safe_equal(plain_password, stored_hash_or_plain)


def authenticate_user(username: str, password: str) -> UserOut | None:
    """Xác thực tài khoản và trả về thông tin người dùng cùng vai trò (admin hoặc viewer)."""
    admin_user = os.getenv("AUTH_ADMIN_USER", "").strip()
    admin_pass = os.getenv("AUTH_ADMIN_PASSWORD", "").strip()
    viewer_user = os.getenv("AUTH_VIEWER_USER", "").strip()
    viewer_pass = os.getenv("AUTH_VIEWER_PASSWORD", "").strip()

    if admin_user and _safe_equal(username, admin_user):
        if admin_pass and verify_password(password, admin_pass):
            return UserOut(username=admin_user, role="admin")

    if viewer_user and _safe_equal(username, viewer_user):
        if viewer_pass and verify_password(password, viewer_pass):
            return UserOut(username=viewer_user, role="viewer")

    return None


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    """Tạo JWT access token. Trả về cặp (token, số giây hiệu lực)."""
    secret = _get_env_secret()

    minutes = _get_token_minutes()
    if expires_delta is not None:
        expire_dt = datetime.now(timezone.utc) + expires_delta
        expires_in = int(expires_delta.total_seconds())
    else:
        expire_dt = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        expires_in = minutes * 60

    to_encode = data.copy()
    to_encode.update({"exp": expire_dt})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm="HS256")
    return encoded_jwt, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """Giải mã và xác minh JWT token."""
    secret = _get_env_secret()

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
) -> UserOut:
    """Dependency: lấy người dùng hiện tại từ Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu token xác thực",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    username: str | None = payload.get("sub")
    role: str | None = payload.get("role")
    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không chứa đủ thông tin xác thực",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserOut(username=username, role=role)


async def require_user(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    """Dependency: yêu cầu người dùng đã đăng nhập (Viewer hoặc Admin)."""
    return current_user


async def require_admin(current_user: UserOut = Depends(get_current_user)) -> UserOut:
    """Dependency: chỉ cho phép người dùng có vai trò Quản trị viên (Admin)."""
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yêu cầu quyền Quản trị viên (Admin)",
        )
    return current_user

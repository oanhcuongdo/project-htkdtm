import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status
from supabase import Client

from src.backend.config.settings import settings
from src.backend.database.supabase_client import get_supabase_client


def get_db() -> Client:
    """Dependency cung cấp Supabase client."""
    return get_supabase_client()


def validate_uuid(value: str, field_name: str = "fact_id") -> str:
    """Kiểm tra chuỗi đầu vào đúng định dạng UUID, tránh lỗi 500 từ PostgreSQL."""
    try:
        return str(uuid.UUID(str(value).strip()))
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tham số '{field_name}' không đúng định dạng UUID.",
        )


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user_id: str, email: str, role: str, ttl_seconds: int = 7 * 24 * 3600) -> str:
    """Tạo token HMAC-SHA256 mang thông tin phiên và vai trò người dùng."""
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(settings.AUTH_SECRET_KEY.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_b64}.{_b64url_encode(sig)}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Giải mã và xác thực chữ ký token HMAC-SHA256."""
    try:
        payload_b64, sig_b64 = token.split(".", 1)
        expected_sig = hmac.new(
            settings.AUTH_SECRET_KEY.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
        ).digest()
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_current_user_optional(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
    """Trích xuất người dùng hiện tại từ Bearer token (trả None nếu khách vãng lai)."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return decode_access_token(token)


def require_current_user(user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)) -> Dict[str, Any]:
    """Bắt buộc người dùng đã đăng nhập hợp lệ."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu đăng nhập để thực hiện thao tác này.",
        )
    return user


def require_admin(user: Dict[str, Any] = Depends(require_current_user)) -> Dict[str, Any]:
    """Bắt buộc quyền Quản trị viên (admin)."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Quản trị viên (admin) mới có quyền truy cập chức năng này.",
        )
    return user

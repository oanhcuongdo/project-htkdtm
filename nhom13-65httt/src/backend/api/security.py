import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt
import jwt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.config import settings
from api.dependencies import get_db, get_db_session

bearer_scheme = HTTPBearer(auto_error=False)


def _get_fernet() -> Fernet:
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_config(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
    return _get_fernet().encrypt(raw).decode("utf-8")


def decrypt_config(token: Optional[str]) -> Dict[str, Any]:
    if not token:
        return {}
    try:
        raw = _get_fernet().decrypt(token.encode("utf-8"))
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash or password_hash == "PENDING_INIT":
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int, email: str, full_name: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "full_name": full_name,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Bắt buộc đăng nhập JWT hợp lệ."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vui lòng đăng nhập để sử dụng chức năng này.",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập không hợp lệ hoặc đã hết hạn.",
        )

    user_id = int(payload["sub"])
    row = db.execute(
        text("SELECT user_id, email, full_name, is_active, created_at FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).mappings().first()

    if not row or not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại hoặc đã bị khóa.")

    return dict(row)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Lấy user từ JWT nếu có; fallback về tài khoản Demo (user_id=1) cho các lệnh test Swagger."""
    if credentials and credentials.credentials:
        return get_current_user(credentials, db)
    row = db.execute(
        text("SELECT user_id, email, full_name, is_active, created_at FROM users WHERE user_id = 1")
    ).mappings().first()
    if row:
        return dict(row)
    return {"user_id": 1, "email": "demo@finance.local", "full_name": "Tài khoản Demo (Nhóm 13)", "is_active": True}


def ensure_demo_user_ready():
    """Đảm bảo tài khoản Demo (demo@finance.local / Demo@123) có mật khẩu bcrypt chuẩn khi khởi động."""
    try:
        with get_db_session() as db:
            row = db.execute(
                text("SELECT user_id, password_hash FROM users WHERE email = 'demo@finance.local'")
            ).first()
            if not row:
                db.execute(
                    text("""
                        INSERT INTO users (user_id, email, password_hash, full_name, is_active)
                        VALUES (1, 'demo@finance.local', :phash, 'Tài khoản Demo (Nhóm 13)', TRUE)
                        ON CONFLICT (email) DO NOTHING
                    """),
                    {"phash": hash_password("Demo@123")},
                )
            elif row[1] == "PENDING_INIT":
                db.execute(
                    text("UPDATE users SET password_hash = :phash WHERE user_id = :uid"),
                    {"phash": hash_password("Demo@123"), "uid": int(row[0])},
                )
    except Exception:
        pass

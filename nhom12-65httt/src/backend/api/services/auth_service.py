import hashlib
import hmac
import secrets
from fastapi import HTTPException, status
from supabase import Client

from src.backend.api.dependencies import create_access_token
from src.backend.api.schemas.auth import AuthTokenResponse, UserLogin, UserProfileDTO, UserRegister


def hash_password(password: str) -> str:
    """Băm mật khẩu bằng PBKDF2-HMAC-SHA256 kèm salt ngẫu nhiên."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 100_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Kiểm tra mật khẩu khớp với PBKDF2 hash đã lưu."""
    try:
        salt, hex_dk = stored_hash.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 100_000)
        return hmac.compare_digest(dk.hex(), hex_dk)
    except Exception:
        return False


def register_user(db: Client, payload: UserRegister) -> AuthTokenResponse:
    """Đăng ký tài khoản người dùng mới (mặc định vai trò user)."""
    email = payload.email.strip().lower()
    existing = db.table("user_profiles").select("user_id").eq("email", email).limit(1).execute()
    if existing.data:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email này đã được đăng ký.")

    res = (
        db.table("user_profiles")
        .insert({
            "email": email,
            "full_name": payload.full_name.strip(),
            "password_hash": hash_password(payload.password),
            "role": "user",
        })
        .execute()
    )
    created = res.data[0]
    user_dto = UserProfileDTO(
        user_id=str(created["user_id"]),
        email=created["email"],
        full_name=created["full_name"],
        role=created["role"],
        created_at=str(created.get("created_at")) if created.get("created_at") else None,
    )
    token = create_access_token(user_dto.user_id, user_dto.email, user_dto.role)
    return AuthTokenResponse(access_token=token, user=user_dto)


def login_user(db: Client, payload: UserLogin) -> AuthTokenResponse:
    """Xác thực tài khoản và cấp Bearer token kèm vai trò."""
    email = payload.email.strip().lower()
    res = db.table("user_profiles").select("*").eq("email", email).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không đúng.")

    row = res.data[0]
    if not row.get("password_hash") or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email hoặc mật khẩu không đúng.")

    user_dto = UserProfileDTO(
        user_id=str(row["user_id"]),
        email=row["email"],
        full_name=row["full_name"] or row["email"],
        role=row["role"],
        created_at=str(row.get("created_at")) if row.get("created_at") else None,
    )
    token = create_access_token(user_dto.user_id, user_dto.email, user_dto.role)
    return AuthTokenResponse(access_token=token, user=user_dto)


def get_profile_by_id(db: Client, user_id: str) -> UserProfileDTO:
    """Lấy thông tin hồ sơ người dùng theo user_id."""
    res = db.table("user_profiles").select("*").eq("user_id", user_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng.")
    row = res.data[0]
    return UserProfileDTO(
        user_id=str(row["user_id"]),
        email=row["email"],
        full_name=row["full_name"] or row["email"],
        role=row["role"],
        created_at=str(row.get("created_at")) if row.get("created_at") else None,
    )

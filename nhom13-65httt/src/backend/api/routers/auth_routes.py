from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication (Multi-User JWT)"])


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=150)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Tạo tài khoản cá nhân mới và khởi tạo sẵn nguồn dữ liệu mặc định cho người dùng."""
    email_norm = payload.email.strip().lower()
    existing = db.execute(text("SELECT 1 FROM users WHERE email = :email"), {"email": email_norm}).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email này đã được đăng ký. Vui lòng đăng nhập.")

    pw_hash = hash_password(payload.password)
    row = db.execute(
        text("""
            INSERT INTO users (email, password_hash, full_name, is_active)
            VALUES (:email, :pw_hash, :full_name, TRUE)
            RETURNING user_id, email, full_name, created_at
        """),
        {"email": email_norm, "pw_hash": pw_hash, "full_name": payload.full_name.strip()},
    ).mappings().first()

    uid = int(row["user_id"])

    # Tự động khởi tạo 1 nguồn dữ liệu Upload CSV/Excel mặc định đang bật
    db.execute(
        text("""
            INSERT INTO user_data_sources (user_id, source_type, display_name, is_enabled)
            VALUES (:uid, 'CSV_UPLOAD', 'Tải lên sao kê Excel / CSV / PDF', TRUE)
            ON CONFLICT (user_id, source_type) DO NOTHING
        """),
        {"uid": uid},
    )
    db.commit()

    token = create_access_token(uid, row["email"], row["full_name"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": uid,
            "email": row["email"],
            "full_name": row["full_name"],
        },
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập bằng email & mật khẩu, trả về JWT Bearer Token."""
    email_norm = payload.email.strip().lower()
    row = db.execute(
        text("SELECT user_id, email, password_hash, full_name, is_active FROM users WHERE email = :email"),
        {"email": email_norm},
    ).mappings().first()

    if not row or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không chính xác.")

    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị vô hiệu hóa.")

    token = create_access_token(int(row["user_id"]), row["email"], row["full_name"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": int(row["user_id"]),
            "email": row["email"],
            "full_name": row["full_name"],
        },
    }


@router.get("/me")
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lấy thông tin tài khoản hiện tại cùng thống kê số giao dịch sở hữu."""
    tx_count = db.execute(
        text("SELECT COUNT(*) FROM fact_transactions WHERE user_id = :uid"),
        {"uid": current_user["user_id"]},
    ).scalar() or 0

    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "transaction_count": int(tx_count),
    }

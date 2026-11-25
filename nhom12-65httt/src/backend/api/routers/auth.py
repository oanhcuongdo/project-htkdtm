from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from supabase import Client

from src.backend.api.dependencies import get_db, require_current_user
from src.backend.api.schemas.auth import AuthTokenResponse, UserLogin, UserProfileDTO, UserRegister
from src.backend.api.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Client = Depends(get_db)):
    """Đăng ký tài khoản mới (mặc định vai trò user)."""
    return auth_service.register_user(db=db, payload=payload)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: UserLogin, db: Client = Depends(get_db)):
    """Đăng nhập lấy access_token theo vai trò user hoặc admin."""
    return auth_service.login_user(db=db, payload=payload)


@router.get("/me", response_model=UserProfileDTO)
def me(
    current_user: Dict[str, Any] = Depends(require_current_user),
    db: Client = Depends(get_db),
):
    """Lấy thông tin tài khoản hiện tại từ Bearer token."""
    return auth_service.get_profile_by_id(db=db, user_id=current_user["sub"])

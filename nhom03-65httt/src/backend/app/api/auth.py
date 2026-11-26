"""Router xác thực JWT và phân quyền Admin/Viewer (EduVision BI, Nhóm 03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import (
    authenticate_user,
    create_access_token,
    require_admin,
    require_user,
)
from app.schemas.auth import LoginIn, TokenOut, UserOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenOut,
    summary="Đăng nhập và nhận JWT token",
)
def login(payload: LoginIn) -> TokenOut:
    """Xác thực tài khoản với tên đăng nhập và mật khẩu cấu hình từ .env."""
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return TokenOut(
        access_token=token,
        token_type="bearer",
        role=user.role,
        expires_in=expires_in,
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Lấy thông tin tài khoản hiện tại",
)
def get_me(user: UserOut = Depends(require_user)) -> UserOut:
    """Trả về tên đăng nhập và vai trò của tài khoản đang đăng nhập."""
    return user


@router.get(
    "/admin/ping",
    summary="Kiểm tra quyền Quản trị viên (Admin)",
)
def admin_ping(_admin: UserOut = Depends(require_admin)) -> dict[str, str]:
    """Điểm cuối kiểm tra quyền Admin. Viewer truy cập sẽ bị từ chối 403."""
    return {"status": "ok", "role": "admin"}

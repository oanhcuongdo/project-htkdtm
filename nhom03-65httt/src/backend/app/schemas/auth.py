"""Schemas cho xác thực và phân quyền (JWT) - EduVision BI Nhóm 03."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=100, description="Tên đăng nhập")
    password: str = Field(min_length=1, max_length=100, description="Mật khẩu")


class TokenOut(BaseModel):
    access_token: str = Field(description="JWT Bearer token")
    token_type: str = Field(default="bearer", description="Loại token")
    role: str = Field(description="Vai trò người dùng: admin hoặc viewer")
    expires_in: int = Field(description="Thời hạn token (giây)")


class UserOut(BaseModel):
    username: str = Field(description="Tên người dùng")
    role: str = Field(description="Vai trò người dùng: admin hoặc viewer")

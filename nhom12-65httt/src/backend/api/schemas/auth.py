from typing import Literal, Optional
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    email: str = Field(min_length=4, max_length=255)
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfileDTO(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: Literal["user", "admin"] = "user"
    created_at: Optional[str] = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileDTO

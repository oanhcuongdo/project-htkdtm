from __future__ import annotations

from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    status: str = "ok"
    env: str


class DbHealthOut(BaseModel):
    status: str
    schemas_present: list[str]
    schemas_missing: list[str]
    migration_version: str | None = Field(default=None, description="Phiên bản Alembic hiện tại (rỗng nếu chưa chạy migration)")


class PlatformOut(BaseModel):
    id: str = Field(description="Mã nền tảng, trùng khóa id trong config/platforms.yml")
    group: str = Field(description="trong_nuoc hoặc quoc_te")
    play_id: str | None = None
    ios_id: str | None = None


class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000, description="Nội dung đánh giá cần phân tích")


class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ErrorOut(BaseModel):
    detail: str

"""Đánh giá món đã mua, tách khỏi feedback của gợi ý."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.menu.schemas import EntityId


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    menu_item_id: EntityId
    rating: int = Field(strict=True, ge=1, le=5)
    comment: str = Field(default="", max_length=2000)

    @field_validator("comment", mode="before")
    @classmethod
    def clean_comment(cls, value):
        return value.strip() if isinstance(value, str) else value


class ReviewOut(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    snapshot_name: str
    snapshot_price: int
    rating: int
    comment: str
    created_at: datetime

"""Batch sự kiện hành vi, event_id do client cấp để gửi lại an toàn."""

from datetime import datetime

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.menu.schemas import EntityId
from app.tracking.models import EventType


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID4
    session_id: UUID4
    event_type: EventType
    request_id: UUID4 | None = None
    menu_item_id: EntityId | None = None
    value: int | None = Field(default=None, strict=True)
    occurred_at: datetime

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at phải có múi giờ.")
        return value

    @model_validator(mode="after")
    def context(self):
        kind = self.event_type
        if kind in (EventType.IMPRESSION, EventType.CLICK, EventType.FEEDBACK):
            valid = self.request_id is not None and self.menu_item_id is not None
        elif kind == EventType.ADD_TO_CART:
            valid = self.menu_item_id is not None
        else:
            valid = self.request_id is None and self.menu_item_id is None
        if not valid or (kind == EventType.FEEDBACK) != (self.value in (0, 1)):
            raise ValueError("Ngữ cảnh hoặc giá trị sự kiện không hợp lệ.")
        if kind != EventType.FEEDBACK and self.value is not None:
            raise ValueError("Chỉ feedback nhận giá trị.")
        return self


class EventBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[EventInput] = Field(min_length=1, max_length=100)


class EventBatchResult(BaseModel):
    accepted: int
    duplicates: int

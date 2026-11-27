"""Đơn COD và snapshot; client không tự đặt tổng tiền, chủ sở hữu hoặc trạng thái."""

from datetime import datetime
from typing import Annotated

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from app.menu.schemas import EntityId, Price
from app.orders.models import OrderStatus
from app.restaurants.schemas import Latitude, Longitude


class OrderLineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    menu_item_id: EntityId
    quantity: Annotated[int, Field(strict=True, ge=1, le=99)]
    expected_price: Price


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    restaurant_id: EntityId
    items: list[OrderLineInput] = Field(min_length=1, max_length=100)
    delivery_address: str = Field(min_length=5, max_length=500)
    latitude: Latitude
    longitude: Longitude
    session_id: UUID4
    idempotency_key: UUID4

    @field_validator("delivery_address", mode="before")
    @classmethod
    def clean_address(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("items")
    @classmethod
    def unique_items(cls, value):
        if len({item.menu_item_id for item in value}) != len(value):
            raise ValueError("Mỗi món chỉ xuất hiện một lần trong đơn.")
        return value


class RejectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason", mode="before")
    @classmethod
    def clean_reason(cls, value):
        return value.strip() if isinstance(value, str) else value


class OrderLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    menu_item_id: int
    quantity: int
    snapshot_price: int
    snapshot_name: str


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: OrderStatus
    reason: str | None
    created_at: datetime


class OrderDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    restaurant_id: int
    status: OrderStatus
    total: int
    delivery_address: str
    latitude: float
    longitude: float
    created_at: datetime
    items: list[OrderLineOut]
    history: list[HistoryOut]

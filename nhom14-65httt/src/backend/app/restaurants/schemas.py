"""Hồ sơ quán và DTO công khai; client không tự duyệt quán hoặc gán người quản lý."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from app.restaurants.models import RestaurantStatus

Latitude = Annotated[float, Field(strict=True, ge=-90, le=90, allow_inf_nan=False)]
Longitude = Annotated[float, Field(strict=True, ge=-180, le=180, allow_inf_nan=False)]
DeliveryRadius = Annotated[float, Field(strict=True, gt=0, le=50, allow_inf_nan=False)]
LocalTime = Annotated[str, Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")]


class RestaurantCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=160)
    address: str = Field(min_length=1, max_length=500)
    latitude: Latitude
    longitude: Longitude
    delivery_radius_km: DeliveryRadius = 5.0
    opens_at: LocalTime = "00:00"
    closes_at: LocalTime = "00:00"

    @field_validator("name", "address", mode="before")
    @classmethod
    def normalize_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class RestaurantUpdate(RestaurantCreate):
    """PUT thay toàn bộ hồ sơ; không bỏ trường rồi vô tình đặt lại mặc định."""

    delivery_radius_km: DeliveryRadius
    opens_at: LocalTime
    closes_at: LocalTime
    accepting_orders: StrictBool


class RestaurantPublic(BaseModel):
    id: int
    name: str
    address: str
    latitude: float
    longitude: float
    delivery_radius_km: float
    opens_at: str
    closes_at: str
    accepting_orders: bool
    is_open: bool
    can_receive_orders: bool


class RestaurantDetail(RestaurantPublic):
    status: RestaurantStatus
    is_simulated: bool


class RestaurantPage(BaseModel):
    items: list[RestaurantPublic]
    total: int
    offset: int
    limit: int

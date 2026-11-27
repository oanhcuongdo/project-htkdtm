"""Query tìm kiếm công khai và kết quả có khoảng cách theo km."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.menu.schemas import MenuItemPublic
from app.restaurants.schemas import RestaurantPublic


class SearchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lng: float = Field(ge=-180, le=180, allow_inf_nan=False)
    radius: float = Field(default=5, gt=0, le=50, allow_inf_nan=False)
    q: str = Field(default="", max_length=180)
    offset: int = Field(default=0, ge=0, le=2**31 - 1)
    limit: int = Field(default=20, ge=1, le=100)

    @field_validator("q", mode="before")
    @classmethod
    def clean_query(cls, value):
        return " ".join(value.split()) if isinstance(value, str) else value


class DishSearchResult(MenuItemPublic):
    distance_km: float
    restaurant: RestaurantPublic


class RestaurantSearchResult(RestaurantPublic):
    distance_km: float


class DishSearchPage(BaseModel):
    items: list[DishSearchResult]
    total: int
    offset: int
    limit: int


class RestaurantSearchPage(BaseModel):
    items: list[RestaurantSearchResult]
    total: int
    offset: int
    limit: int

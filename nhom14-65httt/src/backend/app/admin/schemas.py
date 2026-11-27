"""Danh sách quán quản trị có trạng thái và cờ mô phỏng."""

from pydantic import BaseModel

from app.menu.schemas import CanonicalDishDetail, IngredientDetail
from app.restaurants.schemas import RestaurantDetail


class AdminRestaurantPage(BaseModel):
    items: list[RestaurantDetail]
    total: int
    offset: int
    limit: int


class AdminCanonicalDishPage(BaseModel):
    items: list[CanonicalDishDetail]
    total: int
    offset: int
    limit: int


class AdminIngredientPage(BaseModel):
    items: list[IngredientDetail]
    total: int
    offset: int
    limit: int

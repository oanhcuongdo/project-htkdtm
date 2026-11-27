"""Quản trị trạng thái quán và danh mục món chuẩn/nguyên liệu."""

from sqlalchemy.orm import Session

from app.admin.schemas import AdminCanonicalDishPage, AdminIngredientPage, AdminRestaurantPage
from app.menu import service as menu
from app.menu.models import CanonicalDish, Ingredient
from app.menu.schemas import CanonicalDishCreate, CanonicalDishUpdate, IngredientInput
from app.restaurants import service as restaurants
from app.restaurants.models import Restaurant, RestaurantStatus


def list_restaurants(
    db: Session, *, offset: int, limit: int, status: RestaurantStatus | None
) -> AdminRestaurantPage:
    rows, total = restaurants.list_restaurants(
        db, offset=offset, limit=limit, public=False, status=status
    )
    now = restaurants.utcnow()
    return AdminRestaurantPage(
        items=[restaurants.detail_data(row, now) for row in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


def approve(db: Session, restaurant_id: int) -> Restaurant:
    return restaurants.set_status(db, restaurant_id, RestaurantStatus.APPROVED)


def suspend(db: Session, restaurant_id: int) -> Restaurant:
    return restaurants.set_status(db, restaurant_id, RestaurantStatus.SUSPENDED)


def canonical_dishes(db: Session, *, offset: int, limit: int) -> AdminCanonicalDishPage:
    rows, total = menu.catalog(db, CanonicalDish, offset=offset, limit=limit)
    return AdminCanonicalDishPage(items=rows, total=total, offset=offset, limit=limit)


def save_dish(
    db: Session, payload: CanonicalDishCreate | CanonicalDishUpdate, entry_id: int | None = None
) -> CanonicalDish:
    return menu.save_canonical(db, payload, entry_id)


def delete_dish(db: Session, entry_id: int) -> None:
    menu.delete_catalog_entry(db, CanonicalDish, entry_id)


def ingredients(db: Session, *, offset: int, limit: int) -> AdminIngredientPage:
    rows, total = menu.catalog(db, Ingredient, offset=offset, limit=limit)
    return AdminIngredientPage(items=rows, total=total, offset=offset, limit=limit)


def save_ingredient(
    db: Session, payload: IngredientInput, entry_id: int | None = None
) -> Ingredient:
    return menu.save_ingredient(db, payload, entry_id)


def delete_ingredient(db: Session, entry_id: int) -> None:
    menu.delete_catalog_entry(db, Ingredient, entry_id)

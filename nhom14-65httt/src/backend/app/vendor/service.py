"""Hồ sơ và thực đơn lấy quán từ membership, không nhận ID quán từ client."""

from sqlalchemy.orm import Session

from app.exceptions import ForbiddenError, NotFoundError
from app.menu import service as menu
from app.menu.schemas import MenuItemDetail, MenuItemPage
from app.restaurants import service as restaurants
from app.restaurants.models import Restaurant, RestaurantMembership
from app.users.models import User, UserRole
from app.vendor.schemas import (
    VendorMenuItemCreate,
    VendorMenuItemUpdate,
    VendorRestaurantCreate,
    VendorRestaurantUpdate,
)


def _check_vendor(user: User) -> None:
    if user.role != UserRole.VENDOR:
        raise ForbiddenError()


def _restaurant_id(db: Session, user: User) -> int:
    _check_vendor(user)
    membership = db.get(RestaurantMembership, user.id)
    if membership is None:
        raise NotFoundError("Tài khoản chưa được liên kết với quán.")
    return membership.restaurant_id


def get_profile(db: Session, user: User) -> Restaurant:
    return restaurants.get_restaurant(db, _restaurant_id(db, user), public=False)


def create_profile(db: Session, user: User, payload: VendorRestaurantCreate) -> Restaurant:
    _check_vendor(user)
    return restaurants.create_with_owner(db, user.id, payload)


def update_profile(db: Session, user: User, payload: VendorRestaurantUpdate) -> Restaurant:
    return restaurants.update_profile(db, _restaurant_id(db, user), payload)


def menu_items(db: Session, user: User, *, offset: int, limit: int) -> MenuItemPage:
    items, total = menu.owned_menu(db, _restaurant_id(db, user), offset=offset, limit=limit)
    return MenuItemPage(
        items=[menu.menu_data(item, private=True) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_menu_item(db: Session, user: User, item_id: int) -> MenuItemDetail:
    return menu.menu_data(menu.owned_item(db, _restaurant_id(db, user), item_id), private=True)


def save_menu_item(
    db: Session,
    user: User,
    payload: VendorMenuItemCreate | VendorMenuItemUpdate,
    item_id: int | None = None,
) -> MenuItemDetail:
    return menu.save_item(db, _restaurant_id(db, user), payload, item_id)


def stop_selling(db: Session, user: User, item_id: int) -> None:
    menu.stop_selling(db, _restaurant_id(db, user), item_id)

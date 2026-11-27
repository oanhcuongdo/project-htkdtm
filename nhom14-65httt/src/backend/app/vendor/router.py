"""API hồ sơ và thực đơn của vendor đã đăng nhập."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.menu.schemas import MenuItemDetail, MenuItemPage
from app.restaurants.schemas import RestaurantDetail
from app.restaurants.service import detail_data
from app.users.models import User, UserRole
from app.vendor import service
from app.vendor.schemas import (
    VendorMenuItemCreate,
    VendorMenuItemUpdate,
    VendorRestaurantCreate,
    VendorRestaurantUpdate,
)

router = APIRouter(prefix="/vendor", tags=["vendor"])
Vendor = Annotated[User, Depends(require_role(UserRole.VENDOR))]
Database = Annotated[Session, Depends(get_db)]
ItemId = Annotated[int, Path(gt=0, le=2**31 - 1)]
Offset = Annotated[int, Query(ge=0, le=2**31 - 1)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.get("/restaurant", response_model=RestaurantDetail)
def profile(db: Database, user: Vendor):
    return detail_data(service.get_profile(db, user))


@router.post("/restaurant", response_model=RestaurantDetail, status_code=201)
def create(payload: VendorRestaurantCreate, db: Database, user: Vendor):
    return detail_data(service.create_profile(db, user, payload))


@router.put("/restaurant", response_model=RestaurantDetail)
def update(payload: VendorRestaurantUpdate, db: Database, user: Vendor):
    return detail_data(service.update_profile(db, user, payload))


@router.get("/menu-items", response_model=MenuItemPage)
def items(db: Database, user: Vendor, offset: Offset = 0, limit: Limit = 20):
    return service.menu_items(db, user, offset=offset, limit=limit)


@router.get("/menu-items/{item_id}", response_model=MenuItemDetail)
def item(item_id: ItemId, db: Database, user: Vendor):
    return service.get_menu_item(db, user, item_id)


@router.post("/menu-items", response_model=MenuItemDetail, status_code=201)
def create_item(payload: VendorMenuItemCreate, db: Database, user: Vendor):
    return service.save_menu_item(db, user, payload)


@router.put("/menu-items/{item_id}", response_model=MenuItemDetail)
def update_item(item_id: ItemId, payload: VendorMenuItemUpdate, db: Database, user: Vendor):
    return service.save_menu_item(db, user, payload, item_id)


@router.delete("/menu-items/{item_id}", status_code=204, response_class=Response)
def delete_item(item_id: ItemId, db: Database, user: Vendor):
    service.stop_selling(db, user, item_id)
    return Response(status_code=204)

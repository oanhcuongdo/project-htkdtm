"""API quản trị quán và catalog; mọi endpoint yêu cầu vai trò admin từ DB."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.admin import service
from app.admin.schemas import AdminCanonicalDishPage, AdminIngredientPage, AdminRestaurantPage
from app.auth.dependencies import require_role
from app.database import get_db
from app.menu.schemas import (
    CanonicalDishCreate,
    CanonicalDishDetail,
    CanonicalDishUpdate,
    IngredientDetail,
    IngredientInput,
)
from app.restaurants.models import RestaurantStatus
from app.restaurants.schemas import RestaurantDetail
from app.restaurants.service import detail_data
from app.users.models import UserRole

router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_role(UserRole.ADMIN))]
)
Database = Annotated[Session, Depends(get_db)]
RestaurantId = Annotated[int, Path(gt=0, le=2**31 - 1)]
EntryId = Annotated[int, Path(gt=0, le=2**31 - 1)]
Offset = Annotated[int, Query(ge=0, le=2**31 - 1)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.get("/restaurants", response_model=AdminRestaurantPage)
def listing(
    db: Database,
    offset: Annotated[int, Query(ge=0, le=2**31 - 1)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    status: RestaurantStatus | None = None,
):
    return service.list_restaurants(db, offset=offset, limit=limit, status=status)


@router.patch("/restaurants/{restaurant_id}/approve", response_model=RestaurantDetail)
def approve(restaurant_id: RestaurantId, db: Database):
    return detail_data(service.approve(db, restaurant_id))


@router.patch("/restaurants/{restaurant_id}/suspend", response_model=RestaurantDetail)
def suspend(restaurant_id: RestaurantId, db: Database):
    return detail_data(service.suspend(db, restaurant_id))


@router.get("/canonical-dishes", response_model=AdminCanonicalDishPage)
def dishes(db: Database, offset: Offset = 0, limit: Limit = 20):
    return service.canonical_dishes(db, offset=offset, limit=limit)


@router.post("/canonical-dishes", response_model=CanonicalDishDetail, status_code=201)
def create_dish(payload: CanonicalDishCreate, db: Database):
    return service.save_dish(db, payload)


@router.put("/canonical-dishes/{entry_id}", response_model=CanonicalDishDetail)
def update_dish(entry_id: EntryId, payload: CanonicalDishUpdate, db: Database):
    return service.save_dish(db, payload, entry_id)


@router.delete("/canonical-dishes/{entry_id}", status_code=204, response_class=Response)
def delete_dish(entry_id: EntryId, db: Database):
    service.delete_dish(db, entry_id)
    return Response(status_code=204)


@router.get("/ingredients", response_model=AdminIngredientPage)
def ingredients(db: Database, offset: Offset = 0, limit: Limit = 20):
    return service.ingredients(db, offset=offset, limit=limit)


@router.post("/ingredients", response_model=IngredientDetail, status_code=201)
def create_ingredient(payload: IngredientInput, db: Database):
    return service.save_ingredient(db, payload)


@router.put("/ingredients/{entry_id}", response_model=IngredientDetail)
def update_ingredient(entry_id: EntryId, payload: IngredientInput, db: Database):
    return service.save_ingredient(db, payload, entry_id)


@router.delete("/ingredients/{entry_id}", status_code=204, response_class=Response)
def delete_ingredient(entry_id: EntryId, db: Database):
    service.delete_ingredient(db, entry_id)
    return Response(status_code=204)

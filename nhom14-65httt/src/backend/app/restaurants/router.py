"""Chỉ công khai quán đã duyệt; danh sách có phân trang, chưa gồm thực đơn."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.restaurants import service
from app.restaurants.schemas import RestaurantPage, RestaurantPublic

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/", response_model=RestaurantPage)
def listing(
    db: Annotated[Session, Depends(get_db)],
    offset: Annotated[int, Query(ge=0, le=2**31 - 1)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    rows, total = service.list_restaurants(db, offset=offset, limit=limit, public=True)
    now = service.utcnow()
    return RestaurantPage(
        items=[service.public_data(row, now) for row in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{restaurant_id}", response_model=RestaurantPublic)
def detail(
    restaurant_id: Annotated[int, Path(gt=0, le=2**31 - 1)], db: Annotated[Session, Depends(get_db)]
):
    return service.public_data(service.get_restaurant(db, restaurant_id))

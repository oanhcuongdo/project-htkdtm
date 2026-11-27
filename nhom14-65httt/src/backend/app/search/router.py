"""Hai API tìm kiếm công khai, vị trí do client cung cấp trong query."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.search import service
from app.search.schemas import DishSearchPage, RestaurantSearchPage, SearchParams

router = APIRouter(prefix="/search", tags=["search"])
Database = Annotated[Session, Depends(get_db)]
SearchQuery = Annotated[SearchParams, Query()]


@router.get("/dishes", response_model=DishSearchPage)
def dishes(params: SearchQuery, db: Database):
    return service.search_dishes(db, params)


@router.get("/restaurants", response_model=RestaurantSearchPage)
def restaurants(params: SearchQuery, db: Database):
    return service.search_restaurants(db, params)

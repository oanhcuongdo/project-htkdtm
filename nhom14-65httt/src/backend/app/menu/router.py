"""Món bán công khai của quán approved và các danh mục tra cứu."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.menu import service
from app.menu.models import CanonicalDish, Ingredient
from app.menu.schemas import CanonicalDishPage, IngredientPage, MenuItemPublic

router = APIRouter(tags=["menu"])
Database = Annotated[Session, Depends(get_db)]
ItemId = Annotated[int, Path(gt=0, le=2**31 - 1)]
Offset = Annotated[int, Query(ge=0, le=2**31 - 1)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.get("/menu-items/{item_id}", response_model=MenuItemPublic)
def detail(item_id: ItemId, db: Database):
    return service.public_item(db, item_id)


@router.get("/restaurants/{restaurant_id}/menu", response_model=list[MenuItemPublic])
def restaurant_menu(
    restaurant_id: Annotated[int, Path(gt=0, le=2**31 - 1)],
    db: Database,
    offset: Offset = 0,
    limit: Limit = 20,
):
    return service.public_menu(db, restaurant_id, offset=offset, limit=limit)


@router.get("/canonical-dishes", response_model=CanonicalDishPage)
def dishes(db: Database, offset: Offset = 0, limit: Limit = 20):
    rows, total = service.catalog(db, CanonicalDish, offset=offset, limit=limit)
    return CanonicalDishPage(items=rows, total=total, offset=offset, limit=limit)


@router.get("/ingredients", response_model=IngredientPage)
def ingredients(db: Database, offset: Offset = 0, limit: Limit = 20):
    rows, total = service.catalog(db, Ingredient, offset=offset, limit=limit)
    return IngredientPage(items=rows, total=total, offset=offset, limit=limit)

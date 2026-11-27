"""Danh mục và menu của từng quán; ngừng bán giữ nguyên ID và tham chiếu lịch sử."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.exceptions import ConflictError, NotFoundError
from app.menu.models import CanonicalDish, Ingredient, MenuItem, MenuItemIngredient
from app.menu.schemas import (
    CanonicalDishCreate,
    CanonicalDishUpdate,
    IngredientInput,
    MenuItemCreate,
    MenuItemDetail,
    MenuItemPublic,
    MenuItemUpdate,
)
from app.restaurants.models import Restaurant, RestaurantStatus
from app.restaurants.service import get_restaurant


def _loaded_item_query():
    return select(MenuItem).options(
        joinedload(MenuItem.canonical_dish),
        joinedload(MenuItem.restaurant),
        selectinload(MenuItem.ingredient_links).joinedload(MenuItemIngredient.ingredient),
    )


def menu_data(item: MenuItem, *, private: bool = False) -> MenuItemPublic | MenuItemDetail:
    fields = dict(
        id=item.id,
        restaurant_id=item.restaurant_id,
        restaurant_name=item.restaurant.name,
        canonical_dish_id=item.canonical_dish_id,
        name=item.name,
        price=item.price,
        is_available=item.is_available,
        ingredients_verified=item.ingredients_verified,
        canonical_dish=item.canonical_dish,
        ingredients=[
            link.ingredient
            for link in sorted(item.ingredient_links, key=lambda link: link.ingredient_id)
        ],
    )
    return (
        MenuItemDetail(**fields, is_simulated=item.is_simulated)
        if private
        else MenuItemPublic(**fields)
    )


def public_item(db: Session, item_id: int) -> MenuItemPublic:
    item = db.scalar(
        _loaded_item_query()
        .join(MenuItem.restaurant)
        .where(
            MenuItem.id == item_id,
            MenuItem.is_available.is_(True),
            Restaurant.status == RestaurantStatus.APPROVED,
        )
    )
    if item is None:
        raise NotFoundError("Không tìm thấy món bán.")
    return menu_data(item)


def public_menu(
    db: Session, restaurant_id: int, *, offset: int, limit: int
) -> list[MenuItemPublic]:
    get_restaurant(db, restaurant_id)
    items = db.scalars(
        _loaded_item_query()
        .join(MenuItem.restaurant)
        .where(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.is_available.is_(True),
            Restaurant.status == RestaurantStatus.APPROVED,
        )
        .order_by(MenuItem.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return [menu_data(item) for item in items]


def owned_item(db: Session, restaurant_id: int, item_id: int, *, lock: bool = False) -> MenuItem:
    # Khóa riêng bảng MenuItem, tránh FOR UPDATE trên các bảng outer-join ở PostgreSQL.
    query = select(MenuItem) if lock else _loaded_item_query()
    query = query.where(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    item = db.scalar(query)
    if item is None:
        raise NotFoundError("Không tìm thấy món bán.")
    return item


def owned_menu(
    db: Session, restaurant_id: int, *, offset: int, limit: int
) -> tuple[list[MenuItem], int]:
    condition = MenuItem.restaurant_id == restaurant_id
    total = db.scalar(select(func.count()).select_from(MenuItem).where(condition)) or 0
    items = db.scalars(
        _loaded_item_query().where(condition).order_by(MenuItem.id).offset(offset).limit(limit)
    ).all()
    return list(items), total


def save_item(
    db: Session,
    restaurant_id: int,
    payload: MenuItemCreate | MenuItemUpdate,
    item_id: int | None = None,
) -> MenuItemDetail:
    item = owned_item(db, restaurant_id, item_id, lock=True) if item_id is not None else None
    dish = db.get(CanonicalDish, payload.canonical_dish_id, with_for_update=True)
    if dish is None:
        raise NotFoundError("Món chuẩn không tồn tại.")
    ids = sorted(payload.ingredient_ids)
    ingredients = (
        db.scalars(
            select(Ingredient)
            .where(Ingredient.id.in_(ids))
            .order_by(Ingredient.id)
            .with_for_update()
        ).all()
        if ids
        else []
    )
    if len(ingredients) != len(ids):
        raise NotFoundError("Có nguyên liệu không tồn tại.")
    try:
        if item is None:
            item = MenuItem(restaurant_id=restaurant_id)
            db.add(item)
        for field, value in payload.model_dump(exclude={"ingredient_ids"}).items():
            setattr(item, field, value)
        current = {link.ingredient_id: link for link in item.ingredient_links}
        item.ingredient_links = [
            current[i] if i in current else MenuItemIngredient(ingredient_id=i) for i in ids
        ]
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return menu_data(owned_item(db, restaurant_id, item.id), private=True)


def stop_selling(db: Session, restaurant_id: int, item_id: int) -> None:
    item = owned_item(db, restaurant_id, item_id, lock=True)
    item.is_available = False
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise


def catalog(db: Session, model, *, offset: int, limit: int):
    total = db.scalar(select(func.count()).select_from(model)) or 0
    rows = db.scalars(select(model).order_by(model.id).offset(offset).limit(limit)).all()
    return list(rows), total


def _catalog_entry(db: Session, model, entry_id: int):
    entry = db.get(model, entry_id, with_for_update=True, populate_existing=True)
    if entry is None:
        raise NotFoundError("Không tìm thấy mục danh mục.")
    return entry


def _dish_conflict(db: Session, payload: CanonicalDishCreate, exclude: int | None):
    match = db.scalar(select(CanonicalDish).where(CanonicalDish.name == payload.name))
    if match is not None and match.id != exclude:
        raise ConflictError("DISH_NAME_EXISTS", "Tên món chuẩn đã tồn tại.") from None
    if payload.source_id is not None:
        match = db.scalar(select(CanonicalDish).where(CanonicalDish.source_id == payload.source_id))
        if match is not None and match.id != exclude:
            raise ConflictError("DISH_SOURCE_EXISTS", "Mã nguồn món chuẩn đã tồn tại.") from None


def save_canonical(
    db: Session, payload: CanonicalDishCreate | CanonicalDishUpdate, entry_id: int | None = None
) -> CanonicalDish:
    entry = (
        _catalog_entry(db, CanonicalDish, entry_id)
        if entry_id is not None
        else CanonicalDish(is_simulated=False)
    )
    for field, value in payload.model_dump().items():
        setattr(entry, field, value)
    try:
        db.add(entry)
        db.commit()
    except IntegrityError:
        db.rollback()
        _dish_conflict(db, payload, entry_id)
        raise
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(entry)
    return entry


def save_ingredient(
    db: Session, payload: IngredientInput, entry_id: int | None = None
) -> Ingredient:
    entry = (
        _catalog_entry(db, Ingredient, entry_id)
        if entry_id is not None
        else Ingredient(is_simulated=False)
    )
    entry.name = payload.name
    try:
        db.add(entry)
        db.commit()
    except IntegrityError:
        db.rollback()
        duplicate = db.scalar(select(Ingredient).where(Ingredient.name == payload.name))
        if duplicate is not None and duplicate.id != entry_id:
            raise ConflictError("INGREDIENT_EXISTS", "Nguyên liệu đã tồn tại.") from None
        raise
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(entry)
    return entry


def delete_catalog_entry(db: Session, model, entry_id: int) -> None:
    entry = _catalog_entry(db, model, entry_id)
    referenced_model, fk = (
        (MenuItem, MenuItem.canonical_dish_id)
        if model is CanonicalDish
        else (MenuItemIngredient, MenuItemIngredient.ingredient_id)
    )
    if db.scalar(select(func.count()).select_from(referenced_model).where(fk == entry_id)):
        raise ConflictError("CATALOG_IN_USE", "Mục danh mục đang được sử dụng, không thể xóa.")
    try:
        db.delete(entry)
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.scalar(select(func.count()).select_from(referenced_model).where(fk == entry_id)):
            raise ConflictError(
                "CATALOG_IN_USE", "Mục danh mục đang được sử dụng, không thể xóa."
            ) from None
        raise
    except SQLAlchemyError:
        db.rollback()
        raise

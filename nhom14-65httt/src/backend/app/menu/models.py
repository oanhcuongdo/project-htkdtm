"""Tách đặc trưng món chuẩn khỏi giá/khả dụng và nguyên liệu thực tế ở từng quán."""

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base
from app.restaurants.models import Restaurant


def _clean_text(value: str, field: str, maximum: int, *, lowercase: bool = False) -> str:
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= maximum:
        raise ValueError(f"{field} phải có từ 1 đến {maximum} ký tự sau khi bỏ khoảng trắng.")
    cleaned = value.strip()
    return cleaned.lower() if lowercase else cleaned


class CanonicalDish(Base):
    __tablename__ = "canonical_dishes"
    __table_args__ = (
        UniqueConstraint("name", name="uq_canonical_dishes_name"),
        UniqueConstraint("source_id", name="uq_canonical_dishes_source_id"),
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 180", name="ck_canonical_dishes_name"),
        CheckConstraint("length(trim(region)) BETWEEN 1 AND 40", name="ck_canonical_dishes_region"),
        CheckConstraint("length(trim(method)) BETWEEN 1 AND 40", name="ck_canonical_dishes_method"),
        CheckConstraint("spice_level BETWEEN 0 AND 3", name="ck_canonical_dishes_spice_level"),
        CheckConstraint(
            "source_id IS NULL OR length(trim(source_id)) BETWEEN 1 AND 120",
            name="ck_canonical_dishes_source_id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    region: Mapped[str] = mapped_column(String(40), nullable=False)
    spice_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    method: Mapped[str] = mapped_column(String(40), nullable=False)
    ingredients: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON(none_as_null=True)),
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    labels: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSON(none_as_null=True)),
        nullable=False,
        default=list,
        server_default=text("'[]'"),
    )
    source_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    menu_items: Mapped[list["MenuItem"]] = relationship(
        back_populates="canonical_dish", passive_deletes="all"
    )

    @validates("name", "region", "method")
    def normalize_text(self, key: str, value: str) -> str:
        return _clean_text(value, key, 180 if key == "name" else 40)

    @validates("source_id")
    def normalize_source_id(self, key: str, value: str | None) -> str | None:
        return None if value is None else _clean_text(value, key, 120)

    @validates("spice_level")
    def validate_spice_level(self, _key: str, value: int) -> int:
        if type(value) is not int or not 0 <= value <= 3:
            raise ValueError("spice_level phải là số nguyên từ 0 đến 3.")
        return value

    @validates("ingredients", "labels")
    def normalize_choices(self, key: str, value: list[str]) -> list[str]:
        if not isinstance(value, list):
            raise ValueError(f"{key} phải là danh sách chuỗi.")
        cleaned, seen = [], set()
        for choice in value:
            if not isinstance(choice, str) or not choice.strip():
                raise ValueError(f"{key} không nhận phần tử rỗng hoặc khác kiểu chuỗi.")
            choice = choice.strip()
            if key == "ingredients":
                choice = choice.lower()
            if choice.casefold() not in seen:
                seen.add(choice.casefold())
                cleaned.append(choice)
        return cleaned


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = (
        UniqueConstraint("name", name="uq_ingredients_name"),
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 100", name="ck_ingredients_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    menu_links: Mapped[list["MenuItemIngredient"]] = relationship(
        back_populates="ingredient", passive_deletes="all"
    )

    @validates("name")
    def normalize_name(self, key: str, value: str) -> str:
        return _clean_text(value, key, 100, lowercase=True)


class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = (
        CheckConstraint("price > 0 AND price <= 10000000", name="ck_menu_items_price"),
        CheckConstraint("length(trim(name)) BETWEEN 1 AND 180", name="ck_menu_items_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    canonical_dish_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_dishes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    ingredients_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    restaurant: Mapped[Restaurant] = relationship()
    canonical_dish: Mapped[CanonicalDish] = relationship(back_populates="menu_items")
    ingredient_links: Mapped[list["MenuItemIngredient"]] = relationship(
        back_populates="menu_item", cascade="all, delete-orphan", passive_deletes=True
    )

    @validates("name")
    def normalize_name(self, key: str, value: str) -> str:
        return _clean_text(value, key, 180)

    @validates("price")
    def validate_price(self, _key: str, value: int) -> int:
        if type(value) is not int or not 0 < value <= 10000000:
            raise ValueError("price phải là số nguyên VNĐ lớn hơn 0 và không quá 10.000.000.")
        return value


class MenuItemIngredient(Base):
    __tablename__ = "menu_item_ingredients"

    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"), primary_key=True
    )

    menu_item: Mapped[MenuItem] = relationship(back_populates="ingredient_links")
    ingredient: Mapped[Ingredient] = relationship(back_populates="menu_links")

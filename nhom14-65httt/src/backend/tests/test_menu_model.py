"""Kiểm tra món chuẩn, món bán theo quán và nguyên liệu thực tế."""

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.menu.models import CanonicalDish, Ingredient, MenuItem, MenuItemIngredient
from app.restaurants.models import Restaurant


@pytest.fixture
def db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            Restaurant(id=i, name=f"Quán {i}", address="Hà Nội", latitude=21, longitude=105)
            for i in (1, 2)
        )
        session.add(
            CanonicalDish(
                id=1,
                name="Phở bò",
                region="Bắc",
                method="nước",
                ingredients=["bò", "gạo"],
                source_id="sample:1",
            )
        )
        session.add_all([Ingredient(id=1, name="bò"), Ingredient(id=2, name="lạc")])
        session.commit()
        yield session
    engine.dispose()


def make_item(**overrides):
    values = {"restaurant_id": 1, "canonical_dish_id": 1, "name": "Phở bò tại quán", "price": 50000}
    return MenuItem(**(values | overrides))


def make_dish(**overrides):
    values = {"name": "Bún gà", "region": "Bắc", "method": "nước"}
    return CanonicalDish(**(values | overrides))


def test_canonical_features_and_source_are_persisted(db):
    dish = make_dish(
        name=" Bún gà ",
        region=" Bắc ",
        method=" nước ",
        spice_level=2,
        ingredients=[" GÀ ", "rau", "gà"],
        labels=[" Nhẹ ", "nhẹ"],
        source_id=" vifoodrec:123 ",
        is_simulated=True,
    )
    db.add(dish)
    db.commit()
    db.expire_all()
    stored = db.get(CanonicalDish, dish.id)
    assert (stored.name, stored.region, stored.method) == ("Bún gà", "Bắc", "nước")
    assert stored.ingredients == ["gà", "rau"] and stored.labels == ["Nhẹ"]
    assert stored.spice_level == 2 and stored.source_id == "vifoodrec:123"
    assert stored.is_simulated is True


def test_menu_prices_and_names_are_independent_between_restaurants(db):
    first = make_item(name="Phở đặc biệt", price=50000)
    second = make_item(restaurant_id=2, name="Phở tái", price=70000)
    db.add_all([first, second])
    db.commit()
    first.price = 55000
    db.get(CanonicalDish, 1).name = "Phở bò chuẩn"
    db.commit()
    db.expire_all()
    assert db.get(MenuItem, first.id).price == 55000
    assert db.get(MenuItem, second.id).price == 70000
    assert db.get(MenuItem, second.id).name == "Phở tái"
    assert (
        db.get(MenuItem, first.id).canonical_dish_id
        == db.get(MenuItem, second.id).canonical_dish_id
    )


def test_new_item_is_not_automatically_available_or_verified(db):
    item = make_item(name=" Phở mới ")
    db.add(item)
    db.commit()
    db.expire_all()
    stored = db.get(MenuItem, item.id)
    assert stored.name == "Phở mới"
    assert stored.is_available is False and stored.ingredients_verified is False
    assert stored.is_simulated is False
    assert stored.restaurant.id == 1 and stored.canonical_dish.id == 1


def test_actual_ingredients_are_separate_from_canonical_features(db):
    item = make_item(ingredient_links=[MenuItemIngredient(ingredient_id=2)])
    db.add(item)
    db.commit()
    db.expire_all()
    stored = db.get(MenuItem, item.id)
    assert stored.canonical_dish.ingredients == ["bò", "gạo"]
    assert [link.ingredient.name for link in stored.ingredient_links] == ["lạc"]
    assert stored.ingredient_links[0] in db.get(Ingredient, 2).menu_links


@pytest.mark.parametrize("field", ["restaurant_id", "canonical_dish_id"])
def test_item_requires_existing_restaurant_and_dish(db, field):
    db.add(make_item(**{field: 999}))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("field", ["menu_item_id", "ingredient_id"])
def test_ingredient_link_requires_existing_records(db, field):
    item = make_item()
    db.add(item)
    db.commit()
    values = {"menu_item_id": item.id, "ingredient_id": 1}
    values[field] = 999
    db.add(MenuItemIngredient(**values))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_same_ingredient_cannot_be_linked_twice(db):
    item = make_item(ingredient_links=[MenuItemIngredient(ingredient_id=1)])
    db.add(item)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text("INSERT INTO menu_item_ingredients (menu_item_id, ingredient_id) VALUES (:id, 1)"),
            {"id": item.id},
        )
    db.rollback()


def test_deleting_item_removes_links_and_preserves_catalogs(db):
    item = make_item(ingredient_links=[MenuItemIngredient(ingredient_id=1)])
    db.add(item)
    db.commit()
    db.execute(text("DELETE FROM menu_items WHERE id = :id"), {"id": item.id})
    db.commit()
    assert db.query(MenuItemIngredient).count() == 0
    assert db.get(Ingredient, 1) is not None and db.get(CanonicalDish, 1) is not None
    assert db.get(Restaurant, 1) is not None


@pytest.mark.parametrize("parent", ["restaurants", "canonical_dishes", "ingredients"])
def test_referenced_catalog_records_cannot_be_deleted(db, parent):
    item = make_item(ingredient_links=[MenuItemIngredient(ingredient_id=1)])
    db.add(item)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text(f"DELETE FROM {parent} WHERE id = 1"))
    db.rollback()
    assert db.get(MenuItem, item.id) is not None


def test_ingredient_names_are_normalized_and_unique(db):
    db.add(Ingredient(name=" BÒ "))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("field,value", [("name", "Phở bò"), ("source_id", "sample:1")])
def test_duplicate_canonical_name_or_source_is_rejected(db, field, value):
    db.add(make_dish(**{field: value}))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_dishes_can_have_no_external_source_id(db):
    db.add_all([make_dish(name="Món tự khai báo 1"), make_dish(name="Món tự khai báo 2")])
    db.commit()
    assert db.query(CanonicalDish).filter(CanonicalDish.source_id.is_(None)).count() == 2


@pytest.mark.parametrize("invalid", [0, -1, 10000001, True, 50000.5, "50000"])
def test_invalid_prices_are_rejected(invalid):
    with pytest.raises(ValueError):
        make_item(price=invalid)


@pytest.mark.parametrize("invalid", [0, -1, 10000001])
def test_database_also_checks_price_range(db, invalid):
    item = make_item()
    db.add(item)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE menu_items SET price = :price WHERE id = :id"),
            {"price": invalid, "id": item.id},
        )
    db.rollback()


@pytest.mark.parametrize("invalid", [-1, 4, True, 1.5])
def test_invalid_spice_levels_are_rejected(invalid):
    with pytest.raises(ValueError):
        make_dish(spice_level=invalid)


@pytest.mark.parametrize("invalid", [-1, 4])
def test_database_also_checks_spice_level(db, invalid):
    with pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE canonical_dishes SET spice_level = :value WHERE id = 1"),
            {"value": invalid},
        )
    db.rollback()


@pytest.mark.parametrize(
    "factory,field",
    [
        (make_dish, "name"),
        (make_dish, "region"),
        (make_dish, "method"),
        (Ingredient, "name"),
        (make_item, "name"),
    ],
)
def test_empty_catalog_text_is_rejected(factory, field):
    with pytest.raises(ValueError):
        factory(**{field: "   "})


@pytest.mark.parametrize("field", ["ingredients", "labels"])
@pytest.mark.parametrize("invalid", [None, "bò", [1], ["  "]])
def test_feature_lists_require_nonempty_strings(field, invalid):
    with pytest.raises(ValueError):
        make_dish(**{field: invalid})


@pytest.mark.parametrize("field,value", [("ingredients", "gà"), ("labels", "món nước")])
def test_in_place_feature_updates_are_persisted(db, field, value):
    dish = make_dish()
    db.add(dish)
    db.commit()
    getattr(dish, field).append(value)
    db.commit()
    db.expire_all()
    assert getattr(db.get(CanonicalDish, dish.id), field) == [value]


def test_feature_defaults_are_not_shared_between_dishes(db):
    first, second = make_dish(name="Món 1"), make_dish(name="Món 2")
    db.add_all([first, second])
    db.flush()
    first.labels.append("mô phỏng")
    db.commit()
    db.expire_all()
    assert db.get(CanonicalDish, first.id).labels == ["mô phỏng"]
    assert db.get(CanonicalDish, second.id).labels == []


def test_database_defaults_apply_to_raw_catalog_inserts(db):
    db.execute(
        text("INSERT INTO canonical_dishes (name, region, method) VALUES ('Món SQL', 'Bắc', 'hấp')")
    )
    db.execute(text("INSERT INTO ingredients (name) VALUES ('rau')"))
    db.execute(
        text(
            "INSERT INTO menu_items (restaurant_id, canonical_dish_id, name, price) VALUES (1, 1, 'Món SQL bán', 30000)"
        )
    )
    db.commit()
    dish = db.query(CanonicalDish).filter_by(name="Món SQL").one()
    item = db.query(MenuItem).filter_by(name="Món SQL bán").one()
    assert dish.spice_level == 0 and dish.ingredients == dish.labels == []
    assert dish.source_id is None and dish.is_simulated is False
    assert item.is_available is False and item.ingredients_verified is False
    assert db.query(Ingredient).filter_by(name="rau").one().is_simulated is False


def test_availability_verification_and_simulation_flags_are_independent(db):
    item = make_item(is_available=True, ingredients_verified=True, is_simulated=True)
    db.add(item)
    db.commit()
    item.is_available = False
    db.commit()
    db.expire_all()
    stored = db.get(MenuItem, item.id)
    assert stored.is_available is False
    assert stored.ingredients_verified is True and stored.is_simulated is True

"""Kiểm tra hồ sơ quán, giới hạn phục vụ và liên kết tài khoản quản lý."""

from datetime import UTC, time

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.restaurants.models import Restaurant, RestaurantMembership, RestaurantStatus
from app.users.models import User, UserRole


@pytest.fixture
def db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            User(
                id=user_id,
                email=f"vendor{user_id}@example.vn",
                full_name=f"Chủ quán {user_id}",
                hashed_password="password-hash-from-auth-service",
                role=UserRole.VENDOR,
            )
            for user_id in (1, 2)
        )
        session.commit()
        yield session
    engine.dispose()


def make_restaurant(**overrides):
    values = {
        "name": "Bếp Việt",
        "address": "Hà Nội",
        "latitude": 21.0285,
        "longitude": 105.8542,
    }
    return Restaurant(**(values | overrides))


def test_store_restaurant_with_normalized_fields_and_defaults(db):
    restaurant = make_restaurant(name=" Bếp Việt ", address=" Hà Nội ")
    db.add(restaurant)
    db.commit()
    db.expire_all()
    stored = db.get(Restaurant, restaurant.id)
    assert stored.name == "Bếp Việt" and stored.address == "Hà Nội"
    assert stored.latitude == pytest.approx(21.0285)
    assert stored.longitude == pytest.approx(105.8542)
    assert stored.delivery_radius_km == 5
    assert stored.opens_at == stored.closes_at == time(0)
    assert stored.status is RestaurantStatus.PENDING
    assert stored.accepting_orders is False
    assert stored.is_simulated is False


def test_membership_links_manager_and_restaurant(db):
    restaurant = make_restaurant()
    membership = RestaurantMembership(user_id=1, restaurant=restaurant)
    db.add(membership)
    db.commit()
    db.expire_all()
    stored = db.get(RestaurantMembership, 1)
    assert stored.user.role is UserRole.VENDOR
    assert stored.restaurant.name == "Bếp Việt"
    assert stored in stored.restaurant.memberships


def test_one_manager_cannot_be_linked_to_two_restaurants(db):
    first, second = make_restaurant(), make_restaurant(name="Bếp khác")
    db.add_all([first, second])
    db.flush()
    db.add(RestaurantMembership(user_id=1, restaurant_id=first.id))
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text("INSERT INTO restaurant_memberships (user_id, restaurant_id) VALUES (1, :id)"),
            {"id": second.id},
        )
    db.rollback()
    assert db.get(RestaurantMembership, 1).restaurant_id == first.id


def test_multiple_managers_can_be_linked_to_same_restaurant(db):
    restaurant = make_restaurant()
    db.add_all(RestaurantMembership(user_id=user_id, restaurant=restaurant) for user_id in (1, 2))
    db.commit()
    db.expire_all()
    assert {m.user_id for m in db.get(Restaurant, restaurant.id).memberships} == {1, 2}


@pytest.mark.parametrize("missing", ["user", "restaurant"])
def test_membership_requires_existing_user_and_restaurant(db, missing):
    restaurant = make_restaurant()
    db.add(restaurant)
    db.commit()
    db.add(
        RestaurantMembership(
            user_id=999 if missing == "user" else 1,
            restaurant_id=999 if missing == "restaurant" else restaurant.id,
        )
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("parent", ["users", "restaurants"])
def test_parent_with_membership_cannot_be_deleted_accidentally(db, parent):
    restaurant = make_restaurant()
    db.add(RestaurantMembership(user_id=1, restaurant=restaurant))
    db.commit()
    identifier = 1 if parent == "users" else restaurant.id
    with pytest.raises(IntegrityError):
        db.execute(text(f"DELETE FROM {parent} WHERE id = :id"), {"id": identifier})
    db.rollback()
    assert db.get(RestaurantMembership, 1) is not None


@pytest.mark.parametrize("status", list(RestaurantStatus))
def test_approval_status_is_stored_as_lowercase(db, status):
    restaurant = make_restaurant(status=status)
    db.add(restaurant)
    db.commit()
    assert (
        db.execute(
            text("SELECT status FROM restaurants WHERE id = :id"), {"id": restaurant.id}
        ).scalar_one()
        == status.value
    )


@pytest.mark.parametrize("invalid", ["active", "APPROVED", "rejected"])
def test_database_rejects_unknown_approval_status(db, invalid):
    restaurant = make_restaurant()
    db.add(restaurant)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE restaurants SET status = :status WHERE id = :id"),
            {"status": invalid, "id": restaurant.id},
        )
    db.rollback()


@pytest.mark.parametrize(
    "field,value",
    [
        ("latitude", -90.1),
        ("latitude", 90.1),
        ("longitude", -180.1),
        ("longitude", 180.1),
        ("delivery_radius_km", 0),
        ("delivery_radius_km", -1),
        ("delivery_radius_km", 50.1),
    ],
)
def test_coordinate_and_radius_limits_enforced_in_orm_and_db(db, field, value):
    with pytest.raises(ValueError):
        make_restaurant(**{field: value})
    restaurant = make_restaurant()
    db.add(restaurant)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text(f"UPDATE restaurants SET {field} = :value WHERE id = :id"),
            {"value": value, "id": restaurant.id},
        )
    db.rollback()


@pytest.mark.parametrize("field", ["latitude", "longitude", "delivery_radius_km"])
@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), True, "21"])
def test_nonfinite_and_non_numeric_coordinates_are_rejected(field, invalid):
    with pytest.raises(ValueError):
        make_restaurant(**{field: invalid})


@pytest.mark.parametrize("field", ["name", "address"])
def test_blank_text_is_rejected_in_orm_and_db(db, field):
    with pytest.raises(ValueError):
        make_restaurant(**{field: "   "})
    restaurant = make_restaurant()
    db.add(restaurant)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(
            text(f"UPDATE restaurants SET {field} = '   ' WHERE id = :id"),
            {"id": restaurant.id},
        )
    db.rollback()


@pytest.mark.parametrize("field,maximum", [("name", 160), ("address", 500)])
def test_overlong_text_is_rejected(db, field, maximum):
    with pytest.raises(ValueError):
        make_restaurant(**{field: "x" * (maximum + 1)})


@pytest.mark.parametrize(
    "opening,closing", [("08:00", "22:00"), ("22:00", "02:00"), ("00:00", "00:00")]
)
def test_daily_overnight_and_all_day_hours_are_preserved(db, opening, closing):
    restaurant = make_restaurant(opens_at=opening, closes_at=closing)
    db.add(restaurant)
    db.commit()
    db.expire_all()
    stored = db.get(Restaurant, restaurant.id)
    assert stored.opens_at == time.fromisoformat(opening)
    assert stored.closes_at == time.fromisoformat(closing)


@pytest.mark.parametrize("field", ["opens_at", "closes_at"])
@pytest.mark.parametrize("invalid", ["24:00", "08:60", "8:00", time(8, 0, 1), time(8, tzinfo=UTC)])
def test_invalid_opening_hours_are_rejected(field, invalid):
    with pytest.raises(ValueError):
        make_restaurant(**{field: invalid})


def test_database_defaults_and_simulated_flag(db):
    db.execute(
        text(
            "INSERT INTO restaurants (name, address, latitude, longitude) VALUES ('Bếp mẫu', 'Hà Nội', 21, 105)"
        )
    )
    db.commit()
    stored = db.query(Restaurant).one()
    assert stored.status is RestaurantStatus.PENDING
    assert stored.accepting_orders is False
    assert stored.delivery_radius_km == 5
    assert stored.opens_at == stored.closes_at == time(0)
    stored.is_simulated = True
    db.commit()
    db.expire_all()
    assert db.get(Restaurant, stored.id).is_simulated is True

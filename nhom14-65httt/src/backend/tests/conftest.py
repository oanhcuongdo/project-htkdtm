"""Fixture API quán dùng DB riêng được tạo bằng Alembic, không dùng DB ứng dụng."""

from datetime import UTC, datetime, time
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from alembic import command
from app.config import settings
from app.database import get_db
from app.main import app
from app.menu.models import CanonicalDish, Ingredient, MenuItem, MenuItemIngredient
from app.restaurants import service
from app.restaurants.models import Restaurant, RestaurantMembership
from app.users.models import User


@pytest.fixture
def restaurant_api(tmp_path, monkeypatch):
    monkeypatch.setattr(
        settings, "SECRET_KEY", "restaurant-test-only-key-with-at-least-32-characters"
    )
    monkeypatch.setattr(service, "utcnow", lambda: datetime(2026, 11, 26, 3, tzinfo=UTC))
    url = "sqlite:///" + (tmp_path / "restaurants.db").as_posix()
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    with Session(engine) as db:
        for uid, role in [
            (1, "customer"),
            (2, "vendor"),
            (3, "admin"),
            (4, "vendor"),
            (5, "vendor"),
            (6, "vendor"),
            (7, "vendor"),
        ]:
            db.add(
                User(
                    id=uid,
                    email=f"{role}{uid}@example.vn",
                    full_name=f"Tài khoản {uid}",
                    role=role,
                    hashed_password="not-used-for-login-in-this-fixture",
                )
            )
        for rid, status, start, end, accepting in [
            (1, "approved", time(8), time(22), True),
            (2, "pending", time(8), time(22), False),
            (3, "suspended", time(0), time(0), False),
            (4, "approved", time(22), time(2), True),
            (5, "approved", time(0), time(0), False),
        ]:
            db.add(
                Restaurant(
                    id=rid,
                    name=f"Quán {rid}",
                    address="Hà Nội",
                    latitude=21,
                    longitude=105,
                    status=status,
                    opens_at=start,
                    closes_at=end,
                    accepting_orders=accepting,
                )
            )
        db.flush()
        db.add_all(
            [
                RestaurantMembership(user_id=uid, restaurant_id=rid)
                for uid, rid in [(2, 1), (4, 2), (6, 3), (7, 1)]
            ]
        )
        db.commit()

    def override_db():
        with Session(engine) as db:
            yield db

    previous = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client, engine
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous)
        engine.dispose()


@pytest.fixture
def menu_api(restaurant_api):
    client, engine = restaurant_api
    with Session(engine) as db:
        db.add_all(
            [
                CanonicalDish(
                    id=1,
                    name="Phở bò",
                    region="Bắc",
                    method="nước",
                    ingredients=["bò"],
                    labels=["Truyền thống"],
                    source_id="pho-1",
                    is_simulated=True,
                ),
                CanonicalDish(id=2, name="Bún gà", region="Bắc", method="nước"),
                CanonicalDish(id=3, name="Món chưa dùng", region="Nam", method="hấp"),
            ]
        )
        db.add_all(
            [
                Ingredient(id=i, name=name)
                for i, name in [(1, "bò"), (2, "hành"), (3, "gà"), (4, "nguyên liệu chưa dùng")]
            ]
        )
        db.flush()
        for mid, rid, available in [
            (1, 1, True),
            (2, 1, False),
            (3, 2, True),
            (4, 3, True),
            (5, 4, True),
            (6, 5, True),
        ]:
            db.add(
                MenuItem(
                    id=mid,
                    restaurant_id=rid,
                    canonical_dish_id=1 if mid != 2 else 2,
                    name=f"Món {mid}",
                    price=40000,
                    is_available=available,
                    ingredients_verified=mid == 1,
                    is_simulated=mid == 1,
                )
            )
        db.flush()
        db.add_all([MenuItemIngredient(menu_item_id=1, ingredient_id=i) for i in (1, 2)])
        db.commit()
    yield client, engine

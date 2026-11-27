"""Exercise frozen migrations on temporary DBs, rather than metadata.create_all()."""

from hashlib import sha256
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.util import CommandError
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.config import settings
from app.database import Base
from app.menu.models import CanonicalDish, Ingredient, MenuItem, MenuItemIngredient
from app.orders.models import Order, OrderItem, OrderStatus
from app.preferences.models import Preference
from app.restaurants.models import Restaurant, RestaurantMembership
from app.reviews.models import Review
from app.tracking.models import (
    EventType,
    InteractionEvent,
    RecommendationImpression,
    RecommendationRequest,
)
from app.users.models import User
from migration_support import compare_server_default

BACKEND = Path(__file__).resolve().parents[1]
TABLES = {
    "users",
    "preferences",
    "restaurants",
    "restaurant_memberships",
    "canonical_dishes",
    "ingredients",
    "menu_items",
    "menu_item_ingredients",
    "orders",
    "order_items",
    "order_status_history",
    "reviews",
    "recommendation_requests",
    "recommendation_impressions",
    "interaction_events",
}


def config(buffer=None):
    return Config(str(BACKEND / "alembic.ini"), output_buffer=buffer)


def sqlite_engine(url):
    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "migration.db").as_posix()
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    cfg = config()
    command.upgrade(cfg, "head")
    engine = sqlite_engine(url)
    yield cfg, engine
    engine.dispose()


def populate(session):
    session.add_all(
        [
            User(id=1, email="customer@example.vn", full_name="Khách", hashed_password="hash"),
            User(
                id=2,
                email="vendor@example.vn",
                full_name="Quán",
                hashed_password="hash",
                role="vendor",
            ),
        ]
    )
    session.add(Restaurant(id=1, name="Bếp Việt", address="Hà Nội", latitude=21, longitude=105))
    session.add(CanonicalDish(id=1, name="Phở bò", region="Bắc", method="nước"))
    session.add(Ingredient(id=1, name="bò"))
    session.flush()
    session.add(MenuItem(id=1, restaurant_id=1, canonical_dish_id=1, name="Phở bán", price=50000))
    session.add(RestaurantMembership(user_id=2, restaurant_id=1))
    session.add(Preference(user_id=1, regions=["Bắc"]))
    session.flush()
    session.add(MenuItemIngredient(menu_item_id=1, ingredient_id=1))
    order = Order(
        id=1,
        user_id=1,
        restaurant_id=1,
        status=OrderStatus.COMPLETED,
        total=50000,
        delivery_address="Số 1 Hà Nội",
        latitude=21,
        longitude=105,
        session_id=uuid4(),
        idempotency_key=uuid4(),
        payload_hash=sha256(b"request").hexdigest(),
        items=[
            OrderItem(menu_item_id=1, quantity=1, snapshot_name="Phở lúc đặt", snapshot_price=50000)
        ],
    )
    session.add(order)
    request = RecommendationRequest(
        user_id=1, session_id=order.session_id, algorithm_version="content_v1"
    )
    session.add(request)
    session.flush()
    session.add(RecommendationImpression(request_id=request.id, menu_item_id=1, rank=1))
    session.flush()
    session.add(Review(order_id=1, menu_item_id=1, user_id=1, rating=5))
    session.add(
        InteractionEvent(
            event_id=uuid4(),
            user_id=1,
            session_id=request.session_id,
            request_id=request.id,
            menu_item_id=1,
            event_type=EventType.IMPRESSION,
            occurred_at=request.created_at,
        )
    )
    session.commit()


def test_upgrade_creates_all_fifteen_tables_and_revision(migrated_db):
    _, engine = migrated_db
    assert set(inspect(engine).get_table_names()) == TABLES | {"alembic_version"}
    assert set(Base.metadata.tables) == TABLES
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "001"
        )
    assert inspect(engine).get_view_names() == []


def test_migrated_keys_indexes_and_checks_match_models(migrated_db):
    _, engine = migrated_db
    inspector = inspect(engine)
    for name, table in Base.metadata.tables.items():
        assert inspector.get_pk_constraint(name)["constrained_columns"] == list(
            table.primary_key.columns.keys()
        )
        expected_unique = {
            tuple(c.columns.keys()) for c in table.constraints if isinstance(c, sa.UniqueConstraint)
        }
        actual_unique = {tuple(c["column_names"]) for c in inspector.get_unique_constraints(name)}
        assert actual_unique == expected_unique, name
        expected_indexes = {
            (tuple(c.name for c in index.columns), index.unique) for index in table.indexes
        }
        actual_indexes = {
            (tuple(index["column_names"]), index["unique"]) for index in inspector.get_indexes(name)
        }
        assert actual_indexes == expected_indexes, name
        expected_fk = {
            (
                tuple(c.columns.keys()),
                c.referred_table.name,
                tuple(e.column.name for e in c.elements),
                c.ondelete,
            )
            for c in table.foreign_key_constraints
        }
        actual_fk = {
            (
                tuple(c["constrained_columns"]),
                c["referred_table"],
                tuple(c["referred_columns"]),
                c["options"].get("ondelete"),
            )
            for c in inspector.get_foreign_keys(name)
        }
        assert actual_fk == expected_fk, name
        expected_checks = {c.name for c in table.constraints if isinstance(c, sa.CheckConstraint)}
        assert {c["name"] for c in inspector.get_check_constraints(name)} == expected_checks, name


def test_alembic_check_reports_no_schema_drift(migrated_db):
    cfg, _ = migrated_db
    command.check(cfg)


def test_alembic_check_detects_unmigrated_schema_change(migrated_db):
    cfg, engine = migrated_db
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN unexpected_column VARCHAR(40)"))
    with pytest.raises(CommandError):
        command.check(cfg)


def test_orm_can_store_business_records_on_migrated_schema(migrated_db):
    _, engine = migrated_db
    with Session(engine) as session:
        populate(session)
        assert session.query(Review).one().order_item.snapshot_name == "Phở lúc đặt"
        assert session.query(InteractionEvent).one().request.user_id == 1
        assert session.query(RecommendationImpression).one().displayed_at is None
        assert session.query(Preference).one().regions == ["Bắc"]


@pytest.mark.parametrize(
    "sql,params",
    [
        ("UPDATE users SET role = :value WHERE id = 1", {"value": "owner"}),
        ("UPDATE menu_items SET price = :value WHERE id = 1", {"value": 0}),
        ("UPDATE reviews SET rating = :value", {"value": 6}),
        ("UPDATE interaction_events SET user_id = :value", {"value": 2}),
        ("DELETE FROM order_items WHERE id = :value", {"value": 1}),
    ],
)
def test_constraints_are_enforced_by_actual_migration(migrated_db, sql, params):
    _, engine = migrated_db
    with Session(engine) as session:
        populate(session)
    with engine.connect() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(text(sql), params)
        connection.rollback()


def test_upgrade_head_again_preserves_data(migrated_db):
    cfg, engine = migrated_db
    with Session(engine) as session:
        populate(session)
    command.upgrade(cfg, "head")
    with Session(engine) as session:
        assert session.query(User).count() == 2
        assert session.query(Order).count() == session.query(Review).count() == 1


def test_downgrade_and_upgrade_work_even_with_referenced_data(migrated_db):
    cfg, engine = migrated_db
    with Session(engine) as session:
        populate(session)
    command.downgrade(cfg, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM alembic_version")).scalar_one() == 0
    command.upgrade(cfg, "head")
    assert set(inspect(engine).get_table_names()) == TABLES | {"alembic_version"}
    command.check(cfg)


def test_config_works_from_outside_backend(tmp_path, monkeypatch):
    url = "sqlite:///" + (tmp_path / "other-working-directory.db").as_posix()
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    monkeypatch.chdir(tmp_path)
    command.upgrade(config(), "head")
    engine = sqlite_engine(url)
    assert "interaction_events" in inspect(engine).get_table_names()
    engine.dispose()


def test_encoded_database_password_is_not_escaped_twice(tmp_path, monkeypatch):
    encoded_url = sa.URL.create(
        "postgresql+psycopg2",
        username="migration_test",
        password="test%@:/password",
        host="localhost",
        database="unused",
    ).render_as_string(hide_password=False)
    monkeypatch.setattr(settings, "DATABASE_URL", encoded_url)
    sqlite_url = "sqlite:///" + (tmp_path / "captured-url.db").as_posix()
    original = sa.engine_from_config
    captured = []

    def capture(configuration, **kwargs):
        captured.append(configuration["sqlalchemy.url"])
        return original(configuration | {"sqlalchemy.url": sqlite_url}, **kwargs)

    monkeypatch.setattr(sa, "engine_from_config", capture)
    command.upgrade(config(), "head")
    assert captured == [encoded_url]


def test_postgresql_offline_sql_uses_portable_types_and_defaults(monkeypatch):
    monkeypatch.setattr(
        settings, "DATABASE_URL", "postgresql+psycopg2://test:test@localhost/unused"
    )

    def forbid_connection(*_args, **_kwargs):
        raise AssertionError("Offline mode must not connect to PostgreSQL")

    monkeypatch.setattr(sa, "engine_from_config", forbid_connection)
    output = StringIO()
    command.upgrade(config(output), "head", sql=True)
    sql = output.getvalue()
    for table in TABLES:
        assert f"CREATE TABLE {table} (" in sql
    assert "UUID" in sql and "BIGINT" in sql and "TIMESTAMP WITH TIME ZONE" in sql
    assert "BOOLEAN DEFAULT false" in sql
    assert "BOOLEAN DEFAULT 0" not in sql
    assert "FOREIGN KEY(order_id, menu_item_id) REFERENCES order_items" in sql
    assert "FOREIGN KEY(request_id, user_id, session_id) REFERENCES recommendation_requests" in sql
    assert "CREATE TYPE" not in sql
    output = StringIO()
    command.downgrade(config(output), "001:base", sql=True)
    for table in TABLES:
        assert f"DROP TABLE {table};" in output.getvalue()


@pytest.mark.parametrize(
    "actual,expected,different",
    [
        ("'[]'::json", "'[]'", False),
        ("'[\"bò\"]'::json", "'[]'", True),
        ('\'{"b":2,"a":1}\'::json', '\'{"a":1,"b":2}\'', False),
        ("'[\"O''Connor\"]'::json", "'[\"O''Connor\"]'", False),
        (None, "'[]'", True),
        (None, None, False),
    ],
)
def test_postgresql_json_defaults_are_compared_without_database_queries(
    actual, expected, different
):
    context = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    column = sa.Column("labels", sa.JSON())
    assert compare_server_default(context, column, column, actual, None, expected) is different


@pytest.mark.parametrize(
    "dialect,column_type", [("sqlite", sa.JSON()), ("postgresql", sa.Integer())]
)
def test_other_default_comparisons_are_delegated_to_alembic(dialect, column_type):
    context = SimpleNamespace(dialect=SimpleNamespace(name=dialect))
    column = sa.Column("value", column_type)
    assert compare_server_default(context, column, column, "0", None, "0") is None

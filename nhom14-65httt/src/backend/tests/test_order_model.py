"""Kiểm tra dữ liệu đơn hàng; chưa thay thế kiểm thử giao dịch/API ở phần sau."""

from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256
from uuid import UUID, uuid1, uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.menu.models import CanonicalDish, MenuItem
from app.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from app.restaurants.models import Restaurant
from app.users.models import User


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
                id=i,
                email=f"user{i}@example.vn",
                full_name=f"Người dùng {i}",
                hashed_password="hash",
                role="customer" if i == 1 else "vendor",
            )
            for i in (1, 2)
        )
        session.add(Restaurant(id=1, name="Bếp Việt", address="Hà Nội", latitude=21, longitude=105))
        session.add(CanonicalDish(id=1, name="Phở bò", region="Bắc", method="nước"))
        session.flush()
        session.add_all(
            MenuItem(id=i, restaurant_id=1, canonical_dish_id=1, name=f"Phở {i}", price=50000)
            for i in (1, 2, 3)
        )
        session.commit()
        yield session
    engine.dispose()


def make_order(**overrides):
    values = {
        "user_id": 1,
        "restaurant_id": 1,
        "total": 100000,
        "delivery_address": "Số 1 Hà Nội",
        "latitude": 21,
        "longitude": 105,
        "session_id": uuid4(),
        "idempotency_key": uuid4(),
        "payload_hash": sha256(b"request").hexdigest(),
    }
    return Order(**(values | overrides))


def line(**overrides):
    values = {
        "menu_item_id": 1,
        "quantity": 2,
        "snapshot_price": 50000,
        "snapshot_name": "Phở lúc đặt",
    }
    return OrderItem(**(values | overrides))


def test_store_order_items_history_and_defaults(db):
    order = make_order(
        delivery_address=" Số 1 Hà Nội ",
        items=[line()],
        history=[OrderStatusHistory(status=OrderStatus.PENDING, actor_id=1)],
    )
    db.add(order)
    db.commit()
    db.expire_all()
    stored = db.get(Order, order.id)
    assert stored.status is OrderStatus.PENDING and stored.is_simulated is False
    assert stored.delivery_address == "Số 1 Hà Nội"
    assert stored.user.id == 1 and stored.restaurant.id == 1
    assert isinstance(stored.idempotency_key, UUID) and stored.session_id.version == 4
    assert stored.items[0].order is stored and stored.items[0].menu_item.id == 1
    assert stored.history[0].actor.id == 1 and stored.history[0].order is stored
    assert stored.created_at is not None and stored.history[0].created_at is not None


def test_menu_changes_do_not_rewrite_order_snapshots(db):
    order = make_order(items=[line()])
    db.add(order)
    db.commit()
    item = db.get(MenuItem, 1)
    item.name, item.price, item.is_available = "Tên mới", 90000, False
    db.commit()
    db.expire_all()
    stored = db.get(Order, order.id)
    assert stored.total == 100000
    assert (
        stored.items[0].snapshot_name == "Phở lúc đặt" and stored.items[0].snapshot_price == 50000
    )


def test_same_key_cannot_create_another_order_even_for_different_user(db):
    key = uuid4()
    db.add(make_order(idempotency_key=key))
    db.commit()
    db.add(make_order(user_id=2, idempotency_key=str(key)))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert db.query(Order).count() == 1


def test_same_session_can_contain_distinct_orders(db):
    sid = uuid4()
    db.add_all([make_order(session_id=sid), make_order(session_id=sid)])
    db.commit()
    assert db.query(Order).filter_by(session_id=sid).count() == 2


def test_duplicate_menu_item_in_one_order_is_rejected(db):
    db.add(make_order(items=[line(), line()]))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_large_total_does_not_overflow_32_bit_integer(db):
    items = [line(menu_item_id=i, quantity=99, snapshot_price=10000000) for i in (1, 2, 3)]
    order = make_order(total=2970000000, items=items)
    db.add(order)
    db.commit()
    db.expire_all()
    assert db.get(Order, order.id).total == sum(i.quantity * i.snapshot_price for i in order.items)


@pytest.mark.parametrize("status", list(OrderStatus))
def test_order_and_history_store_lowercase_statuses(db, status):
    order = make_order(
        status=status,
        history=[
            OrderStatusHistory(
                status=status,
                actor_id=1,
                reason="Hết nguyên liệu" if status is OrderStatus.REJECTED else None,
            )
        ],
    )
    db.add(order)
    db.commit()
    assert (
        db.execute(text("SELECT status FROM orders WHERE id = :id"), {"id": order.id}).scalar_one()
        == status.value
    )
    assert (
        db.execute(
            text("SELECT status FROM order_status_history WHERE order_id = :id"), {"id": order.id}
        ).scalar_one()
        == status.value
    )


@pytest.mark.parametrize("table", ["orders", "order_status_history"])
@pytest.mark.parametrize("invalid", ["PENDING", "paid", "unknown"])
def test_database_rejects_unknown_status(db, table, invalid):
    order = make_order(history=[OrderStatusHistory(status="pending", actor_id=1)])
    db.add(order)
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text(f"UPDATE {table} SET status = :status"), {"status": invalid})
    db.rollback()


def test_history_is_sorted_by_time_and_tiebreaker_id(db):
    start = datetime.now(UTC) - timedelta(minutes=10)
    first = OrderStatusHistory(status="pending", actor_id=1, created_at=start)
    second = OrderStatusHistory(
        status="confirmed", actor_id=2, created_at=start + timedelta(minutes=1)
    )
    third = OrderStatusHistory(
        status="preparing", actor_id=2, created_at=start + timedelta(minutes=1)
    )
    order = make_order(status="preparing", history=[first, second, third])
    db.add(order)
    db.commit()
    db.expire_all()
    assert [h.status.value for h in db.get(Order, order.id).history] == [
        "pending",
        "confirmed",
        "preparing",
    ]


def test_rejected_history_requires_reason(db):
    db.add(
        make_order(status="rejected", history=[OrderStatusHistory(status="rejected", actor_id=2)])
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("field", ["user_id", "restaurant_id"])
def test_order_requires_existing_owner_and_restaurant(db, field):
    db.add(make_order(**{field: 999}))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_order_item_requires_existing_menu_item(db):
    db.add(make_order(items=[line(menu_item_id=999)]))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_history_requires_existing_actor(db):
    db.add(make_order(history=[OrderStatusHistory(status="pending", actor_id=999)]))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("child", ["item", "history"])
def test_child_requires_existing_order(db, child):
    record = (
        line(order_id=999)
        if child == "item"
        else OrderStatusHistory(order_id=999, status="pending", actor_id=1)
    )
    db.add(record)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("table", ["orders", "users", "restaurants", "menu_items"])
def test_referenced_transaction_data_cannot_be_deleted(db, table):
    order = make_order(items=[line()], history=[OrderStatusHistory(status="pending", actor_id=2)])
    db.add(order)
    db.commit()
    identifier = order.id if table == "orders" else 1
    with pytest.raises(IntegrityError):
        db.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": identifier})
    db.rollback()
    assert db.get(Order, order.id) is not None


@pytest.mark.parametrize("field", ["session_id", "idempotency_key"])
@pytest.mark.parametrize("invalid", ["not-a-uuid", str(uuid1()), None])
def test_identifiers_require_uuid_v4(field, invalid):
    with pytest.raises(ValueError):
        make_order(**{field: invalid})


@pytest.mark.parametrize("invalid", ["hash", "g" * 64, " " * 64])
def test_payload_hash_requires_sha256_hex(invalid):
    with pytest.raises(ValueError):
        make_order(payload_hash=invalid)


@pytest.mark.parametrize(
    "factory,field,invalid",
    [
        (make_order, "total", 0),
        (make_order, "total", True),
        (make_order, "total", 2**63),
        (line, "quantity", 0),
        (line, "quantity", 100),
        (line, "quantity", 1.5),
        (line, "snapshot_price", 0),
        (line, "snapshot_price", 10000001),
        (line, "snapshot_price", True),
    ],
)
def test_invalid_amounts_are_rejected(factory, field, invalid):
    with pytest.raises(ValueError):
        factory(**{field: invalid})


@pytest.mark.parametrize(
    "table,field,invalid",
    [
        ("orders", "total", 0),
        ("order_items", "quantity", 0),
        ("order_items", "quantity", 100),
        ("order_items", "snapshot_price", 0),
        ("order_items", "snapshot_price", 10000001),
    ],
)
def test_database_also_checks_amount_ranges(db, table, field, invalid):
    db.add(make_order(items=[line()]))
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text(f"UPDATE {table} SET {field} = :value"), {"value": invalid})
    db.rollback()


@pytest.mark.parametrize(
    "field,invalid",
    [("latitude", 91), ("longitude", 181), ("latitude", float("nan")), ("longitude", True)],
)
def test_invalid_delivery_coordinates_are_rejected(field, invalid):
    with pytest.raises(ValueError):
        make_order(**{field: invalid})


@pytest.mark.parametrize(
    "factory,field",
    [(make_order, "delivery_address"), (line, "snapshot_name"), (OrderStatusHistory, "reason")],
)
def test_blank_snapshot_or_delivery_text_is_rejected(factory, field):
    with pytest.raises(ValueError):
        factory(**{field: "   "})


@pytest.mark.parametrize("factory", [make_order, OrderStatusHistory])
def test_explicit_timestamps_require_timezone(factory):
    with pytest.raises(ValueError):
        factory(created_at=datetime(2026, 1, 1))
    value = datetime(2026, 1, 1, 7, tzinfo=timezone(timedelta(hours=7)))
    assert factory(created_at=value).created_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_simulation_flag_and_hash_normalization_are_persisted(db):
    order = make_order(is_simulated=True, payload_hash="A" * 64)
    db.add(order)
    db.commit()
    db.expire_all()
    assert db.get(Order, order.id).is_simulated is True
    assert db.get(Order, order.id).payload_hash == "a" * 64

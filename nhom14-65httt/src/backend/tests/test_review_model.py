"""Kiểm tra dữ liệu đánh giá và liên kết món thực sự xuất hiện trong đơn."""

from datetime import UTC, datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.menu.models import CanonicalDish, MenuItem
from app.orders.models import Order, OrderItem, OrderStatus
from app.restaurants.models import Restaurant
from app.reviews.models import Review
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
                email=f"customer{i}@example.vn",
                full_name=f"Khách {i}",
                hashed_password="hash",
            )
            for i in (1, 2)
        )
        session.add(Restaurant(id=1, name="Bếp Việt", address="Hà Nội", latitude=21, longitude=105))
        session.add(CanonicalDish(id=1, name="Phở bò", region="Bắc", method="nước"))
        session.flush()
        session.add_all(
            MenuItem(id=i, restaurant_id=1, canonical_dish_id=1, name=f"Phở {i}", price=50000)
            for i in (1, 2)
        )
        session.flush()
        for order_id, user_id, item_id in ((1, 1, 1), (2, 1, 2), (3, 2, 1)):
            session.add(
                Order(
                    id=order_id,
                    user_id=user_id,
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
                        OrderItem(
                            menu_item_id=item_id,
                            quantity=1,
                            snapshot_name=f"Phở {item_id} lúc đặt",
                            snapshot_price=50000,
                        )
                    ],
                )
            )
        session.commit()
        yield session
    engine.dispose()


def make_review(**overrides):
    return Review(**({"order_id": 1, "menu_item_id": 1, "user_id": 1, "rating": 5} | overrides))


def test_store_review_and_load_purchased_item(db):
    started = datetime.now(UTC)
    review = make_review(comment="  Món ngon!  ")
    db.add(review)
    db.flush()
    assert started <= review.created_at <= datetime.now(UTC)
    db.commit()
    db.expire_all()
    stored = db.get(Review, review.id)
    assert stored.rating == 5 and stored.comment == "Món ngon!"
    assert stored.order.id == 1 and stored.menu_item.id == 1 and stored.user.id == 1
    assert stored.order_item.snapshot_name == "Phở 1 lúc đặt"
    assert stored.is_simulated is False


def test_item_must_belong_to_that_order_even_when_both_records_exist(db):
    db.add(make_review(menu_item_id=2))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_same_item_in_same_order_can_only_be_reviewed_once(db):
    db.add(make_review(rating=5))
    db.commit()
    db.add(make_review(rating=1))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert db.query(Review).one().rating == 5


def test_same_menu_item_can_be_reviewed_after_separate_purchases(db):
    db.add_all([make_review(), make_review(order_id=3, user_id=2)])
    db.commit()
    assert db.query(Review).filter_by(menu_item_id=1).count() == 2


@pytest.mark.parametrize("field", ["order_id", "menu_item_id", "user_id"])
def test_review_cannot_reference_missing_records(db, field):
    db.add(make_review(**{field: 999}))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("rating", [1, 2, 3, 4, 5])
def test_all_star_ratings_are_persisted(db, rating):
    review = make_review(rating=rating)
    db.add(review)
    db.commit()
    db.expire_all()
    assert db.get(Review, review.id).rating == rating


@pytest.mark.parametrize("invalid", [-1, 0, 6, True, 4.5, "5"])
def test_non_integer_or_out_of_range_ratings_are_rejected(invalid):
    with pytest.raises(ValueError):
        make_review(rating=invalid)


@pytest.mark.parametrize("invalid", [-1, 0, 6])
def test_database_also_enforces_rating_range(db, invalid):
    db.add(make_review())
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text("UPDATE reviews SET rating = :value"), {"value": invalid})
    db.rollback()


@pytest.mark.parametrize("invalid", [None, 123, "x" * 2001])
def test_invalid_comments_are_rejected(invalid):
    with pytest.raises(ValueError):
        make_review(comment=invalid)


def test_rating_does_not_require_comment(db):
    review = make_review()
    db.add(review)
    db.commit()
    db.expire_all()
    assert db.get(Review, review.id).comment == ""


def test_database_rejects_overlong_comment(db):
    db.add(make_review())
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text("UPDATE reviews SET comment = :value"), {"value": "x" * 2001})
    db.rollback()


@pytest.mark.parametrize("table", ["order_items", "orders", "menu_items", "users"])
def test_transaction_records_with_review_are_protected_from_deletion(db, table):
    db.add(make_review())
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text(f"DELETE FROM {table} WHERE id = 1"))
    db.rollback()
    assert db.query(Review).count() == 1


def test_menu_changes_preserve_review_link_to_purchase_snapshot(db):
    review = make_review()
    db.add(review)
    db.commit()
    db.get(MenuItem, 1).name = "Tên món mới"
    db.get(MenuItem, 1).price = 80000
    db.commit()
    db.expire_all()
    stored = db.get(Review, review.id)
    assert stored.order_item.snapshot_name == "Phở 1 lúc đặt"
    assert stored.order_item.snapshot_price == 50000


def test_database_defaults_and_simulated_flag(db):
    db.execute(
        text("INSERT INTO reviews (order_id, menu_item_id, user_id, rating) VALUES (1, 1, 1, 4)")
    )
    db.commit()
    stored = db.query(Review).one()
    assert stored.comment == "" and stored.is_simulated is False and stored.created_at is not None
    stored.is_simulated = True
    db.commit()
    db.expire_all()
    assert db.get(Review, stored.id).is_simulated is True


def test_explicit_timestamp_is_normalized_to_utc():
    with pytest.raises(ValueError):
        make_review(created_at=datetime(2026, 1, 1))
    value = datetime(2026, 1, 1, 7, tzinfo=timezone(timedelta(hours=7)))
    assert make_review(created_at=value).created_at == datetime(2026, 1, 1, tzinfo=UTC)

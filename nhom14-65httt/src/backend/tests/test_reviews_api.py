"""Đánh giá món đã mua: đơn hoàn tất, quyền, snapshot, chống trùng và rollback."""

from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.auth.utils import create_token
from app.menu.models import MenuItem
from app.orders.models import Order, OrderItem, OrderStatus
from app.reviews import service
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate
from app.users.models import User

PATH = "/api/v1/orders/{}/review"


def auth(uid):
    return {} if uid is None else {"Authorization": "Bearer " + create_token(uid, "access")}


def payload(**changes):
    return dict(menu_item_id=1, rating=5, comment="  Rất ngon  ") | changes


@pytest.fixture
def review_api(menu_api):
    client, engine = menu_api
    with Session(engine) as db:
        db.add(
            User(
                id=10,
                email="other@example.vn",
                full_name="Khách khác",
                role="customer",
                hashed_password="fixture",
            )
        )
        db.add_all(
            [
                Order(
                    id=i,
                    user_id=uid,
                    restaurant_id=1,
                    total=40000,
                    delivery_address="Hà Nội",
                    latitude=21,
                    longitude=105,
                    session_id=uuid4(),
                    idempotency_key=uuid4(),
                    payload_hash="a" * 64,
                    status=status,
                )
                for i, uid, status in [
                    (1, 1, OrderStatus.COMPLETED),
                    (2, 1, OrderStatus.PENDING),
                    (3, 10, OrderStatus.COMPLETED),
                    (4, 1, OrderStatus.COMPLETED),
                ]
            ]
        )
        db.flush()
        db.add_all(
            [
                OrderItem(
                    order_id=i,
                    menu_item_id=1,
                    quantity=1,
                    snapshot_price=40000,
                    snapshot_name="Món lúc mua",
                )
                for i in (1, 2, 3, 4)
            ]
        )
        db.commit()
    yield client, engine


def test_review_completed_purchase_and_snapshot(review_api):
    client, engine = review_api
    with Session(engine) as db:
        db.get(MenuItem, 1).name = "Tên mới"
        db.get(MenuItem, 1).price = 50000
        db.get(MenuItem, 1).is_available = False
        db.commit()
    result = client.post(PATH.format(1), headers=auth(1), json=payload())
    assert result.status_code == 201, result.text
    body = result.json()
    assert body["order_id"] == 1 and body["menu_item_id"] == 1
    assert body["snapshot_name"] == "Món lúc mua" and body["snapshot_price"] == 40000
    assert body["rating"] == 5 and body["comment"] == "Rất ngon"
    assert "created_at" in body and "is_simulated" not in body and "user_id" not in body
    with Session(engine) as db:
        row = db.scalar(select(Review))
        assert row.user_id == 1 and row.is_simulated is False
        assert row.order_item.snapshot_name == "Món lúc mua"


@pytest.mark.parametrize("uid,status", [(None, 401), (2, 403), (3, 403), (4, 403)])
def test_role_guards(review_api, uid, status):
    assert (
        review_api[0].post(PATH.format(1), headers=auth(uid), json=payload()).status_code == status
    )


@pytest.mark.parametrize(
    "oid,uid,status,code",
    [
        (2, 1, 409, "ORDER_NOT_COMPLETED"),
        (3, 1, 404, "NOT_FOUND"),
        (999, 1, 404, "NOT_FOUND"),
        (1, 10, 404, "NOT_FOUND"),
        (1, 1, 404, "NOT_FOUND"),
    ],
)
def test_ineligible_orders_or_items_do_not_create_review(review_api, oid, uid, status, code):
    body = payload(menu_item_id=2) if oid == 1 and uid == 1 else payload()
    response = review_api[0].post(PATH.format(oid), headers=auth(uid), json=body)
    assert response.status_code == status and response.json()["error"]["code"] == code
    with Session(review_api[1]) as db:
        assert db.scalar(select(func.count()).select_from(Review)) == 0


def test_one_review_per_order_item_but_later_order_allowed(review_api):
    client, engine = review_api
    assert client.post(PATH.format(1), headers=auth(1), json=payload()).status_code == 201
    duplicate = client.post(PATH.format(1), headers=auth(1), json=payload(rating=1))
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "REVIEW_ALREADY_EXISTS"
    assert client.post(PATH.format(4), headers=auth(1), json=payload(rating=3)).status_code == 201
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Review)) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"rating": 0},
        {"rating": 6},
        {"rating": True},
        {"rating": 3.5},
        {"rating": "5"},
        {"comment": 2},
        {"comment": "x" * 2001},
        {"menu_item_id": "1"},
        {"menu_item_id": True},
        {"menu_item_id": 0},
        {"menu_item_id": 2**31},
        {"user_id": 1},
        {"order_id": 1},
        {"is_simulated": True},
    ],
)
def test_validation_rejects_bad_or_privileged_fields(review_api, changes):
    response = review_api[0].post(PATH.format(1), headers=auth(1), json=payload(**changes))
    assert response.status_code == 422
    assert all("input" not in item for item in response.json()["error"]["details"])


def test_optional_comment_defaults_empty_and_full_length_allowed(review_api):
    client, _ = review_api
    response = client.post(PATH.format(1), headers=auth(1), json={"menu_item_id": 1, "rating": 1})
    assert response.status_code == 201 and response.json()["comment"] == ""
    response = client.post(PATH.format(4), headers=auth(1), json=payload(comment="x" * 2000))
    assert response.status_code == 201 and len(response.json()["comment"]) == 2000


@pytest.mark.parametrize("failure", ["insert", "commit"])
def test_database_failure_rolls_back(review_api, monkeypatch, failure):
    _, engine = review_api

    def fail_insert(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO reviews"):
            raise OperationalError(statement, {}, RuntimeError("injected"))

    with Session(engine) as db:
        if failure == "insert":
            event.listen(engine, "before_cursor_execute", fail_insert)
        else:

            def fail_commit():
                db.flush()
                raise OperationalError("commit", {}, RuntimeError("injected"))

            monkeypatch.setattr(db, "commit", fail_commit)
        try:
            with pytest.raises(OperationalError):
                service.create_review(db, 1, 1, ReviewCreate(**payload()))
        finally:
            if failure == "insert":
                event.remove(engine, "before_cursor_execute", fail_insert)
        assert db.scalar(select(func.count()).select_from(Review)) == 0


def test_unique_race_maps_to_conflict(review_api, monkeypatch):
    client, engine = review_api
    assert client.post(PATH.format(1), headers=auth(1), json=payload()).status_code == 201
    original = service._duplicate
    calls = 0

    def miss_once(*args):
        nonlocal calls
        calls += 1
        return False if calls == 1 else original(*args)

    monkeypatch.setattr(service, "_duplicate", miss_once)
    response = client.post(PATH.format(1), headers=auth(1), json=payload())
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REVIEW_ALREADY_EXISTS"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Review)) == 1


def test_openapi_has_customer_post_only(review_api):
    operation = (
        review_api[0].get("/openapi.json").json()["paths"]["/api/v1/orders/{order_id}/review"]
    )
    assert set(operation) == {"post"} and operation["post"]["security"]

"""Đặt COD, idempotency, phạm vi dữ liệu và chuyển trạng thái qua production API."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.auth.utils import create_token
from app.menu.models import MenuItem
from app.orders import service
from app.orders.models import Order, OrderItem, OrderStatusHistory
from app.orders.schemas import OrderCreate
from app.restaurants.models import Restaurant
from app.users.models import User

ROOT = "/api/v1"


def auth(uid):
    return {} if uid is None else {"Authorization": "Bearer " + create_token(uid, "access")}


def payload(**changes):
    return (
        dict(
            restaurant_id=1,
            items=[dict(menu_item_id=1, quantity=2, expected_price=40000)],
            delivery_address="  Số 1 Hà Nội  ",
            latitude=21,
            longitude=105,
            session_id=str(uuid4()),
            idempotency_key=str(uuid4()),
        )
        | changes
    )


def create(client, body=None):
    response = client.post(ROOT + "/orders/", headers=auth(1), json=body or payload())
    assert response.status_code == 201, response.text
    return response.json()


def test_cod_lifecycle_and_immutable_snapshots(menu_api):
    client, engine = menu_api
    order = create(client)
    oid = order["id"]
    assert order["total"] == 80000 and order["status"] == "pending"
    assert order["delivery_address"] == "Số 1 Hà Nội"
    assert order["items"] == [
        dict(menu_item_id=1, quantity=2, snapshot_price=40000, snapshot_name="Món 1")
    ]
    assert [h["status"] for h in order["history"]] == ["pending"]
    assert (
        not {"payload_hash", "idempotency_key", "session_id", "is_simulated", "user_id"}
        & order.keys()
    )
    with Session(engine) as db:
        row = db.get(MenuItem, 1)
        row.name, row.price, row.is_available = "Đổi tên", 50000, False
        db.commit()
    for action, status in [
        ("confirm", "confirmed"),
        ("preparing", "preparing"),
        ("delivering", "delivering"),
        ("complete", "completed"),
    ]:
        response = client.patch(f"{ROOT}/vendor/orders/{oid}/{action}", headers=auth(2))
        assert response.status_code == 200, response.text
        assert response.json()["status"] == status
    result = client.get(f"{ROOT}/orders/{oid}", headers=auth(1)).json()
    assert result["items"] == order["items"] and result["total"] == 80000
    assert len(result["history"]) == 5
    assert client.patch(f"{ROOT}/orders/{oid}/cancel", headers=auth(1)).status_code == 409


def test_replay_ignores_new_menu_availability_and_restaurant_state(menu_api):
    client, engine = menu_api
    body = payload()
    first = create(client, body)
    with Session(engine) as db:
        db.get(MenuItem, 1).is_available = False
        db.get(Restaurant, 1).status = "suspended"
        db.commit()
    response = client.post(ROOT + "/orders/", headers=auth(1), json=body)
    assert response.status_code == 200 and response.json() == first
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 1
        assert db.scalar(select(func.count()).select_from(OrderStatusHistory)) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("delivery_address", "Địa chỉ khác"),
        ("latitude", 21.01),
        ("restaurant_id", 2),
        ("session_id", str(uuid4())),
    ],
)
def test_key_conflicts_on_changed_payload(menu_api, field, value):
    client, _ = menu_api
    body = payload()
    create(client, body)
    response = client.post(ROOT + "/orders/", headers=auth(1), json=body | {field: value})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_key_is_private_to_customer(menu_api):
    client, engine = menu_api
    body = payload()
    create(client, body)
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
        db.commit()
    response = client.post(ROOT + "/orders/", headers=auth(10), json=body)
    assert response.status_code == 409 and "items" not in response.json()
    assert client.get(ROOT + "/orders/1", headers=auth(10)).status_code == 404
    assert client.get(ROOT + "/orders/", headers=auth(10)).json() == []
    assert client.patch(ROOT + "/orders/1/cancel", headers=auth(10)).status_code == 404


@pytest.mark.parametrize("seconds,status", [(86399, 200), (86400, 409), (86401, 409)])
def test_key_expires_at_24_hours_without_reuse(menu_api, monkeypatch, seconds, status):
    client, engine = menu_api
    now = datetime(2026, 11, 26, 3, tzinfo=UTC)
    monkeypatch.setattr(service, "utcnow", lambda: now)
    body = payload()
    create(client, body)
    monkeypatch.setattr(service, "utcnow", lambda: now + timedelta(seconds=seconds))
    response = client.post(ROOT + "/orders/", headers=auth(1), json=body)
    assert response.status_code == status
    if status == 409:
        assert response.json()["error"]["code"] == "IDEMPOTENCY_EXPIRED"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 1


def test_item_order_and_address_whitespace_do_not_change_key(menu_api):
    client, engine = menu_api
    with Session(engine) as db:
        db.get(MenuItem, 2).is_available = True
        db.commit()
    body = payload(items=[dict(menu_item_id=i, quantity=1, expected_price=40000) for i in [2, 1]])
    first = create(client, body)
    replay = body | {"items": list(reversed(body["items"])), "delivery_address": "Số 1 Hà Nội"}
    response = client.post(ROOT + "/orders/", headers=auth(1), json=replay)
    assert response.status_code == 200 and response.json() == first


@pytest.mark.parametrize(
    "changes,status,code",
    [
        ({"restaurant_id": 999}, 404, "NOT_FOUND"),
        ({"restaurant_id": 2}, 404, "NOT_FOUND"),
        ({"restaurant_id": 3}, 404, "NOT_FOUND"),
        ({"restaurant_id": 4}, 409, "RESTAURANT_UNAVAILABLE"),
        ({"restaurant_id": 5}, 409, "RESTAURANT_UNAVAILABLE"),
        ({"latitude": 22}, 400, "OUTSIDE_DELIVERY_AREA"),
        (
            {"items": [dict(menu_item_id=3, quantity=1, expected_price=40000)]},
            400,
            "ORDER_ITEM_INVALID",
        ),
        (
            {"items": [dict(menu_item_id=999, quantity=1, expected_price=40000)]},
            400,
            "ORDER_ITEM_INVALID",
        ),
        (
            {"items": [dict(menu_item_id=2, quantity=1, expected_price=40000)]},
            409,
            "ORDER_ITEM_UNAVAILABLE",
        ),
        (
            {"items": [dict(menu_item_id=1, quantity=1, expected_price=30000)]},
            409,
            "ORDER_PRICE_CHANGED",
        ),
    ],
)
def test_invalid_business_conditions_leave_no_order(menu_api, changes, status, code):
    client, engine = menu_api
    response = client.post(ROOT + "/orders/", headers=auth(1), json=payload(**changes))
    assert response.status_code == status and response.json()["error"]["code"] == code
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"items": []},
        {"items": [dict(menu_item_id=1, quantity=0, expected_price=40000)]},
        {"items": [dict(menu_item_id=1, quantity=True, expected_price=40000)]},
        {"items": [dict(menu_item_id=1, quantity=100, expected_price=40000)]},
        {"items": [dict(menu_item_id=1, quantity=1, expected_price="40000")]},
        {"items": [dict(menu_item_id=1, quantity=1, expected_price=40000)] * 2},
        {"latitude": True},
        {"longitude": "105"},
        {"latitude": 91},
        {"delivery_address": "  "},
        {"session_id": "bad"},
        {"idempotency_key": "bad"},
        {"total": 1},
        {"status": "completed"},
        {"user_id": 2},
        {"is_simulated": True},
    ],
)
def test_invalid_request_schema(menu_api, changes):
    response = menu_api[0].post(ROOT + "/orders/", headers=auth(1), json=payload(**changes))
    assert response.status_code == 422, response.text


CUSTOMER_OPS = [
    ("POST", "/orders/"),
    ("GET", "/orders/"),
    ("GET", "/orders/1"),
    ("PATCH", "/orders/1/cancel"),
]
VENDOR_OPS = [("GET", "/vendor/orders"), ("GET", "/vendor/orders/1")] + [
    ("PATCH", f"/vendor/orders/1/{action}")
    for action in ("confirm", "reject", "preparing", "delivering", "complete")
]


@pytest.mark.parametrize("method,path", CUSTOMER_OPS)
@pytest.mark.parametrize("uid,status", [(None, 401), (2, 403), (3, 403)])
def test_customer_role_guards(menu_api, method, path, uid, status):
    assert (
        menu_api[0].request(method, ROOT + path, headers=auth(uid), json=payload()).status_code
        == status
    )


@pytest.mark.parametrize("method,path", VENDOR_OPS)
@pytest.mark.parametrize("uid,status", [(None, 401), (1, 403), (3, 403)])
def test_vendor_role_guards(menu_api, method, path, uid, status):
    assert (
        menu_api[0]
        .request(method, ROOT + path, headers=auth(uid), json={"reason": "Hết món"})
        .status_code
        == status
    )


def test_vendor_isolation_listing_and_rejection(menu_api):
    client, _ = menu_api
    order = create(client)
    for method, path in VENDOR_OPS:
        response = client.request(method, ROOT + path, headers=auth(4), json={"reason": "Hết món"})
        if path == "/vendor/orders":
            assert response.status_code == 200 and response.json() == []
        else:
            assert response.status_code == 404
    assert client.get(ROOT + "/vendor/orders", headers=auth(5)).status_code == 404
    assert client.get(ROOT + "/vendor/orders", headers=auth(7)).json()[0]["id"] == order["id"]
    assert (
        client.patch(
            ROOT + "/vendor/orders/1/reject", headers=auth(2), json={"reason": " "}
        ).status_code
        == 422
    )
    response = client.patch(
        ROOT + "/vendor/orders/1/reject", headers=auth(2), json={"reason": "  Hết món  "}
    )
    assert response.json()["history"][-1]["reason"] == "Hết món"
    assert client.patch(ROOT + "/vendor/orders/1/confirm", headers=auth(2)).status_code == 409


def test_customer_cancel_and_pagination(menu_api):
    client, _ = menu_api
    for _ in range(3):
        create(client)
    response = client.get(ROOT + "/orders/?offset=1&limit=1", headers=auth(1))
    assert [row["id"] for row in response.json()] == [2]
    assert client.get(ROOT + "/orders/?offset=99", headers=auth(1)).json() == []
    response = client.patch(ROOT + "/orders/1/cancel", headers=auth(1))
    assert response.json()["status"] == "cancelled" and len(response.json()["history"]) == 2
    assert client.patch(ROOT + "/orders/1/cancel", headers=auth(1)).status_code == 409


@pytest.mark.parametrize("stage", ["line", "history", "commit"])
def test_creation_rolls_back_every_row_on_failure(menu_api, monkeypatch, stage):
    _, engine = menu_api

    def fail_insert(_conn, _cursor, statement, _params, _context, _many):
        table = "order_items" if stage == "line" else "order_status_history"
        if statement.startswith("INSERT INTO " + table):
            raise IntegrityError(statement, {}, RuntimeError("injected failure"))

    with Session(engine) as db:
        if stage == "commit":

            def fail_commit():
                db.flush()
                raise OperationalError("commit", {}, RuntimeError("injected failure"))

            monkeypatch.setattr(db, "commit", fail_commit)
        else:
            event.listen(engine, "before_cursor_execute", fail_insert)
        try:
            with pytest.raises((IntegrityError, OperationalError)):
                service.create_order(db, 1, OrderCreate(**payload()))
        finally:
            if stage != "commit":
                event.remove(engine, "before_cursor_execute", fail_insert)
        for model in (Order, OrderItem, OrderStatusHistory):
            assert db.scalar(select(func.count()).select_from(model)) == 0


@pytest.mark.parametrize("changed", [False, True])
def test_unique_key_race_recovery_after_rollback(menu_api, monkeypatch, changed):
    client, engine = menu_api
    body = payload()
    create(client, body)
    original = service._replay
    calls = 0

    def miss_first_read(*args):
        nonlocal calls
        calls += 1
        return None if calls == 1 else original(*args)

    monkeypatch.setattr(service, "_replay", miss_first_read)
    if changed:
        body["delivery_address"] = "Một địa chỉ khác"
    response = client.post(ROOT + "/orders/", headers=auth(1), json=body)
    assert response.status_code == (409 if changed else 200)
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 1
        assert db.scalar(select(func.count()).select_from(OrderItem)) == 1
        assert db.scalar(select(func.count()).select_from(OrderStatusHistory)) == 1


@pytest.mark.parametrize("path,uid", [("/orders/", 1), ("/vendor/orders", 2)])
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "offset=2147483648"])
def test_order_pagination_bounds(menu_api, path, uid, query):
    assert menu_api[0].get(ROOT + path + "?" + query, headers=auth(uid)).status_code == 422


def test_all_order_operations_are_in_openapi(menu_api):
    paths = menu_api[0].get("/openapi.json").json()["paths"]
    for method, path in CUSTOMER_OPS + VENDOR_OPS:
        operation = paths[ROOT + path.replace("/1", "/{order_id}")][method.lower()]
        assert operation["security"]

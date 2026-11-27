"""Kiểm tra phân quyền và cô lập quán tại API hồ sơ, chưa gồm menu/đơn hàng."""

import pytest
from sqlalchemy.orm import Session

from app.auth.utils import create_token
from app.restaurants.models import Restaurant

VENDOR = "/api/v1/vendor/restaurant"
ADMIN = "/api/v1/admin/restaurants"


def auth(uid):
    return {"Authorization": "Bearer " + create_token(uid, "access")} if uid else {}


def payload(**extra):
    return {
        "name": "Tên mới",
        "address": "Hà Nội",
        "latitude": 21,
        "longitude": 105,
        "delivery_radius_km": 5,
        "opens_at": "00:00",
        "closes_at": "00:00",
        "accepting_orders": False,
    } | extra


@pytest.mark.parametrize("uid,expected", [(None, 401), (1, 403), (3, 403)])
@pytest.mark.parametrize("method", ["GET", "POST", "PUT"])
def test_vendor_profile_requires_vendor_role(restaurant_api, uid, expected, method):
    client, _ = restaurant_api
    body = payload()
    if method == "POST":
        body.pop("accepting_orders")
    response = client.request(
        method, VENDOR, headers=auth(uid), json=body if method != "GET" else None
    )
    assert response.status_code == expected


@pytest.mark.parametrize("uid,expected", [(None, 401), (1, 403), (2, 403)])
@pytest.mark.parametrize(
    "method,path",
    [("GET", ADMIN), ("PATCH", ADMIN + "/1/approve"), ("PATCH", ADMIN + "/1/suspend")],
)
def test_restaurant_administration_requires_admin(restaurant_api, uid, expected, method, path):
    client, _ = restaurant_api
    assert client.request(method, path, headers=auth(uid)).status_code == expected


def test_vendor_without_membership_has_no_profile_to_read_or_update(restaurant_api):
    client, _ = restaurant_api
    assert client.get(VENDOR, headers=auth(5)).status_code == 404
    assert client.put(VENDOR, headers=auth(5), json=payload()).status_code == 404


@pytest.mark.parametrize(
    "field,value",
    [("restaurant_id", 2), ("user_id", 4), ("status", "approved"), ("is_simulated", True)],
)
def test_vendor_cannot_retarget_profile_or_change_admin_fields(restaurant_api, field, value):
    client, engine = restaurant_api
    response = client.put(VENDOR, headers=auth(2), json=payload(**{field: value}))
    assert response.status_code == 422
    with Session(engine) as db:
        assert db.get(Restaurant, 1).name == "Quán 1"
        assert db.get(Restaurant, 2).name == "Quán 2"


def test_vendor_updates_only_own_restaurant_and_shared_members_can_read_it(restaurant_api):
    client, engine = restaurant_api
    assert client.get(VENDOR, headers=auth(2)).json()["id"] == 1
    assert client.get(VENDOR, headers=auth(4)).json()["id"] == 2
    assert client.put(VENDOR, headers=auth(2), json=payload()).status_code == 200
    assert client.get(VENDOR, headers=auth(7)).json()["name"] == "Tên mới"
    with Session(engine) as db:
        assert db.get(Restaurant, 2).name == "Quán 2"

"""Hồ sơ quán, duyệt/tạm ngừng, ràng buộc API và giờ phục vụ địa phương."""

from datetime import datetime, time

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.auth.utils import create_token
from app.exceptions import ConflictError
from app.restaurants import service
from app.restaurants.models import Restaurant, RestaurantMembership
from app.restaurants.schemas import RestaurantCreate, RestaurantUpdate

ROOT = "/api/v1"
VENDOR = ROOT + "/vendor/restaurant"
ADMIN = ROOT + "/admin/restaurants"
PUBLIC = ROOT + "/restaurants"


def auth(user_id):
    return {"Authorization": "Bearer " + create_token(user_id, "access")}


def profile(**changes):
    return {
        "name": "Bếp mới",
        "address": "Số 1 Hà Nội",
        "latitude": 21.02,
        "longitude": 105.85,
        "delivery_radius_km": 5,
        "opens_at": "08:00",
        "closes_at": "22:00",
    } | changes


def test_vendor_registration_approval_receiving_and_suspension_workflow(restaurant_api):
    client, engine = restaurant_api
    registration = {
        "email": "new-vendor@example.vn",
        "password": "Mat khau 123!",
        "full_name": "Chủ quán mới",
        "role": "vendor",
    }
    assert client.post(ROOT + "/auth/register", json=registration).status_code == 201
    login = client.post(
        ROOT + "/auth/login", json={k: registration[k] for k in ("email", "password")}
    )
    assert login.status_code == 200
    vendor = {"Authorization": "Bearer " + login.json()["access_token"]}
    created = client.post(
        VENDOR, headers=vendor, json=profile(name="  Bếp mới  ", address="  Số 1 Hà Nội  ")
    )
    assert created.status_code == 201
    body = created.json()
    rid = body["id"]
    assert body["name"] == "Bếp mới" and body["address"] == "Số 1 Hà Nội"
    assert body["status"] == "pending" and body["accepting_orders"] is False
    assert body["is_simulated"] is False and body["can_receive_orders"] is False
    assert client.get(f"{PUBLIC}/{rid}").status_code == 404
    rejected = client.put(
        VENDOR, headers=vendor, json=profile(name="Không được lưu", accepting_orders=True)
    )
    assert (
        rejected.status_code == 409
        and rejected.json()["error"]["code"] == "RESTAURANT_NOT_APPROVED"
    )
    assert client.get(VENDOR, headers=vendor).json()["name"] == "Bếp mới"
    approved = client.patch(f"{ADMIN}/{rid}/approve", headers=auth(3))
    assert approved.status_code == 200 and approved.json()["accepting_orders"] is False
    updated = client.put(VENDOR, headers=vendor, json=profile(accepting_orders=True))
    assert updated.status_code == 200 and updated.json()["can_receive_orders"] is True
    assert client.get(f"{PUBLIC}/{rid}").json()["can_receive_orders"] is True
    suspended = client.patch(f"{ADMIN}/{rid}/suspend", headers=auth(3))
    assert (
        suspended.json()["status"] == "suspended" and suspended.json()["accepting_orders"] is False
    )
    assert client.get(f"{PUBLIC}/{rid}").status_code == 404
    assert (
        client.put(VENDOR, headers=vendor, json=profile(accepting_orders=True)).status_code == 409
    )
    resumed = client.patch(f"{ADMIN}/{rid}/approve", headers=auth(3))
    assert resumed.json()["accepting_orders"] is False
    with Session(engine) as db:
        membership = db.get(RestaurantMembership, login.json()["user"]["id"])
        assert membership.restaurant_id == rid


def test_create_defaults_are_pending_not_receiving_and_full_day(restaurant_api):
    client, _ = restaurant_api
    response = client.post(
        VENDOR,
        headers=auth(5),
        json={k: profile()[k] for k in ("name", "address", "latitude", "longitude")},
    )
    assert response.status_code == 201
    assert response.json()["delivery_radius_km"] == 5
    assert response.json()["opens_at"] == response.json()["closes_at"] == "00:00"
    assert response.json()["is_open"] is True and response.json()["can_receive_orders"] is False


def test_existing_vendor_cannot_create_second_restaurant(restaurant_api):
    client, engine = restaurant_api
    response = client.post(VENDOR, headers=auth(2), json=profile())
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESTAURANT_ALREADY_LINKED"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Restaurant)) == 5


def test_public_listing_is_paginated_approved_only_and_does_not_leak_memberships(restaurant_api):
    client, _ = restaurant_api
    response = client.get(PUBLIC + "/?offset=1&limit=1&status=pending")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3 and data["offset"] == 1 and data["limit"] == 1
    assert [r["id"] for r in data["items"]] == [4]
    assert not {"status", "is_simulated", "memberships", "user_id", "email"} & set(data["items"][0])
    assert client.get(PUBLIC + "/?offset=99").json()["items"] == []


@pytest.mark.parametrize("rid", [2, 3, 999])
def test_public_hides_pending_suspended_and_missing_restaurants(restaurant_api, rid):
    client, _ = restaurant_api
    response = client.get(f"{PUBLIC}/{rid}")
    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Không tìm thấy quán."


def test_public_hours_do_not_conflate_closed_with_not_accepting(restaurant_api):
    client, _ = restaurant_api
    assert client.get(f"{PUBLIC}/1").json()["can_receive_orders"] is True
    closed = client.get(f"{PUBLIC}/4").json()
    assert closed["accepting_orders"] is True and closed["is_open"] is False
    assert closed["can_receive_orders"] is False
    paused = client.get(f"{PUBLIC}/5").json()
    assert paused["is_open"] is True and paused["accepting_orders"] is False
    assert paused["can_receive_orders"] is False


def test_admin_list_filter_and_pagination_include_private_status(restaurant_api):
    client, _ = restaurant_api
    all_rows = client.get(ADMIN + "?limit=2&offset=1", headers=auth(3)).json()
    assert all_rows["total"] == 5 and [r["id"] for r in all_rows["items"]] == [2, 3]
    pending = client.get(ADMIN + "?status=pending", headers=auth(3)).json()
    assert pending["total"] == 1 and pending["items"][0]["status"] == "pending"
    assert "is_simulated" in pending["items"][0]


@pytest.mark.parametrize("action", ["approve", "suspend"])
def test_admin_status_actions_are_repeatable(restaurant_api, action):
    client, _ = restaurant_api
    first = client.patch(f"{ADMIN}/1/{action}", headers=auth(3))
    second = client.patch(f"{ADMIN}/1/{action}", headers=auth(3))
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.parametrize("action", ["approve", "suspend"])
def test_admin_action_missing_restaurant_is_404(restaurant_api, action):
    client, _ = restaurant_api
    assert client.patch(f"{ADMIN}/999/{action}", headers=auth(3)).status_code == 404


@pytest.mark.parametrize(
    "query", ["limit=0", "limit=101", "offset=-1", "limit=abc", "offset=2147483648"]
)
def test_public_rejects_invalid_pagination(restaurant_api, query):
    client, _ = restaurant_api
    assert client.get(PUBLIC + "/?" + query).status_code == 422


def test_admin_rejects_unknown_status(restaurant_api):
    client, _ = restaurant_api
    assert client.get(ADMIN + "?status=rejected", headers=auth(3)).status_code == 422


def test_admin_rejects_offset_outside_database_integer_range(restaurant_api):
    client, _ = restaurant_api
    assert client.get(ADMIN + "?offset=2147483648", headers=auth(3)).status_code == 422


@pytest.mark.parametrize("rid", [-1, 0, 2**31, "not-an-id"])
def test_public_rejects_invalid_identifiers(restaurant_api, rid):
    client, _ = restaurant_api
    assert client.get(f"{PUBLIC}/{rid}").status_code == 422


@pytest.mark.parametrize(
    "changes",
    [
        {"name": " "},
        {"name": "a" * 161},
        {"address": "\t"},
        {"address": "a" * 501},
        {"latitude": True},
        {"latitude": "21"},
        {"latitude": 91},
        {"longitude": -181},
        {"delivery_radius_km": 0},
        {"delivery_radius_km": 51},
        {"opens_at": "24:00"},
        {"opens_at": "8:00"},
        {"closes_at": "08:00:00"},
        {"opens_at": "08:00Z"},
        {"closes_at": "08:00+07:00"},
        {"status": "approved"},
        {"is_simulated": True},
        {"user_id": 2},
        {"restaurant_id": 1},
        {"accepting_orders": True},
    ],
)
def test_create_validates_profile_and_rejects_privileged_fields(restaurant_api, changes):
    client, engine = restaurant_api
    response = client.post(VENDOR, headers=auth(5), json=profile(**changes))
    assert response.status_code == 422
    with Session(engine) as db:
        assert db.get(RestaurantMembership, 5) is None
        assert db.scalar(select(func.count()).select_from(Restaurant)) == 5


def test_non_finite_coordinate_is_validation_error_not_server_error(restaurant_api):
    client, _ = restaurant_api
    response = client.post(
        VENDOR,
        headers=auth(5) | {"Content-Type": "application/json"},
        content='{"name":"Bep","address":"Ha Noi","latitude":NaN,"longitude":105}',
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "field", ["delivery_radius_km", "opens_at", "closes_at", "accepting_orders"]
)
def test_put_requires_entire_profile_instead_of_resetting_defaults(restaurant_api, field):
    client, _ = restaurant_api
    body = profile(accepting_orders=False)
    body.pop(field)
    assert client.put(VENDOR, headers=auth(2), json=body).status_code == 422


@pytest.mark.parametrize("uid", [4, 6])
def test_unapproved_vendor_can_edit_profile_but_not_enable_receiving(restaurant_api, uid):
    client, _ = restaurant_api
    response = client.put(VENDOR, headers=auth(uid), json=profile(accepting_orders=False))
    assert response.status_code == 200 and response.json()["name"] == "Bếp mới"
    assert (
        client.put(VENDOR, headers=auth(uid), json=profile(accepting_orders=True)).status_code
        == 409
    )


def test_put_receiving_flag_is_strict_boolean(restaurant_api):
    client, _ = restaurant_api
    assert (
        client.put(VENDOR, headers=auth(2), json=profile(accepting_orders="true")).status_code
        == 422
    )


def test_duplicate_membership_race_rolls_back_new_restaurant(restaurant_api, monkeypatch):
    _, engine = restaurant_api
    with Session(engine) as db:
        original = db.get
        membership_reads = 0

        def race(model, *args, **kwargs):
            nonlocal membership_reads
            if model is RestaurantMembership:
                membership_reads += 1
                if membership_reads == 1:
                    return None
            return original(model, *args, **kwargs)

        monkeypatch.setattr(db, "get", race)
        with pytest.raises(ConflictError) as error:
            service.create_with_owner(db, 2, RestaurantCreate(**profile()))
        assert error.value.code == "RESTAURANT_ALREADY_LINKED"
        assert db.scalar(select(func.count()).select_from(Restaurant)) == 5
        assert db.get(Restaurant, 1).name == "Quán 1"


def test_membership_insert_failure_does_not_leave_orphan_restaurant(restaurant_api):
    _, engine = restaurant_api

    def fail_membership(_connection, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO restaurant_memberships"):
            raise IntegrityError(statement, {}, ValueError("injected membership failure"))

    event.listen(engine, "before_cursor_execute", fail_membership)
    try:
        with Session(engine) as db:
            with pytest.raises(IntegrityError):
                service.create_with_owner(db, 5, RestaurantCreate(**profile()))
            assert db.scalar(select(func.count()).select_from(Restaurant)) == 5
            assert db.get(RestaurantMembership, 5) is None
    finally:
        event.remove(engine, "before_cursor_execute", fail_membership)


def test_profile_commit_failure_rolls_back_changes(restaurant_api, monkeypatch):
    _, engine = restaurant_api
    with Session(engine) as db:

        def fail_commit():
            raise OperationalError("update", {}, ValueError("injected failure"))

        monkeypatch.setattr(db, "commit", fail_commit)
        with pytest.raises(OperationalError):
            service.update_profile(db, 1, RestaurantUpdate(**profile(accepting_orders=False)))
        stored = db.get(Restaurant, 1)
        assert stored.name == "Quán 1" and stored.accepting_orders is True


@pytest.mark.parametrize(
    "start,end,at,expected",
    [
        ("08:00", "22:00", "08:00:00+07:00", True),
        ("08:00", "22:00", "07:59:59+07:00", False),
        ("08:00", "22:00", "21:59:59+07:00", True),
        ("08:00", "22:00", "22:00:00+07:00", False),
        ("22:00", "02:00", "22:00:00+07:00", True),
        ("22:00", "02:00", "01:59:59+07:00", True),
        ("22:00", "02:00", "02:00:00+07:00", False),
        ("22:00", "02:00", "12:00:00+07:00", False),
        ("00:00", "00:00", "00:00:00+07:00", True),
        ("09:00", "09:00", "01:00:00+07:00", True),
        ("08:00", "22:00", "01:00:00+00:00", True),
        ("08:00", "22:00", "15:00:00+00:00", False),
    ],
)
def test_opening_hours_boundaries_overnight_and_timezone(start, end, at, expected):
    restaurant = Restaurant(opens_at=time.fromisoformat(start), closes_at=time.fromisoformat(end))
    assert service.is_open(restaurant, datetime.fromisoformat("2026-11-26T" + at)) is expected


def test_opening_hours_rejects_naive_datetime():
    restaurant = Restaurant(opens_at=time(0), closes_at=time(0))
    with pytest.raises(ValueError):
        service.is_open(restaurant, datetime(2026, 11, 26))

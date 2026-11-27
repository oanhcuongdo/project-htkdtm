"""API năm câu khẩu vị: quyền riêng tư, chuẩn hóa, ghi đè và rollback."""

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.auth.utils import create_token
from app.preferences import service
from app.preferences.models import Preference
from app.preferences.schemas import PreferenceInput
from app.users.models import User

PATH = "/api/v1/preferences/"


def auth(uid):
    return {} if uid is None else {"Authorization": "Bearer " + create_token(uid, "access")}


def payload(**changes):
    return {
        "regions": ["  Bắc  ", "bắc", "Nam"],
        "spice_level": 2,
        "liked_ingredients": [" BÒ ", "bò", "hành"],
        "avoided_ingredients": [" ĐẬU PHỘNG "],
        "exploration_level": 1,
    } | changes


def test_get_missing_and_put_create_then_replace_all_fields(restaurant_api):
    client, engine = restaurant_api
    assert client.get(PATH, headers=auth(1)).status_code == 404
    with Session(engine) as db:
        assert db.get(Preference, 1) is None
    first = client.put(PATH, headers=auth(1), json=payload())
    assert first.status_code == 200, first.text
    expected = dict(
        regions=["Bắc", "Nam"],
        spice_level=2,
        liked_ingredients=["bò", "hành"],
        avoided_ingredients=["đậu phộng"],
        exploration_level=1,
    )
    assert first.json() == expected
    assert client.get(PATH, headers=auth(1)).json() == expected
    replacement = payload(
        regions=[], spice_level=0, liked_ingredients=[], avoided_ingredients=[], exploration_level=2
    )
    updated = client.put(PATH, headers=auth(1), json=replacement)
    assert updated.status_code == 200 and updated.json() == replacement
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Preference)) == 1
        assert db.get(Preference, 1).liked_ingredients == []


@pytest.mark.parametrize("method", ["get", "put"])
@pytest.mark.parametrize("uid,status", [(None, 401), (2, 403), (3, 403), (4, 403)])
def test_role_guard(restaurant_api, method, uid, status):
    response = getattr(restaurant_api[0], method)(
        PATH, headers=auth(uid), **({"json": payload()} if method == "put" else {})
    )
    assert response.status_code == status


def test_customer_cannot_read_or_overwrite_another_profile(restaurant_api):
    client, engine = restaurant_api
    with Session(engine) as db:
        db.add(
            User(
                id=10,
                email="customer10@example.vn",
                full_name="Khách 10",
                role="customer",
                hashed_password="fixture",
            )
        )
        db.commit()
    assert client.put(PATH, headers=auth(1), json=payload()).status_code == 200
    assert client.get(PATH, headers=auth(10)).status_code == 404
    assert client.put(PATH, headers=auth(10), json=payload(spice_level=3)).status_code == 200
    assert client.get(PATH, headers=auth(1)).json()["spice_level"] == 2
    assert client.get(PATH, headers=auth(10)).json()["spice_level"] == 3
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Preference)) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"spice_level": -1},
        {"spice_level": 4},
        {"spice_level": True},
        {"spice_level": 1.5},
        {"spice_level": "2"},
        {"exploration_level": -1},
        {"exploration_level": 3},
        {"exploration_level": False},
        {"exploration_level": "1"},
        {"regions": "Bắc"},
        {"regions": [""]},
        {"regions": [" x "] * 101},
        {"regions": ["x" * 101]},
        {"liked_ingredients": [None]},
        {"avoided_ingredients": [2]},
        {"user_id": 2},
        {"is_simulated": True},
    ],
)
def test_invalid_payload_rejected_without_mutation(restaurant_api, changes):
    client, engine = restaurant_api
    response = client.put(PATH, headers=auth(1), json=payload(**changes))
    assert response.status_code == 422, response.text
    assert all("input" not in error for error in response.json()["error"]["details"])
    with Session(engine) as db:
        assert db.get(Preference, 1) is None


@pytest.mark.parametrize(
    "field",
    ["regions", "spice_level", "liked_ingredients", "avoided_ingredients", "exploration_level"],
)
def test_put_requires_all_five_answers(restaurant_api, field):
    body = payload()
    del body[field]
    assert restaurant_api[0].put(PATH, headers=auth(1), json=body).status_code == 422


def test_failed_update_rolls_back_all_answers(restaurant_api, monkeypatch):
    client, engine = restaurant_api
    assert client.put(PATH, headers=auth(1), json=payload()).status_code == 200
    with Session(engine) as db:

        def fail_commit():
            db.flush()
            raise OperationalError("commit", {}, RuntimeError("injected"))

        monkeypatch.setattr(db, "commit", fail_commit)
        with pytest.raises(OperationalError):
            service.save_preference(db, 1, PreferenceInput(**payload(spice_level=3, regions=[])))
        assert db.get(Preference, 1).spice_level == 2
        assert db.get(Preference, 1).regions == ["Bắc", "Nam"]


def test_insert_failure_does_not_leave_partial_profile(restaurant_api):
    _, engine = restaurant_api

    def fail_insert(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO preferences"):
            raise OperationalError(statement, {}, RuntimeError("injected"))

    event.listen(engine, "before_cursor_execute", fail_insert)
    try:
        with Session(engine) as db:
            with pytest.raises(OperationalError):
                service.save_preference(db, 1, PreferenceInput(**payload()))
            assert db.get(Preference, 1) is None
    finally:
        event.remove(engine, "before_cursor_execute", fail_insert)


def test_insert_race_recovers_existing_profile(restaurant_api, monkeypatch):
    client, engine = restaurant_api
    assert client.put(PATH, headers=auth(1), json=payload()).status_code == 200
    original_get = Session.get
    once = False

    def miss_first_preference(session, entity, ident, **kwargs):
        nonlocal once
        if entity is Preference and not once:
            once = True
            return None
        return original_get(session, entity, ident, **kwargs)

    monkeypatch.setattr(Session, "get", miss_first_preference)
    response = client.put(PATH, headers=auth(1), json=payload(spice_level=3))
    assert response.status_code == 200 and response.json()["spice_level"] == 3
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(Preference)) == 1


def test_openapi_exposes_only_get_put(restaurant_api):
    operations = restaurant_api[0].get("/openapi.json").json()["paths"][PATH]
    assert set(operations) == {"get", "put"}
    assert all(operation["security"] for operation in operations.values())

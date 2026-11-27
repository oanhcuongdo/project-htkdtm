"""API menu thật: phân quyền, cô lập quán, catalog, lịch sử và transaction."""

from uuid import uuid4

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.auth.utils import create_token
from app.menu import service
from app.menu.models import CanonicalDish, Ingredient, MenuItem, MenuItemIngredient
from app.menu.schemas import CanonicalDishUpdate, IngredientInput, MenuItemCreate, MenuItemUpdate
from app.orders.models import Order, OrderItem

ROOT = "/api/v1"
VENDOR = ROOT + "/vendor/menu-items"
ADMIN = ROOT + "/admin"


def auth(uid):
    return {} if uid is None else {"Authorization": "Bearer " + create_token(uid, "access")}


def item(**changes):
    return (
        dict(
            canonical_dish_id=1,
            name="Phở đặc biệt",
            price=50000,
            is_available=True,
            ingredients_verified=True,
            ingredient_ids=[1, 2],
        )
        | changes
    )


def dish(**changes):
    return (
        dict(
            name="Món mới",
            region="Trung",
            method="hấp",
            spice_level=1,
            ingredients=[],
            labels=[],
            source_id=None,
        )
        | changes
    )


def test_admin_to_vendor_to_public_workflow(menu_api):
    client, engine = menu_api
    ingredient = client.post(ADMIN + "/ingredients", headers=auth(3), json={"name": "  RAU  "})
    assert ingredient.status_code == 201
    iid = ingredient.json()["id"]
    assert ingredient.json() == {"id": iid, "name": "rau", "is_simulated": False}
    created = client.post(
        ADMIN + "/canonical-dishes",
        headers=auth(3),
        json=dish(name="  Cơm rau  ", ingredients=["  RAU ", "rau"], labels=["Chay", "chay"]),
    )
    assert created.status_code == 201
    cid = created.json()["id"]
    assert created.json()["ingredients"] == ["rau"]
    assert created.json()["labels"] == ["Chay"]
    payload = item(canonical_dish_id=cid, ingredient_ids=[iid])
    minimal = {key: payload[key] for key in ("canonical_dish_id", "name", "price")}
    created = client.post(VENDOR, headers=auth(2), json=minimal)
    assert created.status_code == 201
    mid = created.json()["id"]
    assert created.json()["is_available"] is False
    assert created.json()["ingredients_verified"] is False
    assert created.json()["ingredients"] == []
    assert client.get(f"{ROOT}/menu-items/{mid}").status_code == 404
    published = client.put(f"{VENDOR}/{mid}", headers=auth(2), json=payload)
    assert published.status_code == 200
    assert published.json()["ingredients"] == [{"id": iid, "name": "rau"}]
    public = client.get(f"{ROOT}/menu-items/{mid}")
    assert public.status_code == 200
    assert "is_simulated" not in public.json()
    assert "source_id" not in public.json()["canonical_dish"]
    assert mid in [row["id"] for row in client.get(ROOT + "/restaurants/1/menu").json()]
    for _ in range(2):
        stopped = client.delete(f"{VENDOR}/{mid}", headers=auth(2))
        assert stopped.status_code == 204 and stopped.content == b""
    assert client.get(f"{ROOT}/menu-items/{mid}").status_code == 404
    assert client.get(f"{VENDOR}/{mid}", headers=auth(7)).json()["is_available"] is False
    assert client.delete(ADMIN + f"/canonical-dishes/{cid}", headers=auth(3)).status_code == 409
    assert client.delete(ADMIN + f"/ingredients/{iid}", headers=auth(3)).status_code == 409
    assert client.put(f"{VENDOR}/{mid}", headers=auth(7), json=payload).status_code == 200
    with Session(engine) as db:
        assert db.get(MenuItemIngredient, (mid, iid)) is not None


@pytest.mark.parametrize(
    "mid,status", [(1, 200), (2, 404), (3, 404), (4, 404), (5, 200), (6, 200), (999, 404)]
)
def test_public_visibility(menu_api, mid, status):
    client, _ = menu_api
    assert client.get(f"{ROOT}/menu-items/{mid}").status_code == status


@pytest.mark.parametrize(
    "rid,status,ids",
    [(1, 200, [1]), (2, 404, None), (3, 404, None), (4, 200, [5]), (5, 200, [6]), (999, 404, None)],
)
def test_public_menu_visibility(menu_api, rid, status, ids):
    response = menu_api[0].get(f"{ROOT}/restaurants/{rid}/menu")
    assert response.status_code == status
    if ids is not None:
        assert [row["id"] for row in response.json()] == ids


def test_private_listing_and_public_catalog_do_not_leak_metadata(menu_api):
    client, _ = menu_api
    page = client.get(VENDOR + "?offset=1&limit=1", headers=auth(2)).json()
    assert (page["total"], page["offset"], page["limit"]) == (2, 1, 1)
    assert [row["id"] for row in page["items"]] == [2]
    assert client.get(VENDOR + "/1", headers=auth(2)).json()["is_simulated"] is True
    for catalog in ("canonical-dishes", "ingredients"):
        public = client.get(ROOT + "/" + catalog + "?offset=0&limit=1").json()
        private = client.get(ADMIN + "/" + catalog, headers=auth(3)).json()
        assert public["limit"] == 1 and len(public["items"]) == 1
        assert "is_simulated" not in public["items"][0]
        assert "source_id" not in public["items"][0]
        assert "is_simulated" in private["items"][0]


VENDOR_OPS = [("GET", ""), ("POST", ""), ("GET", "/1"), ("PUT", "/1"), ("DELETE", "/1")]
ADMIN_OPS = [
    (verb, "/" + catalog + suffix)
    for catalog in ("canonical-dishes", "ingredients")
    for verb, suffix in [("GET", ""), ("POST", ""), ("PUT", "/1"), ("DELETE", "/1")]
]


@pytest.mark.parametrize("uid,status", [(None, 401), (1, 403), (3, 403), (5, 404)])
@pytest.mark.parametrize("verb,suffix", VENDOR_OPS)
def test_vendor_endpoints_require_role_and_membership(menu_api, uid, status, verb, suffix):
    response = menu_api[0].request(verb, VENDOR + suffix, headers=auth(uid), json=item())
    assert response.status_code == status


@pytest.mark.parametrize("uid,status", [(None, 401), (1, 403), (2, 403)])
@pytest.mark.parametrize("verb,path", ADMIN_OPS)
def test_catalog_writes_and_private_reads_require_admin(menu_api, uid, status, verb, path):
    payload = {"name": "Mới"} if "/ingredients" in path else dish()
    response = menu_api[0].request(verb, ADMIN + path, headers=auth(uid), json=payload)
    assert response.status_code == status


@pytest.mark.parametrize("uid", [4, 6])
@pytest.mark.parametrize("verb", ["GET", "PUT", "DELETE"])
def test_foreign_menu_is_indistinguishable_from_missing(menu_api, uid, verb):
    client, engine = menu_api
    foreign = client.request(verb, VENDOR + "/1", headers=auth(uid), json=item())
    missing = client.request(verb, VENDOR + "/999", headers=auth(uid), json=item())
    assert foreign.status_code == missing.status_code == 404
    assert foreign.json() == missing.json()
    with Session(engine) as db:
        row = db.get(MenuItem, 1)
        assert (row.name, row.price, row.is_available) == ("Món 1", 40000, True)


@pytest.mark.parametrize("uid,rid", [(4, 2), (6, 3)])
def test_unapproved_owner_can_prepare_menu_but_not_publish_publicly(menu_api, uid, rid):
    client, _ = menu_api
    response = client.post(VENDOR, headers=auth(uid), json=item())
    assert response.status_code == 201
    assert response.json()["restaurant_id"] == rid
    assert client.get(ROOT + f"/menu-items/{response.json()['id']}").status_code == 404


@pytest.mark.parametrize(
    "changes",
    [
        {"price": 0},
        {"price": 10000001},
        {"price": True},
        {"price": 1.5},
        {"price": "40000"},
        {"name": "  "},
        {"name": "a" * 181},
        {"canonical_dish_id": True},
        {"canonical_dish_id": 2**31},
        {"canonical_dish_id": "1"},
        {"canonical_dish_id": 0},
        {"ingredient_ids": [1, 1]},
        {"ingredient_ids": [True]},
        {"ingredient_ids": ["1"]},
        {"ingredient_ids": list(range(1, 102))},
        {"ingredient_ids": [], "ingredients_verified": True},
        {"is_available": "true"},
        {"ingredients_verified": 1},
        {"restaurant_id": 2},
        {"user_id": 4},
        {"is_simulated": True},
    ],
)
def test_invalid_vendor_payload_does_not_change_menu(menu_api, changes):
    client, engine = menu_api
    response = client.put(VENDOR + "/1", headers=auth(2), json=item(**changes))
    assert response.status_code == 422, response.text
    assert all("input" not in detail for detail in response.json()["error"]["details"])
    with Session(engine) as db:
        assert db.get(MenuItem, 1).price == 40000
        assert len(db.get(MenuItem, 1).ingredient_links) == 2


@pytest.mark.parametrize("field", ["is_available", "ingredients_verified", "ingredient_ids"])
def test_put_requires_full_menu_payload(menu_api, field):
    payload = item()
    del payload[field]
    assert menu_api[0].put(VENDOR + "/1", headers=auth(2), json=payload).status_code == 422


@pytest.mark.parametrize("changes", [{"canonical_dish_id": 999}, {"ingredient_ids": [1, 999]}])
@pytest.mark.parametrize("verb,suffix", [("POST", ""), ("PUT", "/1")])
def test_missing_reference_is_atomic(menu_api, changes, verb, suffix):
    client, engine = menu_api
    assert (
        client.request(verb, VENDOR + suffix, headers=auth(2), json=item(**changes)).status_code
        == 404
    )
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(MenuItem)) == 6
        assert db.get(MenuItem, 1).name == "Món 1"


def test_replace_ingredient_links_and_preserve_order_snapshot(menu_api):
    client, engine = menu_api
    with Session(engine) as db:
        order = Order(
            user_id=1,
            restaurant_id=1,
            total=40000,
            delivery_address="Hà Nội",
            latitude=21,
            longitude=105,
            session_id=uuid4(),
            idempotency_key=uuid4(),
            payload_hash="a" * 64,
        )
        db.add(order)
        db.flush()
        db.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=1,
                quantity=1,
                snapshot_price=40000,
                snapshot_name="Món 1",
            )
        )
        db.commit()
    updated = client.put(VENDOR + "/1", headers=auth(2), json=item(ingredient_ids=[2, 3]))
    assert updated.status_code == 200, updated.text
    assert [entry["id"] for entry in updated.json()["ingredients"]] == [2, 3]
    assert client.delete(VENDOR + "/1", headers=auth(2)).status_code == 204
    with Session(engine) as db:
        snapshot = db.scalar(select(OrderItem))
        assert (snapshot.snapshot_name, snapshot.snapshot_price, snapshot.menu_item_id) == (
            "Món 1",
            40000,
            1,
        )
        assert db.get(MenuItem, 1).name == "Phở đặc biệt"
        assert db.get(MenuItemIngredient, (1, 2)) is not None
        assert db.get(MenuItemIngredient, (1, 1)) is None


@pytest.mark.parametrize("catalog,used,unused", [("canonical-dishes", 1, 3), ("ingredients", 1, 4)])
def test_catalog_delete_preserves_references(menu_api, catalog, used, unused):
    client, _ = menu_api
    assert client.delete(ADMIN + f"/{catalog}/{used}", headers=auth(3)).status_code == 409
    assert client.delete(ADMIN + f"/{catalog}/{unused}", headers=auth(3)).status_code == 204
    assert client.delete(ADMIN + f"/{catalog}/{unused}", headers=auth(3)).status_code == 404


@pytest.mark.parametrize(
    "catalog,payload,code",
    [
        ("ingredients", {"name": " BÒ "}, "INGREDIENT_EXISTS"),
        ("canonical-dishes", dish(name="Phở bò"), "DISH_NAME_EXISTS"),
        ("canonical-dishes", dish(source_id="pho-1"), "DISH_SOURCE_EXISTS"),
    ],
)
@pytest.mark.parametrize("verb,suffix", [("POST", ""), ("PUT", "/3")])
def test_catalog_conflicts_rollback(menu_api, catalog, payload, code, verb, suffix):
    client, engine = menu_api
    response = client.request(verb, ADMIN + "/" + catalog + suffix, headers=auth(3), json=payload)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == code
    with Session(engine) as db:
        assert db.get(Ingredient, 3).name == "gà"
        assert db.get(CanonicalDish, 3).name == "Món chưa dùng"


def test_catalog_update_and_optional_source(menu_api):
    client, _ = menu_api
    response = client.put(
        ADMIN + "/canonical-dishes/1",
        headers=auth(3),
        json=dish(
            name="Phở bò", source_id="pho-1", spice_level=3, ingredients=[" BÒ ", "bò", "Hành"]
        ),
    )
    assert response.status_code == 200
    assert response.json()["ingredients"] == ["bò", "hành"]
    assert response.json()["is_simulated"] is True
    for name in ("Món A", "Món B"):
        assert (
            client.post(
                ADMIN + "/canonical-dishes", headers=auth(3), json=dish(name=name)
            ).status_code
            == 201
        )
    response = client.put(ADMIN + "/ingredients/3", headers=auth(3), json={"name": "  NẤM "})
    assert response.status_code == 200 and response.json()["name"] == "nấm"
    assert client.get(ROOT + "/menu-items/1").json()["canonical_dish"]["spice_level"] == 3


@pytest.mark.parametrize(
    "changes",
    [
        {"name": " "},
        {"region": " "},
        {"method": " "},
        {"source_id": " "},
        {"spice_level": 4},
        {"spice_level": True},
        {"ingredients": [""]},
        {"ingredients": [1]},
        {"ingredients": ["x" * 101]},
        {"labels": "chay"},
        {"labels": ["Chay"] * 101},
        {"is_simulated": True},
    ],
)
def test_canonical_validation(menu_api, changes):
    assert (
        menu_api[0]
        .post(ADMIN + "/canonical-dishes", headers=auth(3), json=dish(**changes))
        .status_code
        == 422
    )


@pytest.mark.parametrize(
    "payload",
    [{"name": " "}, {"name": "x" * 101}, {"name": 1}, {"name": "Rau", "is_simulated": True}],
)
def test_ingredient_validation(menu_api, payload):
    assert (
        menu_api[0].post(ADMIN + "/ingredients", headers=auth(3), json=payload).status_code == 422
    )


@pytest.mark.parametrize(
    "path,uid",
    [
        ("/canonical-dishes", None),
        ("/ingredients", None),
        ("/restaurants/1/menu", None),
        ("/vendor/menu-items", 2),
        ("/admin/canonical-dishes", 3),
        ("/admin/ingredients", 3),
    ],
)
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "offset=2147483648"])
def test_pagination_bounds(menu_api, path, uid, query):
    assert menu_api[0].get(ROOT + path + "?" + query, headers=auth(uid)).status_code == 422


def test_empty_pages_and_empty_public_menu(menu_api):
    client, _ = menu_api
    assert client.get(ROOT + "/restaurants/1/menu?offset=100").json() == []
    client.delete(VENDOR + "/1", headers=auth(2))
    assert client.get(ROOT + "/restaurants/1/menu").json() == []
    page = client.get(VENDOR + "?offset=100", headers=auth(2)).json()
    assert page["items"] == [] and page["total"] == 2


@pytest.mark.parametrize("operation", ["create", "update", "stop", "catalog", "dish", "delete"])
def test_commit_failure_rolls_back_menu_and_links(menu_api, monkeypatch, operation):
    _, engine = menu_api
    with Session(engine) as db:

        def fail():
            db.flush()
            raise OperationalError("commit", {}, RuntimeError("injected failure"))

        monkeypatch.setattr(db, "commit", fail)
        with pytest.raises(OperationalError):
            if operation == "create":
                service.save_item(db, 1, MenuItemCreate(**item()))
            elif operation == "update":
                service.save_item(db, 1, MenuItemUpdate(**item(ingredient_ids=[2, 3])), 1)
            elif operation == "stop":
                service.stop_selling(db, 1, 1)
            elif operation == "catalog":
                service.save_ingredient(db, IngredientInput(name="Đổi tên"), 1)
            elif operation == "dish":
                service.save_canonical(db, CanonicalDishUpdate(**dish()), 1)
            else:
                service.delete_catalog_entry(db, CanonicalDish, 3)
        assert db.get(MenuItem, 1).is_available is True
        assert db.get(MenuItem, 1).name == "Món 1"
        assert [row.ingredient_id for row in db.get(MenuItem, 1).ingredient_links] == [1, 2]
        assert db.get(Ingredient, 1).name == "bò"
        assert db.get(CanonicalDish, 1).name == "Phở bò"
        assert db.get(CanonicalDish, 3) is not None
        assert db.scalar(select(func.count()).select_from(MenuItem)) == 6


def test_link_insert_failure_does_not_leave_orphan_menu(menu_api):
    _, engine = menu_api

    def fail(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO menu_item_ingredients"):
            raise IntegrityError(statement, {}, RuntimeError("injected link failure"))

    event.listen(engine, "before_cursor_execute", fail)
    try:
        with Session(engine) as db:
            with pytest.raises(IntegrityError):
                service.save_item(db, 1, MenuItemCreate(**item()))
            assert db.scalar(select(func.count()).select_from(MenuItem)) == 6
    finally:
        event.remove(engine, "before_cursor_execute", fail)


@pytest.mark.parametrize(
    "path,uid", [("/menu-items", None), ("/vendor/menu-items", 2), ("/restaurants", None)]
)
@pytest.mark.parametrize("entry_id", [0, -1, 2147483648])
def test_path_id_bounds(menu_api, path, uid, entry_id):
    suffix = "/menu" if path == "/restaurants" else ""
    assert (
        menu_api[0].get(ROOT + f"{path}/{entry_id}{suffix}", headers=auth(uid)).status_code == 422
    )


@pytest.mark.parametrize("catalog", ["canonical-dishes", "ingredients"])
@pytest.mark.parametrize("verb", ["PUT", "DELETE"])
def test_missing_catalog_entry(menu_api, catalog, verb):
    payload = dish() if catalog == "canonical-dishes" else {"name": "Rau"}
    response = menu_api[0].request(verb, ADMIN + f"/{catalog}/999", headers=auth(3), json=payload)
    assert response.status_code == 404


def test_menu_operations_are_registered_in_production_openapi(menu_api):
    paths = menu_api[0].get("/openapi.json").json()["paths"]
    expected = {
        "/menu-items/{item_id}": {"get"},
        "/restaurants/{restaurant_id}/menu": {"get"},
        "/canonical-dishes": {"get"},
        "/ingredients": {"get"},
        "/vendor/menu-items": {"get", "post"},
        "/vendor/menu-items/{item_id}": {"get", "put", "delete"},
        "/admin/canonical-dishes": {"get", "post"},
        "/admin/canonical-dishes/{entry_id}": {"put", "delete"},
        "/admin/ingredients": {"get", "post"},
        "/admin/ingredients/{entry_id}": {"put", "delete"},
    }
    for path, methods in expected.items():
        assert set(paths[ROOT + path]) == methods

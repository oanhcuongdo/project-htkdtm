"""Tìm món/quán: tiếng Việt, phạm vi phục vụ, phân trang và tọa độ biên."""

import math
import unicodedata
from datetime import time

import pytest
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from app.menu.models import MenuItem, MenuItemIngredient
from app.restaurants.models import Restaurant
from app.search.service import haversine_km, normalize_text

ROOT = "/api/v1/search"
CENTER = {"lat": 21, "lng": 105}


@pytest.fixture
def search_api(menu_api):
    client, engine = menu_api
    with Session(engine) as db:
        db.get(Restaurant, 1).name = "Bếp Đậm Đà"
        db.get(Restaurant, 1).address = "Số 1, đường Hà Nội"
        db.get(MenuItem, 1).name = "Phở bò tái"
        for rid, name, latitude, delivery in [
            (6, "Bếp %_ Việt", 21.005, 5),
            (7, "Ngoài phạm vi", 21.02, 1),
            (8, "Quán xa", 21.06, 10),
            (9, "Bếp Gà", 21.02, 5),
            (10, "Quán chưa có món", 21.015, 5),
        ]:
            db.add(
                Restaurant(
                    id=rid,
                    name=name,
                    address="Hà Nội",
                    latitude=latitude,
                    longitude=105,
                    delivery_radius_km=delivery,
                    status="approved",
                    opens_at=time(0),
                    closes_at=time(0),
                    accepting_orders=True,
                )
            )
        db.flush()
        for mid, rid, cid, name in [
            (7, 6, 2, "Mâm 100%_ rau"),
            (8, 7, 1, "Phở ngoài vùng giao"),
            (9, 8, 1, "Phở ở xa"),
            (10, 9, 2, "Gà hấp"),
            (11, 9, 1, "Phở đỏ"),
        ]:
            db.add(
                MenuItem(
                    id=mid,
                    restaurant_id=rid,
                    canonical_dish_id=cid,
                    name=name,
                    price=50000,
                    is_available=True,
                )
            )
        db.commit()
    yield client, engine


def search(client, kind, **params):
    return client.get(f"{ROOT}/{kind}", params=CENTER | params)


def ids(response):
    assert response.status_code == 200, response.text
    return [item["id"] for item in response.json()["items"]]


def test_default_search_filters_scope_before_sort_and_count(search_api):
    client, _ = search_api
    dishes = search(client, "dishes")
    assert ids(dishes) == [1, 5, 6, 7, 10, 11]
    assert dishes.json()["total"] == 6
    assert (dishes.json()["offset"], dishes.json()["limit"]) == (0, 20)
    restaurants = search(client, "restaurants")
    assert ids(restaurants) == [1, 4, 5, 6, 10, 9]
    assert restaurants.json()["total"] == 6
    distances = [item["distance_km"] for item in dishes.json()["items"]]
    assert distances == sorted(distances)
    assert distances[3] == pytest.approx(0.5559754, abs=0.000001)


@pytest.mark.parametrize(
    "q,expected",
    [
        ("PHO BO", [1, 5, 6, 11]),
        ("  phở\tBÒ   ", [1, 5, 6, 11]),
        (unicodedata.normalize("NFD", "Phở bò"), [1, 5, 6, 11]),
        ("pho tai dam", [1]),
        ("do", [11]),
        ("bun ga", [7, 10]),
        ("100%_", [7]),
        ("%", [7]),
        ("_", [7]),
        ("khong co mon nay", []),
        ("' OR 1=1 --", []),
        ("", [1, 5, 6, 7, 10, 11]),
        (" \t ", [1, 5, 6, 7, 10, 11]),
    ],
)
def test_dish_text_is_literal_accent_insensitive_all_words(search_api, q, expected):
    assert ids(search(search_api[0], "dishes", q=q)) == expected


@pytest.mark.parametrize(
    "q,expected",
    [
        ("DAM DA", [1]),
        ("đậm đường", [1]),
        ("HA NOI", [1, 4, 5, 6, 10, 9]),
        ("bep viet", [6]),
        ("%_", [6]),
        ("%", [6]),
        ("_", [6]),
        ("Phở bò", []),
        ("' OR 1=1 --", []),
    ],
)
def test_restaurant_text_matches_name_and_address(search_api, q, expected):
    assert ids(search(search_api[0], "restaurants", q=q)) == expected


def test_closed_paused_and_empty_restaurants_remain_discoverable(search_api):
    client, _ = search_api
    rows = {row["id"]: row for row in search(client, "restaurants").json()["items"]}
    assert rows[4]["is_open"] is False
    assert rows[4]["accepting_orders"] is True
    assert rows[4]["can_receive_orders"] is False
    assert rows[5]["is_open"] is True
    assert rows[5]["accepting_orders"] is False
    assert rows[5]["can_receive_orders"] is False
    assert rows[10]["can_receive_orders"] is True
    dishes = {row["id"]: row for row in search(client, "dishes").json()["items"]}
    assert dishes[5]["restaurant"]["is_open"] is False
    assert dishes[6]["restaurant"]["accepting_orders"] is False


def test_public_search_does_not_require_token_or_expose_private_data(search_api):
    client, _ = search_api
    response = search(client, "dishes")
    row = response.json()["items"][0]
    assert row["restaurant_id"] == row["restaurant"]["id"] == 1
    assert row["restaurant_name"] == row["restaurant"]["name"] == "Bếp Đậm Đà"
    assert row["canonical_dish"]["name"] == "Phở bò"
    assert row["ingredients"] == [{"id": 1, "name": "bò"}, {"id": 2, "name": "hành"}]
    for kind in ("dishes", "restaurants"):
        data = search(client, kind).json()
        serialized = str(data)
        for private in ("is_simulated", "source_id", "memberships", "hashed_password", "user_id"):
            assert private not in serialized


@pytest.mark.parametrize("kind", ["dishes", "restaurants"])
def test_pagination_uses_filtered_results_and_stable_distance_ties(search_api, kind):
    client, _ = search_api
    expected = [1, 5, 6, 7, 10, 11] if kind == "dishes" else [1, 4, 5, 6, 10, 9]
    for offset in range(len(expected)):
        response = search(client, kind, offset=offset, limit=1)
        assert ids(response) == [expected[offset]]
        assert response.json()["total"] == len(expected)
    empty = search(client, kind, offset=2147483647, limit=100)
    assert ids(empty) == []
    assert empty.json()["total"] == len(expected)
    assert empty.json()["offset"] == 2147483647


def test_filters_run_before_pagination_including_empty_match(search_api):
    client, _ = search_api
    response = search(client, "dishes", q="pho", offset=2, limit=1)
    assert ids(response) == [6]
    assert response.json()["total"] == 4
    response = search(client, "restaurants", q="khong ton tai", offset=1)
    assert response.json() == {"items": [], "total": 0, "offset": 1, "limit": 20}


def test_customer_radius_and_restaurant_delivery_radius_both_apply(search_api):
    client, _ = search_api
    assert ids(search(client, "dishes", radius=1)) == [1, 5, 6, 7]
    assert ids(search(client, "dishes", radius=10)) == [1, 5, 6, 7, 10, 11, 9]
    assert 8 not in ids(search(client, "dishes", radius=50))
    assert 7 not in ids(search(client, "restaurants", radius=50))


@pytest.mark.parametrize("kind", ["dishes", "restaurants"])
@pytest.mark.parametrize(
    "changes",
    [
        {"lat": "nan"},
        {"lat": "inf"},
        {"lat": "-inf"},
        {"lat": 90.0001},
        {"lat": -90.0001},
        {"lng": "nan"},
        {"lng": 180.0001},
        {"lng": -180.0001},
        {"lat": "abc"},
        {"radius": 0},
        {"radius": -1},
        {"radius": 50.0001},
        {"radius": "nan"},
        {"radius": "inf"},
        {"offset": -1},
        {"offset": 2147483648},
        {"offset": "1.5"},
        {"limit": 0},
        {"limit": 101},
        {"q": "a" * 181},
        {"status": "pending"},
    ],
)
def test_invalid_search_query_has_standard_422(search_api, kind, changes):
    response = search(search_api[0], kind, **changes)
    assert response.status_code == 422, response.text
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert all("input" not in detail for detail in error["details"])


@pytest.mark.parametrize("kind", ["dishes", "restaurants"])
@pytest.mark.parametrize("params", [{}, {"lat": 21}, {"lng": 105}])
def test_location_is_required_without_silent_fallback(search_api, kind, params):
    assert search_api[0].get(f"{ROOT}/{kind}", params=params).status_code == 422


@pytest.mark.parametrize("lat,lng", [(90, 180), (-90, -180), (0, 180), (0, -180)])
def test_valid_coordinate_extremes_do_not_fail(search_api, lat, lng):
    assert search(search_api[0], "restaurants", lat=lat, lng=lng).status_code == 200


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ((0, 0), (0, 0), 0),
        ((0, 0), (0, 1), 111.1950802),
        ((0, 0), (0, 180), 20015.1144420),
        ((0, 179.99), (0, -179.99), 2.2239016),
        ((90, 0), (90, 180), 0),
    ],
)
def test_haversine_known_distances_and_symmetry(a, b, expected):
    distance = haversine_km(*a, *b)
    assert math.isfinite(distance)
    assert distance == pytest.approx(expected, abs=0.000001)
    assert haversine_km(*b, *a) == pytest.approx(distance, abs=1e-9)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("  ĐẬM\tĐà  ", "dam da"),
        (unicodedata.normalize("NFD", "Phở bò"), "pho bo"),
        ("100%_", "100%_"),
        ("Đường", "duong"),
    ],
)
def test_normalize_vietnamese_text_without_treating_punctuation_as_wildcards(text, expected):
    assert normalize_text(text) == expected


@pytest.mark.parametrize(
    "center,point",
    [
        ((0, 179.99), (0, -179.99)),
        ((0, -179.99), (0, 179.99)),
        ((89.99, 0), (89.99, 180)),
        ((-89.99, 0), (-89.99, 180)),
        ((90, 0), (89.99, 120)),
    ],
)
def test_search_bounding_box_keeps_date_line_and_pole_neighbors(search_api, center, point):
    client, engine = search_api
    with Session(engine) as db:
        row = db.get(Restaurant, 1)
        row.latitude, row.longitude = point
        db.commit()
    response = search(client, "dishes", lat=center[0], lng=center[1], radius=5)
    assert ids(response) == [1]
    assert response.json()["items"][0]["distance_km"] == pytest.approx(
        haversine_km(*center, *point), abs=1e-9
    )


def test_radius_comparison_does_not_round_in_a_dish_just_outside(search_api):
    client, engine = search_api
    with Session(engine) as db:
        row = db.get(Restaurant, 1)
        row.latitude = 21 + math.degrees(5.00001 / 6371.0088)
        row.delivery_radius_km = 10
        db.commit()
    assert 1 not in ids(search(client, "dishes", radius=5))
    assert 1 in ids(search(client, "dishes", radius=5.00002))


def test_delivery_boundary_is_inclusive(search_api):
    client, engine = search_api
    boundary = haversine_km(21, 105, 21.02, 105)
    with Session(engine) as db:
        row = db.get(Restaurant, 7)
        row.delivery_radius_km = boundary
        db.commit()
    assert 8 in ids(search(client, "dishes", radius=boundary))


def test_search_reads_do_not_write_and_do_not_query_per_menu_item(search_api):
    client, engine = search_api
    statements = []

    def track(_conn, _cursor, statement, _params, _context, _many):
        statements.append(statement.strip().split()[0].upper())

    event.listen(engine, "before_cursor_execute", track)
    try:
        for _ in range(2):
            response = search(client, "dishes", radius=50)
            assert response.status_code == 200
    finally:
        event.remove(engine, "before_cursor_execute", track)
    assert set(statements) == {"SELECT"}
    assert len(statements) <= 8
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(MenuItem)) == 11
        assert db.scalar(select(func.count()).select_from(MenuItemIngredient)) == 2


def test_search_endpoints_are_in_production_openapi(search_api):
    paths = search_api[0].get("/openapi.json").json()["paths"]
    for kind in ("dishes", "restaurants"):
        operation = paths[f"{ROOT}/{kind}"]["get"]
        assert not operation.get("security")
        parameters = {entry["name"]: entry for entry in operation["parameters"]}
        assert parameters["lat"]["required"] is True
        assert parameters["lng"]["required"] is True
        assert parameters["radius"]["schema"]["default"] == 5

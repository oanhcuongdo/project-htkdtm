"""Lọc vùng SQL, đo Haversine và tìm chữ Unicode cho tập dữ liệu MVP.

Lọc chính xác và sắp xếp trước phân trang; không cắt ứng viên làm sai total.
Không cần extension unaccent/PostGIS hoặc hàm lượng giác riêng của DB.
"""

from math import asin, atan2, cos, degrees, isfinite, radians, sin, sqrt
from unicodedata import combining, normalize

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.menu import service as menu
from app.menu.models import MenuItem, MenuItemIngredient
from app.restaurants import service as restaurants
from app.restaurants.models import Restaurant, RestaurantStatus
from app.search.schemas import (
    DishSearchPage,
    DishSearchResult,
    RestaurantSearchPage,
    RestaurantSearchResult,
    SearchParams,
)

EARTH_RADIUS_KM = 6371.0088


def normalize_text(value: str) -> str:
    decomposed = normalize("NFD", value.casefold().replace("đ", "d"))
    return " ".join("".join(char for char in decomposed if not combining(char)).split())


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Khoảng cách đường chim bay trên mặt cầu, xử lý cả hai cực/kinh tuyến 180°."""
    for value, maximum in ((lat1, 90), (lng1, 180), (lat2, 90), (lng2, 180)):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or abs(value) > maximum
        ):
            raise ValueError("Tọa độ phải là số hữu hạn trong phạm vi vĩ độ/kinh độ.")
    dlat, dlng = radians(lat2 - lat1), radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    a = min(1.0, max(0.0, a))
    return 2 * EARTH_RADIUS_KM * atan2(sqrt(a), sqrt(1 - a))


def _area_filters(params: SearchParams):
    angular = params.radius / EARTH_RADIUS_KM
    # Nới hộp vài phần tỷ độ để sai số lượng giác không loại nhầm điểm sát biên.
    delta_lat = degrees(angular) + 1e-9
    lower_lat, upper_lat = max(-90, params.lat - delta_lat), min(90, params.lat + delta_lat)
    filters = [Restaurant.latitude.between(lower_lat, upper_lat)]
    if lower_lat <= -90 or upper_lat >= 90:
        return filters
    delta_lng = degrees(asin(min(1, sin(angular) / cos(radians(params.lat))))) + 1e-9
    lower_lng, upper_lng = params.lng - delta_lng, params.lng + delta_lng
    if lower_lng < -180:
        filters.append(
            or_(Restaurant.longitude >= lower_lng + 360, Restaurant.longitude <= upper_lng)
        )
    elif upper_lng > 180:
        filters.append(
            or_(Restaurant.longitude >= lower_lng, Restaurant.longitude <= upper_lng - 360)
        )
    else:
        filters.append(Restaurant.longitude.between(lower_lng, upper_lng))
    return filters


def _distance(restaurant: Restaurant, params: SearchParams) -> float | None:
    distance = haversine_km(params.lat, params.lng, restaurant.latitude, restaurant.longitude)
    return distance if distance <= min(params.radius, restaurant.delivery_radius_km) else None


def _matches(tokens: list[str], *fields: str) -> bool:
    text = normalize_text(" ".join(fields))
    return all(token in text for token in tokens)


def search_restaurants(db: Session, params: SearchParams) -> RestaurantSearchPage:
    tokens = normalize_text(params.q).split()
    candidates = db.scalars(
        select(Restaurant).where(
            Restaurant.status == RestaurantStatus.APPROVED, *_area_filters(params)
        )
    ).all()
    matches = []
    for restaurant in candidates:
        distance = _distance(restaurant, params)
        if distance is not None and _matches(tokens, restaurant.name, restaurant.address):
            matches.append((distance, restaurant))
    matches.sort(key=lambda match: (match[0], match[1].id))
    now = restaurants.utcnow()
    return RestaurantSearchPage(
        items=[
            RestaurantSearchResult(
                **restaurants.public_data(row, now).model_dump(), distance_km=dist
            )
            for dist, row in matches[params.offset : params.offset + params.limit]
        ],
        total=len(matches),
        offset=params.offset,
        limit=params.limit,
    )


def search_dishes(db: Session, params: SearchParams) -> DishSearchPage:
    tokens = normalize_text(params.q).split()
    candidates = db.scalars(
        select(MenuItem)
        .join(MenuItem.restaurant)
        .options(joinedload(MenuItem.restaurant), joinedload(MenuItem.canonical_dish))
        .where(
            MenuItem.is_available.is_(True),
            Restaurant.status == RestaurantStatus.APPROVED,
            *_area_filters(params),
        )
    ).all()
    matches = []
    for item in candidates:
        distance = _distance(item.restaurant, params)
        if distance is not None and _matches(
            tokens, item.name, item.canonical_dish.name, item.restaurant.name
        ):
            matches.append((distance, item))
    matches.sort(key=lambda match: (match[0], match[1].id))
    page = matches[params.offset : params.offset + params.limit]
    if page:
        # Chỉ nạp nguyên liệu của trang kết quả; không có một query cho từng món.
        db.scalars(
            select(MenuItem)
            .where(MenuItem.id.in_([row.id for _, row in page]))
            .options(
                selectinload(MenuItem.ingredient_links).joinedload(MenuItemIngredient.ingredient)
            )
        ).all()
    now = restaurants.utcnow()
    return DishSearchPage(
        items=[
            DishSearchResult(
                **menu.menu_data(row).model_dump(),
                distance_km=dist,
                restaurant=restaurants.public_data(row.restaurant, now),
            )
            for dist, row in page
        ],
        total=len(matches),
        offset=params.offset,
        limit=params.limit,
    )

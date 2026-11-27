"""Hồ sơ quán, giờ Việt Nam và transaction quản lý quán."""

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.restaurants.models import Restaurant, RestaurantMembership, RestaurantStatus
from app.restaurants.schemas import (
    RestaurantCreate,
    RestaurantDetail,
    RestaurantPublic,
    RestaurantUpdate,
)
from app.users.models import User, UserRole

VIETNAM = ZoneInfo("Asia/Ho_Chi_Minh")


def utcnow() -> datetime:
    return datetime.now(UTC)


def is_open(restaurant: Restaurant, at: datetime | None = None) -> bool:
    """Giờ mở tính cả đầu, không tính cuối; bằng nhau = 24h; hỗ trợ qua đêm."""
    instant = at if at is not None else utcnow()
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Thời điểm kiểm tra giờ mở cửa phải có múi giờ.")
    local = instant.astimezone(VIETNAM).time()
    start, end = restaurant.opens_at, restaurant.closes_at
    if start == end:
        return True
    return start <= local < end if start < end else local >= start or local < end


def get_restaurant(
    db: Session, restaurant_id: int, *, public: bool = True, lock: bool = False
) -> Restaurant:
    query = select(Restaurant).where(Restaurant.id == restaurant_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    restaurant = db.scalar(query)
    if restaurant is None or (public and restaurant.status != RestaurantStatus.APPROVED):
        raise NotFoundError("Không tìm thấy quán.")
    return restaurant


def public_data(restaurant: Restaurant, at: datetime | None = None) -> RestaurantPublic:
    opened = is_open(restaurant, at)
    return RestaurantPublic(
        id=restaurant.id,
        name=restaurant.name,
        address=restaurant.address,
        latitude=restaurant.latitude,
        longitude=restaurant.longitude,
        delivery_radius_km=restaurant.delivery_radius_km,
        opens_at=restaurant.opens_at.strftime("%H:%M"),
        closes_at=restaurant.closes_at.strftime("%H:%M"),
        accepting_orders=restaurant.accepting_orders,
        is_open=opened,
        can_receive_orders=bool(
            opened
            and restaurant.accepting_orders
            and restaurant.status == RestaurantStatus.APPROVED
        ),
    )


def detail_data(restaurant: Restaurant, at: datetime | None = None) -> RestaurantDetail:
    return RestaurantDetail(
        **public_data(restaurant, at).model_dump(),
        status=restaurant.status,
        is_simulated=restaurant.is_simulated,
    )


def list_restaurants(
    db: Session, *, offset: int, limit: int, public: bool, status: RestaurantStatus | None = None
) -> tuple[list[Restaurant], int]:
    filters = []
    if public:
        filters.append(Restaurant.status == RestaurantStatus.APPROVED)
    elif status is not None:
        filters.append(Restaurant.status == status)
    total = db.scalar(select(func.count()).select_from(Restaurant).where(*filters)) or 0
    rows = db.scalars(
        select(Restaurant).where(*filters).order_by(Restaurant.id).offset(offset).limit(limit)
    ).all()
    return list(rows), total


def _profile_values(payload: RestaurantCreate | RestaurantUpdate) -> dict:
    values = payload.model_dump()
    values["opens_at"] = time.fromisoformat(payload.opens_at)
    values["closes_at"] = time.fromisoformat(payload.closes_at)
    return values


def create_with_owner(db: Session, owner_id: int, payload: RestaurantCreate) -> Restaurant:
    # PostgreSQL khóa tài khoản để tuần tự hóa tạo quán; PK membership vẫn chống trùng.
    owner = db.get(User, owner_id, with_for_update=True, populate_existing=True)
    if owner is None or owner.role != UserRole.VENDOR:
        raise ForbiddenError()
    if db.get(RestaurantMembership, owner_id) is not None:
        raise ConflictError("RESTAURANT_ALREADY_LINKED", "Tài khoản đã được liên kết với một quán.")
    restaurant = Restaurant(
        **_profile_values(payload),
        status=RestaurantStatus.PENDING,
        accepting_orders=False,
        is_simulated=False,
    )
    try:
        db.add(restaurant)
        db.flush()
        db.add(RestaurantMembership(user_id=owner_id, restaurant_id=restaurant.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        if db.get(RestaurantMembership, owner_id) is not None:
            raise ConflictError(
                "RESTAURANT_ALREADY_LINKED", "Tài khoản đã được liên kết với một quán."
            ) from None
        raise
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(restaurant)
    return restaurant


def update_profile(db: Session, restaurant_id: int, payload: RestaurantUpdate) -> Restaurant:
    restaurant = get_restaurant(db, restaurant_id, public=False, lock=True)
    if payload.accepting_orders and restaurant.status != RestaurantStatus.APPROVED:
        raise ConflictError(
            "RESTAURANT_NOT_APPROVED", "Quán cần được duyệt trước khi bật nhận đơn."
        )
    for field, value in _profile_values(payload).items():
        setattr(restaurant, field, value)
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(restaurant)
    return restaurant


def set_status(db: Session, restaurant_id: int, target: RestaurantStatus) -> Restaurant:
    if target not in (RestaurantStatus.APPROVED, RestaurantStatus.SUSPENDED):
        raise ValueError("Chỉ hỗ trợ duyệt hoặc tạm ngừng quán.")
    restaurant = get_restaurant(db, restaurant_id, public=False, lock=True)
    restaurant.status = target
    if target == RestaurantStatus.SUSPENDED:
        restaurant.accepting_orders = False
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    db.refresh(restaurant)
    return restaurant

"""Đơn COD: snapshot, idempotency, phạm vi dữ liệu và lịch sử nguyên tử."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.menu.models import MenuItem
from app.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from app.orders.schemas import OrderCreate, OrderDetail
from app.orders.state_machine import validate_transition
from app.restaurants import service as restaurants
from app.restaurants.models import Restaurant, RestaurantMembership, RestaurantStatus
from app.search.service import haversine_km
from app.users.models import User, UserRole


def _reason(target: OrderStatus, reason: str | None) -> str | None:
    if target == OrderStatus.REJECTED:
        if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 500:
            raise AppError("INVALID_REJECTION_REASON", "Lý do từ chối phải có từ 1 đến 500 ký tự.")
        return reason.strip()
    if reason is not None:
        raise AppError("UNEXPECTED_ORDER_REASON", "Chỉ thao tác từ chối đơn nhận lý do.")
    return None


def transition_order(
    db: Session, order_id: int, actor_id: int, target: OrderStatus, *, reason: str | None = None
) -> Order:
    """Dùng session của request; service sở hữu commit/rollback, không ghép ghi việc khác.

    actor_id phải lấy từ dependency xác thực, không lấy trực tiếp từ body.
    Đọc lại quyền/membership và trạng thái từ DB; khóa hàng khi DB hỗ trợ.
    UPDATE có điều kiện trạng thái bảo vệ khỏi ghi đè thay đổi cạnh tranh.
    """
    try:
        actor = db.get(User, actor_id, populate_existing=True)
        if actor is None or actor.role not in (UserRole.CUSTOMER, UserRole.VENDOR):
            raise ForbiddenError()
        conditions = [Order.id == order_id]
        if actor.role == UserRole.CUSTOMER:
            conditions.append(Order.user_id == actor.id)
        else:
            membership = db.get(RestaurantMembership, actor.id, populate_existing=True)
            if membership is None:
                raise NotFoundError("Không tìm thấy đơn hàng.")
            conditions.append(Order.restaurant_id == membership.restaurant_id)
        order = db.scalar(
            select(Order)
            .where(*conditions)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if order is None:
            raise NotFoundError("Không tìm thấy đơn hàng.")
        validate_transition(order.status, target, actor.role)
        cleaned_reason = _reason(target, reason)
        previous = order.status
        result = db.execute(
            update(Order)
            .where(*conditions, Order.status == previous)
            .values(status=target)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            raise ConflictError(
                "ORDER_STATE_CHANGED", "Đơn hàng đã thay đổi, hãy tải lại trước khi thao tác."
            )
        db.add(
            OrderStatusHistory(
                order_id=order.id, status=target, actor_id=actor.id, reason=cleaned_reason
            )
        )
        db.commit()
    except (AppError, SQLAlchemyError):
        db.rollback()
        raise
    db.refresh(order)
    return order


def utcnow() -> datetime:
    return datetime.now(UTC)


def _payload_hash(payload: OrderCreate) -> str:
    values = payload.model_dump(mode="json", exclude={"idempotency_key"})
    values["items"] = sorted(values["items"], key=lambda row: row["menu_item_id"])
    # -0.0 và 0.0 là cùng một tọa độ.
    for field in ("latitude", "longitude"):
        if values[field] == 0:
            values[field] = 0.0
    return hashlib.sha256(
        json.dumps(values, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def _replay(db: Session, user_id: int, payload: OrderCreate, digest: str) -> Order | None:
    existing = db.scalar(select(Order).where(Order.idempotency_key == payload.idempotency_key))
    if existing is None:
        return None
    if existing.user_id != user_id or existing.payload_hash != digest:
        raise ConflictError("IDEMPOTENCY_CONFLICT", "Mã yêu cầu đã được dùng cho nội dung khác.")
    created = existing.created_at
    if created.tzinfo is None:  # SQLite bỏ timezone khi đọc TIMESTAMPTZ.
        created = created.replace(tzinfo=UTC)
    if utcnow() >= created + timedelta(hours=24):
        raise ConflictError(
            "IDEMPOTENCY_EXPIRED", "Mã yêu cầu đã hết hạn; kiểm tra đơn cũ trước khi đặt lại."
        )
    return existing


def create_order(db: Session, user_id: int, payload: OrderCreate) -> tuple[Order, bool]:
    digest = _payload_hash(payload)
    try:
        # Tuần tự hóa các lần gửi của cùng khách trên PostgreSQL; UNIQUE key vẫn là chốt DB.
        user = db.get(User, user_id, with_for_update=True, populate_existing=True)
        if user is None or user.role != UserRole.CUSTOMER:
            raise ForbiddenError()
        existing = _replay(db, user_id, payload, digest)
        if existing is not None:
            return existing, False
        restaurant = db.get(
            Restaurant, payload.restaurant_id, with_for_update=True, populate_existing=True
        )
        if restaurant is None or restaurant.status != RestaurantStatus.APPROVED:
            raise NotFoundError("Không tìm thấy quán đang hoạt động.")
        if not restaurant.accepting_orders or not restaurants.is_open(restaurant):
            raise ConflictError(
                "RESTAURANT_UNAVAILABLE", "Quán hiện không nhận đơn hoặc đã đóng cửa."
            )
        distance = haversine_km(
            payload.latitude, payload.longitude, restaurant.latitude, restaurant.longitude
        )
        if distance > restaurant.delivery_radius_km:
            raise AppError(
                "OUTSIDE_DELIVERY_AREA", "Địa chỉ nhận hàng nằm ngoài phạm vi giao của quán."
            )
        ids = sorted(item.menu_item_id for item in payload.items)
        rows = db.scalars(
            select(MenuItem)
            .where(MenuItem.id.in_(ids))
            .order_by(MenuItem.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
        by_id = {row.id: row for row in rows}
        snapshots = []
        for line in sorted(payload.items, key=lambda entry: entry.menu_item_id):
            row = by_id.get(line.menu_item_id)
            if row is None or row.restaurant_id != restaurant.id:
                raise AppError("ORDER_ITEM_INVALID", "Đơn chỉ được chứa món thuộc quán đã chọn.")
            if not row.is_available:
                raise ConflictError(
                    "ORDER_ITEM_UNAVAILABLE", "Có món đã ngừng bán.", {"menu_item_id": row.id}
                )
            if row.price != line.expected_price:
                raise ConflictError(
                    "ORDER_PRICE_CHANGED",
                    "Giá món đã thay đổi, vui lòng kiểm tra lại.",
                    {"menu_item_id": row.id, "current_price": row.price},
                )
            snapshots.append(
                OrderItem(
                    menu_item_id=row.id,
                    quantity=line.quantity,
                    snapshot_price=row.price,
                    snapshot_name=row.name,
                )
            )
        order = Order(
            user_id=user.id,
            restaurant_id=restaurant.id,
            total=sum(row.quantity * row.snapshot_price for row in snapshots),
            delivery_address=payload.delivery_address,
            latitude=payload.latitude,
            longitude=payload.longitude,
            session_id=payload.session_id,
            idempotency_key=payload.idempotency_key,
            payload_hash=digest,
            status=OrderStatus.PENDING,
            created_at=utcnow(),
            is_simulated=False,
        )
        order.items = snapshots
        db.add(order)
        db.flush()
        db.add(OrderStatusHistory(order_id=order.id, status=OrderStatus.PENDING, actor_id=user.id))
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _replay(db, user_id, payload, digest)
        if existing is not None:
            return existing, False
        raise
    except (AppError, SQLAlchemyError):
        db.rollback()
        raise
    return order, True


def _scope(db: Session, actor_id: int):
    actor = db.get(User, actor_id, populate_existing=True)
    if actor is None:
        raise ForbiddenError()
    if actor.role == UserRole.CUSTOMER:
        return Order.user_id == actor.id
    if actor.role == UserRole.VENDOR:
        member = db.get(RestaurantMembership, actor.id, populate_existing=True)
        if member is None:
            raise NotFoundError("Tài khoản chưa được liên kết với quán.")
        return Order.restaurant_id == member.restaurant_id
    raise ForbiddenError()


def _read_query():
    return select(Order).options(selectinload(Order.items), selectinload(Order.history))


def detail(db: Session, actor_id: int, order_id: int) -> OrderDetail:
    row = db.scalar(_read_query().where(_scope(db, actor_id), Order.id == order_id))
    if row is None:
        raise NotFoundError("Không tìm thấy đơn hàng.")
    result = OrderDetail.model_validate(row)
    result.items.sort(key=lambda item: item.menu_item_id)
    return result


def listing(db: Session, actor_id: int, *, offset: int, limit: int) -> list[OrderDetail]:
    rows = db.scalars(
        _read_query()
        .where(_scope(db, actor_id))
        .order_by(Order.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    result = [OrderDetail.model_validate(row) for row in rows]
    for item in result:
        item.items.sort(key=lambda line: line.menu_item_id)
    return result

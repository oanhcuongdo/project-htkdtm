"""Chỉ người mua đánh giá một món thuộc đơn đã hoàn tất, một lần mỗi đơn/món."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.orders.models import Order, OrderItem, OrderStatus
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate, ReviewOut
from app.users.models import User, UserRole


def _out(review: Review, line: OrderItem) -> ReviewOut:
    return ReviewOut(
        id=review.id,
        order_id=review.order_id,
        menu_item_id=review.menu_item_id,
        snapshot_name=line.snapshot_name,
        snapshot_price=line.snapshot_price,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


def _duplicate(db: Session, order_id: int, menu_item_id: int) -> bool:
    return (
        db.scalar(
            select(Review.id).where(
                Review.order_id == order_id, Review.menu_item_id == menu_item_id
            )
        )
        is not None
    )


def create_review(db: Session, actor_id: int, order_id: int, payload: ReviewCreate) -> ReviewOut:
    try:
        user = db.get(User, actor_id, populate_existing=True)
        if user is None or user.role != UserRole.CUSTOMER:
            raise ForbiddenError()
        # Khóa Order để tuần tự hóa đánh giá và chuyển trạng thái khi DB hỗ trợ.
        order = db.scalar(
            select(Order)
            .where(Order.id == order_id, Order.user_id == actor_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if order is None:
            raise NotFoundError("Không tìm thấy đơn hàng.")
        if order.status != OrderStatus.COMPLETED:
            raise ConflictError("ORDER_NOT_COMPLETED", "Chỉ đánh giá đơn đã hoàn tất.")
        line = db.scalar(
            select(OrderItem).where(
                OrderItem.order_id == order_id, OrderItem.menu_item_id == payload.menu_item_id
            )
        )
        if line is None:
            raise NotFoundError("Món không thuộc đơn hàng này.")
        if _duplicate(db, order_id, payload.menu_item_id):
            raise ConflictError("REVIEW_ALREADY_EXISTS", "Món này đã được đánh giá trong đơn.")
        review = Review(
            order_id=order_id,
            menu_item_id=payload.menu_item_id,
            user_id=actor_id,
            rating=payload.rating,
            comment=payload.comment,
            is_simulated=False,
        )
        db.add(review)
        db.commit()
    except IntegrityError:
        db.rollback()
        if _duplicate(db, order_id, payload.menu_item_id):
            raise ConflictError(
                "REVIEW_ALREADY_EXISTS", "Món này đã được đánh giá trong đơn."
            ) from None
        raise
    except (ConflictError, ForbiddenError, NotFoundError, SQLAlchemyError):
        db.rollback()
        raise
    db.refresh(review)
    return _out(review, line)

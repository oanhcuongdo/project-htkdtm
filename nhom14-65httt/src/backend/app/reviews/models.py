"""Dữ liệu đánh giá một món trong đơn; quyền gửi do service kiểm tra."""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base
from app.menu.models import MenuItem
from app.orders.models import Order, OrderItem
from app.users.models import User


def _utc_now() -> datetime:
    return datetime.now(UTC)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("order_id", "menu_item_id", name="uq_reviews_order_menu_item"),
        ForeignKeyConstraint(
            ["order_id", "menu_item_id"],
            ["order_items.order_id", "order_items.menu_item_id"],
            ondelete="RESTRICT",
            name="fk_reviews_purchased_item",
        ),
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
        CheckConstraint("length(comment) <= 2000", name="ck_reviews_comment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(
        String(2000), nullable=False, default="", server_default=text("''")
    )
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now()
    )

    order: Mapped[Order] = relationship(foreign_keys=[order_id])
    menu_item: Mapped[MenuItem] = relationship(foreign_keys=[menu_item_id])
    user: Mapped[User] = relationship()
    order_item: Mapped[OrderItem] = relationship(viewonly=True)

    @validates("rating")
    def validate_rating(self, _key: str, value: int) -> int:
        if type(value) is not int or not 1 <= value <= 5:
            raise ValueError("Điểm đánh giá phải là số nguyên từ 1 đến 5.")
        return value

    @validates("comment")
    def normalize_comment(self, _key: str, value: str) -> str:
        if not isinstance(value, str) or len(value.strip()) > 2000:
            raise ValueError("Nhận xét phải là chuỗi không quá 2000 ký tự.")
        return value.strip()

    @validates("created_at")
    def normalize_created_at(self, _key: str, value: datetime) -> datetime:
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Thời điểm đánh giá phải có múi giờ.")
        return value.astimezone(UTC)

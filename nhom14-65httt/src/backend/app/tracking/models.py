"""Lưu nguồn tracking có mã duy nhất; tiếp nhận sự kiện và tính KPI được làm ở service/ETL sau."""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.database import Base
from app.menu.models import MenuItem
from app.users.models import User


class EventType(StrEnum):
    IMPRESSION = "impression"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    FEEDBACK = "feedback"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


def _uuid_v4(value: UUID | str, field: str) -> UUID:
    if isinstance(value, str):
        value = UUID(value)
    if not isinstance(value, UUID) or value.version != 4:
        raise ValueError(f"{field} phải là UUID v4.")
    return value


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _utc_timestamp(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Thời điểm tracking phải có múi giờ.")
    return value.astimezone(UTC)


class RecommendationRequest(Base):
    __tablename__ = "recommendation_requests"
    __table_args__ = (
        UniqueConstraint("id", "user_id", "session_id", name="uq_rec_requests_owner_session"),
        CheckConstraint(
            "length(trim(algorithm_version)) BETWEEN 1 AND 40",
            name="ck_rec_requests_algorithm_version",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    algorithm_version: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now()
    )
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    user: Mapped[User] = relationship()
    impressions: Mapped[list["RecommendationImpression"]] = relationship(
        back_populates="request",
        passive_deletes="all",
        order_by="RecommendationImpression.rank",
    )

    @validates("id", "session_id")
    def normalize_identifier(self, key: str, value: UUID | str) -> UUID:
        return _uuid_v4(value, key)

    @validates("algorithm_version")
    def normalize_algorithm_version(self, _key: str, value: str) -> str:
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= 40:
            raise ValueError("algorithm_version phải có từ 1 đến 40 ký tự.")
        return value.strip()

    @validates("created_at")
    def normalize_created_at(self, _key: str, value: datetime) -> datetime:
        return _utc_timestamp(value)


class RecommendationImpression(Base):
    __tablename__ = "recommendation_impressions"
    __table_args__ = (
        UniqueConstraint("request_id", "menu_item_id", name="uq_rec_impressions_request_item"),
        UniqueConstraint("request_id", "rank", name="uq_rec_impressions_request_rank"),
        CheckConstraint("rank BETWEEN 1 AND 5", name="ck_rec_impressions_rank"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("recommendation_requests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    displayed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    request: Mapped[RecommendationRequest] = relationship(back_populates="impressions")
    menu_item: Mapped[MenuItem] = relationship()

    @validates("request_id")
    def normalize_request_id(self, key: str, value: UUID | str) -> UUID:
        return _uuid_v4(value, key)

    @validates("rank")
    def validate_rank(self, _key: str, value: int) -> int:
        if type(value) is not int or not 1 <= value <= 5:
            raise ValueError("rank phải là số nguyên từ 1 đến 5.")
        return value

    @validates("displayed_at")
    def normalize_displayed_at(self, _key: str, value: datetime | None) -> datetime | None:
        return None if value is None else _utc_timestamp(value)


class InteractionEvent(Base):
    __tablename__ = "interaction_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["request_id", "user_id", "session_id"],
            [
                "recommendation_requests.id",
                "recommendation_requests.user_id",
                "recommendation_requests.session_id",
            ],
            ondelete="RESTRICT",
            name="fk_interaction_events_request_owner",
        ),
        ForeignKeyConstraint(
            ["request_id", "menu_item_id"],
            ["recommendation_impressions.request_id", "recommendation_impressions.menu_item_id"],
            ondelete="RESTRICT",
            name="fk_interaction_events_impression",
        ),
        CheckConstraint(
            "(event_type IN ('impression', 'click', 'feedback') AND request_id IS NOT NULL AND menu_item_id IS NOT NULL) "
            "OR (event_type = 'add_to_cart' AND menu_item_id IS NOT NULL) "
            "OR (event_type IN ('session_start', 'session_end') AND request_id IS NULL AND menu_item_id IS NULL)",
            name="ck_interaction_events_context",
        ),
        CheckConstraint(
            "(event_type = 'feedback' AND value IS NOT NULL AND value IN (0, 1)) "
            "OR (event_type <> 'feedback' AND value IS NULL)",
            name="ck_interaction_events_feedback",
        ),
    )

    event_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    session_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(
        Enum(
            EventType,
            values_callable=lambda types: [event_type.value for event_type in types],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="ck_interaction_events_type",
            length=30,
        ),
        nullable=False,
    )
    request_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    menu_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("menu_items.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, server_default=func.now()
    )
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    user: Mapped[User] = relationship()
    menu_item: Mapped[MenuItem | None] = relationship()
    request: Mapped[RecommendationRequest | None] = relationship(viewonly=True)
    impression: Mapped[RecommendationImpression | None] = relationship(viewonly=True)

    @validates("event_id", "session_id")
    def normalize_identifier(self, key: str, value: UUID | str) -> UUID:
        return _uuid_v4(value, key)

    @validates("request_id")
    def normalize_request_id(self, key: str, value: UUID | str | None) -> UUID | None:
        return None if value is None else _uuid_v4(value, key)

    @validates("value")
    def validate_feedback_value(self, _key: str, value: int | None) -> int | None:
        if value is not None and (type(value) is not int or value not in (0, 1)):
            raise ValueError("Feedback chỉ nhận số nguyên 0 hoặc 1.")
        return value

    @validates("occurred_at", "received_at")
    def normalize_timestamp(self, _key: str, value: datetime) -> datetime:
        return _utc_timestamp(value)

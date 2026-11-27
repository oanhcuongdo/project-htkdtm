"""Tiếp nhận batch nguyên tử, kiểm tra chủ request và ghi mốc hiển thị thực tế."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import AppError, ConflictError, ForbiddenError, NotFoundError
from app.menu.models import MenuItem
from app.tracking.models import (
    EventType,
    InteractionEvent,
    RecommendationImpression,
    RecommendationRequest,
)
from app.tracking.schemas import EventBatch, EventBatchResult, EventInput
from app.users.models import User, UserRole


def utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _same(existing: InteractionEvent, event: EventInput, user_id: int) -> bool:
    return (
        existing.user_id == user_id
        and existing.session_id == event.session_id
        and existing.event_type == event.event_type
        and existing.request_id == event.request_id
        and existing.menu_item_id == event.menu_item_id
        and existing.value == event.value
        and _as_utc(existing.occurred_at) == _as_utc(event.occurred_at)
    )


def _validate_reference(db: Session, event: EventInput, user_id: int):
    if event.menu_item_id is not None and db.get(MenuItem, event.menu_item_id) is None:
        raise NotFoundError("Không tìm thấy món trong sự kiện.")
    if event.request_id is None:
        return None
    request = db.get(RecommendationRequest, event.request_id)
    if request is None or request.user_id != user_id or request.session_id != event.session_id:
        raise NotFoundError("Không tìm thấy yêu cầu gợi ý trong phiên này.")
    impression = db.scalar(
        select(RecommendationImpression)
        .where(
            RecommendationImpression.request_id == event.request_id,
            RecommendationImpression.menu_item_id == event.menu_item_id,
        )
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if impression is None:
        raise NotFoundError("Món không thuộc danh sách gợi ý này.")
    return impression


def ingest_events(db: Session, user_id: int, batch: EventBatch) -> EventBatchResult:
    inserted = duplicates = 0
    now = utcnow()
    seen = {}
    try:
        user = db.get(User, user_id, populate_existing=True)
        if user is None or user.role != UserRole.CUSTOMER:
            raise ForbiddenError()
        for event in batch.events:
            prior = seen.get(event.event_id)
            if prior is not None:
                if prior != event:
                    raise ConflictError(
                        "EVENT_ID_CONFLICT", "Mã sự kiện đã dùng cho nội dung khác."
                    )
                duplicates += 1
                continue
            seen[event.event_id] = event
            existing = db.get(InteractionEvent, event.event_id)
            if existing is not None:
                if not _same(existing, event, user_id):
                    raise ConflictError(
                        "EVENT_ID_CONFLICT", "Mã sự kiện đã dùng cho nội dung khác."
                    )
                duplicates += 1
                continue
            occurred = _as_utc(event.occurred_at)
            if occurred < now - timedelta(hours=24) or occurred > now + timedelta(minutes=5):
                raise AppError(
                    "EVENT_TIME_INVALID", "Thời điểm sự kiện nằm ngoài cửa sổ tiếp nhận."
                )
            impression = _validate_reference(db, event, user_id)
            if event.event_type in (EventType.CLICK, EventType.FEEDBACK) and (
                impression is None
                or impression.displayed_at is None
                or occurred < _as_utc(impression.displayed_at)
            ):
                raise ConflictError(
                    "IMPRESSION_NOT_DISPLAYED", "Món chưa được ghi nhận hiển thị trước tương tác."
                )
            if event.event_type == EventType.IMPRESSION and impression.displayed_at is None:
                impression.displayed_at = occurred
            db.add(
                InteractionEvent(
                    event_id=event.event_id,
                    user_id=user_id,
                    session_id=event.session_id,
                    event_type=event.event_type,
                    request_id=event.request_id,
                    menu_item_id=event.menu_item_id,
                    value=event.value,
                    occurred_at=occurred,
                    received_at=now,
                    is_simulated=False,
                )
            )
            inserted += 1
        db.commit()
    except IntegrityError:
        db.rollback()
        # Hai request gửi song song cùng event_id: trả idempotent chỉ khi toàn batch đã ghi đúng.
        if all(
            (row := db.get(InteractionEvent, event.event_id)) is not None
            and _same(row, event, user_id)
            for event in batch.events
        ):
            return EventBatchResult(accepted=0, duplicates=len(batch.events))
        raise ConflictError(
            "EVENT_ID_CONFLICT", "Có sự kiện trùng hoặc dữ liệu tham chiếu đã thay đổi."
        ) from None
    except (AppError, SQLAlchemyError):
        db.rollback()
        raise
    return EventBatchResult(accepted=inserted, duplicates=duplicates)

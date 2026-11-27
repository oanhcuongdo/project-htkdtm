"""Kiểm tra dữ liệu tracking; chưa thay thế API tiếp nhận và ETL/KPI."""

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid1, uuid4

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.menu.models import CanonicalDish, MenuItem
from app.restaurants.models import Restaurant
from app.tracking.models import (
    EventType,
    InteractionEvent,
    RecommendationImpression,
    RecommendationRequest,
)
from app.users.models import User


@pytest.fixture
def db():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            User(
                id=i,
                email=f"customer{i}@example.vn",
                full_name=f"Khách {i}",
                hashed_password="hash",
            )
            for i in (1, 2)
        )
        session.add(Restaurant(id=1, name="Bếp Việt", address="Hà Nội", latitude=21, longitude=105))
        session.add(CanonicalDish(id=1, name="Phở bò", region="Bắc", method="nước"))
        session.flush()
        session.add_all(
            MenuItem(id=i, restaurant_id=1, canonical_dish_id=1, name=f"Phở {i}", price=50000)
            for i in (1, 2, 3)
        )
        session.flush()
        first = RecommendationRequest(user_id=1, session_id=uuid4(), algorithm_version="content_v1")
        second = RecommendationRequest(
            user_id=2, session_id=uuid4(), algorithm_version="explore_v1"
        )
        session.add_all([first, second])
        session.flush()
        session.add_all(
            [
                RecommendationImpression(
                    request_id=first.id, menu_item_id=1, rank=1, displayed_at=datetime.now(UTC)
                ),
                RecommendationImpression(
                    request_id=first.id, menu_item_id=2, rank=2, displayed_at=datetime.now(UTC)
                ),
                RecommendationImpression(
                    request_id=second.id, menu_item_id=2, rank=1, displayed_at=datetime.now(UTC)
                ),
            ]
        )
        session.commit()
        session.info.update(
            request_id=first.id, session_id=first.session_id, other_request_id=second.id
        )
        yield session
    engine.dispose()


def make_event(db, **overrides):
    values = {
        "event_id": uuid4(),
        "user_id": 1,
        "session_id": db.info["session_id"],
        "event_type": EventType.CLICK,
        "request_id": db.info["request_id"],
        "menu_item_id": 1,
        "occurred_at": datetime.now(UTC),
    }
    return InteractionEvent(**(values | overrides))


def test_backend_request_id_version_and_algorithm_are_stored(db):
    request = RecommendationRequest(
        user_id=1, session_id=str(uuid4()), algorithm_version=" content_v2 "
    )
    db.add(request)
    db.commit()
    db.expire_all()
    stored = db.get(RecommendationRequest, request.id)
    assert isinstance(stored.id, UUID) and stored.id.version == stored.session_id.version == 4
    assert stored.algorithm_version == "content_v2" and stored.created_at is not None
    assert stored.is_simulated is False and stored.user.id == 1


def test_returned_item_does_not_automatically_count_as_displayed(db):
    impression = RecommendationImpression(request_id=db.info["request_id"], menu_item_id=3, rank=3)
    db.add(impression)
    db.commit()
    db.expire_all()
    assert db.get(RecommendationImpression, impression.id).displayed_at is None
    assert db.query(RecommendationImpression).count() == 4
    assert (
        db.query(RecommendationImpression)
        .filter(RecommendationImpression.displayed_at.is_not(None))
        .count()
        == 3
    )


def test_request_impressions_are_ordered_and_linked_to_menu_items(db):
    request = db.get(RecommendationRequest, db.info["request_id"])
    assert [i.rank for i in request.impressions] == [1, 2]
    assert request.impressions[0].menu_item.name == "Phở 1"


@pytest.mark.parametrize("item_id,rank", [(1, 3), (3, 1)])
def test_request_cannot_duplicate_item_or_rank(db, item_id, rank):
    db.add(
        RecommendationImpression(request_id=db.info["request_id"], menu_item_id=item_id, rank=rank)
    )
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_same_menu_item_can_appear_in_another_request(db):
    db.add(RecommendationImpression(request_id=db.info["other_request_id"], menu_item_id=1, rank=2))
    db.commit()
    assert db.query(RecommendationImpression).filter_by(menu_item_id=1).count() == 2


def test_event_loads_correct_request_owner_session_and_impression(db):
    record = make_event(db)
    db.add(record)
    db.commit()
    db.expire_all()
    stored = db.get(InteractionEvent, record.event_id)
    assert stored.event_type is EventType.CLICK
    assert (
        stored.request.id == db.info["request_id"] and stored.request.user_id == stored.user.id == 1
    )
    assert stored.session_id == stored.request.session_id
    assert stored.impression.menu_item_id == stored.menu_item.id == 1
    assert stored.received_at is not None and stored.is_simulated is False


def test_duplicate_client_event_id_is_rejected(db):
    identifier = uuid4()
    db.add(make_event(db, event_id=identifier))
    db.commit()
    db.add(make_event(db, event_id=str(identifier)))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()
    assert db.query(InteractionEvent).count() == 1


def test_distinct_clicks_are_preserved_for_later_kpi_aggregation(db):
    db.add_all([make_event(db), make_event(db)])
    db.commit()
    assert db.query(InteractionEvent).count() == 2


@pytest.mark.parametrize("mismatch", ["owner", "session"])
def test_request_cannot_be_linked_to_another_owner_or_session(db, mismatch):
    overrides = {"user_id": 2} if mismatch == "owner" else {"session_id": uuid4()}
    db.add(make_event(db, **overrides))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_event_item_must_have_been_returned_in_that_request(db):
    db.add(make_event(db, menu_item_id=3))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize(
    "kind", [EventType.IMPRESSION, EventType.CLICK, EventType.ADD_TO_CART, EventType.FEEDBACK]
)
def test_linked_recommendation_event_types_are_stored(db, kind):
    record = make_event(db, event_type=kind, value=1 if kind is EventType.FEEDBACK else None)
    db.add(record)
    db.commit()
    db.expire_all()
    assert db.get(InteractionEvent, record.event_id).event_type is kind


@pytest.mark.parametrize("kind", [EventType.SESSION_START, EventType.SESSION_END])
def test_session_events_do_not_require_request_or_menu_item(db, kind):
    record = make_event(db, event_type=kind, request_id=None, menu_item_id=None)
    db.add(record)
    db.commit()
    db.expire_all()
    stored = db.get(InteractionEvent, record.event_id)
    assert stored.request is None and stored.impression is None and stored.menu_item is None


def test_cart_event_can_come_from_search_without_recommendation(db):
    record = make_event(db, event_type=EventType.ADD_TO_CART, request_id=None, menu_item_id=3)
    db.add(record)
    db.commit()
    assert db.get(InteractionEvent, record.event_id).request_id is None


@pytest.mark.parametrize(
    "kind,missing",
    [
        (EventType.IMPRESSION, "request_id"),
        (EventType.CLICK, "menu_item_id"),
        (EventType.FEEDBACK, "request_id"),
        (EventType.ADD_TO_CART, "menu_item_id"),
    ],
)
def test_item_events_require_their_context(db, kind, missing):
    record = make_event(
        db, event_type=kind, value=1 if kind is EventType.FEEDBACK else None, **{missing: None}
    )
    db.add(record)
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("kind", [EventType.SESSION_START, EventType.SESSION_END])
def test_session_events_reject_item_context(db, kind):
    db.add(make_event(db, event_type=kind))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("value", [0, 1])
def test_feedback_values_are_persisted(db, value):
    record = make_event(db, event_type=EventType.FEEDBACK, value=value)
    db.add(record)
    db.commit()
    assert db.get(InteractionEvent, record.event_id).value == value


@pytest.mark.parametrize("kind,value", [(EventType.FEEDBACK, None), (EventType.CLICK, 1)])
def test_feedback_value_matches_event_type(db, kind, value):
    db.add(make_event(db, event_type=kind, value=value))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("invalid", [-1, 2, True, 0.5, "1"])
def test_invalid_feedback_values_are_rejected(db, invalid):
    with pytest.raises(ValueError):
        make_event(db, value=invalid)


@pytest.mark.parametrize("invalid", [0, 6, True, 1.5])
def test_rank_must_be_integer_in_top_five(invalid):
    with pytest.raises(ValueError):
        RecommendationImpression(rank=invalid)


@pytest.mark.parametrize("invalid", [0, 6])
def test_database_also_checks_rank(db, invalid):
    with pytest.raises(IntegrityError):
        db.execute(
            text("UPDATE recommendation_impressions SET rank = :value WHERE id = 1"),
            {"value": invalid},
        )
    db.rollback()


@pytest.mark.parametrize("invalid", ["view", "rec_click", "CLICK"])
def test_database_rejects_unsupported_event_types(db, invalid):
    db.add(make_event(db))
    db.commit()
    with pytest.raises(IntegrityError):
        db.execute(text("UPDATE interaction_events SET event_type = :value"), {"value": invalid})
    db.rollback()


@pytest.mark.parametrize("invalid", [" ", "x" * 41, None])
def test_algorithm_version_is_required(invalid):
    with pytest.raises(ValueError):
        RecommendationRequest(algorithm_version=invalid)


@pytest.mark.parametrize("field", ["event_id", "session_id", "request_id"])
@pytest.mark.parametrize("invalid", ["bad-uuid", str(uuid1())])
def test_event_identifiers_require_uuid_v4(db, field, invalid):
    with pytest.raises(ValueError):
        make_event(db, **{field: invalid})


@pytest.mark.parametrize("field", ["user_id", "menu_item_id", "request_id"])
def test_events_require_existing_reference_records(db, field):
    db.add(make_event(db, **{field: uuid4() if field == "request_id" else 999}))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize("field", ["request_id", "menu_item_id"])
def test_impressions_require_existing_reference_records(db, field):
    values = {"request_id": db.info["request_id"], "menu_item_id": 3, "rank": 3}
    values[field] = uuid4() if field == "request_id" else 999
    db.add(RecommendationImpression(**values))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


@pytest.mark.parametrize(
    "table", ["recommendation_requests", "recommendation_impressions", "menu_items", "users"]
)
def test_tracking_records_with_references_are_protected(db, table):
    db.add(make_event(db))
    db.commit()
    identifier = db.info["request_id"].hex if table == "recommendation_requests" else 1
    with pytest.raises(IntegrityError):
        db.execute(text(f"DELETE FROM {table} WHERE id = :id"), {"id": identifier})
    db.rollback()


def test_simulation_flags_are_persisted(db):
    request = db.get(RecommendationRequest, db.info["request_id"])
    request.is_simulated = True
    request.impressions[0].is_simulated = True
    record = make_event(db, is_simulated=True)
    db.add(record)
    db.commit()
    db.expire_all()
    assert db.get(InteractionEvent, record.event_id).is_simulated is True
    assert db.get(RecommendationRequest, request.id).is_simulated is True
    assert db.get(RecommendationRequest, request.id).impressions[0].is_simulated is True


@pytest.mark.parametrize(
    "factory,field",
    [
        (RecommendationRequest, "created_at"),
        (RecommendationImpression, "displayed_at"),
        (InteractionEvent, "occurred_at"),
        (InteractionEvent, "received_at"),
    ],
)
def test_timestamps_require_timezone_and_are_normalized(factory, field):
    with pytest.raises(ValueError):
        factory(**{field: datetime(2026, 1, 1)})
    value = datetime(2026, 1, 1, 7, tzinfo=timezone(timedelta(hours=7)))
    assert getattr(factory(**{field: value}), field) == datetime(2026, 1, 1, tzinfo=UTC)

"""Tracking batch: quyền, ngữ cảnh gợi ý, mốc hiển thị, retry và rollback."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.utils import create_token
from app.tracking import service
from app.tracking.models import InteractionEvent, RecommendationImpression, RecommendationRequest
from app.users.models import User

PATH = "/api/v1/tracking/events"
NOW = datetime(2026, 11, 27, 3, tzinfo=UTC)


def auth(uid):
    return {} if uid is None else {"Authorization": "Bearer " + create_token(uid, "access")}


@pytest.fixture
def tracking_api(menu_api, monkeypatch):
    client, engine = menu_api
    monkeypatch.setattr(service, "utcnow", lambda: NOW)
    session_id, request_id = uuid4(), uuid4()
    with Session(engine) as db:
        db.add(
            User(
                id=10,
                email="customer10@example.vn",
                full_name="Khách 10",
                role="customer",
                hashed_password="fixture",
            )
        )
        db.add(
            RecommendationRequest(
                id=request_id, user_id=1, session_id=session_id, algorithm_version="content_v1"
            )
        )
        db.flush()
        db.add_all(
            [
                RecommendationImpression(request_id=request_id, menu_item_id=mid, rank=rank)
                for rank, mid in [(1, 1), (2, 2)]
            ]
        )
        db.commit()
    yield client, engine, str(session_id), str(request_id)


def entry(
    session_id,
    request_id=None,
    *,
    kind="session_start",
    menu_id=None,
    value=None,
    event_id=None,
    occurred_at=None,
):
    return dict(
        event_id=str(event_id or uuid4()),
        session_id=session_id,
        event_type=kind,
        request_id=request_id,
        menu_item_id=menu_id,
        value=value,
        occurred_at=(occurred_at or NOW).isoformat(),
    )


def post(client, uid, events):
    return client.post(PATH, headers=auth(uid), json={"events": events})


def test_full_batch_sets_displayed_at_and_retry_is_idempotent(tracking_api):
    client, engine, sid, rid = tracking_api
    events = [
        entry(sid),
        entry(sid, rid, kind="impression", menu_id=1),
        entry(sid, rid, kind="click", menu_id=1),
        entry(sid, rid, kind="feedback", menu_id=1, value=1),
        entry(sid, rid, kind="add_to_cart", menu_id=1),
        entry(sid, kind="session_end"),
    ]
    first = post(client, 1, events)
    assert first.status_code == 200, first.text
    assert first.json() == {"accepted": 6, "duplicates": 0}
    second = post(client, 1, events)
    assert second.status_code == 200 and second.json() == {"accepted": 0, "duplicates": 6}
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(InteractionEvent)) == 6
        impression = db.scalar(
            select(RecommendationImpression).where(RecommendationImpression.menu_item_id == 1)
        )
        assert impression.displayed_at is not None
        assert (
            db.scalar(
                select(RecommendationImpression).where(RecommendationImpression.menu_item_id == 2)
            ).displayed_at
            is None
        )
        assert all(
            row.user_id == 1 and not row.is_simulated
            for row in db.scalars(select(InteractionEvent))
        )


@pytest.mark.parametrize("uid,status", [(None, 401), (2, 403), (3, 403), (10, 404)])
def test_role_and_request_owner(tracking_api, uid, status):
    client, _, sid, rid = tracking_api
    response = post(client, uid, [entry(sid, rid, kind="impression", menu_id=1)])
    assert response.status_code == status


@pytest.mark.parametrize(
    "kind,value,has_request,menu",
    [
        ("impression", None, None, 1),
        ("click", None, None, 1),
        ("feedback", None, None, 1),
        ("feedback", None, "req", 1),
        ("feedback", 2, "req", 1),
        ("click", 1, "req", 1),
        ("add_to_cart", None, None, None),
        ("session_start", None, "req", 1),
        ("session_end", None, "req", None),
    ],
)
def test_schema_context_rejected(tracking_api, kind, value, has_request, menu):
    client, engine, sid, rid = tracking_api
    response = post(
        client, 1, [entry(sid, rid if has_request else None, kind=kind, menu_id=menu, value=value)]
    )
    assert response.status_code == 422, response.text
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(InteractionEvent)) == 0


@pytest.mark.parametrize("kind", ["click", "feedback"])
def test_click_and_feedback_need_prior_display(tracking_api, kind):
    client, engine, sid, rid = tracking_api
    response = post(
        client, 1, [entry(sid, rid, kind=kind, menu_id=1, value=1 if kind == "feedback" else None)]
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IMPRESSION_NOT_DISPLAYED"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(InteractionEvent)) == 0


def test_batch_failure_rolls_back_events_and_display_timestamp(tracking_api):
    client, engine, sid, rid = tracking_api
    response = post(
        client,
        1,
        [entry(sid, rid, kind="impression", menu_id=1), entry(sid, rid, kind="click", menu_id=2)],
    )
    assert response.status_code == 409
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(InteractionEvent)) == 0
        assert (
            db.scalar(
                select(RecommendationImpression).where(RecommendationImpression.menu_item_id == 1)
            ).displayed_at
            is None
        )


def test_foreign_session_and_unlisted_item_rejected(tracking_api):
    client, _, sid, rid = tracking_api
    for item in [
        entry(str(uuid4()), rid, kind="impression", menu_id=1),
        entry(sid, rid, kind="impression", menu_id=999),
        entry(sid, rid, kind="impression", menu_id=3),
    ]:
        assert post(client, 1, [item]).status_code == 404


def test_add_to_cart_without_request_and_duplicate_in_one_batch(tracking_api):
    client, engine, sid, _ = tracking_api
    item = entry(sid, kind="add_to_cart", menu_id=1)
    response = post(client, 1, [item, item])
    assert response.status_code == 200 and response.json() == {"accepted": 1, "duplicates": 1}
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(InteractionEvent)) == 1


def test_same_id_different_content_conflicts_and_keeps_original(tracking_api):
    client, engine, sid, _ = tracking_api
    item = entry(sid)
    assert post(client, 1, [item]).status_code == 200
    changed = item | {"event_type": "session_end"}
    response = post(client, 1, [changed])
    assert response.status_code == 409 and response.json()["error"]["code"] == "EVENT_ID_CONFLICT"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(InteractionEvent)) == 1


@pytest.mark.parametrize("delta", [-86401, 301])
def test_time_window_rejects_old_or_future_event(tracking_api, delta):
    client, engine, sid, _ = tracking_api
    response = post(client, 1, [entry(sid, occurred_at=NOW + timedelta(seconds=delta))])
    assert response.status_code == 400 and response.json()["error"]["code"] == "EVENT_TIME_INVALID"
    with Session(engine) as db:
        assert db.scalar(select(func.count()).select_from(InteractionEvent)) == 0


def test_retry_after_window_still_succeeds(tracking_api, monkeypatch):
    client, _, sid, _ = tracking_api
    item = entry(sid)
    assert post(client, 1, [item]).status_code == 200
    monkeypatch.setattr(service, "utcnow", lambda: NOW + timedelta(days=2))
    assert post(client, 1, [item]).json() == {"accepted": 0, "duplicates": 1}


@pytest.mark.parametrize(
    "change",
    [
        {"event_id": "bad"},
        {"session_id": "bad"},
        {"event_type": "rec_click"},
        {"occurred_at": "2026-11-27T03:00:00"},
        {"value": True},
        {"user_id": 2},
        {"is_simulated": True},
    ],
)
def test_invalid_event_input(tracking_api, change):
    client, _, sid, _ = tracking_api
    assert post(client, 1, [entry(sid) | change]).status_code == 422


def test_openapi_and_batch_limits(tracking_api):
    client, _, sid, _ = tracking_api
    assert post(client, 1, []).status_code == 422
    assert post(client, 1, [entry(sid)] * 101).status_code == 422
    op = client.get("/openapi.json").json()["paths"][PATH]
    assert set(op) == {"post"} and op["post"]["security"]

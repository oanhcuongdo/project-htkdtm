from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.models.recommendation import RecommendationItem, RecommendationRun
from app.schemas.recommendation import RecommendationRunTrace
from app.services.recommendation_service import (
    RecommendationTraceConflictError,
    persist_recommendation_trace,
)


def build_trace(**overrides) -> RecommendationRunTrace:
    payload = {
        "request_id": "00000000-0000-4000-8000-000000000001",
        "student_id": None,
        "learner_key": "learner-test",
        "model_name": "M2",
        "model_version": "m2-hybrid-v1-test",
        "dataset_version_id": "dataset-test-v1",
        "created_at": datetime(2026, 11, 27, tzinfo=timezone.utc),
        "candidate_set_hash": "a" * 64,
        "top_k": 2,
        "model_config": {"weights": {"S": 0.5, "G": 0.35, "L": 0.15}},
        "input_snapshot": {"learner_profile": {"goals": ["analytics"]}},
        "filter_snapshot": {"eligible_candidate_ids": ["course-1"]},
        "items": [
            {
                "course_id": "course-1",
                "rank": 1,
                "score": 91.25,
                "score_scale": "0-100",
                "ranking_method": "m2_hybrid",
                "fallback_reason": None,
                "score_components": {"S": 1.0, "G": 0.75, "L": 0.5},
                "score_metadata": {
                    "effective_weights": {"S": 0.5, "G": 0.35, "L": 0.15},
                    "completeness": "complete",
                },
                "course_snapshot": {"title": "Analytics"},
                "explanation": {
                    "claims": [
                        {
                            "type": "skill_gap",
                            "text": "SQL",
                            "source_fields": ["profile.target_skills"],
                        }
                    ],
                    "missing_fields_to_confirm": [],
                },
            }
        ],
    }
    payload.update(overrides)
    return RecommendationRunTrace.model_validate(payload)


class FakeAsyncSession:
    def __init__(self) -> None:
        self.added = []
        self.existing = None
        self.commit_count = 0

    async def scalar(self, _statement):
        return self.existing

    def add(self, instance) -> None:
        self.added.append(instance)
        self.existing = instance

    async def commit(self) -> None:
        self.commit_count += 1

    async def refresh(self, _instance) -> None:
        return None


def test_recommendation_trace_tables_are_sqlite_ddl_compatible():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[
            RecommendationRun.__table__,
            RecommendationItem.__table__,
        ],
    )

    assert {
        "recommendation_runs",
        "recommendation_items",
    }.issubset(inspect(engine).get_table_names())
    engine.dispose()


@pytest.mark.asyncio
async def test_persist_trace_copies_versions_and_evidence_to_every_item():
    session = FakeAsyncSession()
    trace = build_trace()

    run = await persist_recommendation_trace(session, trace)

    assert session.commit_count == 1
    assert run.trace_sha256
    assert run.input_snapshot == trace.input_snapshot
    assert run.filter_snapshot == trace.filter_snapshot
    assert len(run.items) == 1
    assert run.items[0].model_version == trace.model_version
    assert run.items[0].dataset_version_id == trace.dataset_version_id
    assert run.items[0].explanation == trace.items[0].explanation
    assert run.items[0].score_metadata == trace.items[0].score_metadata
    assert run.items[0].course_snapshot == trace.items[0].course_snapshot


@pytest.mark.asyncio
async def test_persist_trace_is_idempotent_but_rejects_changed_evidence():
    session = FakeAsyncSession()
    original = build_trace()
    saved = await persist_recommendation_trace(session, original)

    same = await persist_recommendation_trace(session, original)
    assert same is saved
    assert session.commit_count == 1

    changed = build_trace(
        items=[
            {
                **original.items[0].model_dump(mode="json"),
                "score": 92.0,
            }
        ]
    )
    with pytest.raises(RecommendationTraceConflictError, match="different"):
        await persist_recommendation_trace(session, changed)
    assert session.commit_count == 1


def test_trace_rejects_duplicate_ranks_and_unversioned_item_identity():
    duplicate_rank_items = [
        {
            **build_trace().items[0].model_dump(mode="json"),
            "course_id": "course-2",
        },
        build_trace().items[0].model_dump(mode="json"),
    ]
    with pytest.raises(ValueError, match="ranks must be unique"):
        build_trace(items=duplicate_rank_items)

    with pytest.raises(ValueError, match="exactly one"):
        build_trace(student_id=str(uuid4()))

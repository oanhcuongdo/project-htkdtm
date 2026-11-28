from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.models.model_evaluation import ModelEvaluation
from app.schemas.model_evaluation import ModelEvaluationBatch
from app.services.model_evaluation_service import (
    ModelEvaluationConflictError,
    persist_model_evaluation_batch,
)


def build_batch(**overrides) -> ModelEvaluationBatch:
    payload = {
        "schema_version": 1,
        "evaluation_batch_id": str(uuid4()),
        "created_at": datetime(2026, 11, 27, tzinfo=timezone.utc),
        "dataset_version_id": "dataset-test-v1",
        "evaluation_split": "test",
        "top_k": 5,
        "course_count": 300,
        "profile_count": 30,
        "labeled_pair_count": 300,
        "evaluation_metadata": {"judgment_coverage": 0.2},
        "metrics": [
            {
                "model_name": "M0",
                "model_version": "m0-tfidf-v1",
                "profile_count": 30,
                "labeled_pair_count": 300,
                "course_count": 300,
                "ndcg_at_5": 0.7,
                "precision_at_5": 0.72,
                "prerequisite_violations": 0,
                "profiles_under_5_results": 2,
                "p50_latency_ms": 32.0,
                "p95_latency_ms": 62.0,
                "relative_ndcg_gain_vs_m0": 0.0,
                "goal_status": {"zero_prerequisite_violations": True},
            }
        ],
    }
    payload.update(overrides)
    return ModelEvaluationBatch.model_validate(payload)


class FakeScalarResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return list(self.rows)


class FakeAsyncSession:
    def __init__(self) -> None:
        self.rows = []
        self.commit_count = 0

    async def scalars(self, _statement):
        return FakeScalarResult(self.rows)

    def add_all(self, rows) -> None:
        self.rows.extend(rows)

    async def commit(self) -> None:
        self.commit_count += 1

    async def refresh(self, _row) -> None:
        return None


def test_model_evaluation_table_is_sqlite_ddl_compatible():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=[ModelEvaluation.__table__])

    assert "model_evaluations" in inspect(engine).get_table_names()
    engine.dispose()


def test_evaluation_batch_schema_rejects_non_test_or_duplicate_models():
    batch = build_batch()
    payload = batch.model_dump(mode="json")
    payload["evaluation_split"] = "dev"
    with pytest.raises(ValueError, match="test"):
        ModelEvaluationBatch.model_validate(payload)

    duplicate = batch.model_dump(mode="json")
    duplicate["metrics"].append(dict(duplicate["metrics"][0]))
    with pytest.raises(ValueError, match="unique"):
        ModelEvaluationBatch.model_validate(duplicate)


@pytest.mark.asyncio
async def test_evaluation_persistence_is_idempotent_and_rejects_changed_batch():
    session = FakeAsyncSession()
    batch = build_batch()

    first, first_digest = await persist_model_evaluation_batch(session, batch)
    retry, retry_digest = await persist_model_evaluation_batch(session, batch)

    assert first[0] is retry[0]
    assert first_digest == retry_digest
    assert session.commit_count == 1
    assert len(session.rows) == 1
    assert session.rows[0].ndcg_at_5 == 0.7
    assert session.rows[0].evaluation_metadata["judgment_coverage"] == 0.2

    changed = build_batch(
        evaluation_batch_id=str(batch.evaluation_batch_id),
        metrics=[
            {
                **batch.metrics[0].model_dump(mode="json"),
                "ndcg_at_5": 0.9,
            }
        ],
    )
    with pytest.raises(ModelEvaluationConflictError, match="different"):
        await persist_model_evaluation_batch(session, changed)

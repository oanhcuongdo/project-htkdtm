import hashlib
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_evaluation import ModelEvaluation
from app.schemas.model_evaluation import ModelEvaluationBatch


class ModelEvaluationConflictError(Exception):
    """Raised when an existing batch identifier is reused with changed evidence."""


def _batch_digest(batch: ModelEvaluationBatch) -> str:
    canonical = json.dumps(
        batch.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def persist_model_evaluation_batch(
    db: AsyncSession,
    batch: ModelEvaluationBatch,
) -> tuple[list[ModelEvaluation], str]:
    digest = _batch_digest(batch)
    existing = list(
        (
            await db.scalars(
                select(ModelEvaluation)
                .where(
                    ModelEvaluation.evaluation_batch_id == batch.evaluation_batch_id
                )
                .order_by(ModelEvaluation.model_name)
            )
        ).all()
    )
    if existing:
        if any(row.batch_sha256 != digest for row in existing):
            raise ModelEvaluationConflictError(
                "evaluation_batch_id already exists with different evaluation evidence"
            )
        if len(existing) != len(batch.metrics):
            raise ModelEvaluationConflictError(
                "stored evaluation batch is incomplete"
            )
        return existing, digest

    metadata = dict(batch.evaluation_metadata)
    rows = [
        ModelEvaluation(
            evaluation_batch_id=batch.evaluation_batch_id,
            batch_sha256=digest,
            model_name=metric.model_name,
            model_version=metric.model_version,
            dataset_version_id=batch.dataset_version_id,
            split_name=batch.evaluation_split,
            top_k=batch.top_k,
            profile_count=metric.profile_count,
            labeled_pair_count=metric.labeled_pair_count,
            course_count=metric.course_count,
            ndcg_at_5=metric.ndcg_at_5,
            precision_at_5=metric.precision_at_5,
            prerequisite_violations=metric.prerequisite_violations,
            profiles_under_5_results=metric.profiles_under_5_results,
            p50_latency_ms=metric.p50_latency_ms,
            p95_latency_ms=metric.p95_latency_ms,
            relative_ndcg_gain_vs_m0=metric.relative_ndcg_gain_vs_m0,
            goal_status=metric.goal_status,
            evaluation_metadata={
                **metadata,
                **metric.evaluation_metadata,
            },
            created_at=batch.created_at,
        )
        for metric in batch.metrics
    ]
    db.add_all(rows)
    await db.commit()
    for row in rows:
        await db.refresh(row)
    return rows, digest

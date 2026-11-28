import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.recommendation import RecommendationItem, RecommendationRun
from app.schemas.recommendation import RecommendationRunTrace


class RecommendationTraceConflictError(ValueError):
    """Raised when a request ID is reused for different recommendation evidence."""


async def persist_recommendation_trace(
    db: AsyncSession,
    trace: RecommendationRunTrace,
) -> RecommendationRun:
    """Persist an immutable run and its ranked items in one transaction."""
    serialized = trace.model_dump(mode="json", by_alias=True)
    canonical = json.dumps(
        serialized,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    trace_sha256 = hashlib.sha256(canonical).hexdigest()

    existing = await db.scalar(
        select(RecommendationRun)
        .options(selectinload(RecommendationRun.items))
        .where(RecommendationRun.request_id == trace.request_id)
    )
    if existing is not None:
        if existing.trace_sha256 != trace_sha256:
            raise RecommendationTraceConflictError(
                "request_id already exists with different recommendation evidence"
            )
        return existing

    run = RecommendationRun(
        request_id=trace.request_id,
        student_id=trace.student_id,
        learner_key=trace.learner_key,
        model_name=trace.model_name,
        model_version=trace.model_version,
        dataset_version_id=trace.dataset_version_id,
        candidate_set_hash=trace.candidate_set_hash,
        top_k=trace.top_k,
        input_snapshot=trace.input_snapshot,
        filter_snapshot=trace.filter_snapshot,
        model_config=trace.model_settings,
        trace_sha256=trace_sha256,
        created_at=trace.created_at,
        items=[
            RecommendationItem(
                course_id=item.course_id,
                rank=item.rank,
                score=item.score,
                score_scale=item.score_scale,
                ranking_method=item.ranking_method,
                model_version=trace.model_version,
                dataset_version_id=trace.dataset_version_id,
                score_components=item.score_components,
                score_metadata=item.score_metadata,
                course_snapshot=item.course_snapshot,
                explanation=item.explanation,
            )
            for item in trace.items
        ],
    )
    db.add(run)
    try:
        await db.commit()
    except IntegrityError as error:
        await db.rollback()
        concurrent_run = await db.scalar(
            select(RecommendationRun)
            .options(selectinload(RecommendationRun.items))
            .where(RecommendationRun.request_id == trace.request_id)
        )
        if concurrent_run is None:
            raise
        if concurrent_run.trace_sha256 != trace_sha256:
            raise RecommendationTraceConflictError(
                "request_id already exists with different recommendation evidence"
            ) from error
        return concurrent_run
    await db.refresh(run)
    return run


async def get_recommendation_trace(
    db: AsyncSession,
    request_id: UUID,
) -> RecommendationRun | None:
    """Load a run and its immutable item explanations for audit/replay."""
    result = await db.execute(
        select(RecommendationRun)
        .options(selectinload(RecommendationRun.items))
        .where(RecommendationRun.request_id == request_id)
    )
    return result.scalar_one_or_none()

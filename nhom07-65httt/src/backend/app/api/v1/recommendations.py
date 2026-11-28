import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.dependencies.db import get_db
from app.schemas.recommendation import (
    RecommendationRunReceipt,
    RecommendationRunTrace,
)
from app.schemas.model_evaluation import (
    ModelEvaluationBatch,
    ModelEvaluationBatchReceipt,
)
from app.services.model_evaluation_service import (
    ModelEvaluationConflictError,
    persist_model_evaluation_batch,
)
from app.services.recommendation_service import (
    RecommendationTraceConflictError,
    persist_recommendation_trace,
)


router = APIRouter()


async def require_recommender_service(
    x_internal_api_key: str = Header(..., alias="X-Internal-API-Key"),
) -> None:
    configured_key = settings.INTERNAL_API_KEY
    if not configured_key or not secrets.compare_digest(
        x_internal_api_key,
        configured_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: invalid internal API key",
        )


@router.post(
    "/runs",
    response_model=RecommendationRunReceipt,
    status_code=status.HTTP_201_CREATED,
)
async def record_recommendation_run(
    trace: RecommendationRunTrace,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_recommender_service),
) -> RecommendationRunReceipt:
    try:
        run = await persist_recommendation_trace(db, trace)
    except RecommendationTraceConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return RecommendationRunReceipt(
        id=run.id,
        request_id=run.request_id,
        model_name=run.model_name,
        model_version=run.model_version,
        dataset_version_id=run.dataset_version_id,
        candidate_set_hash=run.candidate_set_hash,
        trace_sha256=run.trace_sha256,
        item_count=len(run.items),
        created_at=run.created_at,
    )


@router.post(
    "/evaluations",
    response_model=ModelEvaluationBatchReceipt,
    status_code=status.HTTP_201_CREATED,
)
async def record_model_evaluation(
    batch: ModelEvaluationBatch,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(require_recommender_service),
) -> ModelEvaluationBatchReceipt:
    try:
        rows, digest = await persist_model_evaluation_batch(db, batch)
    except ModelEvaluationConflictError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return ModelEvaluationBatchReceipt(
        evaluation_batch_id=batch.evaluation_batch_id,
        batch_sha256=digest,
        model_count=len(rows),
        dataset_version_id=batch.dataset_version_id,
        evaluation_split=batch.evaluation_split,
        created_at=batch.created_at,
    )

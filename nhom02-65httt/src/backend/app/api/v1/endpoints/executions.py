"""Marketplace price sync execution history, creation, retry, and cancel endpoints."""

from __future__ import annotations

import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_any_permission, require_permission
from app.core.errors import ConflictError, NotFoundError
from app.core.rbac import Permission
from app.db.session import get_db
from app.models.erp import Product
from app.models.market import SalesChannel
from app.models.pricing import PriceRecommendation, PriceSyncLog
from app.models.user import User
from app.schemas.common import Envelope, PageMeta
from app.schemas.execution import ExecutionCreate, ExecutionRead
from app.services.audit import record_audit_log
from app.services.execution import (
    MAX_ATTEMPTS,
    enqueue_approved_recommendation_sync,
    execute_sync_log,
)
from app.worker.tasks import execute_price_sync_task

router = APIRouter(prefix="/executions", tags=["executions"])

_ALLOWED_CHANNEL_CODES = frozenset(
    {"SHOPEE", "LAZADA", "TIKTOK_SHOP", "TIKI", "WEBSITE", "OTHER"}
)


@router.get("", response_model=Envelope[list[ExecutionRead]])
def list_executions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    execution_status: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    _: User = Depends(require_permission(Permission.EXECUTION_READ)),
    db: Session = Depends(get_db),
) -> Envelope[list[ExecutionRead]]:
    """Return a paginated list of marketplace price sync execution runs."""
    filters = []
    if execution_status and execution_status.strip():
        filters.append(PriceSyncLog.status == execution_status.strip().upper())
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        filters.append(
            or_(
                PriceSyncLog.sku_code.ilike(pattern),
                PriceSyncLog.channel_name.ilike(pattern),
                PriceSyncLog.idempotency_key.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count()).select_from(PriceSyncLog).where(*filters)) or 0
    total_pages = max(1, math.ceil(total / page_size))

    stmt = (
        select(PriceSyncLog)
        .where(*filters)
        .order_by(PriceSyncLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.scalars(stmt).all()

    return Envelope(
        data=[ExecutionRead.model_validate(row) for row in rows],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.post("", response_model=Envelope[ExecutionRead], status_code=status.HTTP_201_CREATED)
def create_execution(
    payload: ExecutionCreate,
    response: Response,
    current_user: User = Depends(
        require_any_permission(Permission.PRICING_APPROVE, Permission.EXECUTION_RETRY)
    ),
    db: Session = Depends(get_db),
) -> Envelope[ExecutionRead]:
    """Queue or immediately execute a price sync request with idempotency protection."""
    existing = db.scalar(
        select(PriceSyncLog).where(PriceSyncLog.idempotency_key == payload.idempotency_key)
    )
    if existing is not None:
        same_request = (
            existing.sku_code == payload.sku_code
            and existing.channel_code == payload.channel_code
            and existing.requested_price == payload.requested_price
        )
        if not same_request:
            raise ConflictError("Khóa idempotency đã được sử dụng cho yêu cầu đồng bộ khác.")
        response.status_code = status.HTTP_200_OK
        return Envelope(data=ExecutionRead.model_validate(existing))

    channel = db.scalar(select(SalesChannel).where(SalesChannel.code == payload.channel_code))
    if channel is None and payload.channel_code not in _ALLOWED_CHANNEL_CODES:
        raise NotFoundError(f"Không tìm thấy kênh bán {payload.channel_code}.")

    product = db.scalar(select(Product).where(Product.sku_code == payload.sku_code))
    resolved_mode = payload.mode or (channel.integration_mode if channel else "SIMULATED")
    channel_name = channel.name if channel is not None else payload.channel_code

    sync_log = PriceSyncLog(
        recommendation_id=payload.recommendation_id,
        product_id=product.id if product is not None else None,
        channel_id=channel.id if channel is not None else None,
        sku_code=payload.sku_code,
        channel_code=payload.channel_code,
        channel_name=channel_name,
        mode=resolved_mode,
        sync_mode="SIMULATED" if resolved_mode == "SIMULATED" else "API_CONFIRMED",
        requested_price=payload.requested_price,
        previous_price=payload.previous_price,
        status="QUEUED",
        attempts=1,
        idempotency_key=payload.idempotency_key,
    )
    db.add(sync_log)

    if payload.execute_immediately:
        execute_sync_log(
            db,
            sync_log,
            external_listing_id=payload.external_listing_id,
            external_sku=payload.external_sku,
        )

    record_audit_log(
        db,
        actor=current_user.full_name,
        action="EXECUTE_PRICE_SYNC",
        resource_type="price_sync_log",
        after_summary=(
            f"{sync_log.sku_code} -> {sync_log.channel_code}: "
            f"{sync_log.requested_price} ({sync_log.status})"
        ),
    )
    db.commit()
    db.refresh(sync_log)
    return Envelope(data=ExecutionRead.model_validate(sync_log))


@router.post("/{execution_id}/retry", response_model=Envelope[ExecutionRead])
def retry_execution(
    execution_id: UUID,
    current_user: User = Depends(require_permission(Permission.EXECUTION_RETRY)),
    db: Session = Depends(get_db),
) -> Envelope[ExecutionRead]:
    """Re-queue a failed execution run if retry budget has not been exhausted."""
    sync_log = db.get(PriceSyncLog, execution_id)
    if sync_log is None:
        raise NotFoundError("Không tìm thấy tác vụ đồng bộ.")
    if sync_log.status != "FAILED":
        raise ConflictError("Chỉ thử lại được tác vụ đang ở trạng thái thất bại.")
    if sync_log.attempts >= MAX_ATTEMPTS:
        raise ConflictError(
            f"Đã đạt giới hạn {MAX_ATTEMPTS} lần thử. Tạo tác vụ khôi phục thay vì retry."
        )

    before = f"{sync_log.status} (attempts={sync_log.attempts})"
    sync_log.attempts += 1
    sync_log.status = "QUEUED"
    sync_log.http_status = None
    sync_log.error_code = None
    sync_log.error_message = None

    record_audit_log(
        db,
        actor=current_user.full_name,
        action="RETRY_EXECUTION",
        resource_type="price_sync_log",
        before_summary=before,
        after_summary=f"QUEUED (attempts={sync_log.attempts})",
    )
    db.commit()
    db.refresh(sync_log)
    return Envelope(data=ExecutionRead.model_validate(sync_log))


@router.post("/{execution_id}/cancel", response_model=Envelope[ExecutionRead])
def cancel_execution(
    execution_id: UUID,
    current_user: User = Depends(require_permission(Permission.EXECUTION_RETRY)),
    db: Session = Depends(get_db),
) -> Envelope[ExecutionRead]:
    """Cancel a queued execution run before it starts processing."""
    sync_log = db.get(PriceSyncLog, execution_id)
    if sync_log is None:
        raise NotFoundError("Không tìm thấy tác vụ đồng bộ.")
    if sync_log.status != "QUEUED":
        raise ConflictError("Chỉ huỷ được tác vụ đang chờ trong hàng đợi.")

    sync_log.status = "CANCELLED"
    record_audit_log(
        db,
        actor=current_user.full_name,
        action="CANCEL_EXECUTION",
        resource_type="price_sync_log",
        before_summary="QUEUED",
        after_summary="CANCELLED",
    )
    db.commit()
    db.refresh(sync_log)
    return Envelope(data=ExecutionRead.model_validate(sync_log))


@router.post(
    "/from-recommendation/{recommendation_id}",
    response_model=Envelope[ExecutionRead],
    status_code=status.HTTP_201_CREATED,
)
def execute_approved_recommendation(
    recommendation_id: UUID,
    response: Response,
    execute_immediately: bool = Query(True, alias="executeImmediately"),
    dispatch_celery: bool = Query(False, alias="dispatchCelery"),
    current_user: User = Depends(
        require_any_permission(Permission.PRICING_APPROVE, Permission.EXECUTION_RETRY)
    ),
    db: Session = Depends(get_db),
) -> Envelope[ExecutionRead]:
    """Trigger marketplace sync from an APPROVED price recommendation."""
    recommendation = db.get(PriceRecommendation, recommendation_id)
    if recommendation is None:
        raise NotFoundError("Không tìm thấy đề xuất giá.")

    sync_log, created = enqueue_approved_recommendation_sync(
        db,
        recommendation,
        actor=current_user.full_name,
        execute_immediately=execute_immediately,
    )
    if not created:
        response.status_code = status.HTTP_200_OK
        return Envelope(data=ExecutionRead.model_validate(sync_log))

    db.commit()
    db.refresh(sync_log)
    if dispatch_celery and not execute_immediately:
        execute_price_sync_task.delay(str(sync_log.id))

    return Envelope(data=ExecutionRead.model_validate(sync_log))

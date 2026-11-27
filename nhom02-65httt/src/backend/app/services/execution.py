"""Execution synchronization service connecting PriceSyncLog and MarketplaceAdapter."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ProviderUnavailableError
from app.db.base import utc_now
from app.integrations.marketplace import (
    MarketplaceAdapter,
    PriceUpdateRequest,
    SyncMode,
    get_adapter,
)
from app.models.erp import Product
from app.models.market import ChannelProduct, SalesChannel
from app.models.pricing import PriceApproval, PriceRecommendation, PriceSyncLog
from app.services.audit import record_audit_log

MAX_ATTEMPTS = 3


def _sync_recommendation_status(db: Session, sync_log: PriceSyncLog) -> None:
    if sync_log.recommendation_id is None:
        return
    recommendation = db.get(PriceRecommendation, sync_log.recommendation_id)
    if recommendation is not None:
        recommendation.status = "EXECUTED" if sync_log.status == "SUCCEEDED" else "FAILED"


def execute_sync_log(
    db: Session,
    sync_log: PriceSyncLog,
    *,
    external_listing_id: str | None = None,
    external_sku: str | None = None,
    adapter_override: MarketplaceAdapter | None = None,
) -> PriceSyncLog:
    """Execute a queued PriceSyncLog via MarketplaceAdapter and update persisted status."""
    sync_log.status = "RUNNING"

    listing_id = external_listing_id or sync_log.sku_code
    channel_sku = external_sku or f"{sync_log.channel_code}-{sync_log.sku_code}"
    if sync_log.product_id is not None and sync_log.channel_id is not None:
        mapping = db.scalar(
            select(ChannelProduct).where(
                ChannelProduct.product_id == sync_log.product_id,
                ChannelProduct.channel_id == sync_log.channel_id,
            )
        )
        if mapping is not None:
            listing_id = external_listing_id or mapping.external_listing_id
            channel_sku = external_sku or mapping.external_sku
    else:
        mapping = None

    attempt_key = (
        sync_log.idempotency_key
        if sync_log.attempts <= 1
        else f"{sync_log.idempotency_key}#attempt-{sync_log.attempts}"
    )

    try:
        adapter = adapter_override or get_adapter(
            sync_log.channel_code,
            mode="LIVE" if sync_log.mode == "LIVE" else "SIMULATED",
        )
    except ProviderUnavailableError as exc:
        sync_log.status = "FAILED"
        sync_log.sync_mode = SyncMode.API_CONFIRMED.value
        sync_log.http_status = 503
        sync_log.error_code = exc.code
        sync_log.error_message = exc.message
        _sync_recommendation_status(db, sync_log)
        return sync_log

    result = adapter.update_price(
        PriceUpdateRequest(
            channel_code=sync_log.channel_code,
            external_listing_id=listing_id,
            external_sku=channel_sku,
            new_price=sync_log.requested_price,
            previous_price=sync_log.previous_price,
            idempotency_key=attempt_key,
        )
    )

    sync_log.sync_mode = result.sync_mode.value
    sync_log.http_status = result.http_status
    sync_log.external_reference = result.external_reference
    sync_log.error_code = result.error_code
    sync_log.error_message = result.error_message
    sync_log.status = "SUCCEEDED" if result.success else "FAILED"

    if result.success and mapping is not None:
        mapping.current_price = sync_log.requested_price
        mapping.sync_status = "SYNCED"
        mapping.last_synced_at = utc_now()

    _sync_recommendation_status(db, sync_log)
    return sync_log


def enqueue_approved_recommendation_sync(
    db: Session,
    recommendation: PriceRecommendation,
    *,
    actor: str,
    execute_immediately: bool = True,
) -> tuple[PriceSyncLog, bool]:
    """Create (or replay idempotently) a PriceSyncLog for an APPROVED recommendation."""
    idempotency_key = f"rec-{recommendation.id}"
    existing = db.scalar(
        select(PriceSyncLog).where(PriceSyncLog.idempotency_key == idempotency_key)
    )
    if existing is not None:
        return existing, False

    if recommendation.status != "APPROVED":
        raise ConflictError("Chỉ có thể đồng bộ đề xuất đã được phê duyệt (APPROVED).")

    product = db.get(Product, recommendation.product_id)
    if product is None:
        raise NotFoundError("Không tìm thấy sản phẩm của đề xuất giá.")

    channel = db.get(SalesChannel, recommendation.channel_id)
    if channel is None:
        raise NotFoundError("Không tìm thấy kênh bán của đề xuất giá.")

    latest_approval = db.scalar(
        select(PriceApproval)
        .where(
            PriceApproval.recommendation_id == recommendation.id,
            PriceApproval.decision == "APPROVED",
        )
        .order_by(PriceApproval.decided_at.desc())
    )
    target_price = (
        latest_approval.adjusted_price
        if latest_approval is not None and latest_approval.adjusted_price is not None
        else recommendation.recommended_price
    )

    sync_log = PriceSyncLog(
        recommendation_id=recommendation.id,
        product_id=product.id,
        channel_id=channel.id,
        sku_code=product.sku_code,
        channel_code=channel.code,
        channel_name=channel.name,
        mode=channel.integration_mode,
        sync_mode="SIMULATED" if channel.integration_mode == "SIMULATED" else "API_CONFIRMED",
        requested_price=target_price,
        previous_price=recommendation.current_price,
        status="QUEUED",
        attempts=1,
        idempotency_key=idempotency_key,
    )
    db.add(sync_log)
    recommendation.status = "EXECUTION_QUEUED"

    if execute_immediately:
        execute_sync_log(db, sync_log)

    record_audit_log(
        db,
        actor=actor,
        action="QUEUE_APPROVED_SYNC",
        resource_type="price_recommendation",
        before_summary="APPROVED",
        after_summary=(
            f"{sync_log.sku_code} -> {sync_log.channel_code}: "
            f"{sync_log.requested_price} ({sync_log.status})"
        ),
    )
    return sync_log, True

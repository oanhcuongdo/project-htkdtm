"""Sales channels, channel fees, and adapter connection test endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_any_permission, require_permission
from app.core.errors import NotFoundError, ProviderUnavailableError
from app.core.rbac import Permission
from app.db.base import utc_now
from app.db.session import get_db
from app.integrations.marketplace import get_adapter
from app.models.market import ChannelProduct, SalesChannel
from app.models.user import User
from app.schemas.channel import (
    ChannelFeeComponentRead,
    ChannelFeeRead,
    ChannelRead,
    ConnectionTestRead,
)
from app.schemas.common import Envelope

router = APIRouter(tags=["channels"])


def _resolve_channel(db: Session, channel_ref: str) -> SalesChannel | None:
    try:
        channel_uuid = UUID(channel_ref)
    except ValueError:
        code = channel_ref.strip().upper()
        return db.scalar(select(SalesChannel).where(SalesChannel.code == code))
    return db.get(SalesChannel, channel_uuid)


@router.get("/channels", response_model=Envelope[list[ChannelRead]])
def list_channels(
    _: User = Depends(require_permission(Permission.CHANNEL_READ)),
    db: Session = Depends(get_db),
) -> Envelope[list[ChannelRead]]:
    """Return configured sales channels along with mapped SKU listing counts."""
    listing_counts = dict(
        db.execute(
            select(ChannelProduct.channel_id, func.count(ChannelProduct.id)).group_by(
                ChannelProduct.channel_id
            )
        ).all()
    )
    channels = db.scalars(select(SalesChannel).order_by(SalesChannel.name.asc())).all()
    data = [
        ChannelRead(
            id=channel.id,
            code=channel.code,
            name=channel.name,
            integration_mode=channel.integration_mode,
            connection_status=channel.connection_status,
            is_active=channel.is_active,
            listing_count=int(listing_counts.get(channel.id, 0)),
            fee_rate=channel.fee_rate,
        )
        for channel in channels
    ]
    return Envelope(data=data)


@router.get("/channel-fees", response_model=Envelope[list[ChannelFeeRead]])
def list_channel_fees(
    _: User = Depends(require_any_permission(Permission.CHANNEL_READ, Permission.SETTINGS_READ)),
    db: Session = Depends(get_db),
) -> Envelope[list[ChannelFeeRead]]:
    """Return fee breakdowns configured per sales channel."""
    channels = db.scalars(select(SalesChannel).order_by(SalesChannel.name.asc())).all()
    data = [
        ChannelFeeRead(
            channel_id=channel.id,
            channel_name=channel.name,
            total_rate=channel.fee_rate,
            effective_from=channel.fee_effective_from or channel.created_at,
            source=channel.fee_source or "Cấu hình hệ thống",
            components=[
                ChannelFeeComponentRead(
                    name="Phí nền tảng",
                    type="PERCENT",
                    value=channel.platform_fee_rate,
                    verified=True,
                ),
                ChannelFeeComponentRead(
                    name="Phí thanh toán",
                    type="PERCENT",
                    value=channel.payment_fee_rate,
                    verified=True,
                ),
                ChannelFeeComponentRead(
                    name="Phí dịch vụ / affiliate",
                    type="PERCENT",
                    value=channel.service_fee_rate,
                    verified=channel.service_fee_rate > 0,
                ),
            ],
        )
        for channel in channels
    ]
    return Envelope(data=data)


@router.post(
    "/channels/{channel_id}/test-connection",
    response_model=Envelope[ConnectionTestRead],
)
def test_channel_connection(
    channel_id: str,
    _: User = Depends(require_permission(Permission.CHANNEL_READ)),
    db: Session = Depends(get_db),
) -> Envelope[ConnectionTestRead]:
    """Exercise the MarketplaceAdapter connection check without mutating marketplace prices."""
    channel = _resolve_channel(db, channel_id)
    if channel is None:
        raise NotFoundError("Không tìm thấy kênh bán.")

    mode = "LIVE" if channel.integration_mode == "LIVE" else "SIMULATED"
    try:
        adapter = get_adapter(channel.code, mode=mode)
    except ProviderUnavailableError as exc:
        return Envelope(
            data=ConnectionTestRead(
                ok=False,
                mode=channel.integration_mode,
                message=exc.message,
                checked_at=utc_now(),
            )
        )

    check = adapter.test_connection()
    return Envelope(
        data=ConnectionTestRead(
            ok=check.ok,
            mode=channel.integration_mode,
            message=check.message,
            checked_at=utc_now(),
        )
    )

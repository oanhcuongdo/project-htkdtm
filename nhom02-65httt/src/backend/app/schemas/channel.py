"""Sales channel, fee configuration, and connection test schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from app.schemas.common import ApiModel


class ChannelRead(ApiModel):
    """Sales channel representation matching frontend Channel shape."""

    id: UUID
    code: str
    name: str
    integration_mode: str
    connection_status: str
    is_active: bool
    listing_count: int
    fee_rate: Decimal


class ChannelFeeComponentRead(ApiModel):
    """Individual fee component inside a channel fee configuration."""

    name: str
    type: Literal["PERCENT", "FIXED"] = "PERCENT"
    value: Decimal
    verified: bool = True


class ChannelFeeRead(ApiModel):
    """Channel fee configuration matching frontend ChannelFee shape."""

    channel_id: UUID
    channel_name: str
    total_rate: Decimal
    effective_from: datetime
    source: str
    components: list[ChannelFeeComponentRead]


class ConnectionTestRead(ApiModel):
    """Adapter connection check response matching frontend ConnectionTest shape."""

    ok: bool
    mode: str
    message: str
    checked_at: datetime

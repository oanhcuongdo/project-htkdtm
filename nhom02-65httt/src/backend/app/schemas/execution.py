"""Marketplace price sync execution schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.common import ApiModel


class ExecutionCreate(ApiModel):
    """Request payload to queue or immediately execute a marketplace price sync."""

    sku_code: str = Field(min_length=1, max_length=64)
    channel_code: str = Field(min_length=1, max_length=32)
    requested_price: Decimal = Field(gt=0)
    previous_price: Decimal = Field(ge=0)
    idempotency_key: str = Field(min_length=1, max_length=128)
    mode: Literal["SIMULATED", "LIVE"] | None = None
    recommendation_id: UUID | None = None
    external_listing_id: str | None = Field(default=None, max_length=120)
    external_sku: str | None = Field(default=None, max_length=120)
    execute_immediately: bool = True

    @field_validator("sku_code", "channel_code")
    @classmethod
    def _normalize_upper(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("Giá trị không được để trống.")
        return cleaned

    @field_validator("idempotency_key")
    @classmethod
    def _clean_key(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("idempotencyKey không được để trống.")
        return cleaned


class ExecutionRead(ApiModel):
    """Price sync log representation matching frontend ExecutionRun shape."""

    id: UUID
    sku_code: str
    channel_code: str
    channel_name: str
    mode: str
    sync_mode: str
    requested_price: Decimal
    previous_price: Decimal
    status: str
    attempts: int
    http_status: int | None
    external_reference: str | None
    error_code: str | None
    error_message: str | None
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

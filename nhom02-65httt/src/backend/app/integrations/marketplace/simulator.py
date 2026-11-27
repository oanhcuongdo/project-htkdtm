"""Deterministic Sandbox Marketplace Simulator for write-back sync testing."""

from __future__ import annotations

import hashlib
import time
from decimal import Decimal

from app.integrations.marketplace.base import (
    ConnectionCheck,
    MarketplaceAdapter,
    PriceUpdateRequest,
    PriceUpdateResult,
    SyncMode,
)


class SimulatedMarketplaceAdapter(MarketplaceAdapter):
    """In-process deterministic marketplace simulator keyed by idempotency_key."""

    def __init__(
        self,
        channel_code: str,
        failure_rate: float = 0.0,
        latency_range_ms: tuple[int, int] = (50, 300),
        sleep: bool = False,
    ) -> None:
        if not 0.0 <= failure_rate <= 1.0:
            raise ValueError("failure_rate must be between 0.0 and 1.0")
        min_ms, max_ms = latency_range_ms
        if min_ms < 0 or max_ms < min_ms:
            raise ValueError("latency_range_ms must satisfy 0 <= min_ms <= max_ms")

        self.channel_code = channel_code.strip().upper()
        self.failure_rate = failure_rate
        self.latency_range_ms = latency_range_ms
        self.sleep = sleep
        self._cache: dict[str, PriceUpdateResult] = {}

    @property
    def sync_mode(self) -> SyncMode:
        return SyncMode.SIMULATED

    def update_price(self, request: PriceUpdateRequest) -> PriceUpdateResult:
        if request.new_price <= Decimal("0"):
            return PriceUpdateResult(
                success=False,
                sync_mode=SyncMode.SIMULATED,
                http_status=422,
                external_reference=None,
                error_code="VALIDATION_ERROR",
                error_message="Giá cập nhật phải lớn hơn 0.",
                latency_ms=0,
                raw_response={
                    "mode": SyncMode.SIMULATED.value,
                    "channelCode": self.channel_code,
                    "errorCode": "VALIDATION_ERROR",
                },
            )

        cached = self._cache.get(request.idempotency_key)
        if cached is not None:
            return cached

        digest = hashlib.sha256(request.idempotency_key.encode("utf-8")).digest()
        min_ms, max_ms = self.latency_range_ms
        span = max_ms - min_ms + 1
        latency_ms = min_ms + (int.from_bytes(digest[:4], "big") % span)

        if self.sleep and latency_ms > 0:
            time.sleep(latency_ms / 1000.0)

        roll = int.from_bytes(digest[4:8], "big") / (1 << 32)
        if roll < self.failure_rate:
            if digest[8] % 2 == 0:
                http_status = 503
                error_code = "PROVIDER_UNAVAILABLE"
                error_message = f"Kênh mô phỏng {self.channel_code} tạm thời không phản hồi."
            else:
                http_status = 429
                error_code = "RATE_LIMITED"
                error_message = f"Kênh mô phỏng {self.channel_code} vượt giới hạn tần suất."
            result = PriceUpdateResult(
                success=False,
                sync_mode=SyncMode.SIMULATED,
                http_status=http_status,
                external_reference=None,
                error_code=error_code,
                error_message=error_message,
                latency_ms=latency_ms,
                raw_response={
                    "mode": SyncMode.SIMULATED.value,
                    "channelCode": self.channel_code,
                    "externalListingId": request.external_listing_id,
                    "errorCode": error_code,
                    "idempotencyKey": request.idempotency_key,
                },
            )
        else:
            external_ref = f"SIM-{digest[:4].hex()}"
            result = PriceUpdateResult(
                success=True,
                sync_mode=SyncMode.SIMULATED,
                http_status=200,
                external_reference=external_ref,
                error_code=None,
                error_message=None,
                latency_ms=latency_ms,
                raw_response={
                    "mode": SyncMode.SIMULATED.value,
                    "channelCode": self.channel_code,
                    "externalListingId": request.external_listing_id,
                    "externalSku": request.external_sku,
                    "newPrice": str(request.new_price),
                    "externalReference": external_ref,
                    "idempotencyKey": request.idempotency_key,
                },
            )

        self._cache[request.idempotency_key] = result
        return result

    def test_connection(self) -> ConnectionCheck:
        return ConnectionCheck(
            ok=True,
            mode=SyncMode.SIMULATED,
            message=f"Sandbox simulator sẵn sàng cho kênh {self.channel_code}.",
        )

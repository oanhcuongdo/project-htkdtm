"""Abstract interface and value objects for marketplace price sync adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any


class SyncMode(StrEnum):
    """Execution authenticity marker stored with sync logs."""

    SIMULATED = "SIMULATED"
    API_CONFIRMED = "API_CONFIRMED"


@dataclass(frozen=True, slots=True)
class PriceUpdateRequest:
    """Normalized outbound price synchronization request."""

    channel_code: str
    external_listing_id: str
    external_sku: str
    new_price: Decimal
    previous_price: Decimal | None
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class PriceUpdateResult:
    """Result returned by a marketplace adapter after a price update call."""

    success: bool
    sync_mode: SyncMode
    http_status: int
    external_reference: str | None
    error_code: str | None
    error_message: str | None
    latency_ms: int
    raw_response: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ConnectionCheck:
    """Health/connectivity check response for a sales channel adapter."""

    ok: bool
    mode: SyncMode
    message: str


class MarketplaceAdapter(ABC):
    """Abstract base adapter implemented by Sandbox Simulator and future Partner APIs."""

    channel_code: str

    @property
    @abstractmethod
    def sync_mode(self) -> SyncMode:
        """Return whether execution is SIMULATED or API_CONFIRMED."""

    @abstractmethod
    def update_price(self, request: PriceUpdateRequest) -> PriceUpdateResult:
        """Push an updated unit price to the target channel."""

    @abstractmethod
    def test_connection(self) -> ConnectionCheck:
        """Check connectivity/credentials for the configured channel."""

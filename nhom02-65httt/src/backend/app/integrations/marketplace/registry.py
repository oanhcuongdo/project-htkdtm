"""Registry for resolving channel adapters by channel code and integration mode."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from app.core.errors import AppError, ProviderUnavailableError
from app.integrations.marketplace.base import MarketplaceAdapter
from app.integrations.marketplace.simulator import SimulatedMarketplaceAdapter

IntegrationMode = Literal["SIMULATED", "LIVE"]

DEFAULT_SIMULATED_CHANNELS: frozenset[str] = frozenset(
    {"SHOPEE", "LAZADA", "TIKTOK_SHOP", "TIKI", "WEBSITE"}
)

_ADAPTER_REGISTRY: dict[tuple[str, str], Callable[[str], MarketplaceAdapter]] = {}


def register_adapter(
    channel_code: str,
    mode: IntegrationMode,
    factory: Callable[[str], MarketplaceAdapter],
) -> None:
    """Register an adapter factory for a (channel_code, mode) pair."""
    key = (channel_code.strip().upper(), mode.strip().upper())
    _ADAPTER_REGISTRY[key] = factory


def get_adapter(
    channel_code: str,
    mode: IntegrationMode = "SIMULATED",
) -> MarketplaceAdapter:
    """Resolve an adapter for the target channel and integration mode."""
    normalized_channel = channel_code.strip().upper()
    if not normalized_channel:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Mã kênh bán không được để trống.",
            status_code=422,
        )

    normalized_mode = mode.strip().upper()
    registered = _ADAPTER_REGISTRY.get((normalized_channel, normalized_mode))
    if registered is not None:
        return registered(normalized_channel)

    if normalized_mode == "SIMULATED":
        return SimulatedMarketplaceAdapter(channel_code=normalized_channel)

    if normalized_mode == "LIVE":
        raise ProviderUnavailableError(
            f"Kênh {normalized_channel} chưa hỗ trợ đồng bộ LIVE (chưa có Seller Partner API)."
        )

    raise AppError(
        code="VALIDATION_ERROR",
        message=f"Chế độ đồng bộ không hợp lệ: {mode}.",
        status_code=422,
    )

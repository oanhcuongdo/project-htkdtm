"""Marketplace adapter contracts, simulator, and registry."""

from app.integrations.marketplace.base import (
    ConnectionCheck,
    MarketplaceAdapter,
    PriceUpdateRequest,
    PriceUpdateResult,
    SyncMode,
)
from app.integrations.marketplace.registry import (
    DEFAULT_SIMULATED_CHANNELS,
    get_adapter,
    register_adapter,
)
from app.integrations.marketplace.simulator import SimulatedMarketplaceAdapter

__all__ = [
    "ConnectionCheck",
    "DEFAULT_SIMULATED_CHANNELS",
    "MarketplaceAdapter",
    "PriceUpdateRequest",
    "PriceUpdateResult",
    "SimulatedMarketplaceAdapter",
    "SyncMode",
    "get_adapter",
    "register_adapter",
]

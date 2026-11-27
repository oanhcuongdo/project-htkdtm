"""Tests for MarketplaceAdapter interface, Simulator determinism, and registry."""

from __future__ import annotations

from decimal import Decimal

import pytest
from app.core.errors import ProviderUnavailableError
from app.integrations.marketplace import (
    DEFAULT_SIMULATED_CHANNELS,
    ConnectionCheck,
    MarketplaceAdapter,
    PriceUpdateRequest,
    PriceUpdateResult,
    SimulatedMarketplaceAdapter,
    SyncMode,
    get_adapter,
    register_adapter,
)


def _sample_request(
    *,
    channel_code: str = "SHOPEE",
    new_price: Decimal = Decimal("199000"),
    idempotency_key: str = "sync-001",
) -> PriceUpdateRequest:
    return PriceUpdateRequest(
        channel_code=channel_code,
        external_listing_id="1592328943",
        external_sku="M185-BLK",
        new_price=new_price,
        previous_price=Decimal("219000"),
        idempotency_key=idempotency_key,
    )


def test_default_simulated_channels_resolve() -> None:
    for channel in DEFAULT_SIMULATED_CHANNELS:
        adapter = get_adapter(channel, mode="SIMULATED")
        assert isinstance(adapter, SimulatedMarketplaceAdapter)
        assert adapter.sync_mode == SyncMode.SIMULATED
        check = adapter.test_connection()
        assert check.ok is True
        assert check.mode == SyncMode.SIMULATED


def test_simulator_success_and_idempotency() -> None:
    adapter = SimulatedMarketplaceAdapter("SHOPEE", failure_rate=0.5, sleep=False)
    req = _sample_request(idempotency_key="idemp-stable-1")

    first = adapter.update_price(req)
    second = adapter.update_price(req)

    assert first == second
    assert first.sync_mode == SyncMode.SIMULATED
    if first.success:
        assert first.http_status == 200
        assert first.external_reference is not None
        assert first.external_reference.startswith("SIM-")
        assert len(first.external_reference) == 12


def test_simulator_deterministic_across_instances() -> None:
    a = SimulatedMarketplaceAdapter("LAZADA", failure_rate=0.5, sleep=False)
    b = SimulatedMarketplaceAdapter("LAZADA", failure_rate=0.5, sleep=False)

    keys = [f"k-{idx}" for idx in range(25)]
    results_a = [
        a.update_price(_sample_request(channel_code="LAZADA", idempotency_key=k))
        for k in keys
    ]
    results_b = [
        b.update_price(_sample_request(channel_code="LAZADA", idempotency_key=k))
        for k in keys
    ]

    assert results_a == results_b
    assert any(not r.success and r.http_status in {429, 503} for r in results_a)
    assert any(r.success and r.http_status == 200 for r in results_a)
    for res in results_a:
        assert res.sync_mode == SyncMode.SIMULATED
        if not res.success:
            assert res.error_code in {"PROVIDER_UNAVAILABLE", "RATE_LIMITED"}


def test_simulator_rejects_non_positive_price() -> None:
    adapter = SimulatedMarketplaceAdapter("TIKI")
    result = adapter.update_price(_sample_request(channel_code="TIKI", new_price=Decimal("0")))
    assert result.success is False
    assert result.http_status == 422
    assert result.error_code == "VALIDATION_ERROR"
    assert result.sync_mode == SyncMode.SIMULATED


def test_live_mode_unregistered_raises_provider_unavailable() -> None:
    with pytest.raises(ProviderUnavailableError):
        get_adapter("SHOPEE", mode="LIVE")


def test_register_custom_live_adapter() -> None:
    class DummyLiveAdapter(MarketplaceAdapter):
        def __init__(self, channel_code: str) -> None:
            self.channel_code = channel_code

        @property
        def sync_mode(self) -> SyncMode:
            return SyncMode.API_CONFIRMED

        def update_price(self, request: PriceUpdateRequest) -> PriceUpdateResult:
            return PriceUpdateResult(
                success=True,
                sync_mode=SyncMode.API_CONFIRMED,
                http_status=200,
                external_reference="LIVE-1",
                error_code=None,
                error_message=None,
                latency_ms=10,
                raw_response={},
            )

        def test_connection(self) -> ConnectionCheck:
            return ConnectionCheck(ok=True, mode=SyncMode.API_CONFIRMED, message="ok")

    from app.integrations.marketplace import registry

    register_adapter("WEBSITE", "LIVE", DummyLiveAdapter)
    try:
        adapter = get_adapter("website", mode="LIVE")
        assert adapter.sync_mode == SyncMode.API_CONFIRMED
        assert (
            adapter.update_price(_sample_request(channel_code="WEBSITE")).external_reference
            == "LIVE-1"
        )
    finally:
        registry._ADAPTER_REGISTRY.pop(("WEBSITE", "LIVE"), None)

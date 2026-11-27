"""Sales channel default seeding and lookup helpers."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.models.market import SalesChannel

DEFAULT_CHANNELS: tuple[dict[str, object], ...] = (
    {
        "code": "SHOPEE",
        "name": "Shopee",
        "integration_mode": "SIMULATED",
        "connection_status": "DEMO",
        "platform_fee_rate": Decimal("0.0720"),
        "payment_fee_rate": Decimal("0.0360"),
        "service_fee_rate": Decimal("0.0120"),
        "fee_rate": Decimal("0.1200"),
        "fee_source": "Biểu phí mặc định ngành hàng (Simulator)",
    },
    {
        "code": "TIKTOK_SHOP",
        "name": "TikTok Shop",
        "integration_mode": "SIMULATED",
        "connection_status": "DEMO",
        "platform_fee_rate": Decimal("0.0840"),
        "payment_fee_rate": Decimal("0.0420"),
        "service_fee_rate": Decimal("0.0140"),
        "fee_rate": Decimal("0.1400"),
        "fee_source": "Biểu phí mặc định ngành hàng (Simulator)",
    },
    {
        "code": "LAZADA",
        "name": "Lazada",
        "integration_mode": "SIMULATED",
        "connection_status": "NOT_CONNECTED",
        "platform_fee_rate": Decimal("0.0600"),
        "payment_fee_rate": Decimal("0.0300"),
        "service_fee_rate": Decimal("0.0100"),
        "fee_rate": Decimal("0.1000"),
        "fee_source": "Bảng phí công bố",
    },
    {
        "code": "WEBSITE",
        "name": "Website / Other",
        "integration_mode": "SIMULATED",
        "connection_status": "CONNECTED",
        "platform_fee_rate": Decimal("0.0150"),
        "payment_fee_rate": Decimal("0.0150"),
        "service_fee_rate": Decimal("0.0000"),
        "fee_rate": Decimal("0.0300"),
        "fee_source": "Cổng thanh toán nội bộ",
    },
)


def seed_default_channels(db: Session) -> tuple[int, int]:
    """Create missing default sales channels idempotently. Return (created, skipped)."""
    created = 0
    skipped = 0
    now = utc_now()
    for spec in DEFAULT_CHANNELS:
        existing = db.scalar(select(SalesChannel).where(SalesChannel.code == spec["code"]))
        if existing is not None:
            skipped += 1
            continue
        db.add(
            SalesChannel(
                code=str(spec["code"]),
                name=str(spec["name"]),
                integration_mode=str(spec["integration_mode"]),
                connection_status=str(spec["connection_status"]),
                platform_fee_rate=spec["platform_fee_rate"],
                payment_fee_rate=spec["payment_fee_rate"],
                service_fee_rate=spec["service_fee_rate"],
                fee_rate=spec["fee_rate"],
                fee_effective_from=now,
                fee_source=str(spec["fee_source"]),
                is_active=True,
            )
        )
        created += 1
    if created:
        db.commit()
    return created, skipped

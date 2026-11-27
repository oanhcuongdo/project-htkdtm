"""Dashboard summary response schemas matching frontend DashboardSummary shape."""

from __future__ import annotations

from decimal import Decimal

from app.schemas.common import ApiModel


class RevenueTrendPoint(ApiModel):
    """Single day revenue and net profit point."""

    date: str
    revenue: Decimal
    profit: Decimal


class ChannelProfitPoint(ApiModel):
    """Aggregated profit for a sales channel."""

    channel: str
    profit: Decimal


class PricePositionBucket(ApiModel):
    """SKU count grouped by price position against competitors."""

    bucket: str
    count: int


class DashboardSummaryRead(ApiModel):
    """Executive overview KPIs and chart series."""

    revenue: Decimal
    gross_profit: Decimal
    margin: Decimal
    skus_below_floor: int
    low_stock_count: int
    pending_approvals: int
    revenue_trend: list[RevenueTrendPoint]
    profit_by_channel: list[ChannelProfitPoint]
    price_vs_competitor: list[PricePositionBucket]

"""Executive BI dashboard summary endpoint."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.rbac import Permission
from app.db.session import get_db
from app.models.erp import Inventory, Product
from app.models.market import CompetitorPrice, SalesChannel, SalesRecord
from app.models.pricing import PriceRecommendation
from app.models.user import User
from app.schemas.common import Envelope
from app.schemas.dashboard import (
    ChannelProfitPoint,
    DashboardSummaryRead,
    PricePositionBucket,
    RevenueTrendPoint,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=Envelope[DashboardSummaryRead])
def get_dashboard_summary(
    days: int = Query(14, ge=1, le=365),
    _: User = Depends(require_permission(Permission.BI_READ)),
    db: Session = Depends(get_db),
) -> Envelope[DashboardSummaryRead]:
    """Aggregate KPIs, trend series, channel profit, and competitor price position."""
    totals = db.execute(
        select(
            func.coalesce(func.sum(SalesRecord.gross_revenue), 0),
            func.coalesce(func.sum(SalesRecord.net_profit), 0),
        )
    ).one()
    revenue = Decimal(totals[0]).quantize(Decimal("0.01"))
    gross_profit = Decimal(totals[1]).quantize(Decimal("0.01"))
    margin = (
        (gross_profit / revenue).quantize(Decimal("0.0001"))
        if revenue > 0
        else Decimal("0.0000")
    )

    skus_below_floor = int(
        db.scalar(
            select(func.count())
            .select_from(PriceRecommendation)
            .where(PriceRecommendation.recommended_price < PriceRecommendation.floor_price)
        )
        or 0
    )
    low_stock_count = int(
        db.scalar(
            select(func.count())
            .select_from(Inventory)
            .where((Inventory.on_hand_qty - Inventory.reserved_qty) <= Inventory.reorder_point)
        )
        or 0
    )
    pending_approvals = int(
        db.scalar(
            select(func.count())
            .select_from(PriceRecommendation)
            .where(PriceRecommendation.status == "PENDING_APPROVAL")
        )
        or 0
    )

    trend_rows = db.execute(
        select(
            SalesRecord.order_date,
            func.coalesce(func.sum(SalesRecord.gross_revenue), 0),
            func.coalesce(func.sum(SalesRecord.net_profit), 0),
        )
        .group_by(SalesRecord.order_date)
        .order_by(SalesRecord.order_date.desc())
        .limit(days)
    ).all()
    revenue_trend = [
        RevenueTrendPoint(
            date=row[0].isoformat(),
            revenue=Decimal(row[1]).quantize(Decimal("0.01")),
            profit=Decimal(row[2]).quantize(Decimal("0.01")),
        )
        for row in reversed(trend_rows)
    ]

    channel_rows = db.execute(
        select(
            SalesChannel.name,
            func.coalesce(func.sum(SalesRecord.net_profit), 0),
        )
        .join(SalesRecord, SalesRecord.channel_id == SalesChannel.id)
        .group_by(SalesChannel.id, SalesChannel.name)
        .order_by(func.sum(SalesRecord.net_profit).desc())
    ).all()
    profit_by_channel = [
        ChannelProfitPoint(
            channel=str(row[0]),
            profit=Decimal(row[1]).quantize(Decimal("0.01")),
        )
        for row in channel_rows
    ]

    obs_rows = db.execute(
        select(Product.id, Product.current_price, CompetitorPrice.listed_price)
        .join(Product, CompetitorPrice.product_id == Product.id)
        .where(
            CompetitorPrice.is_outlier.is_(False),
            CompetitorPrice.listed_price > 0,
        )
        .order_by(CompetitorPrice.observed_at.desc())
    ).all()

    seen_products: set[UUID] = set()
    lower = 0
    equal = 0
    higher = 0
    threshold = Decimal("0.02")
    for prod_id, current_price, listed_price in obs_rows:
        if prod_id in seen_products:
            continue
        seen_products.add(prod_id)
        gap = (Decimal(current_price) - Decimal(listed_price)) / Decimal(listed_price)
        if gap < -threshold:
            lower += 1
        elif gap > threshold:
            higher += 1
        else:
            equal += 1

    price_vs_competitor = [
        PricePositionBucket(bucket="Thấp hơn", count=lower),
        PricePositionBucket(bucket="Tương đương", count=equal),
        PricePositionBucket(bucket="Cao hơn", count=higher),
    ]

    return Envelope(
        data=DashboardSummaryRead(
            revenue=revenue,
            gross_profit=gross_profit,
            margin=margin,
            skus_below_floor=skus_below_floor,
            low_stock_count=low_stock_count,
            pending_approvals=pending_approvals,
            revenue_trend=revenue_trend,
            profit_by_channel=profit_by_channel,
            price_vs_competitor=price_vs_competitor,
        )
    )

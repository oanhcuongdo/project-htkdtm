from collections import defaultdict
from typing import Any, Dict, List
from supabase import Client

from src.backend.api.schemas.bi import (
    DistrictPriceStat,
    LiquidityDistrictStat,
    MarketBIOverviewResponse,
    MonthlyTrendStat,
    PriceSegmentStat,
    PropertyTypeStat,
)

SEGMENT_LABELS = {
    "binh_dan": "Bình dân (< 3tr)",
    "trung_cap": "Trung cấp (3 - 6tr)",
    "cao_cap": "Cao cấp (> 6tr)",
}


def get_market_bi_overview(db: Client) -> MarketBIOverviewResponse:
    """
    Tổng hợp 3 nhóm Insight BI từ view_rental_market_analytics trên Supabase:
    1. Mặt bằng giá thuê & đơn giá/m² theo quận/huyện, loại hình phòng.
    2. Cơ cấu nguồn cung theo quận/huyện & phân khúc giá.
    3. Biến động giá theo thời gian & độ thanh khoản (days_on_market).
    """
    res = (
        db.table("view_rental_market_analytics")
        .select(
            "district, type_name, price, price_per_m2, price_segment, "
            "is_active, is_duplicate, room_status, days_on_market, month, year"
        )
        .eq("is_duplicate", False)
        .limit(1000)
        .execute()
    )
    rows: List[Dict[str, Any]] = res.data or []

    active_rows = [r for r in rows if r.get("is_active", True)]

    dist_prices: Dict[str, List[float]] = defaultdict(list)
    dist_ppm2: Dict[str, List[float]] = defaultdict(list)
    dist_counts: Dict[str, int] = defaultdict(int)

    type_prices: Dict[str, List[float]] = defaultdict(list)
    type_ppm2: Dict[str, List[float]] = defaultdict(list)
    type_counts: Dict[str, int] = defaultdict(int)

    seg_counts: Dict[str, int] = defaultdict(int)

    month_prices: Dict[str, List[float]] = defaultdict(list)
    month_ppm2: Dict[str, List[float]] = defaultdict(list)
    month_counts: Dict[str, int] = defaultdict(int)

    liq_days: Dict[str, List[float]] = defaultdict(list)
    liq_active: Dict[str, int] = defaultdict(int)
    liq_closed: Dict[str, int] = defaultdict(int)

    all_prices: List[float] = []
    all_ppm2: List[float] = []
    all_dom: List[float] = []

    for r in rows:
        dist = r.get("district") or "Khác"
        dom = r.get("days_on_market")
        is_act = bool(r.get("is_active", True))
        if is_act:
            liq_active[dist] += 1
        else:
            liq_closed[dist] += 1

        if dom is not None and float(dom) >= 0:
            liq_days[dist].append(float(dom))
            all_dom.append(float(dom))

    for r in active_rows:
        dist = r.get("district") or "Khác"
        ptype = r.get("type_name") or "Phòng trọ"
        seg = r.get("price_segment") or "trung_cap"
        price = float(r.get("price") or 0)
        ppm2 = float(r.get("price_per_m2") or 0)

        dist_counts[dist] += 1
        type_counts[ptype] += 1
        seg_counts[seg] += 1

        if price > 0:
            all_prices.append(price)
            dist_prices[dist].append(price)
            type_prices[ptype].append(price)

        if ppm2 > 0:
            all_ppm2.append(ppm2)
            dist_ppm2[dist].append(ppm2)
            type_ppm2[ptype].append(ppm2)

        yr = r.get("year")
        mo = r.get("month")
        if yr and mo:
            period = f"{int(yr):04d}-{int(mo):02d}"
            month_counts[period] += 1
            if price > 0:
                month_prices[period].append(price)
            if ppm2 > 0:
                month_ppm2[period].append(ppm2)

    price_by_district = [
        DistrictPriceStat(
            district=d,
            avg_price=round(sum(dist_prices[d]) / len(dist_prices[d])) if dist_prices[d] else 0.0,
            avg_price_per_m2=round(sum(dist_ppm2[d]) / len(dist_ppm2[d])) if dist_ppm2[d] else 0.0,
            listing_count=cnt,
        )
        for d, cnt in sorted(dist_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    price_by_property_type = [
        PropertyTypeStat(
            type_name=t,
            avg_price=round(sum(type_prices[t]) / len(type_prices[t])) if type_prices[t] else 0.0,
            avg_price_per_m2=round(sum(type_ppm2[t]) / len(type_ppm2[t])) if type_ppm2[t] else 0.0,
            listing_count=cnt,
        )
        for t, cnt in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    ]

    supply_by_segment = [
        PriceSegmentStat(
            segment=s,
            label=SEGMENT_LABELS.get(s, s),
            listing_count=cnt,
        )
        for s, cnt in seg_counts.items()
    ]

    trend_by_month = [
        MonthlyTrendStat(
            period=p,
            avg_price=round(sum(month_prices[p]) / len(month_prices[p])) if month_prices[p] else 0.0,
            avg_price_per_m2=round(sum(month_ppm2[p]) / len(month_ppm2[p])) if month_ppm2[p] else 0.0,
            listing_count=month_counts[p],
        )
        for p in sorted(month_counts.keys())
    ]

    liquidity_by_district = [
        LiquidityDistrictStat(
            district=d,
            avg_days_on_market=round(sum(liq_days[d]) / len(liq_days[d]), 1) if liq_days[d] else 0.0,
            active_count=liq_active[d],
            closed_count=liq_closed[d],
        )
        for d in sorted(dist_counts.keys(), key=lambda x: dist_counts[x], reverse=True)[:10]
    ]

    return MarketBIOverviewResponse(
        total_active_listings=len(active_rows),
        total_districts=len(dist_counts),
        avg_price=round(sum(all_prices) / len(all_prices)) if all_prices else 0.0,
        avg_price_per_m2=round(sum(all_ppm2) / len(all_ppm2)) if all_ppm2 else 0.0,
        avg_days_on_market=round(sum(all_dom) / len(all_dom), 1) if all_dom else None,
        price_by_district=price_by_district,
        price_by_property_type=price_by_property_type,
        supply_by_segment=supply_by_segment,
        trend_by_month=trend_by_month,
        liquidity_by_district=liquidity_by_district,
    )

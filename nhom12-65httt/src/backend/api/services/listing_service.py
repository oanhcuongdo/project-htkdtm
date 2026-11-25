import datetime
import math
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from supabase import Client

from src.backend.api.dependencies import validate_uuid
from src.backend.api.schemas.listing import (
    CompareResponse,
    DistrictStatDTO,
    ListingCardDTO,
    ListingDetailDTO,
    ListingListResponse,
)
from src.backend.scraper.osm_service import haversine_distance

FACT_EMBEDDED_SELECT = (
    "*, dim_time(*), dim_location(*), dim_property_type(*), dim_amenities(*), dim_landlord(*)"
)


def _compute_days_on_market(row: Dict[str, Any]) -> Optional[float]:
    orig_raw = row.get("orig_published_at")
    if not orig_raw:
        return None
    try:
        start = datetime.datetime.fromisoformat(str(orig_raw).replace("Z", "+00:00"))
        end_raw = row.get("closed_at")
        end = (
            datetime.datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
            if end_raw
            else datetime.datetime.now(datetime.timezone.utc)
        )
        return round(max(0.0, (end - start).total_seconds() / 86400.0), 2)
    except Exception:
        return None


def flatten_fact_row(row: Dict[str, Any], include_detail: bool = False) -> Dict[str, Any]:
    """Làm phẳng bản ghi fact_rental_listings kèm các bảng Dimension liên kết."""
    loc = row.get("dim_location") or {}
    pt = row.get("dim_property_type") or {}
    am = row.get("dim_amenities") or {}
    ll = row.get("dim_landlord") or {}

    base = {
        "fact_id": str(row["fact_id"]),
        "source": row.get("source") or "",
        "external_id": str(row.get("external_id") or ""),
        "title": row.get("title") or "",
        "original_url": row.get("original_url"),
        "images": row.get("images") or [],
        "videos": row.get("videos") or [],
        "price": float(row.get("price") or 0),
        "original_price": float(row["original_price"]) if row.get("original_price") is not None else None,
        "area": float(row["area"]) if row.get("area") is not None else None,
        "price_per_m2": float(row["price_per_m2"]) if row.get("price_per_m2") is not None else None,
        "estimated_total_cost": float(row["estimated_total_cost"]) if row.get("estimated_total_cost") is not None else None,
        "price_diff_rate": float(row.get("price_diff_rate") or 0.0),
        "price_segment": row.get("price_segment") or "trung_cap",
        "risk_score": float(row.get("risk_score") or 0.0),
        "completeness_score": float(row.get("completeness_score") or 0.0),
        "is_active": bool(row.get("is_active", True)),
        "is_promoted": bool(row.get("is_promoted", False)),
        "room_status": row.get("room_status") or "con_trong",
        "view_count": int(row.get("view_count") or 0),
        "wishlist_count": int(row.get("wishlist_count") or 0),
        "district": loc.get("district") or "",
        "ward": loc.get("ward") or "",
        "street": loc.get("street") or "",
        "latitude": float(loc["latitude"]) if loc.get("latitude") is not None else None,
        "longitude": float(loc["longitude"]) if loc.get("longitude") is not None else None,
        "nearest_university": loc.get("nearest_university"),
        "distance_to_university_km": (
            float(loc["distance_to_university_km"]) if loc.get("distance_to_university_km") is not None else None
        ),
        "distance_to_target_km": row.get("distance_to_target_km"),
        "type_code": pt.get("type_code") or "phong_tro",
        "type_name": pt.get("type_name") or "Phòng trọ / Nhà trọ",
        "poster_name": ll.get("poster_name") or "Chính chủ",
        "poster_type": ll.get("poster_type") or "unknown",
        "landlord_trust_score": float(ll.get("trust_score") or 5.0),
        "is_verified_seller": bool(ll.get("is_verified_seller", False)),
        "has_air_conditioner": bool(am.get("has_air_conditioner", False)),
        "has_water_heater": bool(am.get("has_water_heater", False)),
        "has_washing_machine": bool(am.get("has_washing_machine", False)),
        "has_private_bathroom": bool(am.get("has_private_bathroom", False)),
        "has_elevator": bool(am.get("has_elevator", False)),
        "has_flexible_hours": bool(am.get("has_flexible_hours", False)),
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
    }

    if include_detail:
        base.update({
            "description": row.get("description"),
            "deposit_amount": float(row.get("deposit_amount") or 0.0),
            "electricity_cost": float(row["electricity_cost"]) if row.get("electricity_cost") is not None else None,
            "water_cost": float(row["water_cost"]) if row.get("water_cost") is not None else None,
            "service_cost": float(row.get("service_cost") or 0.0),
            "extraction_source": row.get("extraction_source") or "regex",
            "orig_published_at": str(row["orig_published_at"]) if row.get("orig_published_at") else None,
            "last_bumped_at": str(row["last_bumped_at"]) if row.get("last_bumped_at") else None,
            "closed_at": str(row["closed_at"]) if row.get("closed_at") else None,
            "days_on_market": _compute_days_on_market(row),
            "phone_masked": ll.get("phone_masked"),
            "sold_ads_count": int(ll.get("sold_ads_count") or 0),
            "has_refrigerator": bool(am.get("has_refrigerator", False)),
            "has_kitchen": bool(am.get("has_kitchen", False)),
            "has_balcony": bool(am.get("has_balcony", False)),
            "has_parking": bool(am.get("has_parking", False)),
            "has_security": bool(am.get("has_security", False)),
            "has_mezzanine": bool(am.get("has_mezzanine", False)),
            "raw_amenities": am.get("raw_amenities") or [],
        })
    return base


def _matches_filters(
    item: Dict[str, Any],
    q: Optional[str],
    district: Optional[str],
    ward: Optional[str],
    property_type: Optional[str],
    amenity_keys: List[str],
    lat: Optional[float],
    lon: Optional[float],
    radius_km: Optional[float],
) -> bool:
    if q:
        q_low = q.lower().strip()
        haystack = f"{item['title']} {item['district']} {item['ward']} {item['street']}".lower()
        if q_low not in haystack:
            return False

    if district and district.lower() not in item["district"].lower():
        return False
    if ward and ward.lower() not in item["ward"].lower():
        return False
    if property_type and item["type_code"] != property_type:
        return False

    for am_key in amenity_keys:
        col_name = am_key if am_key.startswith("has_") else f"has_{am_key}"
        if not item.get(col_name):
            return False

    if lat is not None and lon is not None and radius_km is not None:
        if item["latitude"] is None or item["longitude"] is None:
            return False
        dist = haversine_distance(lat, lon, item["latitude"], item["longitude"])
        item["distance_to_target_km"] = dist
        if dist > radius_km:
            return False

    return True


def _sort_items(items: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
    if sort_by == "price_asc":
        return sorted(items, key=lambda x: x["price"])
    if sort_by == "price_desc":
        return sorted(items, key=lambda x: x["price"], reverse=True)
    if sort_by == "total_cost_asc":
        return sorted(items, key=lambda x: x["estimated_total_cost"] or x["price"])
    if sort_by == "price_per_m2_asc":
        return sorted(items, key=lambda x: x["price_per_m2"] if x["price_per_m2"] is not None else float("inf"))
    if sort_by == "trust_desc":
        return sorted(items, key=lambda x: (x["risk_score"], -x["completeness_score"]))
    if sort_by == "distance_asc":
        return sorted(items, key=lambda x: x["distance_to_target_km"] if x["distance_to_target_km"] is not None else float("inf"))
    return sorted(items, key=lambda x: x["created_at"] or "", reverse=True)


def list_listings(
    db: Client,
    q: Optional[str] = None,
    district: Optional[str] = None,
    ward: Optional[str] = None,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    amenities: Optional[str] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    radius_km: Optional[float] = None,
    sort_by: str = "newest",
    page: int = 1,
    limit: int = 20,
) -> ListingListResponse:
    """Truy vấn danh sách phòng trọ hợp lệ kèm lọc đa tiêu chí, bán kính Haversine và phân trang."""
    query = (
        db.table("fact_rental_listings")
        .select(FACT_EMBEDDED_SELECT)
        .eq("is_active", True)
        .eq("is_duplicate", False)
    )
    if min_price is not None:
        query = query.gte("price", min_price)
    if max_price is not None:
        query = query.lte("price", max_price)
    if min_area is not None:
        query = query.gte("area", min_area)
    if max_area is not None:
        query = query.lte("area", max_area)

    rows: List[Dict[str, Any]] = []
    batch_size = 1000
    offset = 0
    while True:
        batch = query.range(offset, offset + batch_size - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size

    amenity_keys = [a.strip() for a in (amenities or "").split(",") if a.strip()]

    filtered: List[Dict[str, Any]] = []
    for row in rows:
        flat = flatten_fact_row(row, include_detail=bool(amenity_keys))
        if _matches_filters(flat, q, district, ward, property_type, amenity_keys, lat, lon, radius_km):
            filtered.append(flat)

    sorted_items = _sort_items(filtered, sort_by)
    total = len(sorted_items)
    total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1
    start = (page - 1) * limit
    page_items = [ListingCardDTO(**item) for item in sorted_items[start : start + limit]]

    return ListingListResponse(
        items=page_items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


def get_listing_detail(db: Client, fact_id: str) -> ListingDetailDTO:
    """Lấy chi tiết 1 phòng trọ theo fact_id."""
    clean_id = validate_uuid(fact_id, "fact_id")
    res = (
        db.table("fact_rental_listings")
        .select(FACT_EMBEDDED_SELECT)
        .eq("fact_id", clean_id)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phòng trọ yêu cầu.")
    return ListingDetailDTO(**flatten_fact_row(res.data[0], include_detail=True))


def compare_listings(db: Client, ids: List[str]) -> CompareResponse:
    """So sánh 2 đến 3 phòng trọ theo danh sách fact_id."""
    clean_ids = [validate_uuid(i, "ids") for i in ids if i.strip()][:3]
    if len(clean_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần tối thiểu 2 mã phòng (fact_id) để so sánh.",
        )
    res = (
        db.table("fact_rental_listings")
        .select(FACT_EMBEDDED_SELECT)
        .in_("fact_id", clean_ids)
        .execute()
    )
    by_id = {str(r["fact_id"]): ListingDetailDTO(**flatten_fact_row(r, include_detail=True)) for r in (res.data or [])}
    ordered = [by_id[fid] for fid in clean_ids if fid in by_id]
    return CompareResponse(items=ordered)


def get_district_stats(db: Client) -> List[DistrictStatDTO]:
    """Thống kê mặt bằng giá, số lượng tin và rủi ro trung bình theo từng quận/huyện."""
    rows = (
        db.table("view_rental_market_analytics")
        .select("district, price, price_per_m2, risk_score, latitude, longitude")
        .eq("is_active", True)
        .eq("is_duplicate", False)
        .execute()
        .data
        or []
    )
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r.get("district"):
            grouped[r["district"]].append(r)

    stats: List[DistrictStatDTO] = []
    for dist, items in grouped.items():
        prices = [float(x["price"]) for x in items if x.get("price")]
        ppm2 = [float(x["price_per_m2"]) for x in items if x.get("price_per_m2")]
        risks = [float(x.get("risk_score") or 0) for x in items]
        lats = [float(x["latitude"]) for x in items if x.get("latitude") is not None]
        lons = [float(x["longitude"]) for x in items if x.get("longitude") is not None]
        if not prices:
            continue
        stats.append(
            DistrictStatDTO(
                district=dist,
                listing_count=len(items),
                avg_price=round(sum(prices) / len(prices), 0),
                avg_price_per_m2=round(sum(ppm2) / len(ppm2), 0) if ppm2 else None,
                min_price=min(prices),
                max_price=max(prices),
                avg_risk_score=round(sum(risks) / len(risks), 2) if risks else 0.0,
                latitude=round(sum(lats) / len(lats), 6) if lats else None,
                longitude=round(sum(lons) / len(lons), 6) if lons else None,
            )
        )
    return sorted(stats, key=lambda s: s.listing_count, reverse=True)

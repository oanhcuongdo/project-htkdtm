import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from supabase import Client

from src.backend.api.schemas.admin_bi import (
    AnomalyListResponse,
    AnomalyListingDTO,
    AnomalyRecalculateResponse,
    AnomalySummaryDTO,
)
from src.backend.etl.cleaner import (
    SPAM_PATTERNS,
    calculate_completeness_score,
    calculate_risk_score,
    compute_price_diff_rate,
)

logger = logging.getLogger(__name__)


def classify_risk_level(risk_score: float) -> str:
    """Phân loại mức độ rủi ro tin đăng dựa trên điểm risk_score (0 - 100)."""
    if risk_score >= 50.0:
        return "high"
    if risk_score >= 25.0:
        return "medium"
    return "low"


def extract_risk_flags(
    price: float,
    area: Optional[float],
    title: str,
    desc: str,
    price_diff_rate: float = 0.0,
    is_promoted: bool = False,
    completeness_score: float = 100.0,
    report_count: int = 0,
) -> List[str]:
    """Liệt kê các dấu hiệu bất thường cụ thể phục vụ giải thích cho Admin."""
    flags: List[str] = []
    combined = f"{title} {desc}".lower()

    if price > 0 and price < 1_200_000 and any(k in combined for k in ["chung cư", "studio", "full đồ"]):
        flags.append("Giá quá thấp so với mô tả cao cấp (nghi ngờ tin mồi)")
    elif price > 0 and price < 800_000:
        flags.append("Giá thuê thấp bất thường (< 800.000đ/tháng)")

    if price_diff_rate <= -35.0:
        flags.append(f"Đơn giá/m² thấp hơn {abs(price_diff_rate):.1f}% so với mặt bằng khu vực")
    elif price_diff_rate <= -25.0:
        flags.append(f"Đơn giá/m² thấp hơn {abs(price_diff_rate):.1f}% so với khu vực")
    elif price_diff_rate >= 100.0:
        flags.append(f"Đơn giá/m² cao đột biến (+{price_diff_rate:.1f}% so với khu vực)")

    if not area or area <= 0:
        flags.append("Thiếu thông tin diện tích")
    elif area < 8 or area > 150:
        flags.append(f"Diện tích bất thường ({area:.1f} m²)")

    if any(k in combined for k in SPAM_PATTERNS):
        flags.append("Tiêu đề/mô tả chứa từ khóa câu khách")

    if is_promoted and not area:
        flags.append("Tin đẩy quảng cáo nhưng thiếu diện tích")

    if completeness_score < 50.0:
        flags.append(f"Độ đầy đủ thông tin thấp ({completeness_score:.0f}/100)")

    if report_count > 0:
        flags.append(f"Có {report_count} báo cáo vi phạm từ người dùng")

    return flags


def analyze_listing_anomaly(
    row: Dict[str, Any],
    avg_price_per_m2: Optional[float],
    report_count: int = 0,
) -> Dict[str, Any]:
    """
    Tính toán đồng bộ completeness_score, price_diff_rate, risk_score và danh sách risk_flags
    cho một bản ghi tin đăng.
    """
    price = float(row.get("price") or 0)
    area_raw = row.get("area")
    area = float(area_raw) if area_raw is not None else None
    title = row.get("title") or ""
    desc = row.get("description") or ""
    is_promoted = bool(row.get("is_promoted"))

    price_per_m2 = row.get("price_per_m2")
    if price_per_m2 is None and price > 0 and area and area > 0:
        price_per_m2 = round(price / area, 2)
    else:
        price_per_m2 = float(price_per_m2) if price_per_m2 is not None else None

    loc = row.get("dim_location") or {}
    district = row.get("district") or loc.get("district") or ""

    completeness_score = calculate_completeness_score({
        "title": title,
        "price": price,
        "area": area,
        "district": district,
        "description": desc,
        "images": row.get("images") or [],
        "electricity_cost": row.get("electricity_cost"),
        "water_cost": row.get("water_cost"),
        "deposit_amount": row.get("deposit_amount"),
    })

    price_diff_rate = compute_price_diff_rate(price_per_m2, avg_price_per_m2)
    base_risk = calculate_risk_score(
        price=price,
        area=area or 0.0,
        title=title,
        desc=desc,
        price_diff_rate=price_diff_rate,
        is_promoted=is_promoted,
    )

    # Cộng thêm trọng số rủi ro nếu thông tin quá sơ sài hoặc đã bị người dùng báo cáo
    extra_risk = 0.0
    if completeness_score < 50.0:
        extra_risk += 10.0
    if report_count > 0:
        extra_risk += min(25.0, report_count * 10.0)

    risk_score = min(100.0, round(base_risk + extra_risk, 2))
    flags = extract_risk_flags(
        price=price,
        area=area,
        title=title,
        desc=desc,
        price_diff_rate=price_diff_rate,
        is_promoted=is_promoted,
        completeness_score=completeness_score,
        report_count=report_count,
    )

    return {
        "completeness_score": round(completeness_score, 2),
        "price_diff_rate": price_diff_rate,
        "risk_score": risk_score,
        "risk_level": classify_risk_level(risk_score),
        "risk_flags": flags,
        "price_per_m2": price_per_m2,
    }


def _fetch_report_counts(db: Client) -> Dict[str, int]:
    """Đếm số báo cáo vi phạm theo từng fact_id."""
    counts: Dict[str, int] = defaultdict(int)
    res = db.table("listing_reports").select("fact_id").execute()
    for r in res.data or []:
        fid = str(r.get("fact_id") or "")
        if fid:
            counts[fid] += 1
    return counts


def _compute_area_benchmarks(rows: List[Dict[str, Any]]) -> Tuple[Dict[Tuple[str, Any], float], Dict[str, float]]:
    """
    Tính đơn giá/m² trung bình theo cặp (quận, loại phòng) và fallback theo quận.
    Chỉ tính trên các tin không trùng lặp và có diện tích hợp lệ.
    """
    group_prices: Dict[Tuple[str, Any], List[float]] = defaultdict(list)
    district_prices: Dict[str, List[float]] = defaultdict(list)

    for r in rows:
        if r.get("is_duplicate"):
            continue
        ppm2 = r.get("price_per_m2")
        if not ppm2 or float(ppm2) <= 0:
            continue
        loc = r.get("dim_location") or {}
        district = loc.get("district") or ""
        ptype = r.get("property_type_id")
        if district:
            group_prices[(district, ptype)].append(float(ppm2))
            district_prices[district].append(float(ppm2))

    group_avg = {k: sum(v) / len(v) for k, v in group_prices.items() if len(v) >= 2}
    district_avg = {k: sum(v) / len(v) for k, v in district_prices.items() if v}
    return group_avg, district_avg


def recalculate_market_anomalies(db: Client) -> AnomalyRecalculateResponse:
    """
    Quét toàn bộ bảng fact_rental_listings, tính lại completeness_score, price_diff_rate,
    risk_score và cập nhật về Supabase.
    """
    res = (
        db.table("fact_rental_listings")
        .select(
            "fact_id, title, description, price, area, price_per_m2, deposit_amount, "
            "electricity_cost, water_cost, images, is_promoted, is_duplicate, property_type_id, "
            "dim_location(district)"
        )
        .execute()
    )
    rows = res.data or []
    if not rows:
        return AnomalyRecalculateResponse(
            updated_count=0,
            high_risk_count=0,
            medium_risk_count=0,
            low_risk_count=0,
            avg_completeness_score=0.0,
            message="Chưa có dữ liệu tin đăng để phân tích.",
        )

    report_counts = _fetch_report_counts(db)
    group_avg, district_avg = _compute_area_benchmarks(rows)

    updated = 0
    high_cnt = 0
    med_cnt = 0
    low_cnt = 0
    comp_total = 0.0

    for r in rows:
        fid = str(r["fact_id"])
        loc = r.get("dim_location") or {}
        district = loc.get("district") or ""
        ptype = r.get("property_type_id")
        avg_ppm2 = group_avg.get((district, ptype)) or district_avg.get(district)

        metrics = analyze_listing_anomaly(r, avg_ppm2, report_count=report_counts.get(fid, 0))
        comp_total += metrics["completeness_score"]

        if metrics["risk_level"] == "high":
            high_cnt += 1
        elif metrics["risk_level"] == "medium":
            med_cnt += 1
        else:
            low_cnt += 1

        try:
            db.table("fact_rental_listings").update({
                "completeness_score": metrics["completeness_score"],
                "price_diff_rate": metrics["price_diff_rate"],
                "risk_score": metrics["risk_score"],
            }).eq("fact_id", fid).execute()
            updated += 1
        except Exception as e:
            logger.warning("Không thể cập nhật anomaly metrics cho %s: %s", fid, e)

    avg_comp = round(comp_total / len(rows), 2)
    return AnomalyRecalculateResponse(
        updated_count=updated,
        high_risk_count=high_cnt,
        medium_risk_count=med_cnt,
        low_risk_count=low_cnt,
        avg_completeness_score=avg_comp,
        message=f"Đã rà soát và cập nhật chỉ số bất thường cho {updated} tin đăng.",
    )


def list_market_anomalies(
    db: Client,
    min_risk_score: float = 25.0,
    limit: int = 50,
) -> AnomalyListResponse:
    """Lấy danh sách tin có dấu hiệu bất thường và thống kê tổng quan cho Admin."""
    res = (
        db.table("fact_rental_listings")
        .select(
            "fact_id, title, description, original_url, price, area, price_per_m2, "
            "deposit_amount, electricity_cost, water_cost, images, is_promoted, is_active, "
            "is_duplicate, price_diff_rate, risk_score, completeness_score, property_type_id, "
            "dim_location(district), dim_property_type(type_name)"
        )
        .order("risk_score", desc=True)
        .execute()
    )
    rows = res.data or []
    report_counts = _fetch_report_counts(db)
    group_avg, district_avg = _compute_area_benchmarks(rows)

    high_cnt = 0
    med_cnt = 0
    low_cnt = 0
    comp_sum = 0.0
    risk_sum = 0.0
    items: List[AnomalyListingDTO] = []

    for r in rows:
        fid = str(r["fact_id"])
        loc = r.get("dim_location") or {}
        ptype_obj = r.get("dim_property_type") or {}
        district = loc.get("district") or ""
        ptype = r.get("property_type_id")
        avg_ppm2 = group_avg.get((district, ptype)) or district_avg.get(district)

        rep_cnt = report_counts.get(fid, 0)
        # Dùng score đã lưu nếu có, kết hợp trích xuất risk_flags trực tiếp
        stored_risk = float(r.get("risk_score") or 0.0)
        stored_comp = float(r.get("completeness_score") or 0.0)
        stored_diff = float(r.get("price_diff_rate") or 0.0)

        if stored_risk == 0.0 and stored_comp == 0.0:
            analyzed = analyze_listing_anomaly(r, avg_ppm2, report_count=rep_cnt)
            stored_risk = analyzed["risk_score"]
            stored_comp = analyzed["completeness_score"]
            stored_diff = analyzed["price_diff_rate"]
            flags = analyzed["risk_flags"]
        else:
            flags = extract_risk_flags(
                price=float(r.get("price") or 0),
                area=float(r["area"]) if r.get("area") is not None else None,
                title=r.get("title") or "",
                desc=r.get("description") or "",
                price_diff_rate=stored_diff,
                is_promoted=bool(r.get("is_promoted")),
                completeness_score=stored_comp,
                report_count=rep_cnt,
            )

        level = classify_risk_level(stored_risk)
        if level == "high":
            high_cnt += 1
        elif level == "medium":
            med_cnt += 1
        else:
            low_cnt += 1

        comp_sum += stored_comp
        risk_sum += stored_risk

        if stored_risk >= min_risk_score and len(items) < limit:
            items.append(
                AnomalyListingDTO(
                    fact_id=fid,
                    title=r.get("title") or "",
                    district=district or None,
                    type_name=ptype_obj.get("type_name"),
                    price=float(r.get("price") or 0),
                    area=float(r["area"]) if r.get("area") is not None else None,
                    price_per_m2=float(r["price_per_m2"]) if r.get("price_per_m2") is not None else None,
                    price_diff_rate=stored_diff,
                    completeness_score=stored_comp,
                    risk_score=stored_risk,
                    risk_level=level,
                    risk_flags=flags,
                    report_count=rep_cnt,
                    is_active=bool(r.get("is_active", True)),
                    original_url=r.get("original_url"),
                )
            )

    total = len(rows)
    summary = AnomalySummaryDTO(
        total_listings=total,
        high_risk_count=high_cnt,
        medium_risk_count=med_cnt,
        low_risk_count=low_cnt,
        avg_completeness_score=round(comp_sum / total, 2) if total else 0.0,
        avg_risk_score=round(risk_sum / total, 2) if total else 0.0,
    )
    return AnomalyListResponse(summary=summary, items=items)

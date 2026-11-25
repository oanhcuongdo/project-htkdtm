import datetime
import logging
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from src.backend.database.supabase_client import get_supabase_client
from src.backend.etl.cleaner import (
    HANOI_DISTRICT_COORDS,
    calculate_completeness_score,
    calculate_risk_score,
    compute_price_diff_rate,
    estimate_monthly_total_cost,
    extract_amenities,
    infer_property_type,
    is_valid_listing,
    normalize_district_name,
    normalize_title_for_dedup,
    parse_timestamp_to_dt,
)
from src.backend.etl.gemini_extractor import GeminiRentalExtractor
from src.backend.scraper.osm_service import find_nearest_university

logger = logging.getLogger(__name__)

VN_DAY_NAMES = ["Chủ Nhật", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy"]
VN_MONTH_NAMES = [
    "", "Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6",
    "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12",
]


class ETLPipeline:
    """
    Quy trình ETL: Làm sạch dữ liệu thô từ Staging, bóc tách thông tin bằng Google Gemini/Regex,
    khử trùng lặp đa nguồn, tính toán chỉ số thị trường và nạp Star Schema trên Supabase.
    """

    def __init__(self, use_gemini: bool = True):
        self.client = get_supabase_client()
        self.extractor = GeminiRentalExtractor() if use_gemini else None
        self._property_type_cache: Dict[str, int] = {}
        self._time_cache: set = set()
        self._location_cache: Dict[Tuple[str, str, str], int] = {}
        self._load_caches()

    def _load_caches(self):
        """Tải cache danh mục loại phòng và các mốc thời gian/vị trí đã có."""
        try:
            res = self.client.table("dim_property_type").select("property_type_id, type_code").execute()
            for row in res.data:
                self._property_type_cache[row["type_code"]] = row["property_type_id"]
        except Exception as e:
            logger.error("Không thể tải danh mục property_types: %s", e)

        try:
            res = self.client.table("dim_time").select("time_id").execute()
            self._time_cache = {row["time_id"] for row in res.data}
        except Exception as e:
            logger.warning("Không thể tải cache dim_time: %s", e)

    def _ensure_dim_time(self, target_date: datetime.date) -> int:
        """Đảm bảo ngày tồn tại trong dim_time và trả về time_id (YYYYMMDD)."""
        time_id = int(target_date.strftime("%Y%m%d"))
        if time_id in self._time_cache:
            return time_id

        # Python weekday(): 0=Mon..6=Sun -> SQL: 0=CN, 1=T2..6=T7
        dow = (target_date.weekday() + 1) % 7
        month = target_date.month
        row = {
            "time_id": time_id,
            "full_date": target_date.isoformat(),
            "day_of_week": dow,
            "day_name": VN_DAY_NAMES[dow],
            "day_of_month": target_date.day,
            "month": month,
            "month_name": VN_MONTH_NAMES[month],
            "quarter": (month - 1) // 3 + 1,
            "year": target_date.year,
            "is_weekend": dow in (0, 6),
            "is_peak_student_season": month in (1, 2, 7, 8, 9),
        }
        try:
            self.client.table("dim_time").upsert(row, on_conflict="time_id").execute()
            self._time_cache.add(time_id)
        except Exception as e:
            logger.warning("Không thể upsert dim_time (%s): %s", time_id, e)
        return time_id

    def _get_or_create_location(
        self,
        district: str,
        ward: str,
        street: str,
        lat: Optional[float],
        lon: Optional[float],
    ) -> Optional[int]:
        """Tìm hoặc tạo bản ghi dim_location tránh nhân bản trùng lặp."""
        cache_key = (district, ward, street)
        if cache_key in self._location_cache:
            return self._location_cache[cache_key]

        try:
            q = (
                self.client.table("dim_location")
                .select("location_id")
                .eq("district", district)
                .eq("ward", ward)
                .eq("street", street)
                .limit(1)
                .execute()
            )
            if q.data:
                loc_id = q.data[0]["location_id"]
                self._location_cache[cache_key] = loc_id
                return loc_id
        except Exception:
            pass

        nearest_uni, dist_km = find_nearest_university(lat, lon)
        loc_data = {
            "province": "Hà Nội",
            "district": district,
            "ward": ward,
            "street": street,
            "full_address": ", ".join(p for p in [street, ward, district, "Hà Nội"] if p),
            "latitude": lat,
            "longitude": lon,
            "nearest_university": nearest_uni,
            "distance_to_university_km": dist_km,
        }
        loc_res = self.client.table("dim_location").insert(loc_data).execute()
        if loc_res.data:
            loc_id = loc_res.data[0]["location_id"]
            self._location_cache[cache_key] = loc_id
            return loc_id
        return None

    def save_raw_listings(self, listings: List[Dict[str, Any]]) -> int:
        """Lưu danh sách tin cào thô vào bảng staging_raw_listings theo batch."""
        if not listings:
            return 0

        batch = []
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        for item in listings:
            batch.append({
                "source": item["source"],
                "external_id": str(item["external_id"]),
                "raw_payload": item.get("raw_payload", item),
                "status": "pending",
                "scraped_at": now_iso,
            })

        saved_count = 0
        chunk_size = 50
        for i in range(0, len(batch), chunk_size):
            chunk = batch[i:i + chunk_size]
            try:
                self.client.table("staging_raw_listings").upsert(
                    chunk, on_conflict="source,external_id"
                ).execute()
                saved_count += len(chunk)
            except Exception as e:
                logger.error("Lỗi khi lưu batch staging: %s", e)

        logger.info("Đã lưu %d/%d tin vào bảng staging_raw_listings.", saved_count, len(listings))
        return saved_count

    def _extract_item_from_raw(self, source: str, external_id: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Khôi phục cấu trúc tin chuẩn từ raw_payload đã lưu trong staging_raw_listings."""
        if source == "chotot":
            return {
                "source": source,
                "external_id": external_id,
                "title": (raw.get("subject") or "").strip(),
                "description": (raw.get("body") or "").strip(),
                "original_url": f"https://www.nhatot.com/phong-tro-nha-tro-ha-noi/{external_id}.htm",
                "price": raw.get("price"),
                "original_price": raw.get("original_price"),
                "deposit": raw.get("deposit"),
                "area": raw.get("size"),
                "latitude": raw.get("latitude"),
                "longitude": raw.get("longitude"),
                "district": raw.get("area_name"),
                "ward": raw.get("ward_name") or "",
                "street": raw.get("street_name") or "",
                "images": raw.get("images", []),
                "videos": raw.get("videos", []),
                "poster_name": raw.get("account_name"),
                "poster_id": str(raw.get("account_id") or ""),
                "poster_type": "moi_gioi" if raw.get("company_ad") else "chinh_chu",
                "sold_ads_count": raw.get("sold_ads") or 0,
                "is_verified_seller": bool(raw.get("is_shop_verified")),
                "is_promoted": bool(
                    raw.get("is_sticky") or raw.get("sticky_ad_platinum") or raw.get("special_display")
                ),
                "orig_published_at": raw.get("orig_list_time"),
                "published_at": raw.get("list_time"),
            }

        # Phongtro123
        ld = raw.get("ld_json") or {}
        detail_addr = raw.get("detail_address") or {}
        price_val = None
        if ld.get("priceRange"):
            try:
                price_val = float(ld["priceRange"])
            except (TypeError, ValueError):
                pass
        desc = raw.get("detail_description") or ld.get("description") or ""
        images = raw.get("detail_images") or ([ld["image"]] if ld.get("image") else [])
        addr_obj = ld.get("address") if isinstance(ld.get("address"), dict) else {}
        return {
            "source": source,
            "external_id": external_id,
            "title": (ld.get("name") or "").strip(),
            "description": desc.strip(),
            "original_url": ld.get("url") or "",
            "price": price_val,
            "area": None,
            "district": detail_addr.get("district") or "",
            "ward": detail_addr.get("ward") or "",
            "street": detail_addr.get("street") or addr_obj.get("streetAddress") or "",
            "images": images,
            "videos": [],
            "phone": ld.get("telephone") or "",
            "poster_type": "unknown",
            "is_promoted": False,
        }

    def _build_dedup_index(self) -> Tuple[Dict[Tuple[str, str, int], str], Dict[Tuple[str, str], str]]:
        """Tải danh sách tin chuẩn hiện có để phát hiện trùng lặp đa nguồn."""
        by_title_loc: Dict[Tuple[str, str, int], str] = {}
        by_phone_price: Dict[Tuple[str, str], str] = {}
        try:
            res = (
                self.client.table("fact_rental_listings")
                .select("fact_id, title, price, is_duplicate, dim_location(district), dim_landlord(phone_masked)")
                .eq("is_duplicate", False)
                .execute()
            )
            for r in res.data:
                fid = r["fact_id"]
                loc = r.get("dim_location") or {}
                ll = r.get("dim_landlord") or {}
                dist = loc.get("district") or ""
                norm_t = normalize_title_for_dedup(r.get("title") or "")
                price_bucket = int(round(float(r.get("price") or 0) / 100_000))
                if norm_t and dist:
                    by_title_loc[(norm_t, dist, price_bucket)] = fid
                phone = (ll.get("phone_masked") or "").strip()
                if phone and dist:
                    by_phone_price[(phone, f"{dist}_{price_bucket}")] = fid
        except Exception as e:
            logger.warning("Không thể dựng index khử trùng lặp: %s", e)
        return by_title_loc, by_phone_price

    def _extract_fees_and_amenities(self, item: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Kết hợp dữ liệu API có sẵn + Google Gemini/Regex để bóc tách phí và tiện nghi."""
        title = item.get("title", "")
        desc = item.get("description", "")
        price = float(item.get("price") or 0.0)

        llm_data = self.extractor.extract(title, desc, price) if self.extractor else {}
        if not llm_data:
            from src.backend.etl.gemini_extractor import extract_fees_regex
            llm_data = extract_fees_regex(title, desc, price)
            llm_data["extraction_source"] = "regex"

        api_deposit = item.get("deposit")
        deposit_amount = float(api_deposit) if api_deposit is not None and float(api_deposit) > 0 else llm_data.get("deposit_amount")
        if deposit_amount is None:
            deposit_amount = 0.0

        extraction_source = llm_data.get("extraction_source", "regex")
        if api_deposit and extraction_source == "regex":
            extraction_source = "api"

        fees = {
            "deposit_amount": deposit_amount,
            "electricity_cost": llm_data.get("electricity_cost"),
            "water_cost": llm_data.get("water_cost"),
            "service_cost": llm_data.get("service_cost") if llm_data.get("service_cost") is not None else 0.0,
            "room_status": llm_data.get("room_status", "con_trong"),
            "extraction_source": extraction_source,
        }
        amenities = extract_amenities(title, desc, llm_data)
        return fees, amenities

    def process_and_load_star_schema(self, listings: List[Dict[str, Any]]) -> int:
        """
        Kiểm tra hợp lệ, khử trùng lặp, bóc tách AI/Regex và nạp vào Star Schema.
        """
        loaded_count = 0
        invalid_count = 0
        dedup_count = 0

        existing_facts = set()
        try:
            res = self.client.table("fact_rental_listings").select("source, external_id").execute()
            for r in res.data:
                existing_facts.add((r["source"], str(r["external_id"])))
        except Exception as e:
            logger.warning("Không thể tải danh sách fact đã tồn tại: %s", e)

        by_title_loc, by_phone_price = self._build_dedup_index()

        for item in listings:
            source = item["source"]
            external_id = str(item["external_id"])

            if (source, external_id) in existing_facts:
                continue

            valid, reason = is_valid_listing(item)
            if not valid:
                invalid_count += 1
                self.client.table("staging_raw_listings").update({
                    "status": "failed",
                    "error_message": reason,
                    "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }).eq("source", source).eq("external_id", external_id).execute()
                continue

            try:
                title = item.get("title", "")
                desc = item.get("description", "")
                price = float(item.get("price") or 0.0)
                area = float(item["area"]) if item.get("area") else None
                original_price = float(item["original_price"]) if item.get("original_price") else None

                # 1. Thời gian (dim_time)
                orig_dt = parse_timestamp_to_dt(item.get("orig_published_at") or item.get("published_at"))
                bump_dt = parse_timestamp_to_dt(item.get("published_at"))
                target_date = (orig_dt or bump_dt or datetime.datetime.now(datetime.timezone.utc)).date()
                time_id = self._ensure_dim_time(target_date)

                # 2. Vị trí (dim_location)
                district = normalize_district_name(item.get("district", ""))
                ward = item.get("ward") or ""
                street = item.get("street") or ""
                lat = item.get("latitude")
                lon = item.get("longitude")
                if (lat is None or lon is None) and district in HANOI_DISTRICT_COORDS:
                    lat, lon = HANOI_DISTRICT_COORDS[district]
                location_id = self._get_or_create_location(district, ward, street, lat, lon)

                # 3. Loại hình & Tiện ích & Phí
                type_code = infer_property_type(title, desc)
                property_type_id = self._property_type_cache.get(type_code, 1)

                fees, amenities_data = self._extract_fees_and_amenities(item)
                amenities_res = self.client.table("dim_amenities").insert(amenities_data).execute()
                amenity_id = amenities_res.data[0]["amenity_id"] if amenities_res.data else None

                # 4. Người đăng (dim_landlord)
                poster_name = item.get("poster_name") or "Chính chủ"
                phone_raw = item.get("phone") or ""
                phone_masked = phone_raw[:4] + "***" + phone_raw[-3:] if len(phone_raw) >= 7 else phone_raw
                poster_code = f"{source}_{item.get('poster_id') or hash(phone_masked or poster_name) % 1000000}"
                poster_type = item.get("poster_type", "unknown")
                sold_ads_count = int(item.get("sold_ads_count") or 0)
                is_verified_seller = bool(item.get("is_verified_seller"))
                trust_score = 8.0 if is_verified_seller else (7.5 if poster_type == "chinh_chu" else 5.0)

                landlord_data = {
                    "poster_code": poster_code,
                    "poster_name": poster_name,
                    "phone_masked": phone_masked,
                    "poster_type": poster_type,
                    "total_listings": 1,
                    "sold_ads_count": sold_ads_count,
                    "is_verified_seller": is_verified_seller,
                    "trust_score": trust_score,
                }
                landlord_res = self.client.table("dim_landlord").upsert(
                    landlord_data, on_conflict="poster_code"
                ).execute()
                landlord_id = landlord_res.data[0]["landlord_id"] if landlord_res.data else None

                # 5. Khử trùng lặp đa nguồn
                norm_title = normalize_title_for_dedup(title)
                price_bucket = int(round(price / 100_000))
                matched_fact_id = by_title_loc.get((norm_title, district, price_bucket))
                if not matched_fact_id and phone_masked:
                    matched_fact_id = by_phone_price.get((phone_masked, f"{district}_{price_bucket}"))

                is_duplicate = matched_fact_id is not None
                duplicate_group_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, matched_fact_id)) if matched_fact_id else None
                if is_duplicate:
                    dedup_count += 1

                # 6. Metrics kinh doanh
                price_per_m2 = round(price / area, 2) if (area and area > 0 and price > 0) else None
                estimated_total_cost = estimate_monthly_total_cost(
                    price, fees["electricity_cost"], fees["water_cost"], fees["service_cost"]
                )
                price_segment = "binh_dan" if price < 3_000_000 else ("trung_cap" if price <= 6_000_000 else "cao_cap")
                is_promoted = bool(item.get("is_promoted"))

                risk_score = calculate_risk_score(price, area or 0, title, desc, 0.0, is_promoted)
                completeness_score = calculate_completeness_score({
                    "title": title, "price": price, "area": area,
                    "district": district, "description": desc,
                    "images": item.get("images", []),
                    "electricity_cost": fees["electricity_cost"],
                    "water_cost": fees["water_cost"],
                    "deposit_amount": fees["deposit_amount"],
                })

                fact_payload = {
                    "source": source,
                    "external_id": external_id,
                    "title": title,
                    "description": desc,
                    "original_url": item.get("original_url", ""),
                    "images": item.get("images", []),
                    "videos": item.get("videos", []),
                    "time_id": time_id,
                    "location_id": location_id,
                    "property_type_id": property_type_id,
                    "amenity_id": amenity_id,
                    "landlord_id": landlord_id,
                    "price": price,
                    "original_price": original_price,
                    "area": area,
                    "price_per_m2": price_per_m2,
                    "deposit_amount": fees["deposit_amount"],
                    "electricity_cost": fees["electricity_cost"],
                    "water_cost": fees["water_cost"],
                    "service_cost": fees["service_cost"],
                    "estimated_total_cost": estimated_total_cost,
                    "price_diff_rate": 0.0,
                    "price_segment": price_segment,
                    "risk_score": risk_score,
                    "completeness_score": completeness_score,
                    "is_active": True,
                    "is_promoted": is_promoted,
                    "room_status": fees["room_status"],
                    "extraction_source": fees["extraction_source"],
                    "is_duplicate": is_duplicate,
                    "duplicate_group_id": duplicate_group_id,
                    "orig_published_at": orig_dt.isoformat() if orig_dt else None,
                    "last_bumped_at": bump_dt.isoformat() if bump_dt else None,
                }

                upserted = self.client.table("fact_rental_listings").upsert(
                    fact_payload, on_conflict="source,external_id"
                ).execute()

                if not is_duplicate and upserted.data:
                    new_fid = upserted.data[0]["fact_id"]
                    if norm_title and district:
                        by_title_loc[(norm_title, district, price_bucket)] = new_fid
                    if phone_masked:
                        by_phone_price[(phone_masked, f"{district}_{price_bucket}")] = new_fid

                self.client.table("staging_raw_listings").update({
                    "status": "processed",
                    "error_message": None,
                    "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }).eq("source", source).eq("external_id", external_id).execute()

                loaded_count += 1
                existing_facts.add((source, external_id))

            except Exception as e:
                logger.error("Lỗi khi xử lý tin %s-%s vào Star Schema: %s", source, external_id, e)

        if loaded_count > 0:
            self.recalculate_price_diff_rates()

        logger.info(
            "ETL hoàn tất: nạp %d tin (trùng lặp đa nguồn: %d, loại bỏ không hợp lệ: %d).",
            loaded_count, dedup_count, invalid_count,
        )
        return loaded_count

    def recalculate_price_diff_rates(self) -> int:
        """
        Tính lại price_diff_rate (% chênh lệch đơn giá/m² so với trung bình cùng quận + loại phòng)
        và cập nhật risk_score cho toàn bộ tin hợp lệ.
        """
        try:
            res = (
                self.client.table("fact_rental_listings")
                .select("fact_id, price, area, price_per_m2, title, description, property_type_id, is_promoted, is_duplicate, dim_location(district)")
                .eq("is_active", True)
                .eq("is_duplicate", False)
                .execute()
            )
            rows = res.data or []
            if not rows:
                return 0

            group_prices: Dict[Tuple[str, int], List[float]] = defaultdict(list)
            for r in rows:
                ppm2 = r.get("price_per_m2")
                dist = (r.get("dim_location") or {}).get("district") or ""
                pt_id = r.get("property_type_id") or 1
                if ppm2 and float(ppm2) > 0 and dist:
                    group_prices[(dist, pt_id)].append(float(ppm2))

            group_avg = {k: sum(v) / len(v) for k, v in group_prices.items() if v}

            updated = 0
            for r in rows:
                ppm2 = float(r["price_per_m2"]) if r.get("price_per_m2") else None
                dist = (r.get("dim_location") or {}).get("district") or ""
                pt_id = r.get("property_type_id") or 1
                avg_val = group_avg.get((dist, pt_id))
                diff_rate = compute_price_diff_rate(ppm2, avg_val)
                new_risk = calculate_risk_score(
                    float(r.get("price") or 0),
                    float(r.get("area") or 0),
                    r.get("title") or "",
                    r.get("description") or "",
                    diff_rate,
                    bool(r.get("is_promoted")),
                )
                self.client.table("fact_rental_listings").update({
                    "price_diff_rate": diff_rate,
                    "risk_score": new_risk,
                }).eq("fact_id", r["fact_id"]).execute()
                updated += 1

            logger.info("Đã tính lại price_diff_rate và risk_score cho %d tin.", updated)
            return updated
        except Exception as e:
            logger.error("Lỗi khi tính lại price_diff_rate: %s", e)
            return 0

    def backfill_from_staging(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Làm giàu lại dữ liệu hiện có từ bảng staging_raw_listings:
        - Cập nhật các trường thật từ raw_payload (Chợ Tốt / Phongtro123)
        - Chạy Gemini/Regex bóc tách chi phí điện, nước, cọc, dịch vụ, tiện nghi
        - Khử trùng lặp đa nguồn và tính lại price_diff_rate
        """
        q = self.client.table("staging_raw_listings").select("source, external_id, raw_payload")
        if limit:
            q = q.limit(limit)
        staging_rows = q.execute().data or []

        fact_res = (
            self.client.table("fact_rental_listings")
            .select("fact_id, source, external_id, title, description, price, area, images, amenity_id, landlord_id, location_id, dim_location(district), dim_landlord(phone_masked)")
            .execute()
        )
        facts_map = {(f["source"], str(f["external_id"])): f for f in (fact_res.data or [])}

        seen_title_loc: Dict[Tuple[str, str, int], str] = {}
        seen_phone_price: Dict[Tuple[str, str], str] = {}

        stats = {"total": len(staging_rows), "updated": 0, "gemini": 0, "regex": 0, "duplicates": 0}

        for row in staging_rows:
            source = row["source"]
            ext_id = str(row["external_id"])
            fact = facts_map.get((source, ext_id))
            if not fact:
                continue

            item = self._extract_item_from_raw(source, ext_id, row.get("raw_payload") or {})
            # Giữ giá trị đã có nếu raw thiếu
            item["title"] = item.get("title") or fact.get("title") or ""
            item["description"] = item.get("description") or fact.get("description") or ""
            item["price"] = item.get("price") or fact.get("price") or 0
            item["area"] = item.get("area") or fact.get("area")
            item["images"] = item.get("images") or fact.get("images") or []

            fees, amenities = self._extract_fees_and_amenities(item)
            if fees["extraction_source"] == "gemini":
                stats["gemini"] += 1
            else:
                stats["regex"] += 1

            district = (fact.get("dim_location") or {}).get("district") or normalize_district_name(item.get("district", ""))
            phone_masked = (fact.get("dim_landlord") or {}).get("phone_masked") or ""

            # Kiểm tra trùng lặp đa nguồn
            norm_t = normalize_title_for_dedup(item["title"])
            price_val = float(item["price"] or 0)
            price_bucket = int(round(price_val / 100_000))
            matched_fid = seen_title_loc.get((norm_t, district, price_bucket))
            if not matched_fid and phone_masked:
                matched_fid = seen_phone_price.get((phone_masked, f"{district}_{price_bucket}"))

            is_dup = matched_fid is not None and matched_fid != fact["fact_id"]
            dup_group = str(uuid.uuid5(uuid.NAMESPACE_DNS, matched_fid)) if is_dup else None
            if is_dup:
                stats["duplicates"] += 1
            else:
                if norm_t and district:
                    seen_title_loc[(norm_t, district, price_bucket)] = fact["fact_id"]
                if phone_masked:
                    seen_phone_price[(phone_masked, f"{district}_{price_bucket}")] = fact["fact_id"]

            orig_dt = parse_timestamp_to_dt(item.get("orig_published_at") or item.get("published_at"))
            bump_dt = parse_timestamp_to_dt(item.get("published_at"))

            est_total = estimate_monthly_total_cost(
                price_val, fees["electricity_cost"], fees["water_cost"], fees["service_cost"]
            )
            comp_score = calculate_completeness_score({
                "title": item["title"],
                "price": price_val,
                "area": item["area"],
                "district": district,
                "description": item["description"],
                "images": item["images"],
                "electricity_cost": fees["electricity_cost"],
                "water_cost": fees["water_cost"],
                "deposit_amount": fees["deposit_amount"],
            })

            update_payload = {
                "original_price": float(item["original_price"]) if item.get("original_price") else None,
                "deposit_amount": fees["deposit_amount"],
                "electricity_cost": fees["electricity_cost"],
                "water_cost": fees["water_cost"],
                "service_cost": fees["service_cost"],
                "estimated_total_cost": est_total,
                "completeness_score": comp_score,
                "is_promoted": bool(item.get("is_promoted")),
                "videos": item.get("videos") or [],
                "room_status": fees["room_status"],
                "extraction_source": fees["extraction_source"],
                "is_duplicate": is_dup,
                "duplicate_group_id": dup_group,
                "orig_published_at": orig_dt.isoformat() if orig_dt else None,
                "last_bumped_at": bump_dt.isoformat() if bump_dt else None,
            }
            if orig_dt:
                update_payload["time_id"] = self._ensure_dim_time(orig_dt.date())

            self.client.table("fact_rental_listings").update(update_payload).eq("fact_id", fact["fact_id"]).execute()

            if fact.get("amenity_id"):
                self.client.table("dim_amenities").update(amenities).eq("amenity_id", fact["amenity_id"]).execute()

            if fact.get("landlord_id") and source == "chotot":
                self.client.table("dim_landlord").update({
                    "sold_ads_count": int(item.get("sold_ads_count") or 0),
                    "is_verified_seller": bool(item.get("is_verified_seller")),
                }).eq("landlord_id", fact["landlord_id"]).execute()

            stats["updated"] += 1

        self.recalculate_price_diff_rates()
        logger.info("Backfill hoàn tất: %s", stats)
        return stats

    def refresh_listing_active_status(self, sample_limit: int = 40) -> Dict[str, int]:
        """
        Kiểm tra các tin đang active còn tồn tại trên nguồn gốc hay đã hết hạn/ẩn.
        Khi tin bị gỡ -> cập nhật is_active=False, room_status='het_han', closed_at=now().
        """
        from src.backend.scraper.chotot_scraper import ChototScraper
        from src.backend.scraper.phongtro123_scraper import Phongtro123Scraper

        chotot = ChototScraper()
        pt123 = Phongtro123Scraper(fetch_details=False)

        res = (
            self.client.table("fact_rental_listings")
            .select("fact_id, source, external_id, original_url")
            .eq("is_active", True)
            .order("updated_at", desc=False)
            .limit(sample_limit)
            .execute()
        )
        rows = res.data or []
        checked = 0
        closed = 0
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        for r in rows:
            active: Optional[bool] = None
            if r["source"] == "chotot":
                active = chotot.is_listing_active(str(r["external_id"]))
            elif r["source"] == "phongtro123":
                active = pt123.is_listing_active(r.get("original_url") or "")

            checked += 1
            if active is False:
                self.client.table("fact_rental_listings").update({
                    "is_active": False,
                    "room_status": "het_han",
                    "closed_at": now_iso,
                    "updated_at": now_iso,
                }).eq("fact_id", r["fact_id"]).execute()
                closed += 1
            else:
                self.client.table("fact_rental_listings").update({
                    "updated_at": now_iso,
                }).eq("fact_id", r["fact_id"]).execute()

        logger.info("Kiểm tra vòng đời tin: %d tin đã kiểm tra, %d tin đã hết hạn/đóng.", checked, closed)
        return {"checked": checked, "closed": closed}

import datetime
import logging
from typing import List, Dict, Any, Optional
from src.backend.database.supabase_client import get_supabase_client
from src.backend.scraper.osm_service import find_nearest_university
from src.backend.etl.cleaner import (
    normalize_district_name,
    HANOI_DISTRICT_COORDS,
    infer_property_type,
    extract_amenities,
    calculate_completeness_score,
    calculate_risk_score
)

logger = logging.getLogger(__name__)

class ETLPipeline:
    """
    Quy trình ETL: Làm sạch dữ liệu thô từ Staging, chuẩn hóa và nạp vào Kho dữ liệu Star Schema trên Supabase.
    """

    def __init__(self):
        self.client = get_supabase_client()
        self._property_type_cache = {}
        self._load_property_types()

    def _load_property_types(self):
        """Cache danh mục loại phòng để tránh query liên tục."""
        try:
            res = self.client.table("dim_property_type").select("property_type_id, type_code").execute()
            for row in res.data:
                self._property_type_cache[row["type_code"]] = row["property_type_id"]
        except Exception as e:
            logger.error("Không thể tải danh mục property_types: %s", e)

    def save_raw_listings(self, listings: List[Dict[str, Any]]) -> int:
        """
        Lưu danh sách tin cào thô vào bảng staging_raw_listings theo batch (Staging Data Lake).
        """
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
                "scraped_at": now_iso
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

    def process_and_load_star_schema(self, listings: List[Dict[str, Any]]) -> int:
        """
        Chuẩn hóa các tin cào và nạp vào hệ thống các bảng Star Schema:
        - dim_location, dim_amenities, dim_landlord
        - fact_rental_listings
        """
        loaded_count = 0
        today = datetime.date.today()
        time_id = int(today.strftime("%Y%m%d"))

        # Tải danh sách các tin đã có trong fact để tránh insert trùng lặp
        existing_facts = set()
        try:
            res = self.client.table("fact_rental_listings").select("source, external_id").execute()
            for r in res.data:
                existing_facts.add((r["source"], str(r["external_id"])))
        except Exception as e:
            logger.warning("Không thể tải danh sách fact đã tồn tại: %s", e)

        for item in listings:
            source = item["source"]
            external_id = str(item["external_id"])

            # Bỏ qua nếu tin đã được xử lý vào fact trước đó
            if (source, external_id) in existing_facts:
                continue

            try:
                title = item.get("title", "")
                desc = item.get("description", "")
                price = float(item.get("price") or 0.0)
                area = float(item.get("area") or 0.0) if item.get("area") else None

                # 1. Xử lý Vị trí (dim_location)
                district = normalize_district_name(item.get("district", ""))
                ward = item.get("ward") or ""
                street = item.get("street") or ""
                lat = item.get("latitude")
                lon = item.get("longitude")

                # Fallback tọa độ nếu thiếu GPS
                if (lat is None or lon is None) and district in HANOI_DISTRICT_COORDS:
                    lat, lon = HANOI_DISTRICT_COORDS[district]

                nearest_uni, dist_km = find_nearest_university(lat, lon)

                loc_data = {
                    "province": "Hà Nội",
                    "district": district,
                    "ward": ward,
                    "street": street,
                    "full_address": f"{street}, {ward}, {district}, Hà Nội".strip(", "),
                    "latitude": lat,
                    "longitude": lon,
                    "nearest_university": nearest_uni,
                    "distance_to_university_km": dist_km
                }
                loc_res = self.client.table("dim_location").insert(loc_data).execute()
                location_id = loc_res.data[0]["location_id"] if loc_res.data else None

                # 2. Xử lý Loại hình (dim_property_type)
                type_code = infer_property_type(title, desc)
                property_type_id = self._property_type_cache.get(type_code, 1)

                # 3. Xử lý Tiện ích (dim_amenities)
                amenities_data = extract_amenities(title, desc)
                amenities_res = self.client.table("dim_amenities").insert(amenities_data).execute()
                amenity_id = amenities_res.data[0]["amenity_id"] if amenities_res.data else None

                # 4. Xử lý Người đăng (dim_landlord)
                poster_name = item.get("poster_name") or "Chính chủ"
                phone_raw = item.get("phone") or ""
                phone_masked = phone_raw[:4] + "***" + phone_raw[-3:] if len(phone_raw) >= 7 else phone_raw
                poster_code = f"{source}_{item.get('poster_id') or hash(phone_masked) % 1000000}"
                poster_type = item.get("poster_type", "unknown")

                landlord_data = {
                    "poster_code": poster_code,
                    "poster_name": poster_name,
                    "phone_masked": phone_masked,
                    "poster_type": poster_type,
                    "total_listings": 1,
                    "trust_score": 7.5 if poster_type == "chinh_chu" else 5.0
                }
                landlord_res = self.client.table("dim_landlord").upsert(
                    landlord_data, on_conflict="poster_code"
                ).execute()
                landlord_id = landlord_res.data[0]["landlord_id"] if landlord_res.data else None

                # 5. Tính toán các chỉ số kinh doanh cốt lõi (Fact Metrics)
                price_per_m2 = round(price / area, 2) if (area and area > 0 and price > 0) else None
                # Ước tính tổng chi phí hàng tháng (tiền phòng + điện/nước/dịch vụ trung bình 450k)
                estimated_total_cost = price + 450000.0 if price > 0 else 0.0

                if price < 3000000:
                    price_segment = "binh_dan"
                elif price <= 6000000:
                    price_segment = "trung_cap"
                else:
                    price_segment = "cao_cap"

                risk_score = calculate_risk_score(price, area or 0, title, desc)
                completeness_score = calculate_completeness_score({
                    "title": title, "price": price, "area": area,
                    "district": district, "description": desc,
                    "images": item.get("images", [])
                })

                # 6. Nạp vào bảng Sự Kiện Trung Tâm (fact_rental_listings)
                fact_payload = {
                    "source": source,
                    "external_id": external_id,
                    "title": title,
                    "description": desc,
                    "original_url": item.get("original_url", ""),
                    "images": item.get("images", []),
                    "time_id": time_id,
                    "location_id": location_id,
                    "property_type_id": property_type_id,
                    "amenity_id": amenity_id,
                    "landlord_id": landlord_id,
                    "price": price,
                    "area": area,
                    "price_per_m2": price_per_m2,
                    "deposit_amount": price, # Tiền cọc thông thường = 1 tháng tiền nhà
                    "electricity_cost": 4000.0, # Giá điện phòng trọ phổ biến 4k/kWh
                    "water_cost": 100000.0,     # Giá nước phổ biến 100k/người
                    "service_cost": 150000.0,   # Phí dịch vụ (wifi, rác, vệ sinh)
                    "estimated_total_cost": estimated_total_cost,
                    "price_diff_rate": 0.0,
                    "price_segment": price_segment,
                    "risk_score": risk_score,
                    "completeness_score": completeness_score,
                    "is_active": True
                }

                self.client.table("fact_rental_listings").upsert(
                    fact_payload, on_conflict="source,external_id"
                ).execute()

                # Cập nhật trạng thái trong staging
                self.client.table("staging_raw_listings").update({
                    "status": "processed",
                    "processed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }).eq("source", source).eq("external_id", external_id).execute()

                loaded_count += 1
                existing_facts.add((source, external_id))

            except Exception as e:
                logger.error("Lỗi khi xử lý tin %s-%s vào Star Schema: %s", item.get("source"), item.get("external_id"), e)

        logger.info("Đã hoàn thành nạp %d/%d tin vào Star Schema trên Supabase.", loaded_count, len(listings))
        return loaded_count

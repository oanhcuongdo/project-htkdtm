import logging
from typing import List, Dict, Any
from src.backend.scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ChototScraper(BaseScraper):
    """
    Crawler thu thập dữ liệu phòng trọ cho thuê tại Hà Nội từ Chợ Tốt (Nhà Tốt) qua Gateway API.
    """
    API_URL = "https://gateway.chotot.com/v1/public/ad-listing"

    def __init__(self):
        super().__init__(source_name="chotot")

    def fetch_listings(self, limit: int = 50, start_offset: int = 0) -> List[Dict[str, Any]]:
        """
        Thu thập các tin đăng phòng trọ tại Hà Nội từ Chợ Tốt.
        :param limit: Số lượng tin tối đa cần cào
        :param start_offset: Vị trí offset bắt đầu cào
        :return: Danh sách dict chứa tin thô
        """
        results: List[Dict[str, Any]] = []
        offset = start_offset
        batch_size = 20

        logger.info("Bắt đầu cào Chợ Tốt (Khu vực Hà Nội, Category: Phòng trọ, Mục tiêu: %d tin)...", limit)

        while len(results) < limit:
            current_limit = min(batch_size, limit - len(results))
            params = {
                "region_v2": 12000, # Mã vùng Hà Nội
                "cg": 1050,         # Chuyên mục: Cho thuê phòng trọ, nhà trọ
                "limit": current_limit,
                "o": offset
            }

            try:
                logger.info("Gửi request Chợ Tốt: offset=%d, limit=%d", offset, current_limit)
                response = self.session.get(self.API_URL, params=params, timeout=self.timeout)
                
                if response.status_code != 200:
                    logger.error("Chợ Tốt trả về lỗi HTTP %d: %s", response.status_code, response.text[:200])
                    break
                
                data = response.json()
                ads = data.get("ads", [])
                if not ads:
                    logger.info("Không còn tin đăng mới từ Chợ Tốt.")
                    break

                for ad in ads:
                    external_id = str(ad.get("ad_id") or ad.get("list_id"))
                    standardized_raw = {
                        "source": self.source_name,
                        "external_id": external_id,
                        "title": ad.get("subject", "").strip(),
                        "description": ad.get("body", "").strip(),
                        "original_url": f"https://www.nhatot.com/phong-tro-nha-tro-ha-noi/{external_id}.htm",
                        "price": ad.get("price"),
                        "original_price": ad.get("original_price"),
                        "price_diff": ad.get("price_diff"),
                        "price_string": ad.get("price_string"),
                        "deposit": ad.get("deposit"),
                        "area": ad.get("size"),
                        "latitude": ad.get("latitude"),
                        "longitude": ad.get("longitude"),
                        "district": ad.get("area_name"),
                        "ward": ad.get("ward_name"),
                        "street": ad.get("street_name"),
                        "images": ad.get("images", []),
                        "videos": ad.get("videos", []),
                        "furnishing_rent": ad.get("furnishing_rent"),
                        "poster_name": ad.get("account_name"),
                        "poster_id": str(ad.get("account_id") or ""),
                        "poster_type": "moi_gioi" if ad.get("company_ad") else "chinh_chu",
                        "sold_ads_count": ad.get("sold_ads") or 0,
                        "is_verified_seller": bool(ad.get("is_shop_verified")),
                        "is_promoted": bool(
                            ad.get("is_sticky")
                            or ad.get("sticky_ad_platinum")
                            or ad.get("special_display")
                        ),
                        "orig_published_at": ad.get("orig_list_time"),
                        "published_at": ad.get("list_time"),
                        "raw_payload": ad
                    }
                    results.append(standardized_raw)
                    if len(results) >= limit:
                        break

                offset += len(ads)
                self.sleep_rate_limit()

            except Exception as e:
                logger.error("Lỗi khi cào dữ liệu từ Chợ Tốt: %s", e)
                break

        logger.info("Hoàn tất cào Chợ Tốt: Thu thập được %d tin.", len(results))
        return results

    def is_listing_active(self, external_id: str) -> Optional[bool]:
        """Kiểm tra tin đăng Chợ Tốt còn tồn tại hay đã ẩn/hết hạn."""
        if not external_id:
            return None
        try:
            resp = self.session.get(f"{self.API_URL}/{external_id}", timeout=self.timeout)
            if resp.status_code in (404, 410):
                return False
            if resp.status_code == 200:
                ad = resp.json().get("ad") or {}
                status = str(ad.get("status", "")).lower()
                if status in ("sold", "deleted", "expired", "inactive"):
                    return False
                return True
        except Exception:
            pass
        return None

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
                        "price_string": ad.get("price_string"),
                        "area": ad.get("size"),
                        "latitude": ad.get("latitude"),
                        "longitude": ad.get("longitude"),
                        "district": ad.get("area_name"),
                        "ward": ad.get("ward_name"),
                        "street": ad.get("street_name"),
                        "images": ad.get("images", []),
                        "poster_name": ad.get("account_name"),
                        "poster_id": str(ad.get("account_id") or ""),
                        "poster_type": "moi_gioi" if ad.get("company_ad") else "chinh_chu",
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

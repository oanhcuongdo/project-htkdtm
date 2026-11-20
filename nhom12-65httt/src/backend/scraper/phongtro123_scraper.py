import re
import json
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.backend.scraper.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class Phongtro123Scraper(BaseScraper):
    """
    Crawler thu thập dữ liệu phòng trọ cho thuê tại Hà Nội từ Phongtro123.
    """
    BASE_URL = "https://phongtro123.com/tinh-thanh/ha-noi"

    def __init__(self):
        super().__init__(source_name="phongtro123")

    def _extract_acreage(self, text: str) -> Optional[float]:
        """Trích xuất diện tích (m²) từ chuỗi text."""
        match = re.search(r'(\d+(?:[.,]\d+)?)\s*m[²2]', text)
        if match:
            try:
                val = match.group(1).replace(',', '.')
                return float(val)
            except ValueError:
                pass
        return None

    def fetch_listings(self, limit: int = 50, start_page: int = 1) -> List[Dict[str, Any]]:
        """
        Thu thập các tin đăng phòng trọ tại Hà Nội từ Phongtro123 qua phân trang.
        :param limit: Số lượng tin tối đa cần cào
        :param start_page: Trang bắt đầu cào
        :return: Danh sách dict chứa tin thô
        """
        results: List[Dict[str, Any]] = []
        page = start_page

        logger.info("Bắt đầu cào Phongtro123 (Khu vực Hà Nội, Mục tiêu: %d tin)...", limit)

        while len(results) < limit:
            url = f"{self.BASE_URL}?page={page}"
            try:
                logger.info("Gửi request Phongtro123: page=%d (%s)", page, url)
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code != 200:
                    logger.error("Phongtro123 trả về lỗi HTTP %d: %s", response.status_code, response.text[:200])
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                listing_container = soup.find("ul", class_="post__listing")
                if not listing_container:
                    logger.warning("Không tìm thấy ul.post__listing trên trang %d", page)
                    break

                items = listing_container.find_all("li", recursive=False)
                if not items:
                    logger.info("Không còn tin đăng trên trang %d", page)
                    break

                for li in items:
                    # Trích xuất JSON-LD nếu có
                    ld_script = li.find("script", type="application/ld+json")
                    ld_data = {}
                    if ld_script and ld_script.string:
                        try:
                            ld_data = json.loads(ld_script.string.strip())
                        except Exception:
                            pass

                    # Lấy ID tin
                    url_full = ld_data.get("url") or ""
                    id_match = re.search(r'pr(\d+)\.html', url_full)
                    external_id = id_match.group(1) if id_match else str(hash(url_full) % 10000000)

                    # Tiêu đề
                    title = ld_data.get("name") or ""
                    if not title:
                        title_tag = li.find(["h2", "h3", "h4"])
                        title = title_tag.get_text(strip=True) if title_tag else ""

                    # Mô tả
                    desc = ld_data.get("description") or ""

                    # Giá
                    price_val = None
                    price_str = ld_data.get("priceRange")
                    if price_str:
                        try:
                            price_val = float(price_str)
                        except ValueError:
                            pass

                    # Diện tích
                    full_li_text = li.get_text(separator=" ", strip=True)
                    acreage = self._extract_acreage(full_li_text)

                    # Địa chỉ & Quận huyện từ link danh mục khu vực
                    district = ""
                    for a_tag in li.find_all("a"):
                        href = a_tag.get("href", "")
                        if "/ha-noi/" in href:
                            link_text = a_tag.get_text(strip=True).replace(", Hà Nội", "").strip()
                            if "quan-" in href:
                                district = f"Quận {link_text}"
                            elif "huyen-" in href:
                                district = f"Huyện {link_text}"
                            else:
                                district = link_text
                            break

                    address_obj = ld_data.get("address", {})
                    street_address = address_obj.get("streetAddress", "") if isinstance(address_obj, dict) else ""

                    # SĐT & Tên người đăng
                    phone = ld_data.get("telephone", "")
                    image_url = ld_data.get("image", "")

                    standardized_raw = {
                        "source": self.source_name,
                        "external_id": external_id,
                        "title": title.strip(),
                        "description": desc.strip(),
                        "original_url": url_full,
                        "price": price_val,
                        "price_string": f"{price_val/1000000:.1f} triệu/tháng" if price_val else "",
                        "area": acreage,
                        "latitude": None, # Sẽ được bổ sung qua Geocoding / Quận
                        "longitude": None,
                        "district": district or "Hà Nội",
                        "ward": "",
                        "street": street_address,
                        "images": [image_url] if image_url else [],
                        "poster_name": "Chính chủ / Môi giới",
                        "phone": phone,
                        "poster_type": "unknown",
                        "raw_payload": {
                            "ld_json": ld_data,
                            "html_snippet": str(li)[:500]
                        }
                    }
                    results.append(standardized_raw)
                    if len(results) >= limit:
                        break

                page += 1
                self.sleep_rate_limit()

            except Exception as e:
                logger.error("Lỗi khi cào dữ liệu từ Phongtro123: %s", e)
                break

        logger.info("Hoàn tất cào Phongtro123: Thu thập được %d tin.", len(results))
        return results

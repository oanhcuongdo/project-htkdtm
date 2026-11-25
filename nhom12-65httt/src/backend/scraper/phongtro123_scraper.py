import re
import json
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.backend.scraper.base_scraper import BaseScraper
from src.backend.scraper.osm_service import geocode_address_nominatim

logger = logging.getLogger(__name__)


class Phongtro123Scraper(BaseScraper):
    """
    Crawler thu thập dữ liệu phòng trọ cho thuê tại Hà Nội từ Phongtro123.
    Hỗ trợ cào trang danh sách kèm truy cập trang chi tiết để lấy mô tả đầy đủ,
    danh sách ảnh, người đăng và geocode tọa độ địa chỉ qua OSM Nominatim.
    """
    BASE_URL = "https://phongtro123.com/tinh-thanh/ha-noi"

    def __init__(self, fetch_details: bool = True):
        super().__init__(source_name="phongtro123")
        self.fetch_details = fetch_details

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

    def fetch_detail(self, url: str) -> Dict[str, Any]:
        """
        Cào trang chi tiết của một tin Phongtro123 để lấy:
        - Mô tả đầy đủ (chứa giá điện, nước, cọc, dịch vụ)
        - Địa chỉ chi tiết (đường, phường)
        - Danh sách ảnh gallery
        - Tên người đăng & tổng số tin đăng để phân loại chính chủ / môi giới
        """
        detail: Dict[str, Any] = {}
        if not url:
            return detail

        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                return detail

            soup = BeautifulSoup(resp.text, "html.parser")

            # 1. Mô tả đầy đủ từ mục "Thông tin mô tả"
            desc_heading = soup.find(string=lambda s: s and "Thông tin mô tả" in s)
            if desc_heading and desc_heading.parent and desc_heading.parent.parent:
                container = desc_heading.parent.parent
                text_parts = [
                    p.get_text(" ", strip=True)
                    for p in container.find_all(["p", "li", "div"], recursive=False)
                ]
                full_text = "\n".join(t for t in text_parts if t)
                if not full_text:
                    full_text = container.get_text("\n", strip=True)
                full_text = re.sub(r'^Thông tin mô tả\s*', '', full_text).strip()
                if full_text:
                    detail["description"] = full_text

            # 2. Địa chỉ chi tiết từ mục "Vị trí & bản đồ"
            addr_heading = soup.find(string=lambda s: s and "Vị trí" in s)
            if addr_heading and addr_heading.parent and addr_heading.parent.parent:
                addr_text = addr_heading.parent.parent.get_text(" ", strip=True)
                addr_match = re.search(r'Địa chỉ:\s*(.+?)(?:Xem bản đồ|$)', addr_text)
                if addr_match:
                    raw_addr = addr_match.group(1).strip(" |")
                    detail["full_address"] = raw_addr
                    ward_match = re.search(r'(Phường\s+[^,]+|Xã\s+[^,]+|Thị trấn\s+[^,]+)', raw_addr, re.I)
                    if ward_match:
                        detail["ward"] = ward_match.group(1).strip()
                    first_part = raw_addr.split(",")[0].strip()
                    if first_part and "Hà Nội" not in first_part:
                        detail["street"] = first_part

            # 3. Gallery hình ảnh
            gallery_imgs: List[str] = []
            for img in soup.select(".post-images img, .swiper img, .carousel img, img"):
                src = img.get("src") or img.get("data-src") or ""
                if "pt123.cdn.static123.com/images/" in src and src not in gallery_imgs:
                    gallery_imgs.append(src)
                if len(gallery_imgs) >= 12:
                    break
            if gallery_imgs:
                detail["images"] = gallery_imgs

            # 4. Thông tin liên hệ người đăng
            contact_heading = soup.find(string=lambda s: s and "Thông tin liên hệ" in s)
            if contact_heading and contact_heading.parent and contact_heading.parent.parent:
                c_text = contact_heading.parent.parent.get_text(" | ", strip=True)
                parts = [p.strip() for p in c_text.split("|") if p.strip() and "Thông tin liên hệ" not in p]
                if parts:
                    detail["poster_name"] = parts[0][:100]
                count_match = re.search(r'(\d+)\s*tin đăng', c_text)
                if count_match:
                    cnt = int(count_match.group(1))
                    detail["poster_total_listings"] = cnt
                    detail["poster_type"] = "moi_gioi" if cnt >= 5 else "chinh_chu"

            detail["raw_detail_html_len"] = len(resp.text)
        except Exception as e:
            logger.debug("Không thể cào chi tiết Phongtro123 (%s): %s", url, e)

        return detail

    def is_listing_active(self, url: str) -> Optional[bool]:
        """Kiểm tra tin đăng Phongtro123 còn hoạt động hay đã bị gỡ/hết hạn."""
        if not url:
            return None
        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code in (404, 410):
                return False
            if resp.status_code == 200:
                lower = resp.text.lower()
                if "tin đã hết hạn" in lower or "không tìm thấy tin đăng" in lower:
                    return False
                return True
        except Exception:
            pass
        return None

    def fetch_listings(self, limit: int = 50, start_page: int = 1) -> List[Dict[str, Any]]:
        """
        Thu thập các tin đăng phòng trọ tại Hà Nội từ Phongtro123 qua phân trang.
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
                    ld_script = li.find("script", type="application/ld+json")
                    ld_data = {}
                    if ld_script and ld_script.string:
                        try:
                            ld_data = json.loads(ld_script.string.strip())
                        except Exception:
                            pass

                    url_full = ld_data.get("url") or ""
                    id_match = re.search(r'pr(\d+)\.html', url_full)
                    external_id = id_match.group(1) if id_match else str(hash(url_full) % 10000000)

                    title = ld_data.get("name") or ""
                    if not title:
                        title_tag = li.find(["h2", "h3", "h4"])
                        title = title_tag.get_text(strip=True) if title_tag else ""

                    desc = ld_data.get("description") or ""

                    price_val = None
                    price_str = ld_data.get("priceRange")
                    if price_str:
                        try:
                            price_val = float(price_str)
                        except ValueError:
                            pass

                    full_li_text = li.get_text(separator=" ", strip=True)
                    acreage = self._extract_acreage(full_li_text)

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
                    ward = ""

                    phone = ld_data.get("telephone", "")
                    image_url = ld_data.get("image", "")
                    images = [image_url] if image_url else []
                    poster_name = "Chính chủ / Môi giới"
                    poster_type = "unknown"
                    is_promoted = "vip" in " ".join(li.get("class", [])).lower()

                    if self.fetch_details and url_full:
                        detail = self.fetch_detail(url_full)
                        if detail.get("description"):
                            desc = detail["description"]
                        if detail.get("images"):
                            images = detail["images"]
                        if detail.get("street"):
                            street_address = detail["street"]
                        if detail.get("ward"):
                            ward = detail["ward"]
                        if detail.get("poster_name"):
                            poster_name = detail["poster_name"]
                        if detail.get("poster_type"):
                            poster_type = detail["poster_type"]
                        self.sleep_rate_limit()

                    lat, lon = geocode_address_nominatim(street_address, district or "Hà Nội", ward)

                    standardized_raw = {
                        "source": self.source_name,
                        "external_id": external_id,
                        "title": title.strip(),
                        "description": desc.strip(),
                        "original_url": url_full,
                        "price": price_val,
                        "price_string": f"{price_val/1000000:.1f} triệu/tháng" if price_val else "",
                        "area": acreage,
                        "latitude": lat,
                        "longitude": lon,
                        "district": district or "Hà Nội",
                        "ward": ward,
                        "street": street_address,
                        "images": images,
                        "videos": [],
                        "poster_name": poster_name,
                        "phone": phone,
                        "poster_type": poster_type,
                        "is_promoted": is_promoted,
                        "raw_payload": {
                            "ld_json": ld_data,
                            "detail_description": desc.strip(),
                            "detail_images": images,
                            "detail_address": {"street": street_address, "ward": ward, "district": district},
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

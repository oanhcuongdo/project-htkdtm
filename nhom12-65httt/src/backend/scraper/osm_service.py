import math
from typing import Dict, Tuple, Optional, List
import requests
import logging

logger = logging.getLogger(__name__)

# Danh mục tọa độ các trường Đại học trọng điểm tại Hà Nội (Đặc biệt là ĐH Thủy Lợi)
HANOI_UNIVERSITIES = [
    {"name": "Đại học Thủy Lợi (TLU)", "lat": 21.0076, "lon": 105.8247, "address": "175 Tây Sơn, Đống Đa"},
    {"name": "Học viện Ngân Hàng", "lat": 21.0092, "lon": 105.8294, "address": "12 Chùa Bộc, Đống Đa"},
    {"name": "Đại học Y Hà Nội", "lat": 21.0033, "lon": 105.8315, "address": "1 Tôn Thất Tùng, Đống Đa"},
    {"name": "Đại học Bách Khoa Hà Nội", "lat": 21.0044, "lon": 105.8436, "address": "1 Đại Cồ Việt, Hai Bà Trưng"},
    {"name": "Đại học Kinh Tế Quốc Dân (NEU)", "lat": 20.9995, "lon": 105.8427, "address": "207 Giải Phóng, Hai Bà Trưng"},
    {"name": "Đại học Xây Dựng", "lat": 21.0039, "lon": 105.8429, "address": "55 Giải Phóng, Hai Bà Trưng"},
    {"name": "Đại học Quốc Gia Hà Nội (VNU)", "lat": 21.0372, "lon": 105.7818, "address": "144 Xuân Thủy, Cầu Giấy"},
    {"name": "Đại học Sư Phạm Hà Nội", "lat": 21.0365, "lon": 105.7830, "address": "136 Xuân Thủy, Cầu Giấy"},
    {"name": "Đại học Thương Mại (TMU)", "lat": 21.0366, "lon": 105.7745, "address": "79 Hồ Tùng Mậu, Cầu Giấy"},
    {"name": "Học viện Báo Chí và Tuyên Truyền", "lat": 21.0360, "lon": 105.7890, "address": "36 Xuân Thủy, Cầu Giấy"},
    {"name": "Đại học Ngoại Thương (FTU)", "lat": 21.0232, "lon": 105.8052, "address": "91 Chùa Láng, Đống Đa"},
    {"name": "Đại học Giao Thông Vận Tải (UTC)", "lat": 21.0289, "lon": 105.8028, "address": "3 Cầu Giấy, Đống Đa"},
    {"name": "Học viện Bưu Chính Viễn Thông (PTIT)", "lat": 20.9806, "lon": 105.7876, "address": "Km10 Nguyễn Trãi, Hà Đông"},
    {"name": "Đại học Hà Nội (HANU)", "lat": 20.9904, "lon": 105.7944, "address": "Km9 Nguyễn Trãi, Nam Từ Liêm"},
    {"name": "Đại học Kiến Trúc Hà Nội", "lat": 20.9818, "lon": 105.7894, "address": "Km10 Nguyễn Trãi, Thanh Xuân"},
    {"name": "Đại học Công Nghiệp Hà Nội (HaUI)", "lat": 21.0538, "lon": 105.7352, "address": "298 Cầu Diễn, Bắc Từ Liêm"}
]

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách giữa 2 tọa độ GPS (kinh độ, vĩ độ) theo công thức Haversine (đơn vị: km).
    """
    R = 6371.0  # Bán kính trái đất tính bằng km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def find_nearest_university(lat: Optional[float], lon: Optional[float]) -> Tuple[Optional[str], Optional[float]]:
    """
    Tìm trường đại học gần nhất và khoảng cách tính bằng km.
    """
    if lat is None or lon is None or lat == 0 or lon == 0:
        return None, None
    
    nearest_uni = None
    min_dist = float('inf')
    
    for uni in HANOI_UNIVERSITIES:
        dist = haversine_distance(lat, lon, uni["lat"], uni["lon"])
        if dist < min_dist:
            min_dist = dist
            nearest_uni = uni["name"]
            
    return nearest_uni, min_dist

def query_osm_overpass_amenities(lat: float, lon: float, radius_meters: int = 1000) -> Dict[str, int]:
    """
    Truy vấn OpenStreetMap Overpass API để đếm số tiện ích xung quanh trong bán kính radius_meters.
    (Các tiện ích: bến xe bus, bệnh viện/phòng khám, chợ/siêu thị).
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:10];
    (
      node["highway"="bus_stop"](around:{radius_meters},{lat},{lon});
      node["amenity"~"hospital|clinic|pharmacy"](around:{radius_meters},{lat},{lon});
      node["shop"~"supermarket|convenience"](around:{radius_meters},{lat},{lon});
    );
    out count;
    """
    try:
        res = requests.post(overpass_url, data={"data": query}, timeout=8)
        if res.status_code == 200:
            data = res.json()
            return {"amenities_count": data.get("elements", [{}])[0].get("tags", {}).get("total", 0)}
    except Exception as e:
        logger.warning("Không thể truy vấn OSM Overpass API: %s", e)
    return {"amenities_count": 0}

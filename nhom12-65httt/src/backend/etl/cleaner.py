import re
from typing import Dict, Any, Tuple

# Bảng tọa độ trung tâm các quận/huyện Hà Nội để gán fallback khi tin không có GPS
HANOI_DISTRICT_COORDS = {
    "Quận Đống Đa": (21.0180, 105.8290),
    "Quận Cầu Giấy": (21.0360, 105.7905),
    "Quận Thanh Xuân": (20.9930, 105.8040),
    "Quận Hai Bà Trưng": (21.0090, 105.8580),
    "Quận Ba Đình": (21.0350, 105.8340),
    "Quận Hoàn Kiếm": (21.0300, 105.8540),
    "Quận Hoàng Mai": (20.9750, 105.8450),
    "Quận Nam Từ Liêm": (21.0150, 105.7650),
    "Quận Bắc Từ Liêm": (21.0550, 105.7550),
    "Quận Hà Đông": (20.9720, 105.7770),
    "Quận Long Biên": (21.0450, 105.8900),
    "Quận Tây Hồ": (21.0650, 105.8200),
    "Huyện Thanh Trì": (20.9450, 105.8500),
    "Huyện Gia Lâm": (21.0200, 105.9300),
    "Huyện Hoài Đức": (21.0150, 105.7000),
    "Huyện Đông Anh": (21.1350, 105.8450)
}

def normalize_district_name(district_raw: str) -> str:
    """Chuẩn hóa tên quận/huyện thành format chuẩn có tiền tố Quận/Huyện."""
    if not district_raw:
        return "Quận Đống Đa"
    d = district_raw.strip()
    
    # Danh sách chuẩn hóa tên quận/huyện tại Hà Nội
    districts = [
        "Đống Đa", "Cầu Giấy", "Thanh Xuân", "Hai Bà Trưng", "Ba Đình", 
        "Hoàn Kiếm", "Hoàng Mai", "Nam Từ Liêm", "Bắc Từ Liêm", 
        "Hà Đông", "Long Biên", "Tây Hồ"
    ]
    suburbs = ["Thanh Trì", "Gia Lâm", "Hoài Đức", "Đông Anh", "Đan Phượng", "Sóc Sơn", "Thường Tín"]

    for name in districts:
        if name.lower() in d.lower():
            return f"Quận {name}"
    for name in suburbs:
        if name.lower() in d.lower():
            return f"Huyện {name}"

    if not d.startswith("Quận ") and not d.startswith("Huyện "):
        d = f"Quận {d}"
    return d

def infer_property_type(title: str, desc: str) -> str:
    """Xác định loại hình phòng trọ dựa trên từ khóa trong tiêu đề và mô tả."""
    combined = f"{title} {desc}".lower()
    if any(k in combined for k in ["ktx", "ký túc xá", "sleepbox", "giường tầng", "hộp ngủ"]):
        return "ktx_sleepbox"
    if any(k in combined for k in ["ccmn", "chung cư mini", "căn hộ dịch vụ", "studio", "duplex"]):
        return "chung_cu_mini"
    if any(k in combined for k in ["nguyên căn", "nhà riêng", "nhà mặt đất", "nhà 4 tầng", "nhà 3 tầng"]):
        return "nha_nguyen_can"
    if any(k in combined for k in ["căn hộ", "chung cư", "2n1k", "1n1k", "3n2k"]):
        return "can_ho"
    return "phong_tro"

def extract_amenities(title: str, desc: str) -> Dict[str, Any]:
    """Bóc tách các tiện nghi cơ bản từ tiêu đề và mô tả bài đăng."""
    combined = f"{title} {desc}".lower()
    return {
        "has_air_conditioner": bool(re.search(r'(điều hòa|máy lạnh|đh\b)', combined)),
        "has_water_heater": bool(re.search(r'(nóng lạnh|bình nóng|nl\b)', combined)),
        "has_washing_machine": bool(re.search(r'(máy giặt|giặt sấy)', combined)),
        "has_refrigerator": bool(re.search(r'(tủ lạnh|tl\b)', combined)),
        "has_private_bathroom": bool(re.search(r'(khép kín|wc riêng|vệ sinh riêng|toilet riêng)', combined)),
        "has_kitchen": bool(re.search(r'(bếp|kệ bếp|nấu ăn|khu bếp)', combined)),
        "has_balcony": bool(re.search(r'(ban công|cửa sổ|thoáng mát)', combined)),
        "has_elevator": bool(re.search(r'(thang máy|tm\b)', combined)),
        "has_parking": bool(re.search(r'(để xe|chỗ để xe|nhà xe|hầm xe)', combined)),
        "has_security": bool(re.search(r'(bảo vệ|camera|khóa vân tay|an ninh)', combined)),
        "has_flexible_hours": bool(re.search(r'(giờ tự do|tự do|không chung chủ|ko chung chủ)', combined)),
        "has_mezzanine": bool(re.search(r'(gác xép|gác lửng|gác lầu)', combined)),
        "raw_amenities": []
    }

def calculate_completeness_score(item: Dict[str, Any]) -> float:
    """Tính điểm mức độ đầy đủ của thông tin tin đăng (0 - 100 điểm)."""
    score = 0.0
    if item.get("title") and len(item["title"]) > 10:
        score += 20.0
    if item.get("price") and item["price"] > 0:
        score += 20.0
    if item.get("area") and item["area"] > 0:
        score += 15.0
    if item.get("district"):
        score += 15.0
    if item.get("description") and len(item["description"]) > 30:
        score += 15.0
    if item.get("images") and len(item["images"]) > 0:
        score += 15.0
    return min(100.0, score)

def calculate_risk_score(price: float, area: float, title: str, desc: str) -> float:
    """
    Tính điểm đánh giá rủi ro tin ảo / tin mồi (0 - 100 điểm):
    - Giá quá rẻ bất thường (< 1.2 triệu cho căn hộ đầy đủ tiện nghi) -> rủi ro cao.
    - Thiếu diện tích hoặc thông tin mập mờ -> tăng điểm rủi ro.
    """
    risk = 0.0
    combined = f"{title} {desc}".lower()
    
    # Giá thấp bất thường
    if price > 0 and price < 1200000 and any(k in combined for k in ["chung cư", "studio", "full đồ"]):
        risk += 40.0
    elif price > 0 and price < 800000:
        risk += 25.0
        
    # Diện tích bất thường
    if area and (area < 8 or area > 150):
        risk += 20.0
    elif not area:
        risk += 15.0
        
    # Dấu hiệu câu khách / môi giới không rõ ràng
    if any(k in combined for k in ["cắt lỗ", "giá sốc", "thuê gấp trong ngày", "siêu rẻ"]):
        risk += 15.0
        
    return min(100.0, risk)

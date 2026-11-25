import datetime
import re
import unicodedata
from typing import Any, Dict, Optional, Tuple

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
    "Huyện Đông Anh": (21.1350, 105.8450),
}

SPAM_PATTERNS = ("cắt lỗ", "giá sốc", "thuê gấp trong ngày", "siêu rẻ", "inbox nhận phòng", "ib ngay")


def strip_vietnamese_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để so sánh chuẩn hóa phục vụ khử trùng lặp."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalize_title_for_dedup(title: str) -> str:
    """Chuẩn hóa tiêu đề tin đăng thành chuỗi chữ thường không dấu, bỏ ký tự đặc biệt."""
    cleaned = strip_vietnamese_accents((title or "").lower())
    cleaned = re.sub(r'[^a-z0-9\s]', ' ', cleaned)
    return re.sub(r'\s+', ' ', cleaned).strip()


def is_valid_listing(item: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Kiểm tra tính hợp lệ của tin đăng trước khi nạp vào Data Warehouse (đảm bảo KPI >= 95%):
    - Tiêu đề tối thiểu 8 ký tự, không phải chuỗi rác.
    - Giá thuê nằm trong ngưỡng hợp lý của thị trường Hà Nội (300.000đ - 80.000.000đ/tháng).
    - Diện tích (nếu có) trong khoảng 5 m² - 500 m².
    """
    title = (item.get("title") or "").strip()
    if len(title) < 8:
        return False, "Tiêu đề quá ngắn hoặc trống"

    try:
        price = float(item.get("price") or 0)
    except (TypeError, ValueError):
        return False, "Giá thuê không hợp lệ"

    if price < 300_000 or price > 80_000_000:
        return False, f"Giá thuê ngoài ngưỡng hợp lý ({price})"

    area = item.get("area")
    if area is not None:
        try:
            area_val = float(area)
            if area_val <= 0:
                pass
            elif area_val < 5 or area_val > 500:
                return False, f"Diện tích ngoài ngưỡng hợp lý ({area_val})"
        except (TypeError, ValueError):
            return False, "Diện tích không hợp lệ"

    return True, "OK"


def parse_timestamp_to_dt(val: Any) -> Optional[datetime.datetime]:
    """Chuyển đổi epoch ms/s (Chợ Tốt) hoặc chuỗi ISO sang datetime UTC."""
    if val is None or val == "":
        return None
    if isinstance(val, datetime.datetime):
        return val if val.tzinfo else val.replace(tzinfo=datetime.timezone.utc)
    try:
        if isinstance(val, (int, float)) or (isinstance(val, str) and val.isdigit()):
            num = float(val)
            if num > 1e12:
                num /= 1000.0
            if num > 1e9:
                return datetime.datetime.fromtimestamp(num, tz=datetime.timezone.utc)
        if isinstance(val, str):
            return datetime.datetime.fromisoformat(val.replace("Z", "+00:00"))
    except Exception:
        return None
    return None


def normalize_district_name(district_raw: str) -> str:
    """Chuẩn hóa tên quận/huyện thành format chuẩn có tiền tố Quận/Huyện."""
    if not district_raw:
        return "Quận Đống Đa"
    d = district_raw.strip()

    districts = [
        "Đống Đa", "Cầu Giấy", "Thanh Xuân", "Hai Bà Trưng", "Ba Đình",
        "Hoàn Kiếm", "Hoàng Mai", "Nam Từ Liêm", "Bắc Từ Liêm",
        "Hà Đông", "Long Biên", "Tây Hồ",
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


def extract_amenities(title: str, desc: str, llm_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Bóc tách các tiện nghi từ tiêu đề, mô tả và kết hợp kết quả từ Google Gemini (nếu có).
    """
    combined = f"{title} {desc}".lower()
    base = {
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
        "raw_amenities": [],
    }
    if llm_data:
        for key in list(base.keys()):
            if key != "raw_amenities" and isinstance(llm_data.get(key), bool):
                base[key] = base[key] or llm_data[key]
        if isinstance(llm_data.get("extra_amenities"), list):
            base["raw_amenities"] = llm_data["extra_amenities"]
    return base


def estimate_monthly_total_cost(
    price: float,
    electricity_cost: Optional[float],
    water_cost: Optional[float],
    service_cost: Optional[float],
) -> float:
    """
    Ước tính tổng chi phí thuê hàng tháng (VNĐ) minh bạch:
    - Nếu giá điện < 15.000 (theo kWh), nhân định mức sinh viên ~70 kWh/tháng; ngược lại cộng trực tiếp.
    - Nếu giá nước < 50.000 (theo m³), nhân định mức ~3 m³/tháng; ngược lại cộng trực tiếp.
    - Nếu hoàn toàn không có thông tin điện/nước/dịch vụ, cộng mức sinh hoạt tham chiếu 450.000đ.
    """
    if price <= 0:
        return 0.0

    if electricity_cost is None and water_cost is None and service_cost is None:
        return round(price + 450_000.0, 2)

    elec_total = 0.0
    if electricity_cost is not None and electricity_cost > 0:
        elec_total = electricity_cost * 70.0 if electricity_cost < 15_000 else electricity_cost
    else:
        elec_total = 250_000.0

    water_total = 0.0
    if water_cost is not None and water_cost > 0:
        water_total = water_cost * 3.0 if water_cost < 50_000 else water_cost
    else:
        water_total = 100_000.0

    svc_total = service_cost if (service_cost is not None and service_cost >= 0) else 100_000.0
    return round(price + elec_total + water_total + svc_total, 2)


def compute_price_diff_rate(
    price_per_m2: Optional[float],
    avg_price_per_m2: Optional[float],
) -> float:
    """Tính % chênh lệch đơn giá/m² so với mặt bằng chung khu vực."""
    if not price_per_m2 or not avg_price_per_m2 or avg_price_per_m2 <= 0:
        return 0.0
    diff_pct = ((price_per_m2 - avg_price_per_m2) / avg_price_per_m2) * 100.0
    return round(max(-99.9, min(999.9, diff_pct)), 2)


def calculate_completeness_score(item: Dict[str, Any]) -> float:
    """Tính điểm mức độ đầy đủ của thông tin tin đăng (0 - 100 điểm)."""
    score = 0.0
    if item.get("title") and len(item["title"]) > 10:
        score += 15.0
    if item.get("price") and item["price"] > 0:
        score += 15.0
    if item.get("area") and item["area"] > 0:
        score += 15.0
    if item.get("district"):
        score += 10.0
    if item.get("description") and len(item["description"]) > 30:
        score += 15.0
    if item.get("images") and len(item["images"]) > 0:
        score += 15.0
    if item.get("electricity_cost") is not None or item.get("water_cost") is not None:
        score += 10.0
    if item.get("deposit_amount") is not None and item["deposit_amount"] > 0:
        score += 5.0
    return min(100.0, score)


def calculate_risk_score(
    price: float,
    area: float,
    title: str,
    desc: str,
    price_diff_rate: float = 0.0,
    is_promoted: bool = False,
) -> float:
    """
    Tính điểm đánh giá rủi ro tin ảo / tin mồi (0 - 100 điểm):
    - Giá quá rẻ bất thường hoặc thấp hơn mặt bằng khu vực > 35%.
    - Thiếu diện tích hoặc diện tích bất thường.
    - Ngôn từ câu khách / tin đẩy.
    """
    risk = 0.0
    combined = f"{title} {desc}".lower()

    if price > 0 and price < 1_200_000 and any(k in combined for k in ["chung cư", "studio", "full đồ"]):
        risk += 40.0
    elif price > 0 and price < 800_000:
        risk += 25.0

    if price_diff_rate <= -35.0:
        risk += 25.0
    elif price_diff_rate <= -25.0:
        risk += 15.0

    if area and (area < 8 or area > 150):
        risk += 20.0
    elif not area:
        risk += 15.0

    if any(k in combined for k in SPAM_PATTERNS):
        risk += 15.0

    if is_promoted and not area:
        risk += 5.0

    return min(100.0, risk)

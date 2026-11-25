import logging
import re
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from src.backend.config.settings import settings

logger = logging.getLogger(__name__)


class RentalExtractionResult(BaseModel):
    """Schema đầu ra có cấu trúc khi Google Gemini bóc tách thông tin tin đăng phòng trọ."""

    deposit_amount: Optional[float] = Field(
        default=None,
        description="Tiền đặt cọc tính bằng VNĐ (ví dụ cọc 1 tháng với phòng 3tr -> 3000000; null nếu không nêu)."
    )
    electricity_cost: Optional[float] = Field(
        default=None,
        description="Giá điện tính bằng VNĐ/kWh hoặc VNĐ/tháng (ví dụ 3.8k -> 3800; giá dân -> 3000; null nếu không nêu)."
    )
    water_cost: Optional[float] = Field(
        default=None,
        description="Giá nước tính bằng VNĐ/m3 hoặc VNĐ/người/tháng (ví dụ 100k/người -> 100000, 30k/khối -> 30000; null nếu không nêu)."
    )
    service_cost: Optional[float] = Field(
        default=None,
        description="Tổng phí dịch vụ hàng tháng tính bằng VNĐ (wifi, rác, vệ sinh, thang máy; null nếu không nêu)."
    )
    room_status: Literal["con_trong", "da_thue", "het_han"] = Field(
        default="con_trong",
        description="Tình trạng phòng suy ra từ mô tả."
    )
    has_air_conditioner: bool = False
    has_water_heater: bool = False
    has_washing_machine: bool = False
    has_refrigerator: bool = False
    has_private_bathroom: bool = False
    has_kitchen: bool = False
    has_balcony: bool = False
    has_elevator: bool = False
    has_parking: bool = False
    has_security: bool = False
    has_flexible_hours: bool = False
    has_mezzanine: bool = False
    extra_amenities: List[str] = Field(
        default_factory=list,
        description="Các tiện ích bổ sung khác như giường, tủ quần áo, PCCC, vân tay..."
    )


def _parse_vn_amount(num_str: str, unit_str: str) -> Optional[float]:
    """Chuyển đổi chuỗi số tiếng Việt (3.5k, 2tr, 4000) thành số tiền VNĐ."""
    try:
        val = float(num_str.replace(",", "."))
    except ValueError:
        return None
    u = (unit_str or "").lower().strip()
    if u in ("tr", "triệu", "trieu", "m"):
        return round(val * 1_000_000, 2)
    if u in ("k", "nghìn", "nghin", "ngàn", "ngan"):
        return round(val * 1_000, 2)
    if val < 20:
        return round(val * 1_000, 2) if val >= 1 else None
    return round(val, 2)


def extract_fees_regex(title: str, desc: str, listed_price: float = 0.0) -> Dict[str, Any]:
    """
    Trích xuất chi phí điện, nước, cọc, dịch vụ bằng Regex khi chưa có GEMINI_API_KEY
    hoặc làm lớp dự phòng. Không tự ý bịa số khi tin không nhắc tới (trả None).
    """
    text = f"{title}\n{desc}".lower()
    result: Dict[str, Any] = {
        "deposit_amount": None,
        "electricity_cost": None,
        "water_cost": None,
        "service_cost": None,
        "room_status": "con_trong",
        "extra_amenities": [],
    }

    # Tiền điện
    if re.search(r'điện\s*(?:giá\s*)?dân|điện\s*nhà\s*nước', text):
        result["electricity_cost"] = 3000.0
    else:
        elec_m = re.search(
            r'điện[:\s]*(\d+(?:[.,]\d+)?)\s*(k|nghìn|ngàn|đ|vnđ|vnd)?(?:/\s*(?:số|kw|kwh|ký))?',
            text,
        )
        if elec_m:
            val = _parse_vn_amount(elec_m.group(1), elec_m.group(2) or ("k" if float(elec_m.group(1).replace(",", ".")) < 20 else ""))
            if val and 1000 <= val <= 10000:
                result["electricity_cost"] = val

    # Tiền nước
    if re.search(r'nước\s*(?:giá\s*)?dân|nước\s*nhà\s*nước', text):
        result["water_cost"] = 10000.0
    else:
        water_m = re.search(
            r'nước[:\s]*(\d+(?:[.,]\d+)?)\s*(k|nghìn|ngàn|tr|triệu|đ|vnđ|vnd)?',
            text,
        )
        if water_m:
            raw_num = float(water_m.group(1).replace(",", "."))
            unit = water_m.group(2) or ("k" if raw_num < 500 else "")
            val = _parse_vn_amount(water_m.group(1), unit)
            if val and 5000 <= val <= 500000:
                result["water_cost"] = val

    # Tiền cọc
    dep_months = re.search(r'cọc\s*(\d+)\s*tháng', text)
    if dep_months and listed_price > 0:
        months = int(dep_months.group(1))
        if 1 <= months <= 6:
            result["deposit_amount"] = round(listed_price * months, 2)
    else:
        dep_amt = re.search(r'(?:đặt\s*)?cọc[:\s]*(\d+(?:[.,]\d+)?)\s*(tr|triệu|trieu|k|nghìn)', text)
        if dep_amt:
            val = _parse_vn_amount(dep_amt.group(1), dep_amt.group(2))
            if val and val >= 200000:
                result["deposit_amount"] = val

    # Phí dịch vụ
    svc_m = re.search(r'(?:phí\s*)?(?:dịch\s*vụ|dv)[:\s]*(\d+(?:[.,]\d+)?)\s*(k|nghìn|ngàn|tr|triệu)?', text)
    if svc_m:
        raw_num = float(svc_m.group(1).replace(",", "."))
        unit = svc_m.group(2) or ("k" if raw_num < 1000 else "")
        val = _parse_vn_amount(svc_m.group(1), unit)
        if val is not None and 0 <= val <= 2000000:
            result["service_cost"] = val

    if re.search(r'đã\s*(?:cho\s*)?thuê|hết\s*phòng', text):
        result["room_status"] = "da_thue"

    return result


class GeminiRentalExtractor:
    """
    Dịch vụ gọi Google Gemini (Interactions API với Structured Output JSON)
    để trích xuất chi phí thuê và tiện nghi từ mô tả tin đăng phòng trọ.
    """

    def __init__(self):
        self.api_key = (settings.GEMINI_API_KEY or "").strip()
        self.model = settings.GEMINI_MODEL
        self._client = None
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning("Không thể khởi tạo Google GenAI Client: %s", e)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def extract(self, title: str, description: str, listed_price: float = 0.0) -> Dict[str, Any]:
        """
        Trích xuất thông tin có cấu trúc bằng Google Gemini; tự động fallback sang Regex
        nếu chưa cấu hình GEMINI_API_KEY hoặc API gặp lỗi.
        """
        if not self.is_available or not (title or description):
            regex_res = extract_fees_regex(title, description, listed_price)
            regex_res["extraction_source"] = "regex"
            return regex_res

        prompt = (
            "Phân tích tin đăng cho thuê nhà/phòng trọ tại Hà Nội dưới đây và trích xuất "
            "chính xác các khoản phí, tình trạng phòng và tiện nghi. Nếu tin đăng không đề cập "
            "khoản phí nào thì trả về null cho khoản phí đó (không tự suy đoán).\n\n"
            f"Giá niêm yết tham chiếu: {int(listed_price)} VNĐ/tháng\n"
            f"Tiêu đề: {title}\n"
            f"Mô tả: {description[:3000]}"
        )

        try:
            interaction = self._client.interactions.create(
                model=self.model,
                input=prompt,
                store=False,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": RentalExtractionResult.model_json_schema(),
                },
            )
            parsed = RentalExtractionResult.model_validate_json(interaction.output_text)
            data = parsed.model_dump()
            data["extraction_source"] = "gemini"
            return data
        except Exception as e:
            logger.warning("Gemini extraction thất bại, chuyển sang regex fallback: %s", e)
            regex_res = extract_fees_regex(title, description, listed_price)
            regex_res["extraction_source"] = "regex"
            return regex_res

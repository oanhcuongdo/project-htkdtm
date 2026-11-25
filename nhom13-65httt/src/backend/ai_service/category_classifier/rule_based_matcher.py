from typing import Optional, Dict, Any
from .vietnamese_text import preprocess_banking_text

CATEGORY_NAMES = {
    1: "Ăn uống & Cà phê",
    2: "Tiền thuê nhà & Phòng trọ",
    3: "Điện nước & Internet",
    4: "Xăng xe & Đi lại",
    5: "Chăm sóc sức khỏe & Y tế",
    6: "Mua sắm & Đồ dùng",
    7: "Giải trí & Phim ảnh",
    8: "Gặp gỡ bạn bè & Tiệc tùng",
    9: "Du lịch & Nghỉ dưỡng",
    10: "Quỹ tiết kiệm dự phòng",
    11: "Chứng khoán & Tích lũy",
    12: "Lương cố định hàng tháng",
    13: "Thưởng & Thu nhập ngoài (Freelance)",
    14: "Lãi tiền gửi & Cổ tức",
    15: "Chuyển tiền nội bộ giữa các ví",
}


class RuleBasedMatcher:
    """
    Bộ phân loại nhanh bằng luật từ khóa có độ chính xác cao (High-Precision Fast Path)
    trước khi chuyển các mô tả phức tạp sang mô hình Machine Learning NLP.
    """

    HIGH_PRECISION_RULES = [
        (["momo cashin", "ap cashin", "bank2wallet", "nap tien vi", "nap vi momo", "chuyen tien noi bo"], 15, 0.99),
        (["tra lai tien gui", "lai tien gui", "co tuc chung khoan"], 14, 0.99),
        (["tra luong thang", "thanh toan luong", "nhan luong", "salary"], 12, 0.98),
        (["highlands coffee", "phuc long", "starbucks", "the coffee house", "winmart"], 1, 0.97),
        (["evn", "hoa don tien dien", "tien nuoc sinh hoat", "viettel topup", "iris topup", "muathecao"], 3, 0.97),
        (["cgv cinemas", "lotte cinema", "galaxy cinema", "netflix"], 7, 0.97),
        (["petrolimex", "pvoil", "grabbike", "grabcar", "xanh sm"], 4, 0.96),
        (["nha thuoc long chau", "pharmacity", "thu phi gia han bao hiem"], 5, 0.96),
        (["gui tiet kiem online", "trich gui tiet kiem"], 10, 0.98),
    ]

    @classmethod
    def match(cls, raw_description: str, counterparty: str = "") -> Optional[Dict[str, Any]]:
        cleaned = preprocess_banking_text(raw_description, counterparty)
        for keywords, cat_id, conf in cls.HIGH_PRECISION_RULES:
            for kw in keywords:
                if kw in cleaned:
                    return {
                        "category_id": cat_id,
                        "category_name": CATEGORY_NAMES.get(cat_id, "Khác"),
                        "confidence": conf,
                        "method": "rule_based",
                        "matched_keyword": kw,
                        "preprocessed_text": cleaned,
                    }
        return None

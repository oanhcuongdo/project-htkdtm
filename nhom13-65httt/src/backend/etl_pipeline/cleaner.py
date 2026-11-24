import re
import unicodedata
from typing import Optional, Tuple


class DataCleaner:
    """Làm sạch văn bản tiếng Việt (Unicode NFC), loại bỏ mã rác ngân hàng và suy luận danh mục sơ bộ."""

    INTERNAL_TRANSFER_KEYWORDS = [
        "momo-cashin",
        "ap-cashin",
        "bank2wallet",
        "nap tien vi",
        "nap vi momo",
        "nap vi zalopay",
        "chuyen tien noi bo",
        "rut tien tu vi",
    ]

    # Bảng ánh xạ từ khóa -> (category_id, merchant_id) khớp với 01_seed_master_data.sql
    CATEGORY_RULES = [
        (["tra lai tien gui", "lai tien gui", "co tuc"], 14, None),
        (["luong", "salary", "tra luong"], 12, 10),
        (["nha tro", "tien nha", "phong tro", "thue nha"], 2, 8),
        (["evn", "tien dien", "tien nuoc", "internet", "fpt", "vnpt", "topup", "muathecao", "napthe", "iris"], 3, 9),
        (["highlands", "ca phe", "cafe"], 1, 4),
        (["phuc long", "tra sua"], 1, 5),
        (["winmart", "sieu thi", "bach hoa"], 1, 6),
        (["sinh to", "an trua", "an toi", "com ", "bun ", "pho ", "an uong", "do an"], 1, None),
        (["grab", "be ", "xanh sm", "do xang", "petrolimex", "gui xe"], 4, 3),
        (["bao hiem", "thu phi gia han bh", "nha thuoc", "long chau", "y te", "benh vien"], 5, None),
        (["shopee", "shopeepay"], 6, 1),
        (["lazada"], 6, 2),
        (["cgv", "xem phim", "netflix", "ve phim"], 7, 7),
        (["lien hoan", "lau", "bia ", "nhau", "tiec", "sinh nhat"], 8, None),
        (["tiet kiem", "gui tiet kiem"], 10, None),
    ]

    @staticmethod
    def normalize_unicode(text: str) -> str:
        if not text:
            return ""
        return unicodedata.normalize("NFC", text).strip()

    @classmethod
    def clean_description(cls, raw_desc: str, counterparty: Optional[str] = None) -> str:
        text = cls.normalize_unicode(raw_desc)
        # Loại bỏ tiền tố hệ thống ngân hàng phổ biến (CUSTOMER, MBVCB.xxx, Ma GD...)
        text = re.sub(r"^(?:CUSTOMER|MBVCB\.\d+|MBCT|MB\.\d+)\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", " ", text).strip(" .-/")

        if counterparty and counterparty.lower() not in text.lower():
            cp_clean = cls.normalize_unicode(counterparty)
            return f"{text} ({cp_clean})" if text else cp_clean
        return text or "Giao dịch ngân hàng"

    @classmethod
    def is_internal_transfer(cls, raw_desc: str, counterparty: Optional[str] = None) -> bool:
        combined = f"{raw_desc} {counterparty or ''}".lower()
        return any(kw in combined for kw in cls.INTERNAL_TRANSFER_KEYWORDS)

    @classmethod
    def infer_category_and_merchant(
        cls, raw_desc: str, counterparty: Optional[str], direction: str, is_internal: bool
    ) -> Tuple[int, Optional[int]]:
        if is_internal:
            return 15, None  # Chuyển tiền nội bộ giữa các ví

        combined = f"{raw_desc} {counterparty or ''}".lower()

        for keywords, cat_id, merch_id in cls.CATEGORY_RULES:
            if any(kw in combined for kw in keywords):
                return cat_id, merch_id

        # Fallback mặc định theo chiều dòng tiền
        if direction == "INCOME":
            return 13, None  # Thưởng & Thu nhập ngoài / Chuyển khoản đến
        return 1, None  # Mặc định chi tiêu sinh hoạt (Ăn uống / Khác)

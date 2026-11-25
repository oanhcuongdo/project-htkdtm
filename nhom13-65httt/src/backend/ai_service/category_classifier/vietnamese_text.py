import re
import unicodedata

# Từ điển mở rộng viết tắt phổ biến trong nội dung chuyển khoản tiếng Việt
VN_ABBREVIATIONS = {
    "ck": "chuyen khoan",
    "cty": "cong ty",
    "cf": "ca phe",
    "cafe": "ca phe",
    "ts": "tra sua",
    "bh": "bao hiem",
    "gd": "giao dich",
    "hd": "hoa don",
    "tt": "thanh toan",
    "dv": "dich vu",
    "dt": "dien thoai",
    "nh": "ngan hang",
    "tk": "tai khoan",
    "nt": "nha tro",
    "vp": "van phong",
    "sv": "sinh vien",
    "bv": "benh vien",
    "st": "sieu thi",
    "tx": "taxi",
    "xn": "xet nghiem",
}


def strip_vietnamese_accents(text: str) -> str:
    """Chuyển chuỗi tiếng Việt có dấu sang không dấu đồng nhất cho NLP."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def preprocess_banking_text(text: str, counterparty: str = "") -> str:
    """
    Tiền xử lý chuỗi mô tả chuyển khoản ngân hàng Việt Nam:
    - Gộp thông tin đối tác thụ hưởng (nếu có)
    - Chuẩn hóa không dấu, chữ thường
    - Loại bỏ mã giao dịch tự sinh (MBVCB.123456, FT26244..., số dài > 5 chữ số)
    - Mở rộng các từ viết tắt phổ biến
    """
    combined = f"{text or ''} {counterparty or ''}".strip()
    normalized = strip_vietnamese_accents(combined).lower()

    # Loại bỏ mã tham chiếu ngân hàng và chuỗi số dài (không nuốt từ chữ đứng sau dấu chấm)
    normalized = re.sub(r"\b(?:mbvcb|vcb|mbct|ft|acsp|trace|ref)(?:[.\-/]?\d+)+\b", " ", normalized)
    normalized = re.sub(r"\b(?:mbvcb|mbct|acsp|ma\s*gd)\b", " ", normalized)
    normalized = re.sub(r"\b\d{5,}\b", " ", normalized)
    normalized = re.sub(r"\bcustomer\b", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Mở rộng từ viết tắt theo token
    tokens = []
    for tok in normalized.split():
        # Chuẩn hóa dạng t1..t12 -> thang
        if re.match(r"^t(?:1[0-2]|[1-9])$", tok):
            tokens.append("thang")
        elif tok in VN_ABBREVIATIONS:
            tokens.append(VN_ABBREVIATIONS[tok])
        else:
            tokens.append(tok)

    return " ".join(tokens)

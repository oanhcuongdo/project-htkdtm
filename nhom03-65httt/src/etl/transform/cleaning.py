"""Hàm làm sạch thuần (không cần CSDL) cho ETL đánh giá.

Theo docs/dao_duc_phap_ly.md mục 3: che số điện thoại và email trong văn bản trước khi lưu ở lớp clean.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timedelta, timezone

# Giờ Việt Nam (UTC+7) để gán ngày cho đánh giá.
VN_TZ = timezone(timedelta(hours=7))

_ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿\x00"), None)
_WHITESPACE = re.compile(r"\s+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# Số điện thoại Việt Nam: 0xxxxxxxxx hoặc +84xxxxxxxxx, cho phép dấu cách, chấm, gạch nối giữa các nhóm số.
_PHONE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[\s.\-]?\d){8,10}(?!\d)")
_NON_WORD = re.compile(r"[\W_]+", re.UNICODE)


def normalize_text(text: str | None) -> str:
    """Chuẩn hóa Unicode (NFC), bỏ ký tự vô hình, gộp khoảng trắng, cắt hai đầu."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text).translate(_ZERO_WIDTH)
    return _WHITESPACE.sub(" ", text).strip()


def mask_pii(text: str) -> str:
    """Che email và số điện thoại bằng nhãn cố định."""
    text = _EMAIL.sub("[EMAIL]", text)
    return _PHONE.sub("[SDT]", text)


def clean_text(text: str | None) -> str:
    """Chuẩn hóa rồi che thông tin cá nhân. Trả chuỗi rỗng nếu không còn nội dung."""
    return mask_pii(normalize_text(text))


def text_hash(text: str) -> str:
    """Băm nội dung đã chuẩn hóa (không phân biệt hoa thường, bỏ dấu câu) để phát hiện trùng nội dung."""
    canonical = _NON_WORD.sub(" ", text.casefold()).strip()
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def parse_rating(value: str | None) -> int | None:
    """Số sao 1 đến 5; giá trị khác hoặc rỗng (ví dụ bình luận YouTube) trả None."""
    if value is None or str(value).strip() == "":
        return None
    try:
        rating = int(float(str(value).strip()))
    except ValueError:
        return None
    return rating if 1 <= rating <= 5 else None


def parse_int(value: str | None) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


def parse_timestamp(value: str | None) -> datetime | None:
    """Đọc thời điểm ISO 8601; thiếu múi giờ thì coi là UTC."""
    if value is None or str(value).strip() == "":
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def to_time_key(moment: datetime | None) -> int | None:
    """Khóa ngày dạng yyyymmdd theo giờ Việt Nam, khớp dw.dim_time.time_key."""
    if moment is None:
        return None
    local = moment.astimezone(VN_TZ)
    return local.year * 10000 + local.month * 100 + local.day

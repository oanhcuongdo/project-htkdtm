import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from ingestion.models import RawTransactionDTO


class BankEmailParser(ABC):
    """Lớp cơ sở cho tất cả các bộ phân tích email biến động số dư."""

    bank_name: str = "UNKNOWN"

    @abstractmethod
    def can_parse(self, sender: str, subject: str, body_text: str) -> bool:
        pass

    @abstractmethod
    def parse(self, sender: str, subject: str, body_text: str) -> Optional[RawTransactionDTO]:
        pass

    @staticmethod
    def strip_html(html: str) -> str:
        """Loại bỏ thẻ HTML giữ lại nội dung văn bản sạch."""
        text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def parse_signed_amount(sign_str: str, number_str: str) -> float:
        """Chuyển chuỗi số tiền (ví dụ '150,000' hoặc '150.000') kèm dấu +/- thành float."""
        clean_num = re.sub(r"[^\d]", "", number_str)
        if not clean_num:
            raise ValueError(f"Không trích xuất được số tiền từ: {number_str}")
        val = float(clean_num)
        return -val if sign_str.strip() == "-" else val

    @staticmethod
    def parse_datetime_vn(dt_str: str) -> datetime:
        """Phân tích ngày giờ định dạng phổ biến tại Việt Nam."""
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M"):
            try:
                return datetime.strptime(dt_str.strip(), fmt)
            except ValueError:
                continue
        return datetime.now()

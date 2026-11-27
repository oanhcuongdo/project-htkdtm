import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
import unicodedata

from PIL import Image, ImageOps
import pytesseract

from ingestion.models import RawTransactionDTO

VN_TZ = timezone(timedelta(hours=7))
AMOUNT_PATTERN = r"(?:\d{1,3}(?:[.,\s]\d{3})+|\d+)(?:[.,]\d{1,2})?"


class ReceiptOCREngine:
    """Trích xuất số tiền, ngày giao dịch và đơn vị bán hàng từ ảnh chụp hóa đơn / biên lai."""

    KNOWN_MERCHANTS = [
        "Highlands Coffee",
        "Phuc Long",
        "WinMart",
        "Circle K",
        "GS25",
        "Grab",
        "Shopee",
        "CGV",
        "Lotte",
        "Long Chau",
        "Co.opmart",
        "Bach Hoa Xanh",
    ]

    def extract_text_from_image(self, image_path: str) -> str:
        """Tiền xử lý ảnh (grayscale, tăng tương phản) và chạy Tesseract OCR tiếng Việt."""
        with Image.open(image_path) as img:
            gray = ImageOps.grayscale(img)
            enhanced = ImageOps.autocontrast(gray)
            return pytesseract.image_to_string(enhanced, lang="vie+eng").strip()

    @staticmethod
    def _parse_amount(raw_amount: str) -> Optional[float]:
        value = re.sub(r"\s+", "", raw_amount)
        if not value:
            return None

        separators = [separator for separator in (".", ",") if separator in value]
        if len(separators) == 2:
            decimal_separator = max(separators, key=value.rfind)
            decimal_digits = len(value) - value.rfind(decimal_separator) - 1
            if decimal_digits in (1, 2):
                value = value.replace("." if decimal_separator == "," else ",", "")
                value = value.replace(decimal_separator, ".")
            else:
                value = value.replace(".", "").replace(",", "")
        elif separators:
            separator = separators[0]
            decimal_digits = len(value) - value.rfind(separator) - 1
            if value.count(separator) > 1 or decimal_digits == 3:
                value = value.replace(separator, "")
            else:
                value = value.replace(separator, ".")

        try:
            amount = Decimal(value)
        except InvalidOperation:
            return None
        if amount <= 0 or amount > Decimal("500000000"):
            return None
        return float(amount)

    @staticmethod
    def _parse_transaction_time(ocr_text: str) -> Tuple[Optional[datetime], bool]:
        date_match = re.search(
            r"(?<!\d)(\d{1,4}[./-]\d{1,2}[./-]\d{2,4}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?)(?!\d)",
            ocr_text,
        )
        if not date_match:
            return datetime.now(VN_TZ), True

        raw_datetime = date_match.group(1).replace("T", " ")
        formats = (
            "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
            "%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y",
            "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%d.%m.%Y",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
        )
        for date_format in formats:
            try:
                return datetime.strptime(raw_datetime, date_format).replace(tzinfo=VN_TZ), False
            except ValueError:
                continue
        return None, False

    def parse_receipt_text(self, ocr_text: str, chat_id: int = 0) -> Optional[RawTransactionDTO]:
        """Phân tích văn bản OCR từ hóa đơn thành RawTransactionDTO."""
        if not ocr_text or not ocr_text.strip():
            return None

        # 1. Tìm số tiền tổng cộng (Ưu tiên dòng có từ khóa Tổng tiền / Thành tiền / Total / Số tiền)
        total_match = re.search(
            rf"(?:Tổng\s*tiền|Tong\s*tien|Thành\s*tiền|Thanh\s*tien|Tổng\s*cộng|Tong\s*cong|Grand\s*total|Total|Số\s*tiền|So\s*tien|Amount)\s*[:\-]?\s*({AMOUNT_PATTERN})\s*(?:VND|VNĐ|đ|d)?",
            ocr_text,
            re.IGNORECASE,
        )
        amount_val = None
        if total_match:
            amount_val = self._parse_amount(total_match.group(1))
        else:
            # Fallback chỉ xét số có dấu phân nhóm để tránh nhầm năm hoặc mã giao dịch.
            candidates = re.findall(r"\b(\d{1,3}(?:[.,]\d{3})+)\b", ocr_text)
            parsed_nums = [self._parse_amount(candidate) for candidate in candidates]
            valid_nums = [number for number in parsed_nums if number is not None and number >= 1000]
            if valid_nums:
                amount_val = max(valid_nums)

        if amount_val is None:
            return None

        tx_time, inferred_time = self._parse_transaction_time(ocr_text)
        if tx_time is None:
            return None

        # 3. Nhận diện Merchant và nội dung giao dịch
        merchant = None
        normalized_text = unicodedata.normalize("NFC", ocr_text)
        low_text = normalized_text.lower()
        for m in self.KNOWN_MERCHANTS:
            if m.lower() in low_text:
                merchant = m
                break

        content_match = re.search(
            r"(?:Nội\s*dung|Noi\s*dung|Ghi\s*chú|Ghi\s*chu|Mô\s*tả|Mo\s*ta|Description|Details)\s*[:\-]\s*(.+)",
            normalized_text,
            re.IGNORECASE,
        )
        if content_match:
            description = content_match.group(1).strip()
        else:
            ignored_line = re.compile(
                r"(?:tổng\s*(?:tiền|cộng)|tong\s*(?:tien|cong)|thành\s*tiền|"
                r"total|số\s*tiền|so\s*tien|amount|cashier|receipt|biên\s*lai|"
                r"cảm\s*ơn|cam\s*on)",
                re.IGNORECASE,
            )
            date_pattern = re.compile(r"\d{1,4}[./-]\d{1,2}[./-]\d{2,4}")
            candidates = [
                line.strip()
                for line in normalized_text.splitlines()
                if len(line.strip()) > 2
                and not ignored_line.search(line)
                and not date_pattern.search(line)
                and not (merchant and line.strip().lower() == merchant.lower())
            ]
            description = candidates[0] if candidates else "Giao dịch tại cửa hàng"

        if merchant and merchant.lower() not in description.lower():
            description = f"{merchant} - {description}"
        description = re.sub(r"\s+", " ", description).strip()
        desc = f"Thanh toán: {description[:180]}"

        return RawTransactionDTO(
            bank_name="CASH",
            account_number_mask="N/A",
            transaction_time=tx_time,
            amount=-amount_val,
            direction="EXPENSE",
            raw_description=desc,
            counterparty_name=merchant,
            reference_code=None,
            source_type="TELEGRAM",
            raw_metadata={
                "chat_id": chat_id,
                "ocr_length": len(ocr_text),
                "transaction_time_inferred": inferred_time,
            },
        )

    def process_image(self, image_path: str, chat_id: int = 0) -> Tuple[str, Optional[RawTransactionDTO]]:
        ocr_text = self.extract_text_from_image(image_path)
        dto = self.parse_receipt_text(ocr_text, chat_id=chat_id)
        return ocr_text, dto

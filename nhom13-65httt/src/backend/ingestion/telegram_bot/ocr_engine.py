import logging
import re
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ImageOps
import pytesseract

from ingestion.models import RawTransactionDTO

logger = logging.getLogger(__name__)


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
        try:
            img = Image.open(image_path)
            gray = ImageOps.grayscale(img)
            enhanced = ImageOps.autocontrast(gray)
            text = pytesseract.image_to_string(enhanced, lang="vie+eng")
            return text.strip()
        except Exception as exc:
            logger.error(f"Lỗi OCR khi đọc ảnh {image_path}: {exc}")
            return ""

    def parse_receipt_text(self, ocr_text: str, chat_id: int = 0) -> Optional[RawTransactionDTO]:
        """Phân tích văn bản OCR từ hóa đơn thành RawTransactionDTO."""
        if not ocr_text or not ocr_text.strip():
            return None

        # 1. Tìm số tiền tổng cộng (Ưu tiên dòng có từ khóa Tổng tiền / Thành tiền / Total / Số tiền)
        total_match = re.search(
            r"(?:Tổng tiền|Tong tien|Thành tiền|Thanh tien|Total|Số tiền|So tien)\s*[:\-]?\s*([\d\.,]+)\s*(?:VND|VNĐ|đ|d)?",
            ocr_text,
            re.IGNORECASE,
        )
        amount_val = 0.0
        if total_match:
            clean_digits = re.sub(r"[^\d]", "", total_match.group(1))
            amount_val = float(clean_digits) if clean_digits else 0.0
        else:
            # Fallback: lấy số tiền lớn nhất hợp lệ (>= 1000) xuất hiện trong biên lai
            candidates = re.findall(r"\b(\d{1,3}(?:[.,]\d{3})+)\b", ocr_text)
            parsed_nums = [float(re.sub(r"[^\d]", "", c)) for c in candidates]
            valid_nums = [n for n in parsed_nums if 1000 <= n <= 500_000_000]
            if valid_nums:
                amount_val = max(valid_nums)

        if amount_val <= 0:
            return None

        # 2. Tìm ngày giờ trên biên lai
        dt_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)", ocr_text)
        tx_time = datetime.now()
        if dt_match:
            raw_dt = dt_match.group(1).replace("-", "/")
            for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
                try:
                    tx_time = datetime.strptime(raw_dt, fmt)
                    break
                except ValueError:
                    continue

        # 3. Nhận diện Merchant
        merchant = None
        low_text = ocr_text.lower()
        for m in self.KNOWN_MERCHANTS:
            if m.lower() in low_text:
                merchant = m
                break

        first_line = next((line.strip() for line in ocr_text.splitlines() if len(line.strip()) > 3), "Biên lai OCR")
        desc = f"Hóa đơn {merchant}: {first_line[:120]}" if merchant else f"Biên lai OCR: {first_line[:150]}"

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
            raw_metadata={"chat_id": chat_id, "ocr_length": len(ocr_text)},
        )

    def process_image(self, image_path: str, chat_id: int = 0) -> Tuple[str, Optional[RawTransactionDTO]]:
        ocr_text = self.extract_text_from_image(image_path)
        dto = self.parse_receipt_text(ocr_text, chat_id=chat_id)
        return ocr_text, dto

import re
from typing import Optional
from ingestion.models import RawTransactionDTO
from .base_parser import BankEmailParser


class MoMoEmailParser(BankEmailParser):
    """Bộ phân tích email xác nhận thanh toán / nhận tiền Ví MoMo."""

    bank_name = "MoMo"

    def can_parse(self, sender: str, subject: str, body_text: str) -> bool:
        combined = f"{sender} {subject} {body_text}".lower()
        return "momo" in combined

    def parse(self, sender: str, subject: str, body_text: str) -> Optional[RawTransactionDTO]:
        text = self.strip_html(body_text)

        # MoMo có thể ghi "+100.000đ" hoặc "-50.000đ" hoặc "Số tiền: 50.000đ"
        amt_match = re.search(
            r"(?:Số tiền|Thanh toán|Nhận tiền)\s*[:\-]?\s*([+\-])?\s*([\d\.,]+)\s*(?:VND|đ)",
            text,
            re.IGNORECASE,
        )
        if not amt_match:
            return None

        sign = amt_match.group(1)
        if not sign:
            sign = "+" if any(w in text.lower() for w in ["nhận tiền", "nhan tien", "hoàn tiền"]) else "-"

        amount = self.parse_signed_amount(sign, amt_match.group(2))
        direction = "INCOME" if amount > 0 else "EXPENSE"

        dt_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4}\s+\d{2}:\d{2}(?::\d{2})?)", text)
        tx_time = self.parse_datetime_vn(dt_match.group(1)) if dt_match else self.parse_datetime_vn("")

        ref_match = re.search(r"(?:Mã giao dịch|Ma giao dich)\s*[:\-]?\s*(\d{8,20})", text, re.IGNORECASE)
        ref_code = ref_match.group(1) if ref_match else None

        merch_match = re.search(r"(?:Đối tác|Dịch vụ|Tại|Người nhận)\s*[:\-]\s*([^\n.;]+)", text, re.IGNORECASE)
        counterparty = merch_match.group(1).strip() if merch_match else None

        desc_match = re.search(
            r"(?:Lời nhắn|Nội dung|Chi tiết)\s*[:\-]\s*(.+?)(?=(?:Mã giao dịch|Thời gian|$))",
            text,
            re.IGNORECASE,
        )
        raw_desc = desc_match.group(1).strip() if desc_match else f"MoMo {counterparty or 'Thanh toán'}"

        return RawTransactionDTO(
            bank_name=self.bank_name,
            account_number_mask="****9999",
            transaction_time=tx_time,
            amount=amount,
            direction=direction,
            raw_description=raw_desc,
            counterparty_name=counterparty,
            reference_code=ref_code,
            source_type="EMAIL",
            raw_metadata={"sender": sender, "subject": subject},
        )

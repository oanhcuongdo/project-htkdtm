import re
from typing import Optional
from ingestion.models import RawTransactionDTO
from .base_parser import BankEmailParser


class TechcombankEmailParser(BankEmailParser):
    """Bộ phân tích email biến động số dư Techcombank."""

    bank_name = "Techcombank"

    def can_parse(self, sender: str, subject: str, body_text: str) -> bool:
        combined = f"{sender} {subject} {body_text}".lower()
        return "techcombank" in combined or "tcb" in combined

    def parse(self, sender: str, subject: str, body_text: str) -> Optional[RawTransactionDTO]:
        text = self.strip_html(body_text)

        amt_match = re.search(
            r"(?:Số tiền|So tien|Giao dịch|GD)\s*[:\-]?\s*([+\-])\s*([\d\.,]+)\s*(?:VND|đ)",
            text,
            re.IGNORECASE,
        )
        if not amt_match:
            return None

        amount = self.parse_signed_amount(amt_match.group(1), amt_match.group(2))
        direction = "INCOME" if amount > 0 else "EXPENSE"

        dt_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4}\s+\d{2}:\d{2}(?::\d{2})?)", text)
        tx_time = self.parse_datetime_vn(dt_match.group(1)) if dt_match else self.parse_datetime_vn("")

        ref_match = re.search(r"(?:Số bút toán|Ref|FT)\s*[:\-]?\s*([A-Za-z0-9._-]+)", text, re.IGNORECASE)
        ref_code = ref_match.group(1) if ref_match else None

        desc_match = re.search(
            r"(?:Nội dung|Diễn giải|Details)\s*[:\-]\s*(.+?)(?=(?:Số dư|Tài khoản|$))",
            text,
            re.IGNORECASE,
        )
        raw_desc = desc_match.group(1).strip() if desc_match else text[:250]

        return RawTransactionDTO(
            bank_name=self.bank_name,
            account_number_mask="****0000",
            transaction_time=tx_time,
            amount=amount,
            direction=direction,
            raw_description=raw_desc,
            reference_code=ref_code,
            source_type="EMAIL",
            raw_metadata={"sender": sender, "subject": subject},
        )

import re
from typing import Optional
from ingestion.models import RawTransactionDTO
from .base_parser import BankEmailParser


class MBBankEmailParser(BankEmailParser):
    """Bộ phân tích email biến động số dư Ngân hàng Quân Đội (MB Bank)."""

    bank_name = "MBBank"

    def can_parse(self, sender: str, subject: str, body_text: str) -> bool:
        combined = f"{sender} {subject} {body_text}".lower()
        return any(kw in combined for kw in ["mbbank", "mb bank", "ngân hàng quân đội", "bien dong so du mb"])

    def parse(self, sender: str, subject: str, body_text: str) -> Optional[RawTransactionDTO]:
        text = self.strip_html(body_text)

        amt_match = re.search(
            r"(?:GD|Số tiền|So tien|Biến động)\s*[:\-]?\s*([+\-])\s*([\d\.,]+)\s*(?:VND|đ)",
            text,
            re.IGNORECASE,
        )
        if not amt_match:
            return None

        amount = self.parse_signed_amount(amt_match.group(1), amt_match.group(2))
        direction = "INCOME" if amount > 0 else "EXPENSE"

        dt_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4}\s+\d{2}:\d{2}(?::\d{2})?)", text)
        tx_time = self.parse_datetime_vn(dt_match.group(1)) if dt_match else self.parse_datetime_vn("")

        acc_match = re.search(r"(?:TK|Tài khoản)\s*[:\-]?\s*([*\d]{4,20})", text, re.IGNORECASE)
        acc_mask = f"****{acc_match.group(1)[-4:]}" if acc_match else "****5678"

        ref_match = re.search(r"(FT\d{10,20}|Ma GD\s*[:\-]?\s*[A-Za-z0-9]+)", text, re.IGNORECASE)
        ref_code = ref_match.group(1).split(":")[-1].strip() if ref_match else None

        desc_match = re.search(
            r"(?:ND|Nội dung|Noi dung)\s*[:\-]\s*(.+?)(?=(?:Số dư|So du|SD|Mã GD|$))",
            text,
            re.IGNORECASE,
        )
        raw_desc = desc_match.group(1).strip() if desc_match else text[:250]

        return RawTransactionDTO(
            bank_name=self.bank_name,
            account_number_mask=acc_mask,
            transaction_time=tx_time,
            amount=amount,
            direction=direction,
            raw_description=raw_desc,
            reference_code=ref_code,
            source_type="EMAIL",
            raw_metadata={"sender": sender, "subject": subject},
        )

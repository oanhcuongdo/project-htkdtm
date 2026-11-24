import json
import os
import re
from datetime import datetime
from typing import List
import pdfplumber
from sqlalchemy import text

from api.dependencies import get_db_session
from ingestion.models import RawTransactionDTO


class StatementPDFParser:
    """Trích xuất bảng giao dịch từ file sao kê PDF bằng pdfplumber."""

    @staticmethod
    def _parse_money(val: str) -> float:
        if not val:
            return 0.0
        clean = re.sub(r"[^\d.\-]", "", val.replace(",", ""))
        try:
            return float(clean) if clean else 0.0
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_date(val: str) -> datetime:
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                return datetime.strptime(val.strip(), fmt)
            except ValueError:
                continue
        return datetime.now()

    def parse_file(self, file_path: str, bank_name: str = "VCB", save_to_staging: bool = True) -> List[RawTransactionDTO]:
        file_name = os.path.basename(file_path)
        results: List[RawTransactionDTO] = []
        staging_rows = []
        row_counter = 0

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables() or []
                for table in tables:
                    for row in table:
                        if not row or len(row) < 4:
                            continue
                        cells = [c.replace("\n", " ").strip() if c else "" for c in row]
                        # Kiểm tra xem ô đầu có chứa định dạng ngày DD/MM/YYYY không
                        if not re.match(r"^\d{2}/\d{2}/\d{4}", cells[0]):
                            continue

                        row_counter += 1
                        tx_time = self._parse_date(cells[0])

                        # Heuristic cột cho PDF sao kê phổ thông: [Ngày, Mã GD / Số tiền, Nợ/Có, Nội dung]
                        debit = self._parse_money(cells[2]) if len(cells) > 3 else 0.0
                        credit = self._parse_money(cells[3]) if len(cells) > 4 else 0.0
                        if credit > 0:
                            amount = credit
                            direction = "INCOME"
                        elif debit > 0:
                            amount = -debit
                            direction = "EXPENSE"
                        else:
                            val = self._parse_money(cells[1])
                            if val == 0:
                                continue
                            amount = val
                            direction = "INCOME" if val > 0 else "EXPENSE"

                        ref_code = cells[1] if len(cells[1]) >= 6 and not cells[1].replace(",", "").isdigit() else None
                        raw_desc = cells[-1] if cells[-1] else "Giao dịch từ sao kê PDF"

                        dto = RawTransactionDTO(
                            bank_name=bank_name,
                            account_number_mask="****1234",
                            transaction_time=tx_time,
                            amount=amount,
                            direction=direction,
                            raw_description=raw_desc,
                            reference_code=ref_code,
                            source_type="PDF",
                            raw_metadata={"file_name": file_name, "row_number": row_counter},
                        )
                        results.append(dto)

                        if save_to_staging:
                            staging_rows.append(
                                {
                                    "file_name": file_name,
                                    "file_type": "PDF",
                                    "bank_name": bank_name,
                                    "row_number": row_counter,
                                    "raw_payload": json.dumps({"cells": cells}, ensure_ascii=False),
                                    "parsed_status": "PARSED",
                                }
                            )

        if save_to_staging and staging_rows:
            with get_db_session() as db:
                for stg in staging_rows:
                    db.execute(
                        text("""
                            INSERT INTO stg_raw_statements (file_name, file_type, bank_name, row_number, raw_payload, parsed_status)
                            VALUES (:file_name, :file_type, :bank_name, :row_number, CAST(:raw_payload AS JSONB), :parsed_status)
                        """),
                        stg,
                    )

        return results

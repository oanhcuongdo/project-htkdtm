import json
import os
import re
from datetime import datetime
from typing import List, Optional, Tuple
import pandas as pd
from sqlalchemy import text

from api.dependencies import get_db_session
from ingestion.models import RawTransactionDTO


class StatementTabularParser:
    """
    Bộ phân tích sao kê dạng bảng (Excel .xlsx / .xls và CSV).
    Hỗ trợ trực tiếp mẫu Sổ phụ chi tiết của MB Bank (SAO_KE_TAI_KHOAN_1.xlsx),
    cũng như các bảng sao kê chuẩn hóa (VCB, Techcombank, MoMo).
    """

    @staticmethod
    def _parse_money(val) -> float:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return 0.0
        s = str(val).strip()
        if not s or s == "-":
            return 0.0
        # Loại bỏ dấu phẩy/dấu cách hàng nghìn và chữ VND/đ
        s_clean = re.sub(r"[^\d.\-]", "", s.replace(",", ""))
        try:
            return float(s_clean) if s_clean else 0.0
        except ValueError:
            return 0.0

    @staticmethod
    def _parse_vn_datetime(val) -> datetime:
        if isinstance(val, datetime):
            return val
        s = str(val).strip()
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return datetime.now()

    @staticmethod
    def _detect_bank_and_header(df_raw: pd.DataFrame) -> Tuple[str, Optional[str], int]:
        """Tự động nhận diện ngân hàng, số tài khoản và dòng chứa tiêu đề cột trong file Excel/CSV."""
        bank_name = "MBBank"
        acc_mask = None
        header_idx = 0

        for idx, row in df_raw.head(30).iterrows():
            row_text = " ".join(str(x) for x in row.values if pd.notna(x))
            low = row_text.lower()

            if "quân đội" in low or "military commercial" in low or "mbbank" in low:
                bank_name = "MBBank"
            elif "vietcombank" in low or "ngoại thương" in low:
                bank_name = "VCB"
            elif "techcombank" in low or "kỹ thương" in low:
                bank_name = "Techcombank"
            elif "momo" in low:
                bank_name = "MoMo"

            acc_m = re.search(r"(?:Tài khoản|Account No)\s*[:/\-]*\s*(\d{6,20})", row_text, re.IGNORECASE)
            if acc_m:
                acc_mask = f"****{acc_m.group(1)[-4:]}"

            # Dòng tiêu đề chuẩn của bảng giao dịch
            if ("ngày giao dịch" in low and ("phát sinh nợ" in low or "số tiền" in low)) or (
                "transaction date" in low and "debit" in low
            ):
                header_idx = int(idx)
                break

        return bank_name, acc_mask, header_idx

    def parse_file(self, file_path: str, save_to_staging: bool = True) -> List[RawTransactionDTO]:
        ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)

        if ext in (".xlsx", ".xls"):
            df_raw = pd.read_excel(file_path, header=None, dtype=str)
        elif ext == ".csv":
            try:
                df_raw = pd.read_csv(file_path, header=None, dtype=str, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df_raw = pd.read_csv(file_path, header=None, dtype=str, encoding="latin1")
        else:
            raise ValueError(f"Định dạng file không được hỗ trợ: {ext}")

        bank_name, acc_mask, header_idx = self._detect_bank_and_header(df_raw)

        # Đặt dòng header chuẩn và đọc dữ liệu từ phía dưới
        headers = [str(c).strip() if pd.notna(c) else f"col_{i}" for i, c in enumerate(df_raw.iloc[header_idx])]
        df = df_raw.iloc[header_idx + 1 :].copy()
        df.columns = headers
        df = df.reset_index(drop=True)

        # Bỏ qua dòng phụ đề tiếng Anh nếu có (VD: dòng ngay dưới header có chữ 'Transaction date')
        if not df.empty and str(df.iloc[0, 0]).strip().lower() in ("transaction date", "date"):
            df = df.iloc[1:].reset_index(drop=True)

        results: List[RawTransactionDTO] = []
        staging_rows = []

        # Xác định tên cột linh hoạt theo nhiều ngân hàng
        col_map = {c.lower(): c for c in df.columns}
        date_col = col_map.get("ngày giao dịch") or col_map.get("transaction date") or col_map.get("date")
        ref_col = col_map.get("số bút toán") or col_map.get("transaction no") or col_map.get("reference_code")
        debit_col = col_map.get("phát sinh nợ") or col_map.get("debit")
        credit_col = col_map.get("phát sinh có") or col_map.get("credit")
        amount_col = col_map.get("số tiền") or col_map.get("amount")
        desc_col = col_map.get("nội dung") or col_map.get("details") or col_map.get("description") or col_map.get("raw_description")
        counterparty_col = col_map.get("đơn vị thụ hưởng/ đơn vị chuyển") or col_map.get("beneficiary/applicant")
        counterparty_acc_col = col_map.get("tài khoản") or col_map.get("account")
        counterparty_bank_col = col_map.get("ngân hàng đối tác") or col_map.get("remitter bank")

        for idx, row in df.iterrows():
            raw_date = row.get(date_col) if date_col else None
            if pd.isna(raw_date) or not str(raw_date).strip():
                continue

            # Bỏ qua dòng tổng kết cuối bảng sao kê nếu có
            date_str = str(raw_date).strip()
            if any(k in date_str.lower() for k in ["tổng", "total", "số dư cuối", "ending balance", "ghi chú"]):
                continue

            debit = self._parse_money(row.get(debit_col)) if debit_col else 0.0
            credit = self._parse_money(row.get(credit_col)) if credit_col else 0.0
            single_amt = self._parse_money(row.get(amount_col)) if amount_col else 0.0

            if credit > 0:
                amount = credit
                direction = "INCOME"
            elif debit > 0:
                amount = -debit
                direction = "EXPENSE"
            elif single_amt != 0:
                amount = single_amt
                direction = "INCOME" if amount > 0 else "EXPENSE"
            else:
                continue

            tx_time = self._parse_vn_datetime(date_str)
            ref_code = str(row.get(ref_col)).strip() if ref_col and pd.notna(row.get(ref_col)) else None
            raw_desc = str(row.get(desc_col)).strip() if desc_col and pd.notna(row.get(desc_col)) else "Giao dịch sao kê"
            counterparty = str(row.get(counterparty_col)).strip() if counterparty_col and pd.notna(row.get(counterparty_col)) else None

            raw_cp_acc = str(row.get(counterparty_acc_col)).strip() if counterparty_acc_col and pd.notna(row.get(counterparty_acc_col)) else ""
            cp_acc_mask = f"****{raw_cp_acc[-4:]}" if len(raw_cp_acc) >= 4 else (raw_cp_acc or None)
            cp_bank = str(row.get(counterparty_bank_col)).strip() if counterparty_bank_col and pd.notna(row.get(counterparty_bank_col)) else None

            dto = RawTransactionDTO(
                bank_name=bank_name,
                account_number_mask=acc_mask or "****5678",
                transaction_time=tx_time,
                amount=amount,
                direction=direction,
                raw_description=raw_desc,
                counterparty_name=counterparty,
                counterparty_account_mask=cp_acc_mask,
                counterparty_bank=cp_bank,
                reference_code=ref_code,
                source_type="CSV",
                raw_metadata={"file_name": file_name, "row_number": int(idx) + 1},
            )
            results.append(dto)

            if save_to_staging:
                clean_payload = {str(k): (None if pd.isna(v) else str(v)) for k, v in row.to_dict().items()}
                staging_rows.append(
                    {
                        "file_name": file_name,
                        "file_type": "EXCEL" if ext in (".xlsx", ".xls") else "CSV",
                        "bank_name": bank_name,
                        "row_number": int(idx) + 1,
                        "raw_payload": json.dumps(clean_payload, ensure_ascii=False),
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

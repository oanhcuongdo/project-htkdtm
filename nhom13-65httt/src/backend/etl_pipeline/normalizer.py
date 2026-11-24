from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

VN_TZ = timezone(timedelta(hours=7))

VN_DAY_NAMES = {
    0: "Thứ Hai",
    1: "Thứ Ba",
    2: "Thứ Tư",
    3: "Thứ Năm",
    4: "Thứ Sáu",
    5: "Thứ Bảy",
    6: "Chủ Nhật",
}


class DataNormalizer:
    """Chuẩn hóa múi giờ Asia/Ho_Chi_Minh, số tiền và tự động ánh xạ các bảng Dimension."""

    @staticmethod
    def to_vn_datetime(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=VN_TZ)
        return dt.astimezone(VN_TZ)

    @staticmethod
    def to_date_id(dt: datetime) -> int:
        return int(dt.strftime("%Y%m%d%H"))

    @staticmethod
    def ensure_dim_date(db: Session, dt: datetime) -> int:
        vn_dt = DataNormalizer.to_vn_datetime(dt)
        date_id = DataNormalizer.to_date_id(vn_dt)

        exists = db.execute(
            text("SELECT 1 FROM dim_date WHERE date_id = :date_id"),
            {"date_id": date_id},
        ).first()

        if not exists:
            py_weekday = vn_dt.weekday()  # 0=Mon, 6=Sun
            # Quy chuẩn dim_date: 1=Chủ Nhật, 2=Thứ Hai ... 7=Thứ Bảy
            dow = 1 if py_weekday == 6 else py_weekday + 2
            db.execute(
                text("""
                    INSERT INTO dim_date (
                        date_id, full_date, year, quarter, month, day, hour,
                        day_of_week, day_name, is_weekend
                    ) VALUES (
                        :date_id, :full_date, :year, :quarter, :month, :day, :hour,
                        :dow, :day_name, :is_weekend
                    ) ON CONFLICT (date_id) DO NOTHING
                """),
                {
                    "date_id": date_id,
                    "full_date": vn_dt.date(),
                    "year": vn_dt.year,
                    "quarter": (vn_dt.month - 1) // 3 + 1,
                    "month": vn_dt.month,
                    "day": vn_dt.day,
                    "hour": vn_dt.hour,
                    "dow": dow,
                    "day_name": VN_DAY_NAMES[py_weekday],
                    "is_weekend": py_weekday >= 5,
                },
            )
        return date_id

    @staticmethod
    def resolve_account_id(db: Session, bank_name: str, account_mask: Optional[str] = None) -> int:
        row = db.execute(
            text("SELECT account_id FROM dim_account WHERE LOWER(bank_name) = LOWER(:bank) LIMIT 1"),
            {"bank": bank_name},
        ).first()
        if row:
            return int(row[0])

        acc_type = "EWALLET" if bank_name.lower() in ("momo", "zalopay", "shopeepay") else (
            "CASH" if bank_name.upper() == "CASH" else "BANK"
        )
        inserted = db.execute(
            text("""
                INSERT INTO dim_account (account_name, bank_name, account_number_mask, account_type, currency, is_active)
                VALUES (:acc_name, :bank_name, :mask, :acc_type, 'VND', TRUE)
                RETURNING account_id
            """),
            {
                "acc_name": f"Tài khoản {bank_name}",
                "bank_name": bank_name,
                "mask": account_mask or "****0000",
                "acc_type": acc_type,
            },
        ).first()
        return int(inserted[0])

    @staticmethod
    def normalize_amount_and_direction(amount: float, direction: str, is_internal: bool):
        abs_val = abs(float(amount))
        if is_internal:
            return -abs_val, "TRANSFER"
        if direction == "INCOME":
            return abs_val, "INCOME"
        return -abs_val, "EXPENSE"

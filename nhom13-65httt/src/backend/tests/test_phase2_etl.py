from datetime import datetime
from rapidfuzz.distance import JaroWinkler
from ingestion.email_collector.parsers import parse_bank_email
from ingestion.telegram_bot.ocr_engine import ReceiptOCREngine
from etl_pipeline.cleaner import DataCleaner


def test_parse_vcb_email():
    dto = parse_bank_email(
        sender="VCBDigibank@vietcombank.com.vn",
        subject="Thong bao bien dong so du TK VCB",
        body_text="Số dư TK VCB 0011001234 thay đổi -45,000 VND lúc 23/11/2026 08:30:15. Nội dung: Highlands Coffee sang. Mã GD: VCB99887766",
    )
    assert dto is not None
    assert dto.bank_name == "VCB"
    assert dto.amount == -45000.0
    assert dto.direction == "EXPENSE"
    assert dto.reference_code == "VCB99887766"


def test_parse_mbbank_email():
    dto = parse_bank_email(
        sender="noreply@mbbank.com.vn",
        subject="Bien dong so du MB Bank",
        body_text="TK 028205890000 | GD: +3,000,000 VND | 08/09/2026 07:48:40 | ND: DAO THI THIET chuyen tien nha tro | FT26251040310082",
    )
    assert dto is not None
    assert dto.bank_name == "MBBank"
    assert dto.amount == 3000000.0
    assert dto.direction == "INCOME"
    assert dto.reference_code == "FT26251040310082"


def test_parse_momo_email():
    dto = parse_bank_email(
        sender="no-reply@momo.vn",
        subject="Xac nhan thanh toan MoMo",
        body_text="Thanh toán: -55.000đ tại Phúc Long lúc 23/11/2026 14:15. Mã giao dịch: 4512345678. Nội dung: Tra sua oolong",
    )
    assert dto is not None
    assert dto.bank_name == "MoMo"
    assert dto.amount == -55000.0
    assert dto.reference_code == "4512345678"


def test_receipt_ocr_text_parser():
    ocr_sample = """
    HIGHLANDS COFFEE
    23/11/2026 09:15:00
    Phin Sua Da (L)   55,000
    Tong tien:        55,000 VND
    Cam on quy khach!
    """
    dto = ReceiptOCREngine().parse_receipt_text(ocr_sample, chat_id=12345)
    assert dto is not None
    assert dto.amount == -55000.0
    assert dto.counterparty_name == "Highlands Coffee"
    assert dto.source_type == "TELEGRAM"
    assert dto.transaction_time.isoformat() == "2026-11-23T09:15:00+07:00"
    assert "Phin Sua Da" in dto.raw_description
    assert dto.raw_metadata["transaction_time_inferred"] is False


def test_receipt_ocr_normalizes_localized_amount_and_iso_date():
    dto = ReceiptOCREngine().parse_receipt_text(
        "Description: Taxi to airport\nDate: 2026-11-23 09:15\nTotal: 1.234.567 VND"
    )
    assert dto is not None
    assert dto.amount == -1234567.0
    assert dto.transaction_time.isoformat() == "2026-11-23T09:15:00+07:00"
    assert "Taxi to airport" in dto.raw_description


def test_receipt_ocr_rejects_invalid_explicit_date():
    dto = ReceiptOCREngine().parse_receipt_text(
        "Highlands Coffee\n31/02/2026 09:15\nTotal: 55,000 VND"
    )
    assert dto is None


def test_receipt_ocr_marks_missing_date_as_inferred():
    dto = ReceiptOCREngine().parse_receipt_text("Highlands Coffee\nTotal: 55,000 VND")
    assert dto is not None
    assert dto.transaction_time.utcoffset().total_seconds() == 7 * 60 * 60
    assert dto.raw_metadata["transaction_time_inferred"] is True


def test_deduplicator_uses_exact_ten_minute_window():
    from datetime import timedelta, timezone
    from etl_pipeline.deduplicator import DeduplicationEngine

    tx_time = datetime(2026, 11, 23, 9, 15, tzinfo=timezone(timedelta(hours=7)))

    class Result:
        def first(self):
            return None

        def fetchall(self):
            return []

    class Session:
        def __init__(self):
            self.queries = []

        def execute(self, query, params):
            self.queries.append((str(query), params))
            return Result()

    db = Session()
    DeduplicationEngine.check_duplicate(db, 2, -55000, tx_time, None, "Coffee")
    sql, params = db.queries[0]
    assert "created_at BETWEEN :start_time AND :end_time" in sql
    assert params["start_time"] == tx_time - timedelta(minutes=10)
    assert params["end_time"] == tx_time + timedelta(minutes=10)


def test_cleaner_internal_transfer_and_jaro_winkler():
    assert DataCleaner.is_internal_transfer("CUSTOMER MOMO-CASHIN-0977294663") is True
    assert DataCleaner.is_internal_transfer("CUSTOMER THIEU QUANG GIA BAO chuyen tien") is False

    sim = JaroWinkler.similarity("thanh toan tien an trua", "thanh toan tien an trua cty")
    assert sim >= 0.80

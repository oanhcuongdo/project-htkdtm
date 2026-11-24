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


def test_cleaner_internal_transfer_and_jaro_winkler():
    assert DataCleaner.is_internal_transfer("CUSTOMER MOMO-CASHIN-0977294663") is True
    assert DataCleaner.is_internal_transfer("CUSTOMER THIEU QUANG GIA BAO chuyen tien") is False

    sim = JaroWinkler.similarity("thanh toan tien an trua", "thanh toan tien an trua cty")
    assert sim >= 0.80

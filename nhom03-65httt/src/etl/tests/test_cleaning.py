"""Kiểm thử các hàm làm sạch thuần (không cần CSDL)."""

import sys
from datetime import datetime, timezone
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ETL_DIR / "transform"))

import cleaning  # noqa: E402


def test_normalize_collapses_whitespace_and_strips_invisible_chars() -> None:
    assert cleaning.normalize_text("  Học ​ rất   tốt\n\n ") == "Học rất tốt"
    assert cleaning.normalize_text(None) == ""
    assert cleaning.normalize_text("   ") == ""


def test_normalize_uses_nfc_for_vietnamese() -> None:
    decomposed = "Tiếng Việt".replace("ế", "ế")  # ế viết dạng tổ hợp
    assert cleaning.normalize_text(decomposed) == "Tiếng Việt"


def test_mask_pii_hides_phone_and_email() -> None:
    masked = cleaning.mask_pii("Liên hệ 0912 345 678 hoặc +84 98 765 4321, mail abc.def@gmail.com nhé")
    assert "0912" not in masked and "4321" not in masked and "gmail" not in masked
    assert masked.count("[SDT]") == 2
    assert "[EMAIL]" in masked


def test_mask_pii_keeps_ordinary_numbers() -> None:
    text = "Mình dùng 3 tháng, được 120 điểm"
    assert cleaning.mask_pii(text) == text


def test_clean_text_returns_empty_when_only_whitespace() -> None:
    assert cleaning.clean_text(" \n\t ") == ""


def test_text_hash_ignores_case_and_punctuation() -> None:
    assert cleaning.text_hash("App hay quá!") == cleaning.text_hash("app  hay quá")
    assert cleaning.text_hash("app hay") != cleaning.text_hash("app dở")


def test_parse_rating_accepts_only_one_to_five() -> None:
    assert cleaning.parse_rating("5") == 5
    assert cleaning.parse_rating("3.0") == 3
    assert cleaning.parse_rating("") is None
    assert cleaning.parse_rating(None) is None
    assert cleaning.parse_rating("0") is None
    assert cleaning.parse_rating("6") is None
    assert cleaning.parse_rating("abc") is None


def test_parse_timestamp_and_time_key_use_vietnam_time() -> None:
    moment = cleaning.parse_timestamp("2024-03-23T18:30:00+00:00")
    assert moment == datetime(2024, 3, 23, 18, 30, tzinfo=timezone.utc)
    # 18:30 UTC là 01:30 sáng ngày 24 theo giờ Việt Nam
    assert cleaning.to_time_key(moment) == 20240324
    assert cleaning.to_time_key(None) is None


def test_parse_timestamp_rejects_bad_values_and_assumes_utc() -> None:
    assert cleaning.parse_timestamp("không phải ngày") is None
    assert cleaning.parse_timestamp("") is None
    naive = cleaning.parse_timestamp("2025-01-02T03:04:05")
    assert naive is not None and naive.tzinfo is not None

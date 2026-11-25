"""Bước 2: làm sạch văn bản từ raw.review_raw sang clean.review_text.

- Chuẩn hóa Unicode, gộp khoảng trắng, che email và số điện thoại (docs/dao_duc_phap_ly.md mục 3).
- Dòng không còn nội dung sau khi làm sạch bị loại (chỉ đếm, không lưu).
- Loại trùng theo (source, review_id); chạy lại không sinh dòng mới nếu không có dữ liệu thô mới.
Hàm không commit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

_ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ETL_DIR / "transform"))

from cleaning import clean_text, text_hash  # noqa: E402


def load_clean(conn: psycopg.Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.source, r.review_id, r.text, r.lang_guess
            FROM raw.review_raw r
            LEFT JOIN clean.review_text c ON c.source = r.source AND c.review_id = r.review_id
            WHERE c.review_key IS NULL AND r.source IS NOT NULL AND r.review_id IS NOT NULL
            """
        )
        pending = cur.fetchall()

        to_insert = []
        dropped_empty = 0
        for source, review_id, text, lang_guess in pending:
            cleaned = clean_text(text)
            if not cleaned:
                dropped_empty += 1
                continue
            to_insert.append((review_id, source, cleaned, lang_guess, text_hash(cleaned)))

        if to_insert:
            cur.executemany(
                """
                INSERT INTO clean.review_text (review_id, source, text, lang_guess, text_hash)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source, review_id) DO NOTHING
                """,
                to_insert,
            )
    return {"pending": len(pending), "inserted": len(to_insert), "dropped_empty": dropped_empty}

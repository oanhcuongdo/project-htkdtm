"""Bước 1: nạp CSV đánh giá vào raw.review_raw (nguyên văn, chưa làm sạch).

Chạy lại nhiều lần không sinh dòng trùng: dòng đã có theo (source, review_id) bị bỏ qua.
Hàm không commit; người gọi quyết định commit hoặc rollback.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import psycopg

_ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ETL_DIR / "transform"))

from cleaning import parse_int, parse_rating, parse_timestamp  # noqa: E402

REQUIRED_COLUMNS = (
    "source", "product", "review_id", "author_hash", "rating", "text", "lang_guess",
    "created_at", "app_version", "thumbs_up", "reply_text", "crawled_at",
)

STAGING_COLUMNS = REQUIRED_COLUMNS


def _row_values(row: dict[str, str]) -> tuple:
    def text_or_none(key: str) -> str | None:
        value = row.get(key)
        if value is None:
            return None
        value = value.replace("\x00", "")
        return value if value != "" else None

    rating = parse_rating(row.get("rating"))
    return (
        text_or_none("source"),
        text_or_none("product"),
        text_or_none("review_id"),
        text_or_none("author_hash"),
        rating,
        text_or_none("text"),
        text_or_none("lang_guess"),
        parse_timestamp(row.get("created_at")),
        text_or_none("app_version"),
        parse_int(row.get("thumbs_up")),
        text_or_none("reply_text"),
        parse_timestamp(row.get("crawled_at")),
    )


def read_csv_rows(path: Path) -> list[tuple]:
    csv.field_size_limit(10**9)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Tệp {path.name} thiếu cột: {', '.join(missing)}")
        return [_row_values(row) for row in reader]


def load_raw(conn: psycopg.Connection, csv_path: Path) -> dict[str, int]:
    """Nạp một tệp CSV. Trả về số dòng đọc, số dòng mới, số dòng bỏ qua vì trùng hoặc thiếu khóa."""
    all_rows = read_csv_rows(csv_path)
    # Giữ dòng đầu tiên cho mỗi (source, review_id) theo thứ tự trong tệp; bỏ dòng thiếu khóa.
    seen: set[tuple] = set()
    rows = []
    for values in all_rows:
        key = (values[0], values[2])
        if values[0] is None or values[2] is None or key in seen:
            continue
        seen.add(key)
        rows.append(values)
    columns = ", ".join(STAGING_COLUMNS)
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS stg_review")
        cur.execute("CREATE TEMP TABLE stg_review (LIKE raw.review_raw)")
        with cur.copy(f"COPY stg_review ({columns}) FROM STDIN") as copy:
            for values in rows:
                copy.write_row(values)
        cur.execute(
            f"""
            INSERT INTO raw.review_raw ({columns})
            SELECT {", ".join("s." + c for c in STAGING_COLUMNS)}
            FROM stg_review s
            WHERE s.source IS NOT NULL AND s.review_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM raw.review_raw r WHERE r.source = s.source AND r.review_id = s.review_id
              )
            """
        )
        inserted = cur.rowcount
        cur.execute("DROP TABLE IF EXISTS stg_review")
    return {"read": len(all_rows), "inserted": inserted, "skipped": len(all_rows) - inserted}

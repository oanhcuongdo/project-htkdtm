"""Nạp tin báo chí (data/raw/news/news.csv) vào clean.news_article.

Chỉ lưu tiêu đề, tên báo, đường dẫn, ngày đăng (không toàn văn). Chạy lại nhiều lần không sinh trùng:
khóa là (article_id, platform_name), trong đó article_id là title_hash có sẵn trong tệp thu thập.
Hàm không commit.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import psycopg

_ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ETL_DIR))
sys.path.insert(0, str(_ETL_DIR / "transform"))

from cleaning import normalize_text, parse_timestamp  # noqa: E402
from common import load_platforms  # noqa: E402

REQUIRED_COLUMNS = ("platform", "origin", "title", "outlet", "link", "published_at", "collected_at", "title_hash")


def read_news_rows(path: Path, known_platforms: set[str]) -> tuple[list[tuple], dict[str, int]]:
    csv.field_size_limit(10**9)
    rows: list[tuple] = []
    stats = {"read": 0, "unknown_platform": 0, "empty_title": 0, "missing_id": 0}
    seen: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Tệp {path.name} thiếu cột: {', '.join(missing)}")
        for row in reader:
            stats["read"] += 1
            platform = (row["platform"] or "").strip()
            article_id = (row["title_hash"] or "").strip()
            title = normalize_text(row["title"])
            if platform.upper() not in known_platforms:
                stats["unknown_platform"] += 1
                continue
            if not article_id:
                stats["missing_id"] += 1
                continue
            if not title:
                stats["empty_title"] += 1
                continue
            key = (article_id, platform.upper())
            if key in seen:
                continue
            seen.add(key)
            rows.append((
                article_id, platform, (row["origin"] or "").strip() or None, title,
                normalize_text(row["outlet"]) or None, (row["link"] or "").strip() or None,
                parse_timestamp(row["published_at"]), parse_timestamp(row["collected_at"]),
            ))
    return rows, stats


def load_news(conn: psycopg.Connection, csv_path: Path) -> dict[str, int]:
    platform_names = {item["id"] for item in load_platforms()}
    canonical = {name.upper(): name for name in platform_names}
    rows, stats = read_news_rows(csv_path, set(canonical))
    # đưa tên nền tảng về đúng chữ hoa thường trong cấu hình để khớp dw.dim_platform
    rows = [(r[0], canonical[r[1].upper()], *r[2:]) for r in rows]
    inserted = 0
    with conn.cursor() as cur:
        for values in rows:
            cur.execute(
                """
                INSERT INTO clean.news_article
                    (article_id, platform_name, origin, title, outlet, link, published_at, collected_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (article_id, platform_name) DO NOTHING
                """,
                values,
            )
            inserted += cur.rowcount
    stats["inserted"] = inserted
    stats["already_present"] = len(rows) - inserted
    return stats

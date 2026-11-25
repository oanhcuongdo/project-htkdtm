"""Bước 3: nạp chiều và dw.fact_review từ lớp raw và clean.

- dim_platform lấy từ config/platforms.yml (thêm nền tảng = thêm khối cấu hình, không sửa mã).
- dim_source lấy từ các giá trị `source` có trong dữ liệu thô.
- dim_time sinh theo ngày (giờ Việt Nam) phủ khoảng thời gian của dữ liệu.
- fact_review: một dòng cho mỗi đánh giá đã làm sạch có ngày và nền tảng hợp lệ.
Mọi lệnh dùng ON CONFLICT nên chạy lại không sinh trùng. Hàm không commit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg

_ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ETL_DIR))

from common import SOURCE_TYPES, load_platforms  # noqa: E402


def upsert_platforms(conn: psycopg.Connection, platforms: list[dict]) -> int:
    with conn.cursor() as cur:
        for item in platforms:
            group = item.get("platform_group")
            if group not in ("trong_nuoc", "quoc_te"):
                raise ValueError(f"Nền tảng {item.get('id')} có platform_group không hợp lệ: {group!r}")
            cur.execute(
                """
                INSERT INTO dw.dim_platform (platform_name, platform_group, play_id, ios_id)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (platform_name) DO UPDATE
                    SET platform_group = EXCLUDED.platform_group,
                        play_id = EXCLUDED.play_id,
                        ios_id = EXCLUDED.ios_id
                """,
                (item["id"], group, item.get("play_id"), item.get("ios_id")),
            )
    return len(platforms)


def upsert_sources(conn: psycopg.Connection) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT source FROM raw.review_raw WHERE source IS NOT NULL")
        names = [row[0] for row in cur.fetchall()]
        for name in names:
            cur.execute(
                """
                INSERT INTO dw.dim_source (source_name, source_type)
                VALUES (%s, %s)
                ON CONFLICT (source_name) DO NOTHING
                """,
                (name, SOURCE_TYPES.get(name, "khac")),
            )
    return len(names)


def ensure_dim_time(conn: psycopg.Connection) -> int:
    """Sinh các ngày còn thiếu từ ngày đầu của dữ liệu đến ngày cuối (hoặc hôm nay nếu muộn hơn)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT min((created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date),
                   greatest(max((created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date),
                            (now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date)
            FROM raw.review_raw WHERE created_at IS NOT NULL
            """
        )
        first, last = cur.fetchone()
        if first is None:
            return 0
        cur.execute(
            """
            INSERT INTO dw.dim_time (time_key, full_date, week, month, quarter, year)
            SELECT to_char(d, 'YYYYMMDD')::int, d::date,
                   extract(week FROM d)::smallint, extract(month FROM d)::smallint,
                   extract(quarter FROM d)::smallint, extract(year FROM d)::smallint
            FROM generate_series(%s::date, %s::date, interval '1 day') AS g(d)
            ON CONFLICT (time_key) DO NOTHING
            """,
            (first, last),
        )
        return cur.rowcount


def load_fact_review(conn: psycopg.Connection) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM clean.review_text")
        clean_total = cur.fetchone()[0]
        cur.execute(
            """
            INSERT INTO dw.fact_review (review_key, time_key, platform_key, source_key, rating, thumbs_up)
            SELECT c.review_key,
                   to_char((r.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date, 'YYYYMMDD')::int,
                   p.platform_key,
                   s.source_key,
                   CASE WHEN r.rating BETWEEN 1 AND 5 THEN r.rating END,
                   coalesce(greatest(r.thumbs_up, 0), 0)
            FROM clean.review_text c
            JOIN raw.review_raw r ON r.source = c.source AND r.review_id = c.review_id
            JOIN dw.dim_platform p ON upper(p.platform_name) = upper(r.product)
            JOIN dw.dim_source s ON s.source_name = r.source
            JOIN dw.dim_time t ON t.time_key =
                 to_char((r.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date, 'YYYYMMDD')::int
            WHERE r.created_at IS NOT NULL
            ON CONFLICT (review_key) DO NOTHING
            """
        )
        inserted = cur.rowcount
        cur.execute("SELECT count(*) FROM dw.fact_review")
        fact_total = cur.fetchone()[0]
    return {"clean_total": clean_total, "inserted": inserted, "fact_total": fact_total}


def load_dw(conn: psycopg.Connection) -> dict[str, int]:
    platforms = upsert_platforms(conn, load_platforms())
    sources = upsert_sources(conn)
    days_added = ensure_dim_time(conn)
    result = {"platforms": platforms, "sources": sources, "days_added": days_added}
    result.update(load_fact_review(conn))
    return result

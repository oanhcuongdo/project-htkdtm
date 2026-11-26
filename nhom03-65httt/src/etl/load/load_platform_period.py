"""T3: tổng hợp dw.fact_platform_period (grain: một nền tảng x một tháng) từ dw.fact_review.

Cột (đúng schema 02): new_review_count, positive_rate, negative_rate, avg_rating, sentiment_index, bhi,
review_share_in_group. time_key là ngày đầu tháng (yyyymmdd).

Hai cách xác định cảm xúc:
- `rating` (mặc định, quy ước tạm của docs/kpi_bhi.md khi chưa có mô hình): 4 đến 5 sao là tích cực, 3 sao trung tính,
  1 đến 2 sao tiêu cực; chỉ tính trên đánh giá có số sao (bình luận YouTube không có sao nên không vào tỷ lệ).
- `model`: dùng nhãn cảm xúc của mô hình M1 trong bảng chỉ đọc `dw.fact_review_sentiment` (review_key, sentiment_label
  thuộc tich_cuc, trung_tinh, tieu_cuc). Bảng này do bước chấm điểm M1 (T2) tạo; chưa có thì báo lỗi rõ ràng.

Công thức khớp src/bi/bhi.py và docs/kpi_bhi.md:
    SI  = (P - N) / T x 100                      (thang -100 đến 100)
    BHI = 0,6 x (50 + SI / 2) + 0,4 x ((avg_rating - 1) / 4 x 100)   (0 đến 100)
Chạy lại nhiều lần cho cùng kết quả (ghi đè theo khóa (nền tảng, tháng)). Hàm không commit.
"""

from __future__ import annotations

import re
from typing import Any

import psycopg
from psycopg import sql

MODEL_TABLE_DEFAULT = "dw.fact_review_sentiment"
_TABLE_NAME = re.compile(r"^[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*$")
SENTIMENT_SOURCES = ("rating", "model")


class PlatformPeriodError(RuntimeError):
    """Lỗi có thông báo rõ ràng cho người chạy."""


def ensure_month_start_dates(conn: psycopg.Connection) -> int:
    """Bảo đảm dw.dim_time có ngày đầu tháng của mọi tháng có đánh giá (time_key của fact_platform_period là khóa ngoại)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dw.dim_time (time_key, full_date, week, month, quarter, year)
            SELECT to_char(m, 'YYYYMMDD')::int, m,
                   extract(week FROM m)::smallint, extract(month FROM m)::smallint,
                   extract(quarter FROM m)::smallint, extract(year FROM m)::smallint
            FROM (SELECT DISTINCT date_trunc('month', t.full_date)::date AS m
                  FROM dw.fact_review f JOIN dw.dim_time t USING (time_key)) months
            ON CONFLICT (time_key) DO NOTHING
            """
        )
        return cur.rowcount


def _split_table(name: str) -> tuple[str, str]:
    if not _TABLE_NAME.match(name):
        raise PlatformPeriodError(f"Tên bảng không hợp lệ: {name!r} (dạng schema.bang, chữ thường)")
    schema, table = name.split(".", 1)
    return schema, table


def _model_table_exists(conn: psycopg.Connection, name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s) IS NOT NULL", (name,))
        return bool(cur.fetchone()[0])


def _query(sentiment_source: str, model_table: str) -> sql.Composed:
    """Câu INSERT ... ON CONFLICT DO UPDATE. Chỉ khác nhau ở cách đếm tích cực, tiêu cực và mẫu số."""
    if sentiment_source == "rating":
        join = sql.SQL("")
        pos = sql.SQL("count(*) FILTER (WHERE f.rating >= 4)")
        neg = sql.SQL("count(*) FILTER (WHERE f.rating <= 2)")
        base = sql.SQL("count(f.rating)")
    else:
        schema, table = _split_table(model_table)
        join = sql.SQL("LEFT JOIN {}.{} m ON m.review_key = f.review_key").format(
            sql.Identifier(schema), sql.Identifier(table))
        pos = sql.SQL("count(*) FILTER (WHERE m.sentiment_label = 'tich_cuc')")
        neg = sql.SQL("count(*) FILTER (WHERE m.sentiment_label = 'tieu_cuc')")
        base = sql.SQL("count(m.sentiment_label)")

    return sql.SQL(
        """
        WITH agg AS (
            SELECT f.platform_key,
                   date_trunc('month', t.full_date)::date AS month_start,
                   count(*)                       AS new_review_count,
                   {pos}                          AS pos,
                   {neg}                          AS neg,
                   {base}                         AS labeled,
                   avg(f.rating)                  AS avg_rating
            FROM dw.fact_review f
            JOIN dw.dim_time t ON t.time_key = f.time_key
            {join}
            GROUP BY f.platform_key, date_trunc('month', t.full_date)::date
        ), scored AS (
            SELECT a.*, p.platform_group,
                   CASE WHEN a.labeled > 0 THEN 100.0 * (a.pos - a.neg) / a.labeled END AS si,
                   a.new_review_count::numeric
                       / NULLIF(sum(a.new_review_count) OVER (PARTITION BY p.platform_group, a.month_start), 0) AS share
            FROM agg a JOIN dw.dim_platform p USING (platform_key)
        )
        INSERT INTO dw.fact_platform_period
            (platform_key, time_key, new_review_count, positive_rate, negative_rate, avg_rating,
             sentiment_index, bhi, review_share_in_group)
        SELECT s.platform_key,
               to_char(s.month_start, 'YYYYMMDD')::int,
               s.new_review_count,
               round(s.pos::numeric / NULLIF(s.labeled, 0), 4),
               round(s.neg::numeric / NULLIF(s.labeled, 0), 4),
               round(s.avg_rating, 2),
               round(s.si, 3),
               CASE WHEN s.si IS NOT NULL AND s.avg_rating IS NOT NULL
                    THEN least(100, greatest(0, round(0.6 * (50 + s.si / 2) + 0.4 * ((s.avg_rating - 1) / 4 * 100), 2)))
               END,
               round(s.share, 4)
        FROM scored s
        ON CONFLICT (platform_key, time_key) DO UPDATE SET
            new_review_count = EXCLUDED.new_review_count,
            positive_rate = EXCLUDED.positive_rate,
            negative_rate = EXCLUDED.negative_rate,
            avg_rating = EXCLUDED.avg_rating,
            sentiment_index = EXCLUDED.sentiment_index,
            bhi = EXCLUDED.bhi,
            review_share_in_group = EXCLUDED.review_share_in_group
        """
    ).format(pos=pos, neg=neg, base=base, join=join)


def build_platform_period(conn: psycopg.Connection, sentiment_source: str = "rating",
                          model_table: str = MODEL_TABLE_DEFAULT) -> dict[str, Any]:
    if sentiment_source not in SENTIMENT_SOURCES:
        raise PlatformPeriodError(f"sentiment_source phải là một trong {SENTIMENT_SOURCES}")
    if sentiment_source == "model":
        _split_table(model_table)          # từ chối tên bảng không hợp lệ trước khi chạm vào CSDL
    if sentiment_source == "model" and not _model_table_exists(conn, model_table):
        raise PlatformPeriodError(
            f"Chưa có bảng {model_table} (nhãn cảm xúc M1). Chạy bước chấm điểm M1 trước, "
            "hoặc dùng --sentiment-source rating (tạm tính theo số sao)."
        )
    if sentiment_source == "model":
        schema, table = _split_table(model_table)
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT EXISTS (SELECT 1 FROM {}.{})").format(sql.Identifier(schema), sql.Identifier(table)))
            if not cur.fetchone()[0]:
                raise PlatformPeriodError(
                    f"Bảng {model_table} đang rỗng (chưa có nhãn M1). Chấm điểm M1 trước, "
                    "hoặc dùng --sentiment-source rating."
                )
    month_dates = ensure_month_start_dates(conn)
    with conn.cursor() as cur:
        cur.execute(_query(sentiment_source, model_table))
        upserted = cur.rowcount
        cur.execute("SELECT count(*), coalesce(sum(new_review_count), 0) FROM dw.fact_platform_period")
        rows, reviews = cur.fetchone()
        cur.execute("SELECT count(*) FROM dw.fact_review")
        fact_total = cur.fetchone()[0]
    return {"sentiment_source": sentiment_source, "month_dates_added": month_dates, "rows_upserted": upserted,
            "rows_in_table": rows, "reviews_counted": int(reviews), "fact_review_total": fact_total}

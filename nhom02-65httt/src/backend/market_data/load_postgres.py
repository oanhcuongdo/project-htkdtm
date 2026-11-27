from __future__ import annotations
import os
import sys
import pandas as pd
import psycopg
from .normalize import load_dataset

INSERT_SQL = """
INSERT INTO competitor_prices (
    marketplace, external_product_id, category, title, seller, brand,
    price_vnd, original_price_vnd, discount_percent, rating, review_count,
    sold_count, product_url, confidence, observed_at, source_key
) VALUES (
    %(marketplace)s, %(external_product_id)s, %(category)s, %(title)s, %(seller)s, %(brand)s,
    %(price_vnd)s, %(original_price_vnd)s, %(discount_percent)s, %(rating)s, %(review_count)s,
    %(sold_count)s, %(product_url)s, %(confidence)s, %(observed_at)s, %(source_key)s
) ON CONFLICT (source_key, observed_at) DO NOTHING
"""

def as_optional(value):
    if pd.isna(value):
        return None
    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()
    return value

def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python -m market_data.load_postgres <csv-path>")
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required, e.g. postgresql://user:pass@localhost:5432/db")
    df = load_dataset(sys.argv[1])
    rows = []
    for row in df.to_dict(orient="records"):
        rows.append({
            "marketplace": row["marketplace"],
            "external_product_id": row["product_id"],
            "category": as_optional(row.get("category")),
            "title": row["title"],
            "seller": as_optional(row.get("seller")),
            "brand": as_optional(row.get("brand")),
            "price_vnd": float(row["price_vnd"]),
            "original_price_vnd": as_optional(row.get("original_price_vnd")),
            "discount_percent": as_optional(row.get("discount_percent")),
            "rating": as_optional(row.get("rating")),
            "review_count": as_optional(row.get("review_count")),
            "sold_count": as_optional(row.get("sold")),
            "product_url": as_optional(row.get("url")),
            "confidence": as_optional(row.get("confidence")),
            "observed_at": as_optional(row["observed_at"]),
            "source_key": row["source_key"],
        })
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(INSERT_SQL, rows)
    print(f"Đã nạp {len(rows)} bản ghi hợp lệ (bản ghi trùng được bỏ qua).")

if __name__ == "__main__":
    main()

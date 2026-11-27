from __future__ import annotations
import re
from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = {
    "marketplace", "category", "product_id", "title", "price_vnd", "observed_at"
}
OPTIONAL_TEXT = ("category", "title", "brand", "seller", "url", "currency", "fx_source")


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Dataset thiếu các cột bắt buộc: {sorted(missing)}")
    out = df.copy()
    for col in OPTIONAL_TEXT:
        if col in out.columns:
            out[col] = out[col].map(clean_text)
        else:
            out[col] = ""
    for col in ("original_price_vnd", "discount_percent", "rating", "review_count", "confidence"):
        if col not in out.columns:
            out[col] = pd.NA
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["marketplace"] = out["marketplace"].map(clean_text).str.upper()
    out["product_id"] = out["product_id"].map(clean_text)
    out["price_vnd"] = pd.to_numeric(out["price_vnd"], errors="coerce")
    out["observed_at"] = pd.to_datetime(out["observed_at"], errors="coerce", utc=True)
    out = out.dropna(subset=["marketplace", "product_id", "title", "price_vnd", "observed_at"])
    out = out[(out["marketplace"] != "") & (out["product_id"] != "") & (out["title"] != "") & (out["price_vnd"] > 0)].copy()
    out["brand_norm"] = out["brand"].str.casefold().str.strip()
    out["title_norm"] = out["title"].str.casefold()
    out["confidence"] = out["confidence"].fillna(0.5).clip(0, 1)
    out["source_key"] = out["marketplace"] + ":" + out["product_id"]
    return out.drop_duplicates(subset=["source_key", "observed_at"], keep="last").reset_index(drop=True)


def load_dataset(csv_path: str | Path) -> pd.DataFrame:
    return normalize_dataframe(pd.read_csv(csv_path))

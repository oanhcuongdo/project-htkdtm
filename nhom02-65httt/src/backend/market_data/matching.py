
from __future__ import annotations

import re
from difflib import SequenceMatcher

import pandas as pd

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


NOISE_WORDS = {
    "chinh", "hang", "gia", "re", "cao", "cap",
    "new", "moi", "sale", "official", "store"
}


def normalize_name(value: str) -> str:
    value = str(value or "").casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    tokens = [t for t in value.split() if t not in NOISE_WORDS]
    return " ".join(tokens)


def extract_model(value: str) -> str:
    """Trích xuất mã model phổ biến."""

    text = str(value or "").upper()

    # AirPods: phân biệt AirPods 4, AirPods Pro 3, AirPods Max
    airpods = re.search(
        r"\bAIRPODS?\s*(PRO\s*)?(\d+)\b", text
    )
    if airpods:
        pro = "PRO" if airpods.group(1) else ""
        return f"AIRPODS{pro}{airpods.group(2)}"

    if re.search(r"\bAIRPODS?\s+MAX\b", text):
        return "AIRPODSMAX"

    # Mã model laptop, thiết bị: X515JA, F415E...
    patterns = [
        r"\b([A-Z]{1,5}[- ]?\d{2,}[A-Z0-9-]*)\b",
        r"\b([A-Z]{1,4}\d{1,4}[A-Z]{0,3})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return re.sub(r"[^A-Z0-9]", "", match.group(1))

    return ""


def similarity(a: str, b: str) -> float:
    a_norm = normalize_name(a)
    b_norm = normalize_name(b)

    if not a_norm or not b_norm:
        return 0.0

    if fuzz:
        return float(fuzz.token_set_ratio(a_norm, b_norm))

    return SequenceMatcher(
        None, a_norm, b_norm
    ).ratio() * 100


def match_sku(
    erp_product: dict,
    competitor_product: dict
) -> dict:

    erp_name = str(
        erp_product.get("name")
        or erp_product.get("title")
        or ""
    )

    comp_name = str(
        competitor_product.get("title")
        or competitor_product.get("product_title")
        or ""
    )

    erp_brand = normalize_name(
        erp_product.get("brand") or ""
    )

    comp_brand = normalize_name(
        competitor_product.get("brand") or ""
    )

    name_score = similarity(erp_name, comp_name)

    brand_known = bool(erp_brand and comp_brand)
    brand_match = (
        erp_brand == comp_brand if brand_known else None
    )

    model_a = extract_model(erp_name)
    model_b = extract_model(comp_name)

    # Có mã model ở cả hai bên nhưng khác nhau
    model_conflict = bool(
        model_a and model_b and model_a != model_b
    )

    # ERP không có model cụ thể nhưng đối thủ có model
    model_missing_in_erp = bool(
        not model_a and model_b
    )

    brand_conflict = bool(
        brand_known and erp_brand != comp_brand
    )

    score = name_score

    if brand_conflict:
        score = min(score, 40.0)

    if model_conflict:
        score = min(score, 40.0)

    # Phân loại kết quả
    if brand_conflict or model_conflict:
        status = "REJECTED"

    elif model_missing_in_erp:
        status = "NEEDS_REVIEW"

    elif score >= 85:
        status = "MATCHED"

    elif score >= 65:
        status = "NEEDS_REVIEW"

    else:
        status = "REJECTED"

    return {
        "erp_sku": (
            erp_product.get("sku")
            or erp_product.get("product_id")
        ),
        "competitor_product_id": (
            competitor_product.get("product_id")
            or competitor_product.get("external_product_id")
        ),
        "marketplace": competitor_product.get("marketplace"),
        "score": round(score, 2),
        "name_score": round(name_score, 2),
        "brand_match": brand_match,
        "model_conflict": model_conflict,
        "erp_model": model_a or None,
        "competitor_model": model_b or None,
        "status": status,
    }


def match_catalog(
    erp_products: list[dict],
    competitor_products: pd.DataFrame,
    top_n: int = 5
) -> pd.DataFrame:

    """Tìm top-N sản phẩm đối thủ cho từng SKU ERP."""

    results = []
    candidates = competitor_products.to_dict(
        orient="records"
    )

    for erp in erp_products:
        scored = [
            match_sku(erp, cp)
            for cp in candidates
        ]

        scored.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        results.extend(scored[:max(1, int(top_n))])

    return pd.DataFrame(results)

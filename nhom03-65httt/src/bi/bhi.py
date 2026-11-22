"""Tính Brand Health Index (BHI) thuần Python, không phụ thuộc cơ sở dữ liệu."""

from __future__ import annotations

from numbers import Real
from typing import Mapping


# Trọng số mặc định: đề xuất, cần nhóm duyệt.
DEFAULT_WEIGHTS = {
    "sentiment": 0.40,
    "negative": 0.20,
    "rating": 0.40,
}


def _number(name: str, value: object) -> float:
    if value is None:
        raise ValueError(f"{name} không được để trống")
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} phải là số")
    return float(value)


def compute_bhi(
    sentiment_index: float,
    negative_rate: float,
    avg_rating: float,
    review_count: int,
    weights: Mapping[str, float] | None = None,
) -> dict[str, object]:
    """Tính BHI trên thang 0-100 và kèm cờ chất lượng dữ liệu.

    Trả về: ``{"bhi": float, "flags": list[str]}``.
    Trọng số mặc định là đề xuất và cần nhóm duyệt.
    """
    si = _number("sentiment_index", sentiment_index)
    negative = _number("negative_rate", negative_rate)
    rating = _number("avg_rating", avg_rating)
    count = _number("review_count", review_count)

    if not (-1.0 <= si <= 1.0):
        raise ValueError("sentiment_index phải nằm trong [-1, 1]")
    if not (0.0 <= negative <= 1.0):
        raise ValueError("negative_rate phải nằm trong [0, 1]")
    if not (1.0 <= rating <= 5.0):
        raise ValueError("avg_rating phải nằm trong [1, 5]")
    if count < 0:
        raise ValueError("review_count không được âm")
    if count != int(count):
        raise ValueError("review_count phải là số nguyên")

    chosen = dict(DEFAULT_WEIGHTS if weights is None else weights)
    required = {"sentiment", "negative", "rating"}
    if set(chosen) != required:
        raise ValueError("weights phải có đúng ba khóa: sentiment, negative, rating")

    numeric_weights: dict[str, float] = {}
    for name in required:
        numeric_weights[name] = _number(f"weights.{name}", chosen[name])
        if numeric_weights[name] < 0:
            raise ValueError("trọng số không được âm")

    if abs(sum(numeric_weights.values()) - 1.0) > 1e-9:
        raise ValueError("tổng trọng số phải bằng 1")

    sentiment_score = (si + 1.0) * 50.0
    negative_score = (1.0 - negative) * 100.0
    rating_score = (rating - 1.0) / 4.0 * 100.0

    weighted_score = (
        numeric_weights["sentiment"] * sentiment_score
        + numeric_weights["negative"] * negative_score
        + numeric_weights["rating"] * rating_score
    )

    # Hệ số tin cậy đạt tối đa khi có ít nhất 30 đánh giá.
    confidence = min(int(count) / 30.0, 1.0)
    bhi = 50.0 + (weighted_score - 50.0) * confidence
    bhi = max(0.0, min(100.0, bhi))

    flags: list[str] = []
    if int(count) < 30:
        flags.append("du_lieu_it")

    return {"bhi": round(bhi, 2), "flags": flags}

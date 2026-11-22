"""Tính Brand Health Index (BHI).

Công thức khớp queries/bhi_brand_health_index.sql:
BHI = 0.6 * (50 + SI / 2) + 0.4 * ((avg_rating - 1) / 4 * 100)
Trong đó SI nằm trong [-100, 100] và avg_rating nằm trong [1, 5].
"""

from __future__ import annotations

from numbers import Real
from typing import Mapping


# Trọng số mặc định: đề xuất theo đề cương, cần nhóm duyệt ở tuần 5.
DEFAULT_WEIGHTS = {
    "sentiment": 0.6,
    "rating": 0.4,
}


def _number(name: str, value: object) -> float:
    if value is None:
        raise ValueError(f"{name} không được để trống")
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} phải là số")
    return float(value)


def compute_bhi(
    sentiment_index: float,
    avg_rating: float,
    review_count: int,
    weights: Mapping[str, float] | None = None,
) -> dict[str, object]:
    """Trả về {"bhi": float, "flags": list[str]} theo công thức đề cương.

    review_count chỉ tạo cờ chất lượng khi nhỏ hơn 30, không thay đổi BHI.
    """
    si = _number("sentiment_index", sentiment_index)
    rating = _number("avg_rating", avg_rating)

    if isinstance(review_count, bool) or not isinstance(review_count, int):
        raise ValueError("review_count phải là số nguyên")
    if review_count < 0:
        raise ValueError("review_count không được âm")

    if not (-100.0 <= si <= 100.0):
        raise ValueError("sentiment_index phải nằm trong [-100, 100]")
    if not (1.0 <= rating <= 5.0):
        raise ValueError("avg_rating phải nằm trong [1, 5]")

    chosen = dict(DEFAULT_WEIGHTS if weights is None else weights)
    required = {"sentiment", "rating"}
    if set(chosen) != required:
        raise ValueError("weights phải có đúng hai khóa: sentiment, rating")

    numeric_weights: dict[str, float] = {}
    for name in required:
        numeric_weights[name] = _number(f"weights.{name}", chosen[name])
        if numeric_weights[name] < 0:
            raise ValueError("trọng số không được âm")

    if abs(sum(numeric_weights.values()) - 1.0) > 1e-9:
        raise ValueError("tổng trọng số phải bằng 1")

    sentiment_score = 50.0 + si / 2.0
    rating_score = (rating - 1.0) / 4.0 * 100.0
    bhi = (
        numeric_weights["sentiment"] * sentiment_score
        + numeric_weights["rating"] * rating_score
    )
    bhi = max(0.0, min(100.0, round(bhi, 2)))

    flags: list[str] = []
    if review_count < 30:
        flags.append("du_lieu_it")

    return {"bhi": bhi, "flags": flags}

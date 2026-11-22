import sys
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC_ROOT))

from bi.bhi import compute_bhi


def test_values_at_boundaries():
    low = compute_bhi(-1, 1, 1, 30)
    high = compute_bhi(1, 0, 5, 30)

    assert low["bhi"] == 0.0
    assert low["bhi"] >= 0
    assert high["bhi"] == 100.0
    assert high["bhi"] <= 100


def test_negative_rate_is_reversed():
    low_negative = compute_bhi(0, 0.1, 3, 30)
    high_negative = compute_bhi(0, 0.9, 3, 30)

    assert low_negative["bhi"] > high_negative["bhi"]


def test_missing_input_raises_value_error():
    with pytest.raises(ValueError, match="không được để trống"):
        compute_bhi(None, 0.2, 3, 30)


def test_invalid_weights_total_raises_value_error():
    weights = {"sentiment": 0.5, "negative": 0.2, "rating": 0.2}

    with pytest.raises(ValueError, match="tổng trọng số phải bằng 1"):
        compute_bhi(0, 0.2, 3, 30, weights)


def test_low_review_count_has_data_flag():
    result = compute_bhi(0.5, 0.2, 4, 29)

    assert "du_lieu_it" in result["flags"]
    assert 0 <= result["bhi"] <= 100


def test_result_always_stays_in_range_across_inputs():
    cases = [
        (-1, 0, 1, 0),
        (-0.5, 0.25, 2, 15),
        (0, 0.5, 3, 30),
        (0.5, 0.75, 4, 100),
        (1, 1, 5, 1000),
    ]

    for sentiment, negative, rating, count in cases:
        result = compute_bhi(sentiment, negative, rating, count)
        assert 0 <= result["bhi"] <= 100


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ((-1.1, 0.2, 3, 30), "sentiment_index"),
        ((0, 1.1, 3, 30), "negative_rate"),
        ((0, 0.2, 6, 30), "avg_rating"),
        ((0, 0.2, 3, -1), "review_count"),
    ],
)
def test_out_of_range_inputs_raise_value_error(args, message):
    with pytest.raises(ValueError, match=message):
        compute_bhi(*args)

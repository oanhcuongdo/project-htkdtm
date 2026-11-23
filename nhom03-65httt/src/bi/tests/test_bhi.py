import sys
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC_ROOT))

from bi.bhi import compute_bhi


@pytest.mark.parametrize(
    ("si", "rating", "count", "expected"),
    [
        (-100, 1, 100, 0.0),
        (100, 5, 100, 100.0),
        (0, 3, 100, 50.0),
        (50, 4, 100, 75.0),
    ],
)
def test_required_formula_examples(si, rating, count, expected):
    assert compute_bhi(si, rating, count)["bhi"] == expected


def test_low_review_count_flag_does_not_change_bhi():
    low = compute_bhi(50, 4, 10)
    normal = compute_bhi(50, 4, 100)

    assert low["flags"] == ["du_lieu_it"]
    assert low["bhi"] == normal["bhi"] == 75.0


def test_result_always_stays_in_range():
    cases = [
        (-100, 1, 0),
        (-75, 2, 15),
        (-25, 2.5, 29),
        (0, 3, 30),
        (25, 3.5, 50),
        (75, 4.5, 100),
        (100, 5, 1000),
    ]

    for si, rating, count in cases:
        result = compute_bhi(si, rating, count)
        assert 0.0 <= result["bhi"] <= 100.0


def test_missing_input_raises_value_error():
    with pytest.raises(ValueError, match="không được để trống"):
        compute_bhi(None, 3, 30)


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ((-101, 3, 30), "sentiment_index"),
        ((101, 3, 30), "sentiment_index"),
        ((0, 0.9, 30), "avg_rating"),
        ((0, 5.1, 30), "avg_rating"),
        ((0, 3, -1), "review_count"),
        ((0, 3, 3.5), "review_count"),
        (("50", 3, 30), "sentiment_index"),
    ],
)
def test_invalid_inputs_raise_value_error(args, message):
    with pytest.raises(ValueError, match=message):
        compute_bhi(*args)


def test_invalid_weights_total_raises_value_error():
    weights = {"sentiment": 0.5, "rating": 0.4}

    with pytest.raises(ValueError, match="tổng trọng số phải bằng 1"):
        compute_bhi(50, 4, 30, weights)


def test_wrong_weight_keys_raise_value_error():
    weights = {"sentiment": 0.6, "negative": 0.4}

    with pytest.raises(ValueError, match="weights phải có đúng hai khóa"):
        compute_bhi(50, 4, 30, weights)


def test_negative_weight_raises_value_error():
    weights = {"sentiment": -0.1, "rating": 1.1}

    with pytest.raises(ValueError, match="trọng số không được âm"):
        compute_bhi(50, 4, 30, weights)

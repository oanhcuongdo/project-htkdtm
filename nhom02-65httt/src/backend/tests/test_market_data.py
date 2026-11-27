import pandas as pd
import pytest
from market_data.matching import match_sku, extract_model
from market_data.simulator import simulate_price_update
from market_data.normalize import normalize_dataframe

def test_exact_product_match():
    result = match_sku({"sku": "ERP-1", "name": "Apple AirPods 4", "brand": "Apple"},
        {"product_id": "P1", "title": "Tai nghe Apple AirPods 4", "brand": "Apple", "marketplace": "TIKI"})
    assert result["status"] == "MATCHED"

def test_model_conflict_rejected():
    result = match_sku({"sku": "ERP-1", "name": "Samsung Galaxy A55", "brand": "Samsung"},
        {"product_id": "P2", "title": "Samsung Galaxy A35", "brand": "Samsung"})
    assert result["status"] == "REJECTED"

def test_model_extraction():
    assert extract_model("Samsung Galaxy A55 5G") == "A55"

def test_simulator_blocks_below_floor():
    result = simulate_price_update("SKU-1", "SHOPEE", 100, 80, 90)
    assert result["status"] == "BLOCKED_BELOW_PMIN"
    assert result["proposed_price_vnd"] == 80

def test_simulator_rejects_invalid_floor():
    with pytest.raises(ValueError):
        simulate_price_update("SKU-1", "TIKI", 100, 90, 0)

def test_normalizer_handles_optional_columns_and_whitespace():
    df = pd.DataFrame([{"marketplace":" tiki ", "category":"audio", "product_id":"1", "title":"  AirPods   4 ", "price_vnd":"1000000", "observed_at":"2026-11-22T00:00:00Z"}])
    result = normalize_dataframe(df)
    assert len(result) == 1
    assert result.iloc[0].title == "AirPods 4"
    assert result.iloc[0].marketplace == "TIKI"

def test_normalizer_deduplicates_same_snapshot():
    row = {"marketplace":"TIKI", "category":"audio", "product_id":"1", "title":"AirPods 4", "price_vnd":100, "observed_at":"2026-11-22T00:00:00Z"}
    result = normalize_dataframe(pd.DataFrame([row, row]))
    assert len(result) == 1

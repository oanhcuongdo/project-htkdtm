import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

if "supabase" not in sys.modules:
    _supabase_stub = ModuleType("supabase")
    _supabase_stub.Client = object
    _supabase_stub.create_client = MagicMock()
    sys.modules["supabase"] = _supabase_stub

from src.backend.api.main import app
from src.backend.api.services.anomaly_service import (
    analyze_listing_anomaly,
    classify_risk_level,
    list_market_anomalies,
    recalculate_market_anomalies,
)


def test_analyze_listing_anomaly_normal_listing():
    row = {
        "fact_id": "11111111-1111-1111-1111-111111111111",
        "title": "Phòng trọ khép kín full đồ gần Đại học Thủy Lợi",
        "description": "Phòng rộng rãi sạch sẽ, giờ giấc tự do, có điều hòa nóng lạnh và chỗ để xe miễn phí.",
        "price": 3_500_000,
        "area": 25.0,
        "price_per_m2": 140_000,
        "deposit_amount": 3_500_000,
        "electricity_cost": 3_500,
        "water_cost": 100_000,
        "images": ["https://example.com/a.jpg"],
        "is_promoted": False,
        "dim_location": {"district": "Quận Đống Đa"},
    }
    res = analyze_listing_anomaly(row, avg_price_per_m2=150_000, report_count=0)
    assert res["completeness_score"] == 100.0
    assert res["price_diff_rate"] == -6.67
    assert res["risk_score"] == 0.0
    assert res["risk_level"] == "low"
    assert res["risk_flags"] == []


def test_analyze_listing_anomaly_bait_listing_high_risk():
    row = {
        "fact_id": "22222222-2222-2222-2222-222222222222",
        "title": "Chung cư mini full đồ giá sốc inbox nhận phòng",
        "description": "Thuê gấp trong ngày",
        "price": 900_000,
        "area": None,
        "price_per_m2": 50_000,
        "images": [],
        "is_promoted": True,
        "dim_location": {"district": "Quận Cầu Giấy"},
    }
    res = analyze_listing_anomaly(row, avg_price_per_m2=180_000, report_count=2)
    assert res["completeness_score"] < 50.0
    assert res["price_diff_rate"] <= -35.0
    assert res["risk_score"] >= 80.0
    assert res["risk_level"] == "high"
    assert len(res["risk_flags"]) >= 4


def test_classify_risk_level_boundaries():
    assert classify_risk_level(0.0) == "low"
    assert classify_risk_level(24.9) == "low"
    assert classify_risk_level(25.0) == "medium"
    assert classify_risk_level(49.9) == "medium"
    assert classify_risk_level(50.0) == "high"


def _make_mock_db(fact_rows, report_rows):
    db = MagicMock()

    def table_side_effect(table_name):
        tbl = MagicMock()
        if table_name == "listing_reports":
            tbl.select.return_value.execute.return_value = SimpleNamespace(data=report_rows)
        elif table_name == "fact_rental_listings":
            select_chain = tbl.select.return_value
            select_chain.execute.return_value = SimpleNamespace(data=fact_rows)
            select_chain.order.return_value.execute.return_value = SimpleNamespace(data=fact_rows)
            tbl.update.return_value.eq.return_value.execute.return_value = SimpleNamespace(data=[{}])
        return tbl

    db.table.side_effect = table_side_effect
    return db


def test_recalculate_and_list_market_anomalies():
    fact_rows = [
        {
            "fact_id": "11111111-1111-1111-1111-111111111111",
            "title": "Phòng trọ Đống Đa tiêu chuẩn",
            "description": "Phòng sạch đẹp gần trường đại học, có điều hòa, nóng lạnh đầy đủ.",
            "price": 3_000_000,
            "area": 20.0,
            "price_per_m2": 150_000,
            "deposit_amount": 3_000_000,
            "electricity_cost": 3_500,
            "water_cost": 100_000,
            "images": ["img1.jpg"],
            "is_promoted": False,
            "is_active": True,
            "is_duplicate": False,
            "property_type_id": 1,
            "dim_location": {"district": "Quận Đống Đa"},
            "dim_property_type": {"type_name": "Phòng trọ"},
        },
        {
            "fact_id": "22222222-2222-2222-2222-222222222222",
            "title": "Studio full đồ giá sốc",
            "description": "Siêu rẻ",
            "price": 800_000,
            "area": 20.0,
            "price_per_m2": 40_000,
            "images": [],
            "is_promoted": False,
            "is_active": True,
            "is_duplicate": False,
            "property_type_id": 1,
            "dim_location": {"district": "Quận Đống Đa"},
            "dim_property_type": {"type_name": "Phòng trọ"},
        },
    ]
    report_rows = [{"fact_id": "22222222-2222-2222-2222-222222222222"}]

    db = _make_mock_db(fact_rows, report_rows)
    recalc = recalculate_market_anomalies(db)
    assert recalc.updated_count == 2
    assert recalc.high_risk_count == 1
    assert recalc.low_risk_count == 1

    listed = list_market_anomalies(db, min_risk_score=25.0, limit=20)
    assert listed.summary.total_listings == 2
    assert len(listed.items) == 1
    assert listed.items[0].fact_id == "22222222-2222-2222-2222-222222222222"
    assert listed.items[0].report_count == 1


def test_admin_bi_routes_registered():
    paths = set(app.openapi()["paths"].keys())
    assert "/api/admin/anomalies" in paths
    assert "/api/admin/anomalies/recalculate" in paths

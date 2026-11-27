import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

if "supabase" not in sys.modules:
    _supabase_stub = ModuleType("supabase")
    _supabase_stub.Client = object
    _supabase_stub.create_client = MagicMock()
    sys.modules["supabase"] = _supabase_stub

from src.backend.api.main import app
from src.backend.api.services.bi_service import get_market_bi_overview


def test_get_market_bi_overview_aggregates_three_insights():
    mock_rows = [
        {
            "district": "Quận Đống Đa",
            "type_name": "Phòng trọ / Nhà trọ",
            "price": 3_500_000,
            "price_per_m2": 140_000,
            "price_segment": "trung_cap",
            "is_active": True,
            "is_duplicate": False,
            "room_status": "con_trong",
            "days_on_market": 5.0,
            "month": 11,
            "year": 2026,
        },
        {
            "district": "Quận Cầu Giấy",
            "type_name": "Chung cư mini / Căn hộ dịch vụ",
            "price": 5_000_000,
            "price_per_m2": 200_000,
            "price_segment": "trung_cap",
            "is_active": True,
            "is_duplicate": False,
            "room_status": "con_trong",
            "days_on_market": 9.0,
            "month": 11,
            "year": 2026,
        },
        {
            "district": "Quận Cầu Giấy",
            "type_name": "Phòng trọ / Nhà trọ",
            "price": 2_500_000,
            "price_per_m2": 125_000,
            "price_segment": "binh_dan",
            "is_active": False,
            "is_duplicate": False,
            "room_status": "da_thue",
            "days_on_market": 4.0,
            "month": 10,
            "year": 2026,
        },
    ]

    mock_db = MagicMock()
    mock_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = (
        SimpleNamespace(data=mock_rows)
    )

    overview = get_market_bi_overview(mock_db)
    assert overview.total_active_listings == 2
    assert overview.total_districts == 2
    assert overview.avg_price == 4_250_000
    assert overview.avg_price_per_m2 == 170_000
    assert overview.avg_days_on_market == 6.0
    assert len(overview.price_by_district) == 2
    assert len(overview.price_by_property_type) == 2
    assert len(overview.supply_by_segment) == 1
    assert len(overview.trend_by_month) == 1
    assert len(overview.liquidity_by_district) == 2


def test_bi_overview_route_registered():
    paths = set(app.openapi()["paths"].keys())
    assert "/api/bi/overview" in paths

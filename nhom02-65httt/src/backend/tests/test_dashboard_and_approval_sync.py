"""Tests for GET /api/v1/dashboard and approval-to-execution sync flow."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app.core.rbac import Role
from app.models.erp import Category, Inventory, Product
from app.models.market import ChannelProduct, CompetitorPrice, SalesChannel, SalesRecord
from app.models.pricing import PriceRecommendation
from app.services.channels import seed_default_channels
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_dashboard_summary_empty_and_populated(
    client: TestClient,
    db_session: Session,
    make_user,
    auth_headers,
) -> None:
    assert client.get("/api/v1/dashboard").status_code == 401

    viewer = make_user("viewer@erp.demo", role=Role.VIEWER)
    headers = auth_headers(viewer)

    empty_resp = client.get("/api/v1/dashboard", headers=headers)
    assert empty_resp.status_code == 200
    assert empty_resp.json()["data"] == {
        "revenue": "0.00",
        "grossProfit": "0.00",
        "margin": "0.0000",
        "skusBelowFloor": 0,
        "lowStockCount": 0,
        "pendingApprovals": 0,
        "revenueTrend": [],
        "profitByChannel": [],
        "priceVsCompetitor": [
            {"bucket": "Thấp hơn", "count": 0},
            {"bucket": "Tương đương", "count": 0},
            {"bucket": "Cao hơn", "count": 0},
        ],
    }

    seed_default_channels(db_session)
    shopee = db_session.query(SalesChannel).filter_by(code="SHOPEE").one()
    lazada = db_session.query(SalesChannel).filter_by(code="LAZADA").one()

    cat = Category(code="ACC", name="Phụ kiện")
    db_session.add(cat)
    db_session.flush()

    p_low = Product(
        sku_code="SKU-LOW",
        name="Chuột M185",
        category_id=cat.id,
        current_price=Decimal("200000.00"),
    )
    p_eq = Product(
        sku_code="SKU-EQ",
        name="Chuột M220",
        category_id=cat.id,
        current_price=Decimal("300000.00"),
    )
    p_hi = Product(
        sku_code="SKU-HI",
        name="Bàn phím G213",
        category_id=cat.id,
        current_price=Decimal("950000.00"),
    )
    db_session.add_all([p_low, p_eq, p_hi])
    db_session.flush()

    db_session.add_all(
        [
            Inventory(product_id=p_low.id, on_hand_qty=10, reserved_qty=4, reorder_point=6),
            Inventory(product_id=p_eq.id, on_hand_qty=50, reserved_qty=5, reorder_point=10),
        ]
    )

    now = datetime.now(UTC)
    db_session.add_all(
        [
            CompetitorPrice(
                product_id=p_low.id,
                sku_code=p_low.sku_code,
                product_name=p_low.name,
                competitor_name="Shop A",
                marketplace_code="SHOPEE",
                source_type="API",
                source_name="lichsugia",
                listed_price=Decimal("250000.00"),
                observed_at=now - timedelta(hours=1),
            ),
            CompetitorPrice(
                product_id=p_eq.id,
                sku_code=p_eq.sku_code,
                product_name=p_eq.name,
                competitor_name="Shop B",
                marketplace_code="SHOPEE",
                source_type="API",
                source_name="lichsugia",
                listed_price=Decimal("302000.00"),
                observed_at=now - timedelta(hours=1),
            ),
            CompetitorPrice(
                product_id=p_hi.id,
                sku_code=p_hi.sku_code,
                product_name=p_hi.name,
                competitor_name="Shop C",
                marketplace_code="LAZADA",
                source_type="API",
                source_name="lazada",
                listed_price=Decimal("800000.00"),
                observed_at=now - timedelta(hours=1),
            ),
            # Outlier should be ignored
            CompetitorPrice(
                product_id=p_low.id,
                sku_code=p_low.sku_code,
                product_name=p_low.name,
                competitor_name="Shop Outlier",
                marketplace_code="SHOPEE",
                source_type="API",
                source_name="lichsugia",
                listed_price=Decimal("10000.00"),
                is_outlier=True,
                observed_at=now,
            ),
        ]
    )

    db_session.add_all(
        [
            SalesRecord(
                product_id=p_low.id,
                channel_id=shopee.id,
                order_date=date(2026, 11, 20),
                quantity=2,
                unit_price=Decimal("200000.00"),
                gross_revenue=Decimal("400000.00"),
                unit_cost=Decimal("130000.00"),
                channel_fee_amount=Decimal("48000.00"),
                net_profit=Decimal("92000.00"),
            ),
            SalesRecord(
                product_id=p_eq.id,
                channel_id=lazada.id,
                order_date=date(2026, 11, 21),
                quantity=2,
                unit_price=Decimal("300000.00"),
                gross_revenue=Decimal("600000.00"),
                unit_cost=Decimal("200000.00"),
                channel_fee_amount=Decimal("60000.00"),
                net_profit=Decimal("140000.00"),
            ),
        ]
    )

    db_session.add_all(
        [
            PriceRecommendation(
                product_id=p_low.id,
                channel_id=shopee.id,
                status="PENDING_APPROVAL",
                current_price=Decimal("200000.00"),
                floor_price=Decimal("190000.00"),
                recommended_price=Decimal("185000.00"),
                expected_profit_per_unit=Decimal("32800.00"),
                expected_margin=Decimal("0.1773"),
                unit_cost=Decimal("130000.00"),
                channel_fee_rate=Decimal("0.1200"),
                target_margin=Decimal("0.1800"),
                algorithm_version="rule-v1",
                explanation_json={"summary": "test"},
                created_by="Test",
                expires_at=now + timedelta(days=1),
            ),
            PriceRecommendation(
                product_id=p_eq.id,
                channel_id=lazada.id,
                status="PENDING_APPROVAL",
                current_price=Decimal("300000.00"),
                floor_price=Decimal("270000.00"),
                recommended_price=Decimal("295000.00"),
                expected_profit_per_unit=Decimal("65500.00"),
                expected_margin=Decimal("0.2220"),
                unit_cost=Decimal("200000.00"),
                channel_fee_rate=Decimal("0.1000"),
                target_margin=Decimal("0.1800"),
                algorithm_version="rule-v1",
                explanation_json={"summary": "test"},
                created_by="Test",
                expires_at=now + timedelta(days=1),
            ),
        ]
    )
    db_session.commit()

    resp = client.get("/api/v1/dashboard?days=14", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["revenue"] == "1000000.00"
    assert data["grossProfit"] == "232000.00"
    assert data["margin"] == "0.2320"
    assert data["skusBelowFloor"] == 1
    assert data["lowStockCount"] == 1
    assert data["pendingApprovals"] == 2
    assert [pt["date"] for pt in data["revenueTrend"]] == ["2026-11-20", "2026-11-21"]
    assert data["profitByChannel"][0] == {"channel": "Lazada", "profit": "140000.00"}
    assert data["priceVsCompetitor"] == [
        {"bucket": "Thấp hơn", "count": 1},
        {"bucket": "Tương đương", "count": 1},
        {"bucket": "Cao hơn", "count": 1},
    ]


def test_sync_from_approved_recommendation_flow(
    client: TestClient,
    db_session: Session,
    make_user,
    auth_headers,
) -> None:
    seed_default_channels(db_session)
    shopee = db_session.query(SalesChannel).filter_by(code="SHOPEE").one()
    cat = Category(code="NET", name="Thiết bị mạng")
    db_session.add(cat)
    db_session.flush()

    prod = Product(
        sku_code="ROUTER-AX1500",
        name="Router WiFi 6",
        category_id=cat.id,
        current_price=Decimal("790000.00"),
    )
    db_session.add(prod)
    db_session.flush()

    mapping = ChannelProduct(
        product_id=prod.id,
        channel_id=shopee.id,
        external_listing_id="SHP-AX1500",
        external_sku="SHP-ROUTER-AX1500",
        current_price=Decimal("790000.00"),
        sync_status="PENDING",
    )
    db_session.add(mapping)

    now = datetime.now(UTC)
    pending_rec = PriceRecommendation(
        product_id=prod.id,
        channel_id=shopee.id,
        status="PENDING_APPROVAL",
        current_price=Decimal("790000.00"),
        floor_price=Decimal("680000.00"),
        recommended_price=Decimal("750000.00"),
        expected_profit_per_unit=Decimal("100000.00"),
        expected_margin=Decimal("0.1333"),
        unit_cost=Decimal("560000.00"),
        channel_fee_rate=Decimal("0.1200"),
        target_margin=Decimal("0.1200"),
        algorithm_version="rule-v1",
        explanation_json={"summary": "pending"},
        created_by="Analyst",
        expires_at=now + timedelta(days=1),
    )
    approved_rec = PriceRecommendation(
        product_id=prod.id,
        channel_id=shopee.id,
        status="APPROVED",
        current_price=Decimal("790000.00"),
        floor_price=Decimal("680000.00"),
        recommended_price=Decimal("749000.00"),
        expected_profit_per_unit=Decimal("99120.00"),
        expected_margin=Decimal("0.1323"),
        unit_cost=Decimal("560000.00"),
        channel_fee_rate=Decimal("0.1200"),
        target_margin=Decimal("0.1200"),
        algorithm_version="rule-v1",
        explanation_json={"summary": "approved"},
        created_by="Analyst",
        expires_at=now + timedelta(days=1),
    )
    queued_rec = PriceRecommendation(
        product_id=prod.id,
        channel_id=shopee.id,
        status="APPROVED",
        current_price=Decimal("790000.00"),
        floor_price=Decimal("680000.00"),
        recommended_price=Decimal("739000.00"),
        expected_profit_per_unit=Decimal("90320.00"),
        expected_margin=Decimal("0.1222"),
        unit_cost=Decimal("560000.00"),
        channel_fee_rate=Decimal("0.1200"),
        target_margin=Decimal("0.1200"),
        algorithm_version="rule-v1",
        explanation_json={"summary": "queued"},
        created_by="Analyst",
        expires_at=now + timedelta(days=1),
    )
    db_session.add_all([pending_rec, approved_rec, queued_rec])
    db_session.commit()

    manager = make_user("manager@erp.demo", role=Role.MANAGER, full_name="Trần Thị Mai")
    headers = auth_headers(manager)

    blocked = client.post(
        f"/api/v1/executions/from-recommendation/{pending_rec.id}",
        headers=headers,
    )
    assert blocked.status_code == 409

    ok_resp = client.post(
        f"/api/v1/executions/from-recommendation/{approved_rec.id}",
        headers=headers,
    )
    assert ok_resp.status_code == 201
    exec_data = ok_resp.json()["data"]
    assert exec_data["status"] == "SUCCEEDED"
    assert exec_data["requestedPrice"] == "749000.00"
    assert exec_data["idempotencyKey"] == f"rec-{approved_rec.id}"

    db_session.refresh(approved_rec)
    db_session.refresh(mapping)
    assert approved_rec.status == "EXECUTED"
    assert mapping.current_price == Decimal("749000.00")
    assert mapping.sync_status == "SYNCED"

    replay = client.post(
        f"/api/v1/executions/from-recommendation/{approved_rec.id}",
        headers=headers,
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == exec_data["id"]

    queued_resp = client.post(
        f"/api/v1/executions/from-recommendation/{queued_rec.id}?executeImmediately=false",
        headers=headers,
    )
    assert queued_resp.status_code == 201
    assert queued_resp.json()["data"]["status"] == "QUEUED"
    db_session.refresh(queued_rec)
    assert queued_rec.status == "EXECUTION_QUEUED"

    audit_resp = client.get(
        "/api/v1/audit-logs?action=QUEUE_APPROVED_SYNC",
        headers=headers,
    )
    assert audit_resp.status_code == 200
    assert audit_resp.json()["meta"]["total"] == 2

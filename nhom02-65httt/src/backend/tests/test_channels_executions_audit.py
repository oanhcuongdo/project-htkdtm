"""Tests for 18-table schema, Alembic 0002, channels, executions, and audit logs."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from alembic import command
from alembic.config import Config
from app.core.config import get_settings
from app.core.rbac import Role
from app.db.base import Base
from app.integrations.marketplace import SimulatedMarketplaceAdapter
from app.models.erp import Category, Product
from app.models.market import ChannelProduct, SalesChannel
from app.models.pricing import PriceSyncLog
from app.services.channels import seed_default_channels
from app.services.execution import execute_sync_log
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import Session


def test_schema_has_all_18_tables_and_alembic_upgrades_cleanly(
    tmp_path: Path,
    monkeypatch,
) -> None:
    expected_tables = {
        "users",
        "audit_logs",
        "categories",
        "suppliers",
        "products",
        "supplier_products",
        "cost_components",
        "inventory",
        "sales_channels",
        "channel_products",
        "competitor_prices",
        "competitor_price_history",
        "sales_records",
        "pricing_rules",
        "price_recommendations",
        "price_approvals",
        "price_sync_logs",
        "model_runs",
    }
    assert set(Base.metadata.tables.keys()) == expected_tables

    db_file = tmp_path / "alembic_verify.db"
    backend_root = Path(__file__).resolve().parents[1]
    try:
        with monkeypatch.context() as mp:
            mp.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_file.as_posix()}")
            get_settings.cache_clear()
            alembic_cfg = Config(str(backend_root / "alembic.ini"))
            alembic_cfg.set_main_option("script_location", str(backend_root / "alembic"))
            command.upgrade(alembic_cfg, "head")

            from sqlalchemy import create_engine

            check_engine = create_engine(f"sqlite+pysqlite:///{db_file.as_posix()}")
            created_tables = set(inspect(check_engine).get_table_names())
            check_engine.dispose()
            assert expected_tables.issubset(created_tables)
    finally:
        get_settings.cache_clear()


def test_channels_fees_and_connection_test(
    client: TestClient,
    db_session: Session,
    make_user,
    auth_headers,
) -> None:
    created1, skipped1 = seed_default_channels(db_session)
    assert created1 == 4
    assert skipped1 == 0
    created2, skipped2 = seed_default_channels(db_session)
    assert created2 == 0
    assert skipped2 == 4

    cat = Category(code="MOUSE", name="Chuột máy tính")
    db_session.add(cat)
    db_session.flush()
    prod = Product(
        sku_code="LOGI-M185",
        name="Chuột không dây Logitech M185",
        category_id=cat.id,
        current_price=Decimal("229000.00"),
    )
    db_session.add(prod)
    db_session.flush()

    shopee = db_session.query(SalesChannel).filter_by(code="SHOPEE").one()
    db_session.add(
        ChannelProduct(
            product_id=prod.id,
            channel_id=shopee.id,
            external_listing_id="SHP-1001",
            external_sku="SHOPEE-LOGI-M185",
            current_price=Decimal("229000.00"),
            sync_status="PENDING",
        )
    )
    live_channel = SalesChannel(
        code="TIKI",
        name="Tiki Live",
        integration_mode="LIVE",
        connection_status="ERROR",
        fee_rate=Decimal("0.0800"),
        fee_effective_from=datetime.now(UTC),
        fee_source="Partner API",
    )
    db_session.add(live_channel)
    db_session.commit()

    viewer = make_user("viewer@erp.demo", role=Role.VIEWER)
    headers = auth_headers(viewer)

    channels_resp = client.get("/api/v1/channels", headers=headers)
    assert channels_resp.status_code == 200
    items = {c["code"]: c for c in channels_resp.json()["data"]}
    assert items["SHOPEE"]["listingCount"] == 1
    assert items["SHOPEE"]["feeRate"] == "0.1200"

    fees_resp = client.get("/api/v1/channel-fees", headers=headers)
    assert fees_resp.status_code == 200
    assert len(fees_resp.json()["data"]) == 5
    assert len(fees_resp.json()["data"][0]["components"]) == 3

    sim_test = client.post(
        f"/api/v1/channels/{shopee.id}/test-connection",
        headers=headers,
    )
    assert sim_test.status_code == 200
    assert sim_test.json()["data"]["ok"] is True
    assert sim_test.json()["data"]["mode"] == "SIMULATED"

    live_test = client.post(
        "/api/v1/channels/TIKI/test-connection",
        headers=headers,
    )
    assert live_test.status_code == 200
    assert live_test.json()["data"]["ok"] is False
    assert live_test.json()["data"]["mode"] == "LIVE"

    missing_test = client.post(
        "/api/v1/channels/UNKNOWN/test-connection",
        headers=headers,
    )
    assert missing_test.status_code == 404


def test_execution_sync_idempotency_retry_and_cancel(
    client: TestClient,
    db_session: Session,
    make_user,
    auth_headers,
) -> None:
    seed_default_channels(db_session)
    cat = Category(code="KB", name="Bàn phím")
    db_session.add(cat)
    db_session.flush()
    prod = Product(
        sku_code="LOGI-G213",
        name="Bàn phím Logitech G213",
        category_id=cat.id,
        current_price=Decimal("890000.00"),
    )
    db_session.add(prod)
    db_session.flush()
    shopee = db_session.query(SalesChannel).filter_by(code="SHOPEE").one()
    mapping = ChannelProduct(
        product_id=prod.id,
        channel_id=shopee.id,
        external_listing_id="SHP-G213",
        external_sku="SHP-SKU-G213",
        current_price=Decimal("890000.00"),
        sync_status="PENDING",
    )
    db_session.add(mapping)
    db_session.commit()

    manager = make_user("manager@erp.demo", role=Role.MANAGER, full_name="Trần Thị Mai")
    headers = auth_headers(manager)

    payload = {
        "skuCode": "LOGI-G213",
        "channelCode": "SHOPEE",
        "requestedPrice": "849000.00",
        "previousPrice": "890000.00",
        "idempotencyKey": "rec-g213-01",
        "executeImmediately": True,
    }
    first = client.post("/api/v1/executions", json=payload, headers=headers)
    assert first.status_code == 201
    exec_data = first.json()["data"]
    assert exec_data["status"] == "SUCCEEDED"
    assert exec_data["syncMode"] == "SIMULATED"
    assert exec_data["httpStatus"] == 200
    assert exec_data["externalReference"].startswith("SIM-")

    db_session.refresh(mapping)
    assert mapping.current_price == Decimal("849000.00")
    assert mapping.sync_status == "SYNCED"

    replay = client.post("/api/v1/executions", json=payload, headers=headers)
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == exec_data["id"]

    conflict_payload = {**payload, "requestedPrice": "820000.00"}
    conflict = client.post("/api/v1/executions", json=conflict_payload, headers=headers)
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"

    # Cannot retry a SUCCEEDED execution
    retry_succeeded = client.post(
        f"/api/v1/executions/{exec_data['id']}/retry",
        headers=headers,
    )
    assert retry_succeeded.status_code == 409

    # Queue a FAILED execution via deterministic failure simulator
    failed_log = PriceSyncLog(
        sku_code="LOGI-G213",
        channel_code="SHOPEE",
        channel_name="Shopee",
        mode="SIMULATED",
        sync_mode="SIMULATED",
        requested_price=Decimal("830000.00"),
        previous_price=Decimal("849000.00"),
        status="QUEUED",
        attempts=1,
        idempotency_key="rec-g213-fail-01",
    )
    db_session.add(failed_log)
    db_session.flush()
    execute_sync_log(
        db_session,
        failed_log,
        adapter_override=SimulatedMarketplaceAdapter("SHOPEE", failure_rate=1.0),
    )
    db_session.commit()
    assert failed_log.status == "FAILED"

    retry1 = client.post(f"/api/v1/executions/{failed_log.id}/retry", headers=headers)
    assert retry1.status_code == 200
    assert retry1.json()["data"]["status"] == "QUEUED"
    assert retry1.json()["data"]["attempts"] == 2
    assert retry1.json()["data"]["errorCode"] is None

    # Cancel while QUEUED
    cancel_ok = client.post(f"/api/v1/executions/{failed_log.id}/cancel", headers=headers)
    assert cancel_ok.status_code == 200
    assert cancel_ok.json()["data"]["status"] == "CANCELLED"

    # Cannot cancel non-QUEUED execution
    cancel_again = client.post(f"/api/v1/executions/{failed_log.id}/cancel", headers=headers)
    assert cancel_again.status_code == 409

    # Max attempts guard (attempts == 3)
    exhausted = PriceSyncLog(
        sku_code="LOGI-G213",
        channel_code="SHOPEE",
        channel_name="Shopee",
        mode="SIMULATED",
        sync_mode="SIMULATED",
        requested_price=Decimal("830000.00"),
        previous_price=Decimal("849000.00"),
        status="FAILED",
        attempts=3,
        error_code="PROVIDER_UNAVAILABLE",
        idempotency_key="rec-g213-max-attempts",
    )
    db_session.add(exhausted)
    db_session.commit()

    retry_exhausted = client.post(f"/api/v1/executions/{exhausted.id}/retry", headers=headers)
    assert retry_exhausted.status_code == 409
    assert retry_exhausted.json()["error"]["code"] == "CONFLICT"

    list_resp = client.get("/api/v1/executions?page=1&pageSize=10", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["meta"]["total"] == 3


def test_audit_logs_recorded_and_rbac_enforced(
    client: TestClient,
    make_user,
    auth_headers,
) -> None:
    admin = make_user("admin@erp.demo", role=Role.ADMIN, full_name="Nguyễn Quản Trị")
    manager = make_user("manager@erp.demo", role=Role.MANAGER, full_name="Trần Thị Mai")
    viewer = make_user("viewer@erp.demo", role=Role.VIEWER, full_name="Đỗ Minh Khoa")

    create_resp = client.post(
        "/api/v1/users",
        json={
            "email": "staff@erp.demo",
            "fullName": "Nhân viên kho",
            "role": "INVENTORY_STAFF",
            "password": "password123",
        },
        headers=auth_headers(admin),
    )
    assert create_resp.status_code == 201
    created_id = create_resp.json()["data"]["id"]

    patch_resp = client.patch(
        f"/api/v1/users/{created_id}",
        json={"fullName": "Nhân viên kho 2"},
        headers=auth_headers(admin),
    )
    assert patch_resp.status_code == 200

    viewer_audit = client.get("/api/v1/audit-logs", headers=auth_headers(viewer))
    assert viewer_audit.status_code == 403

    manager_audit = client.get(
        "/api/v1/audit-logs?action=CREATE_USER&page=1&pageSize=10",
        headers=auth_headers(manager),
    )
    assert manager_audit.status_code == 200
    body = manager_audit.json()
    assert body["meta"]["total"] == 1
    entry = body["data"][0]
    assert entry["actor"] == "Nguyễn Quản Trị"
    assert entry["action"] == "CREATE_USER"
    assert entry["resourceType"] == "user"
    assert entry["requestId"].startswith("req-")
    assert "staff@erp.demo" in entry["afterSummary"]

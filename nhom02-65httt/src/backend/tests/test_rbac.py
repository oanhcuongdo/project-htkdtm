"""Tests for RBAC permission matrix and endpoint guards."""

from __future__ import annotations

from app.core.rbac import Permission, Role, has_permission, permissions_for_role
from fastapi.testclient import TestClient


def test_permission_matrix_for_all_roles() -> None:
    for perm in Permission:
        assert has_permission(Role.ADMIN, perm)

    assert has_permission(Role.MANAGER, Permission.SETTINGS_READ)
    assert has_permission(Role.MANAGER, Permission.PRICING_APPROVE)
    assert has_permission(Role.MANAGER, Permission.EXECUTION_RETRY)
    assert has_permission(Role.MANAGER, Permission.AUDIT_READ)
    assert not has_permission(Role.MANAGER, Permission.SETTINGS_WRITE)
    assert not has_permission(Role.MANAGER, Permission.USER_MANAGE)

    assert has_permission(Role.PRICING_ANALYST, Permission.COMPETITOR_WRITE)
    assert has_permission(Role.PRICING_ANALYST, Permission.PRICING_RUN)
    assert has_permission(Role.PRICING_ANALYST, Permission.RULE_WRITE)
    assert not has_permission(Role.PRICING_ANALYST, Permission.PRICING_APPROVE)
    assert not has_permission(Role.PRICING_ANALYST, Permission.PRODUCT_WRITE)

    assert has_permission(Role.INVENTORY_STAFF, Permission.PRODUCT_WRITE)
    assert has_permission(Role.INVENTORY_STAFF, Permission.INVENTORY_WRITE)
    assert has_permission(Role.INVENTORY_STAFF, Permission.CHANNEL_WRITE)
    assert not has_permission(Role.INVENTORY_STAFF, Permission.PRICING_RUN)

    assert has_permission(Role.VIEWER, Permission.BI_READ)
    assert not has_permission(Role.VIEWER, Permission.USER_MANAGE)
    assert not has_permission(Role.VIEWER, Permission.PRICING_RUN)
    assert not has_permission(Role.VIEWER, Permission.PRODUCT_WRITE)

    assert permissions_for_role("UNKNOWN_ROLE") == frozenset()
    assert not has_permission("UNKNOWN_ROLE", Permission.BI_READ)
    assert not has_permission(Role.ADMIN, "unknown.permission")


def test_rbac_endpoint_enforcement(client: TestClient, make_user, auth_headers) -> None:
    viewer = make_user("viewer@erp.demo", role=Role.VIEWER)
    manager = make_user("manager@erp.demo", role=Role.MANAGER)
    admin = make_user("admin@erp.demo", role=Role.ADMIN)

    payload = {
        "email": "new.staff@erp.demo",
        "fullName": "Nhân viên mới",
        "role": "INVENTORY_STAFF",
        "password": "password123",
    }

    viewer_create = client.post(
        "/api/v1/users",
        json=payload,
        headers=auth_headers(viewer),
    )
    assert viewer_create.status_code == 403
    assert viewer_create.json()["error"]["code"] == "FORBIDDEN"

    manager_list = client.get("/api/v1/users", headers=auth_headers(manager))
    assert manager_list.status_code == 200

    manager_create = client.post(
        "/api/v1/users",
        json=payload,
        headers=auth_headers(manager),
    )
    assert manager_create.status_code == 403
    assert manager_create.json()["error"]["code"] == "FORBIDDEN"

    admin_create = client.post(
        "/api/v1/users",
        json=payload,
        headers=auth_headers(admin),
    )
    assert admin_create.status_code == 201
    assert admin_create.json()["data"]["email"] == "new.staff@erp.demo"

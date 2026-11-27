"""Tests for user management CRUD, pagination, camelCase output, and conflicts."""

from __future__ import annotations

import uuid

from app.core.rbac import Role
from fastapi.testclient import TestClient


def test_create_user_camel_case_and_nullable_last_login(
    client: TestClient,
    make_user,
    auth_headers,
) -> None:
    admin = make_user("admin@erp.demo", role=Role.ADMIN)

    resp = client.post(
        "/api/v1/users",
        json={
            "email": "Operator@ERP.demo",
            "fullName": "  Phạm Thu Hà  ",
            "role": "INVENTORY_STAFF",
            "password": "password123",
        },
        headers=auth_headers(admin),
    )
    assert resp.status_code == 201
    body = resp.json()
    user_data = body["data"]
    assert user_data["email"] == "operator@erp.demo"
    assert user_data["fullName"] == "Phạm Thu Hà"
    assert user_data["isActive"] is True
    assert "lastLoginAt" in user_data
    assert user_data["lastLoginAt"] is None
    assert "createdAt" in user_data

    duplicate = client.post(
        "/api/v1/users",
        json={
            "email": "operator@erp.demo",
            "fullName": "Duplicate",
            "role": "VIEWER",
            "password": "password123",
        },
        headers=auth_headers(admin),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"


def test_list_users_pagination_and_filters(
    client: TestClient,
    make_user,
    auth_headers,
) -> None:
    admin = make_user("admin@erp.demo", role=Role.ADMIN, full_name="Admin User")
    make_user("a@erp.demo", role=Role.VIEWER, full_name="Alpha Viewer")
    make_user("b@erp.demo", role=Role.VIEWER, full_name="Beta Viewer")
    make_user("c@erp.demo", role=Role.PRICING_ANALYST, full_name="Charlie Pricing")

    page1 = client.get(
        "/api/v1/users?page=1&pageSize=2",
        headers=auth_headers(admin),
    )
    assert page1.status_code == 200
    body1 = page1.json()
    assert len(body1["data"]) == 2
    assert body1["meta"] == {
        "page": 1,
        "pageSize": 2,
        "total": 4,
        "totalPages": 2,
    }

    filtered = client.get(
        "/api/v1/users?q=Viewer&role=VIEWER",
        headers=auth_headers(admin),
    )
    assert filtered.status_code == 200
    assert filtered.json()["meta"]["total"] == 2


def test_update_user_and_self_protection(
    client: TestClient,
    make_user,
    auth_headers,
) -> None:
    admin = make_user("admin@erp.demo", role=Role.ADMIN)
    target = make_user("staff@erp.demo", role=Role.VIEWER, full_name="Old Name")

    updated = client.patch(
        f"/api/v1/users/{target.id}",
        json={"fullName": "New Name", "role": "PRICING_ANALYST", "isActive": False},
        headers=auth_headers(admin),
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["fullName"] == "New Name"
    assert updated.json()["data"]["role"] == "PRICING_ANALYST"
    assert updated.json()["data"]["isActive"] is False

    self_deactivate = client.patch(
        f"/api/v1/users/{admin.id}",
        json={"isActive": False},
        headers=auth_headers(admin),
    )
    assert self_deactivate.status_code == 409
    assert self_deactivate.json()["error"]["code"] == "CONFLICT"

    self_demote = client.patch(
        f"/api/v1/users/{admin.id}",
        json={"role": "VIEWER"},
        headers=auth_headers(admin),
    )
    assert self_demote.status_code == 409
    assert self_demote.json()["error"]["code"] == "CONFLICT"

    missing = client.patch(
        f"/api/v1/users/{uuid.uuid4()}",
        json={"fullName": "Nobody"},
        headers=auth_headers(admin),
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

"""Tests for health check, JWT login, /auth/me, and demo user seeding."""

from __future__ import annotations

from datetime import timedelta

from app.core.rbac import Role
from app.core.security import create_access_token
from app.scripts.seed_users import DEMO_SEED_USERS, seed_demo_users
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_health_ok(client: TestClient) -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {
        "data": {"status": "ok", "database": "ok"},
        "meta": None,
    }


def test_login_success_and_me(client: TestClient, make_user) -> None:
    user = make_user(
        "Admin@ERP.demo ",
        role=Role.ADMIN,
        full_name="Nguyễn Quản Trị",
        password="Password123!",
    )
    assert user.last_login_at is None

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "  ADMIN@erp.demo ", "password": "Password123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"] is None

    data = body["data"]
    assert data["tokenType"] == "bearer"
    assert isinstance(data["token"], str) and data["token"]
    assert data["expiresIn"] > 0
    assert data["user"]["email"] == "admin@erp.demo"
    assert data["user"]["fullName"] == "Nguyễn Quản Trị"
    assert data["user"]["role"] == "ADMIN"
    assert data["user"]["isActive"] is True
    assert data["user"]["lastLoginAt"] is not None
    assert "hashedPassword" not in data["user"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['token']}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["id"] == data["user"]["id"]


def test_login_wrong_password_and_unknown_email(client: TestClient, make_user) -> None:
    make_user("user@erp.demo", role=Role.VIEWER, password="correct-password")

    wrong_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "user@erp.demo", "password": "wrong-password"},
    )
    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@erp.demo", "password": "wrong-password"},
    )

    assert wrong_pw.status_code == 401
    assert unknown.status_code == 401
    assert wrong_pw.headers.get("www-authenticate") == "Bearer"
    assert wrong_pw.json() == unknown.json()
    assert wrong_pw.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_inactive_user(client: TestClient, make_user) -> None:
    make_user(
        "inactive@erp.demo",
        role=Role.VIEWER,
        password="secret1234",
        is_active=False,
    )

    wrong_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@erp.demo", "password": "wrong"},
    )
    assert wrong_pw.status_code == 401

    right_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@erp.demo", "password": "secret1234"},
    )
    assert right_pw.status_code == 403
    assert right_pw.json()["error"]["code"] == "FORBIDDEN"


def test_me_requires_valid_non_expired_token(client: TestClient, make_user) -> None:
    no_token = client.get("/api/v1/auth/me")
    assert no_token.status_code == 401
    assert no_token.headers.get("www-authenticate") == "Bearer"
    assert no_token.json()["error"]["code"] == "UNAUTHORIZED"

    bad_token = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not.a.jwt"},
    )
    assert bad_token.status_code == 401
    assert bad_token.json()["error"]["code"] == "UNAUTHORIZED"

    user = make_user("viewer@erp.demo", role=Role.VIEWER)
    expired = create_access_token(
        user.id,
        user.role,
        expires_delta=timedelta(minutes=-5),
    )
    expired_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert expired_resp.status_code == 401
    assert expired_resp.json()["error"]["code"] == "UNAUTHORIZED"


def test_seed_demo_users_is_idempotent(client: TestClient, db_session: Session) -> None:
    created1, skipped1 = seed_demo_users(db_session, "demo1234")
    assert created1 == len(DEMO_SEED_USERS)
    assert skipped1 == 0

    created2, skipped2 = seed_demo_users(db_session, "demo1234")
    assert created2 == 0
    assert skipped2 == len(DEMO_SEED_USERS)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@erp.demo", "password": "demo1234"},
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["data"]["user"]["role"] == "ADMIN"

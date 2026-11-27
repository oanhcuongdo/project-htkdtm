"""Tests for standardized error envelopes and production secret guard."""

from __future__ import annotations

import pytest
from app.core.config import Settings
from app.core.rbac import Role
from app.main import create_app
from fastapi import APIRouter
from fastapi.testclient import TestClient


def test_validation_error_envelope_strips_body_prefix(
    client: TestClient,
    make_user,
    auth_headers,
) -> None:
    admin = make_user("admin@erp.demo", role=Role.ADMIN)

    resp = client.post(
        "/api/v1/users",
        json={
            "email": "not-an-email",
            "fullName": "   ",
            "role": "VIEWER",
            "password": "short",
        },
        headers=auth_headers(admin),
    )
    assert resp.status_code == 422
    error = resp.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    fields = {item["field"] for item in error["details"]}
    assert {"email", "fullName", "password"}.issubset(fields)
    assert all(not item["field"].startswith("body") for item in error["details"])


def test_http_404_uses_standard_error_envelope(client: TestClient) -> None:
    resp = client.get("/api/v1/nonexistent-endpoint")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


def test_unhandled_exception_does_not_leak_traceback() -> None:
    app = create_app()
    boom_router = APIRouter()

    @boom_router.get("/api/v1/_test-boom")
    def _boom() -> None:
        raise RuntimeError("sensitive internal trace")

    app.include_router(boom_router)

    with TestClient(app, raise_server_exceptions=False) as local_client:
        resp = local_client.get("/api/v1/_test-boom")

    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "sensitive internal trace" not in resp.text


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="change-me-in-dev")

"""Phase 0 checks: app startup, error envelope and environment configuration."""
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app


def test_health_and_request_id():
    with TestClient(app) as client:
        response = client.get("/health", headers={"X-Request-ID": "phase-zero-check"})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"] == "phase-zero-check"


def test_error_envelope():
    with TestClient(app) as client:
        response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_404"


def test_development_cors():
    with TestClient(app) as client:
        response = client.options("/health", headers={
            "Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET",
        })
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_database_url_override():
    settings = Settings(_env_file=None, DATABASE_URL="sqlite:///./local.db")
    assert settings.database_url == "sqlite:///./local.db"


def test_postgres_credentials_are_url_encoded():
    from sqlalchemy.engine import make_url
    settings = Settings(_env_file=None, DATABASE_URL="", POSTGRES_PASSWORD="a@b:/%secret")
    assert make_url(settings.database_url).password == "a@b:/%secret"

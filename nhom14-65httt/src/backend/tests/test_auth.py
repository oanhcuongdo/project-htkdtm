"""API auth và guard được kiểm tra trên DB tạm tạo bằng migration thật."""

from pathlib import Path
from typing import Annotated

import pytest
from alembic.config import Config
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from passlib.hash import pbkdf2_sha256
from pydantic import ValidationError
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.auth import service
from app.auth.dependencies import require_role, require_vendor_owner
from app.auth.router import router
from app.auth.schemas import RegisterRequest
from app.auth.utils import AUDIENCE, ISSUER, create_token, hash_password, verify_password
from app.config import Settings, settings
from app.database import get_db
from app.exceptions import ConflictError
from app.main import app as production_app
from app.middleware import setup_middleware
from app.restaurants.models import Restaurant, RestaurantMembership
from app.users.models import User, UserRole

PASSWORD = "Mat khau thu nghiem 123!"
AUTH = "/api/v1/auth"


@pytest.fixture(scope="module")
def encoded_password():
    return hash_password(PASSWORD)


@pytest.fixture
def api(tmp_path, monkeypatch, encoded_password):
    monkeypatch.setattr(settings, "SECRET_KEY", "test-only-auth-signing-key-at-least-32-characters")
    url = "sqlite:///" + (tmp_path / "auth.db").as_posix()
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    command.upgrade(Config(str(Path(__file__).resolve().parents[1] / "alembic.ini")), "head")
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    with Session(engine) as db:
        for user_id, role in [(1, "customer"), (2, "vendor"), (3, "admin"), (4, "vendor")]:
            db.add(
                User(
                    id=user_id,
                    email=f"{role}{user_id}@example.vn",
                    full_name=f"Tai khoan {user_id}",
                    hashed_password=encoded_password,
                    role=role,
                )
            )
        db.add_all(
            [
                Restaurant(id=i, name=f"Quan {i}", address="Ha Noi", latitude=21, longitude=105)
                for i in (1, 2)
            ]
        )
        db.flush()
        db.add(RestaurantMembership(user_id=2, restaurant_id=1))
        db.commit()

    def override_db():
        with Session(engine) as db:
            yield db

    test_app = FastAPI()
    setup_middleware(test_app)
    test_app.include_router(router, prefix="/api/v1")
    test_app.dependency_overrides[get_db] = override_db

    @test_app.get("/admin-only")
    def admin_only(user: Annotated[User, Depends(require_role(UserRole.ADMIN))]):
        return {"id": user.id}

    @test_app.get("/staff-only")
    def staff_only(user: Annotated[User, Depends(require_role(UserRole.VENDOR, UserRole.ADMIN))]):
        return {"id": user.id}

    @test_app.get("/restaurants/{restaurant_id}/private")
    def vendor_only(restaurant_id: Annotated[int, Depends(require_vendor_owner)]):
        return {"restaurant_id": restaurant_id}

    with TestClient(test_app) as client:
        yield client, engine
    engine.dispose()


def headers(user_id=1, kind="access"):
    return {"Authorization": "Bearer " + create_token(user_id, kind)}


def registration(**overrides):
    return {"email": "new@example.vn", "full_name": "Khach moi", "password": PASSWORD} | overrides


@pytest.mark.parametrize("role", ["customer", "vendor"])
def test_register_stores_normalized_user_and_salted_password(api, role):
    client, engine = api
    payload = registration(email="  NEW@Example.VN  ", full_name="  Khach moi  ")
    if role != "customer":
        payload["role"] = role
    response = client.post(AUTH + "/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.vn" and body["full_name"] == "Khach moi"
    assert body["role"] == role and body["is_simulated"] is False
    assert "password" not in body and "hashed_password" not in body
    with Session(engine) as db:
        user = db.get(User, body["id"])
        assert user.hashed_password != PASSWORD
        assert verify_password(PASSWORD, user.hashed_password)
        assert pbkdf2_sha256.from_string(user.hashed_password).rounds == 600_000


def test_duplicate_email_is_case_insensitive_through_api(api):
    client, _ = api
    response = client.post(AUTH + "/register", json=registration(email=" CUSTOMER1@EXAMPLE.VN "))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_EXISTS"


@pytest.mark.parametrize(
    "changes",
    [
        {"role": "admin"},
        {"role": "owner"},
        {"is_simulated": True},
        {"hashed_password": "attacker"},
        {"password": "1234567"},
        {"password": " " * 8},
        {"password": "a" * 129},
        {"full_name": "  "},
        {"full_name": "a" * 121},
        {"email": "bad-address"},
        {"email": "a b@example.vn"},
    ],
)
def test_invalid_registration_does_not_create_user_or_echo_password(api, changes):
    client, engine = api
    payload = registration(**changes)
    response = client.post(AUTH + "/register", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert payload["password"] not in response.text
    with Session(engine) as db:
        assert len(db.scalars(select(User)).all()) == 4


def test_password_salts_unicode_and_spaces_are_preserved():
    password = "  " + "ẩ" * 80 + "  "
    first, second = hash_password(password), hash_password(password)
    assert first != second
    assert verify_password(password, first)
    assert not verify_password(password.strip(), first)
    assert not verify_password(password, "broken-hash")


@pytest.mark.parametrize("user_id,role", [(1, "customer"), (2, "vendor"), (3, "admin")])
def test_login_and_me_for_each_role(api, user_id, role):
    client, _ = api
    response = client.post(
        AUTH + "/login",
        json={"email": f" {role.upper()}{user_id}@EXAMPLE.VN ", "password": PASSWORD},
    )
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    body = response.json()
    assert body["user"]["role"] == role and body["token_type"] == "bearer"
    assert body["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert "hashed_password" not in response.text and PASSWORD not in response.text
    claims = jwt.decode(
        body["access_token"], settings.SECRET_KEY, algorithms=["HS256"], audience=AUDIENCE
    )
    assert claims["sub"] == str(user_id) and claims["token_type"] == "access"
    assert claims["iss"] == ISSUER and "role" not in claims
    me = client.get(AUTH + "/me", headers={"Authorization": "Bearer " + body["access_token"]})
    assert me.status_code == 200 and me.json() == body["user"]


@pytest.mark.parametrize(
    "email,password", [("missing@example.vn", PASSWORD), ("customer1@example.vn", "wrong")]
)
def test_login_failure_has_same_public_response(api, email, password):
    client, _ = api
    response = client.post(AUTH + "/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "INVALID_CREDENTIALS",
        "message": "Email hoặc mật khẩu không đúng.",
        "details": {},
    }
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_missing_user_still_checks_dummy_password(api, monkeypatch):
    client, _ = api
    checked = []
    original = service.verify_password

    def capture(password, encoded):
        checked.append(encoded)
        return original(password, encoded)

    monkeypatch.setattr(service, "verify_password", capture)
    assert (
        client.post(
            AUTH + "/login", json={"email": "missing@example.vn", "password": PASSWORD}
        ).status_code
        == 401
    )
    assert checked == [service.DUMMY_PASSWORD_HASH]


@pytest.mark.parametrize("authorization", [None, "Basic dXNlcjpwYXNz", "Bearer", "Bearer broken"])
def test_me_requires_bearer_token(api, authorization):
    client, _ = api
    response = client.get(
        AUTH + "/me", headers={"Authorization": authorization} if authorization else {}
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "change",
    [
        {"exp": 1},
        {"sub": None},
        {"sub": "-1"},
        {"sub": "1.0"},
        {"sub": "2147483648"},
        {"sub": 1},
        {"sub": "999"},
        {"iss": "other"},
        {"aud": "other"},
        {"token_type": "refresh"},
        {"token_type": None},
        {"jti": 123},
        {"iat": 4102444800},
        {"iat": "invalid"},
        {"exp": True},
        {"nbf": 4102444800},
    ],
)
def test_me_rejects_invalid_claims_or_missing_account(api, change):
    client, _ = api
    claims = jwt.get_unverified_claims(create_token(1, "access")) | change
    token = jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")
    assert client.get(AUTH + "/me", headers={"Authorization": "Bearer " + token}).status_code == 401


@pytest.mark.parametrize("claim", ["sub", "exp", "iat", "iss", "aud", "jti", "token_type"])
def test_me_rejects_missing_required_claim(api, claim):
    client, _ = api
    claims = jwt.get_unverified_claims(create_token(1, "access"))
    claims.pop(claim)
    token = jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")
    assert client.get(AUTH + "/me", headers={"Authorization": "Bearer " + token}).status_code == 401


@pytest.mark.parametrize("algorithm,key", [("HS512", None), ("HS256", "wrong-signing-key")])
def test_me_rejects_wrong_algorithm_and_signature(api, algorithm, key):
    client, _ = api
    claims = jwt.get_unverified_claims(create_token(1, "access"))
    token = jwt.encode(claims, key or settings.SECRET_KEY, algorithm=algorithm)
    assert client.get(AUTH + "/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_refresh_issues_distinct_tokens_and_access_can_get_me(api):
    client, _ = api
    old_refresh = create_token(1, "refresh")
    response = client.post(AUTH + "/refresh", json={"refresh_token": old_refresh})
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    body = response.json()
    assert body["refresh_token"] != old_refresh
    assert body["access_token"] != body["refresh_token"]
    assert (
        client.get(
            AUTH + "/me", headers={"Authorization": "Bearer " + body["access_token"]}
        ).status_code
        == 200
    )
    claims = jwt.get_unverified_claims(body["refresh_token"])
    assert claims["exp"] - claims["iat"] == settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


@pytest.mark.parametrize("kind,user_id", [("access", 1), ("refresh", 999)])
def test_refresh_rejects_access_token_or_missing_account(api, kind, user_id):
    client, _ = api
    assert (
        client.post(
            AUTH + "/refresh", json={"refresh_token": create_token(user_id, kind)}
        ).status_code
        == 401
    )


def test_refresh_rejects_expired_token(api):
    client, _ = api
    claims = jwt.get_unverified_claims(create_token(1, "refresh")) | {"exp": 1}
    token = jwt.encode(claims, settings.SECRET_KEY, algorithm="HS256")
    assert client.post(AUTH + "/refresh", json={"refresh_token": token}).status_code == 401


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("login", {"email": "customer1@example.vn"}),
        ("login", {"email": "customer1@example.vn", "password": PASSWORD, "role": "admin"}),
        ("refresh", {}),
        ("refresh", {"refresh_token": ""}),
        ("refresh", {"refresh_token": "a" * 4097}),
    ],
)
def test_invalid_login_or_refresh_payload_is_validation_error(api, endpoint, payload):
    client, _ = api
    response = client.post(AUTH + "/" + endpoint, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert PASSWORD not in response.text


def test_corrupted_stored_password_does_not_cause_server_error(api):
    client, engine = api
    with Session(engine) as db:
        db.get(User, 1).hashed_password = "broken-hash"
        db.commit()
    response = client.post(
        AUTH + "/login", json={"email": "customer1@example.vn", "password": PASSWORD}
    )
    assert response.status_code == 401


def test_refresh_is_stateless_and_old_token_remains_valid_until_expiry(api):
    client, _ = api
    token = create_token(1, "refresh")
    for _ in range(2):
        assert client.post(AUTH + "/refresh", json={"refresh_token": token}).status_code == 200


@pytest.mark.parametrize("user_id,status", [(1, 403), (2, 403), (3, 200)])
def test_admin_role_guard(api, user_id, status):
    client, _ = api
    assert client.get("/admin-only", headers=headers(user_id)).status_code == status


@pytest.mark.parametrize("user_id,status", [(1, 403), (2, 200), (3, 200)])
def test_guard_accepts_multiple_allowed_roles(api, user_id, status):
    client, _ = api
    assert client.get("/staff-only", headers=headers(user_id)).status_code == status


def test_role_guard_uses_current_database_role(api):
    client, engine = api
    token_headers = headers(3)
    with Session(engine) as db:
        db.get(User, 3).role = UserRole.CUSTOMER
        db.commit()
    assert client.get("/admin-only", headers=token_headers).status_code == 403


@pytest.mark.parametrize(
    "user_id,restaurant_id,status",
    [(2, 1, 200), (2, 2, 403), (4, 1, 403), (1, 1, 403), (3, 1, 403)],
)
def test_vendor_guard_checks_role_and_exact_membership(api, user_id, restaurant_id, status):
    client, _ = api
    response = client.get(f"/restaurants/{restaurant_id}/private", headers=headers(user_id))
    assert response.status_code == status
    if status == 200:
        assert response.json() == {"restaurant_id": 1}


def test_registration_race_is_reported_as_conflict_and_session_recovers(api, monkeypatch):
    _, engine = api
    with Session(engine) as db:
        original = db.scalar
        calls = 0

        def simulate_race(*args, **kwargs):
            nonlocal calls
            calls += 1
            return None if calls == 1 else original(*args, **kwargs)

        monkeypatch.setattr(db, "scalar", simulate_race)
        with pytest.raises(ConflictError) as exc:
            service.register(db, RegisterRequest(**registration(email="customer1@example.vn")))
        assert exc.value.code == "EMAIL_EXISTS"
        assert db.get(User, 1).email == "customer1@example.vn"


def test_registration_does_not_mask_unrelated_database_error(api, monkeypatch):
    _, engine = api
    with Session(engine) as db:

        def fail_commit():
            raise IntegrityError("insert", {}, ValueError("unrelated constraint"))

        monkeypatch.setattr(db, "commit", fail_commit)
        with pytest.raises(IntegrityError):
            service.register(db, RegisterRequest(**registration()))
        assert db.get(User, 1) is not None


@pytest.mark.parametrize("secret", ["short", "changeme-generate-a-random-secret-key", ""])
def test_placeholder_or_short_secret_cannot_issue_jwt(api, monkeypatch, secret):
    client, _ = api
    monkeypatch.setattr(settings, "SECRET_KEY", secret)
    response = client.post(
        AUTH + "/login", json={"email": "customer1@example.vn", "password": PASSWORD}
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_NOT_CONFIGURED"
    assert PASSWORD not in response.text


@pytest.mark.parametrize(
    "values",
    [
        {"ALGORITHM": "RS256"},
        {"ACCESS_TOKEN_EXPIRE_MINUTES": 0},
        {"ACCESS_TOKEN_EXPIRE_MINUTES": 1441},
        {"REFRESH_TOKEN_EXPIRE_DAYS": 0},
        {"REFRESH_TOKEN_EXPIRE_DAYS": 31},
    ],
)
def test_auth_configuration_rejects_invalid_algorithm_or_lifetime(values):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **values)


def test_production_app_mounts_auth_without_test_guard_routes():
    schema = production_app.openapi()
    assert schema["paths"][AUTH + "/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert {path for path in schema["paths"] if path.startswith(AUTH + "/")} == {
        AUTH + "/register",
        AUTH + "/login",
        AUTH + "/refresh",
        AUTH + "/me",
    }
    assert "/health" in schema["paths"]
    assert not {"/admin-only", "/staff-only"} & set(schema["paths"])

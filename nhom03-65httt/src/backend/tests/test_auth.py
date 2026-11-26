"""Kiểm thử xác thực JWT và phân quyền Admin/Viewer (HA3, Nhóm 03)."""

import base64
from datetime import timedelta
import json
import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password, verify_password
from app.main import app

client = TestClient(app)

TEST_JWT_SECRET = "super-secret-key-for-unit-testing-min-32-chars-long"
TEST_ADMIN_USER = "testadmin"
TEST_ADMIN_PASS = "admin_secure_pass_123"
TEST_VIEWER_USER = "testviewer"
TEST_VIEWER_PASS = "viewer_secure_pass_456"


@pytest.fixture(autouse=True)
def setup_auth_env(monkeypatch):
    """Thiết lập môi trường bảo mật phục vụ kiểm thử."""
    monkeypatch.setenv("AUTH_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("AUTH_TOKEN_MINUTES", "30")
    monkeypatch.setenv("AUTH_ADMIN_USER", TEST_ADMIN_USER)
    monkeypatch.setenv("AUTH_ADMIN_PASSWORD", TEST_ADMIN_PASS)
    monkeypatch.setenv("AUTH_VIEWER_USER", TEST_VIEWER_USER)
    monkeypatch.setenv("AUTH_VIEWER_PASSWORD", TEST_VIEWER_PASS)


def test_password_hashing():
    """Kiểm tra hàm băm mật khẩu và đối soát tính đúng đắn."""
    pwd = "my_secret_password"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_login_success_admin():
    """Đăng nhập Admin thành công trả về 200 kèm JWT token và role=admin."""
    res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "admin"
    assert data["expires_in"] == 30 * 60


def test_login_success_viewer():
    """Đăng nhập Viewer thành công trả về 200 kèm JWT token và role=viewer."""
    res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_VIEWER_USER, "password": TEST_VIEWER_PASS},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "viewer"


def test_login_wrong_password_returns_401():
    """HA3.1: Sai mật khẩu trả về 401."""
    res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USER, "password": "sai_mat_khau"},
    )
    assert res.status_code == 401
    assert "chính xác" in res.json()["detail"].lower()


def test_login_unknown_user_returns_401():
    """Tài khoản không tồn tại trả về 401."""
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "khong_ton_tai", "password": "any"},
    )
    assert res.status_code == 401


def test_missing_token_returns_401():
    """HA3.3: Không có token truy cập điểm cuối được bảo vệ trả về 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_invalid_token_returns_401():
    """Token sai định dạng/sai chữ ký trả về 401."""
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer token.khong.hop.le"},
    )
    assert res.status_code == 401


def test_expired_token_returns_401():
    """HA3.3: Token đã hết hạn trả về 401."""
    expired_token, _ = create_access_token(
        data={"sub": TEST_VIEWER_USER, "role": "viewer"},
        expires_delta=timedelta(seconds=-10),
    )
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "hết hạn" in res.json()["detail"].lower()


def test_me_with_valid_token():
    """Lấy thông tin tài khoản thành công qua GET /api/v1/auth/me."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
    )
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == TEST_ADMIN_USER
    assert data["role"] == "admin"


def test_admin_ping_allowed_for_admin():
    """Admin gọi điểm cuối admin thành công trả về 200."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
    )
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/v1/auth/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "role": "admin"}


def test_admin_ping_forbidden_for_viewer():
    """HA3.2: Viewer gọi điểm cuối Admin bị từ chối 403."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_VIEWER_USER, "password": TEST_VIEWER_PASS},
    )
    token = login_res.json()["access_token"]

    res = client.get(
        "/api/v1/auth/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert "quản trị viên" in res.json()["detail"].lower()


def test_missing_secret_returns_500(monkeypatch):
    """HA3.5: Thiếu AUTH_JWT_SECRET trong môi trường sẽ báo lỗi 500, không lộ bí mật."""
    monkeypatch.setenv("AUTH_JWT_SECRET", "")
    res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
    )
    assert res.status_code == 500
    assert "AUTH_JWT_SECRET" in res.json()["detail"]


@pytest.mark.parametrize("username,password", [
    ("quảntrị", "x"), (TEST_ADMIN_USER, "mậtkhẩu"), ("admin😀", "x"),
])
def test_login_non_ascii_returns_401(username, password):
    """A1: Tên đăng nhập hoặc mật khẩu có dấu tiếng Việt, emoji trả 401 chứ không 500."""
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 401


def test_short_secret_returns_500(monkeypatch):
    """A2: Khóa ký AUTH_JWT_SECRET dưới 32 ký tự bị từ chối 500."""
    monkeypatch.setenv("AUTH_JWT_SECRET", "123")
    res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASS},
    )
    assert res.status_code == 500
    assert "ít nhất 32 ký tự" in res.json()["detail"]


def test_token_alg_none_returns_401():
    """A4: Token giả mạo dùng thuật toán alg=none bị từ chối 401."""
    header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').decode().rstrip("=")
    payload = base64.urlsafe_b64encode(
        f'{{"sub":"{TEST_ADMIN_USER}","role":"admin","exp":9999999999}}'.encode()
    ).decode().rstrip("=")
    token_none = f"{header}.{payload}."
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_none}"})
    assert res.status_code == 401


def test_token_different_key_returns_401():
    """A4: Token ký bằng khóa khác bị từ chối 401."""
    other_key = "a" * 32
    token = jwt.encode(
        {"sub": TEST_ADMIN_USER, "role": "admin", "exp": 9999999999},
        other_key,
        algorithm="HS256",
    )
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_tampered_role_returns_401():
    """A4: Token sửa payload từ viewer thành admin nhưng giữ chữ ký cũ bị từ chối 401."""
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": TEST_VIEWER_USER, "password": TEST_VIEWER_PASS},
    )
    token = login_res.json()["access_token"]
    parts = token.split(".")
    assert len(parts) == 3

    padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
    payload_data = json.loads(base64.urlsafe_b64decode(padded.encode()).decode())
    payload_data["role"] = "admin"
    tampered_payload = (
        base64.urlsafe_b64encode(json.dumps(payload_data).encode()).decode().rstrip("=")
    )
    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    res = client.get(
        "/api/v1/auth/admin/ping",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert res.status_code == 401


def test_token_missing_exp_returns_401():
    """A3/A4: Token không có trường exp (hạn sử dụng) bị từ chối 401."""
    token_no_exp = jwt.encode(
        {"sub": TEST_ADMIN_USER, "role": "admin"},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_no_exp}"})
    assert res.status_code == 401


"""Kiểm thử API tìm kiếm, lọc và phân trang đánh giá (HA2, Nhóm 03).

Quy tắc:
- Không dùng dữ liệu bịa trong mã nguồn để làm test qua.
- Các bài kiểm thử CSDL chạy trên PostgreSQL thật trong giao dịch rollback, tự bỏ qua (pytest.skip) nếu không kết nối được CSDL cục bộ.
- Kiểm tra rõ ràng các mã lỗi HTTP 503, 422, 404 và cơ chế bảo mật che thông tin cá nhân.
"""

from __future__ import annotations

import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
import psycopg

from app.core.config import get_settings
from app.main import app

client = TestClient(app)


# ============================================================================
# Nhóm 1: Kiểm thử không phụ thuộc CSDL (Xác thực đầu vào & xử lý lỗi 503, 422)
# ============================================================================


def test_missing_database_url_returns_503(monkeypatch):
    """B1: DATABASE_URL rỗng trả về HTTP 503 rõ ràng, chứng minh không có nhánh dữ liệu bịa."""
    monkeypatch.setattr(get_settings(), "database_url", "")
    res = client.get("/api/v1/reviews")
    assert res.status_code == 503
    assert "chưa cấu hình cơ sở dữ liệu" in res.json()["detail"].lower()


def test_invalid_database_url_returns_503(monkeypatch):
    """B1: DATABASE_URL sai thông tin kết nối trả về HTTP 503."""
    bad_url = "postgresql://eduvision:sai_mat_khau@127.0.0.1:5432/eduvision_invalid"
    monkeypatch.setattr(get_settings(), "database_url", bad_url)
    res = client.get("/api/v1/reviews")
    assert res.status_code == 503
    assert "không kết nối được cơ sở dữ liệu" in res.json()["detail"].lower()


def test_get_single_review_missing_database_url_returns_503(monkeypatch):
    """B1: GET /reviews/{id} khi thiếu DATABASE_URL trả về 503, không tra trong mẫu bịa."""
    monkeypatch.setattr(get_settings(), "database_url", "")
    res = client.get("/api/v1/reviews/1")
    assert res.status_code == 503


def test_invalid_date_format_returns_422():
    """HA2.5: Ngày sai định dạng trả về 422 Unprocessable Entity."""
    res = client.get("/api/v1/reviews?start_date=ngay-sai-dinh-dang")
    assert res.status_code == 422


def test_invalid_rating_range_returns_422():
    """Số sao ngoài phạm vi 1-5 trả về 422."""
    res = client.get("/api/v1/reviews?rating=6")
    assert res.status_code == 422


def test_invalid_page_returns_422():
    """Số trang < 1 trả về 422."""
    res = client.get("/api/v1/reviews?page=0")
    assert res.status_code == 422


# ============================================================================
# Nhóm 2: Kiểm thử với CSDL PostgreSQL thật (Giao dịch hoàn tác - Rollback)
# ============================================================================


@pytest.fixture()
def db_conn() -> Generator[psycopg.Connection, None, None]:
    """Kết nối PostgreSQL phục vụ kiểm thử, hoàn tác toàn bộ thay đổi sau mỗi bài."""
    settings = get_settings()
    db_url = settings.database_url or os.getenv("DATABASE_URL")
    if not db_url:
        # Thử đọc thông tin cấu hình từ biến môi trường chuẩn của nhóm
        user = os.getenv("POSTGRES_USER", "eduvision")
        pwd = os.getenv("POSTGRES_PASSWORD", "eduvision_secret_2026")
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "eduvision")
        db_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

    try:
        conn = psycopg.connect(db_url, connect_timeout=2)
    except Exception as exc:
        pytest.skip(f"Không kết nối được PostgreSQL cục bộ: {type(exc).__name__}")

    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


def test_sentiment_filter_without_sentiment_table_returns_422(db_conn, monkeypatch):
    """B4: Khi bảng dw.fact_review_sentiment chưa tồn tại, lọc cảm xúc hoặc lệch pha trả 422."""
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", db_conn.info.dsn)

    with db_conn.cursor() as cur:
        cur.execute("SELECT to_regclass('dw.fact_review_sentiment') IS NOT NULL")
        has_table = cur.fetchone()[0]

    if not has_table:
        res = client.get("/api/v1/reviews?sentiment=Tích cực")
        assert res.status_code == 422
        assert "chưa có nhãn cảm xúc từ mô hình" in res.json()["detail"].lower()

        res_mis = client.get("/api/v1/reviews?misaligned_only=true")
        assert res_mis.status_code == 422
        assert "chưa có nhãn cảm xúc từ mô hình" in res_mis.json()["detail"].lower()
    else:
        pytest.skip("Bảng dw.fact_review_sentiment đã tồn tại trên CSDL này")


def test_list_reviews_real_db_default_and_privacy(db_conn, monkeypatch):
    """HA2.4 & HA2.6: Lấy danh sách thật từ CSDL và đảm bảo không lộ thông tin cá nhân."""
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", db_conn.info.dsn)

    res = client.get("/api/v1/reviews?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 10

    for item in data["items"]:
        # HA2.6: Che dữ liệu cá nhân
        assert "author" not in item
        assert "author_name" not in item
        assert "email" not in item
        assert "avatar" not in item
        assert "profile" not in item


def test_keyword_escape_wildcards(db_conn, monkeypatch):
    """B3: Kiểm tra cơ chế thoát ký tự đại diện % và _ trong từ khóa."""
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", db_conn.info.dsn)

    # Tìm kiếm với ký tự % (ví dụ 100%) không được biến thành wildcard so khớp toàn bộ
    res_pct = client.get("/api/v1/reviews?keyword=100%")
    assert res_pct.status_code == 200
    data_pct = res_pct.json()
    for item in data_pct["items"]:
        if item["text"]:
            assert "100%" in item["text"]

    # Tìm kiếm với ký tự _ không được coi là một ký tự bất kỳ của LIKE
    res_underscore = client.get("/api/v1/reviews?keyword=_")
    assert res_underscore.status_code == 200
    data_und = res_underscore.json()
    for item in data_und["items"]:
        if item["text"]:
            assert "_" in item["text"]


def test_list_reviews_page_out_of_range_returns_empty(db_conn, monkeypatch):
    """HA2.5: Trang vượt quá tổng số trang trả về danh sách rỗng, không sập 500."""
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", db_conn.info.dsn)

    res = client.get("/api/v1/reviews?page=999999")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["page"] == 999999


def test_get_single_review_not_found(db_conn, monkeypatch):
    """Đánh giá không tồn tại trả về 404."""
    settings = get_settings()
    monkeypatch.setattr(settings, "database_url", db_conn.info.dsn)

    res = client.get("/api/v1/reviews/999999999")
    assert res.status_code == 404
    assert "không tìm thấy" in res.json()["detail"].lower()

"""Kiểm thử API tìm kiếm, lọc và phân trang đánh giá (HA2, Nhóm 03)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_reviews_default():
    """Lấy danh sách đánh giá mặc định (trang 1, kích thước 20)."""
    res = client.get("/api/v1/reviews")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) > 0


def test_list_reviews_filter_by_platform():
    """HA2.4: Lọc theo nền tảng trả về đúng các đánh giá của nền tảng đó."""
    res = client.get("/api/v1/reviews?platform=ELSA+Speak")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["platform"].lower() == "elsa speak"


def test_list_reviews_filter_by_sentiment():
    """HA2.4: Lọc theo cảm xúc (Tích cực)."""
    res = client.get("/api/v1/reviews?sentiment=Tích cực")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["sentiment"] == "Tích cực"


def test_list_reviews_filter_by_date_range():
    """HA2.4: Lọc theo khoảng ngày (start_date, end_date)."""
    res = client.get("/api/v1/reviews?start_date=2026-10-20&end_date=2026-10-22")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        if item["created_at"]:
            assert "2026-10-20" <= item["created_at"] <= "2026-10-22"


def test_list_reviews_invalid_date_returns_422():
    """HA2.5: Ngày sai định dạng trả về lỗi 422 Unprocessable Entity."""
    res = client.get("/api/v1/reviews?start_date=ngay-sai-dinh-dang")
    assert res.status_code == 422


def test_list_reviews_page_out_of_range_returns_empty():
    """HA2.5: Trang vượt quá tổng số trang trả về danh sách rỗng, không sập 500."""
    res = client.get("/api/v1/reviews?page=999999")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["page"] == 999999


def test_list_reviews_does_not_leak_author_info():
    """HA2.6: Dữ liệu trả về tuyệt đối không chứa tên thật hoặc hồ sơ tác giả."""
    res = client.get("/api/v1/reviews")
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert "author" not in item
        assert "author_name" not in item
        assert "email" not in item
        assert "avatar" not in item
        assert "profile" not in item


def test_list_reviews_misaligned_only():
    """Lọc các ca lệch pha (số sao và nội dung mâu thuẫn)."""
    res = client.get("/api/v1/reviews?misaligned_only=true")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0
    for item in data["items"]:
        assert item["misaligned"] is True


def test_get_single_review_success():
    """Lấy chi tiết đánh giá hợp lệ qua /reviews/{review_key}."""
    res = client.get("/api/v1/reviews/1")
    assert res.status_code == 200
    data = res.json()
    assert data["review_key"] == 1
    assert data["platform"] == "ELSA Speak"


def test_get_single_review_not_found():
    """Đánh giá không tồn tại trả về 404."""
    res = client.get("/api/v1/reviews/99999999")
    assert res.status_code == 404

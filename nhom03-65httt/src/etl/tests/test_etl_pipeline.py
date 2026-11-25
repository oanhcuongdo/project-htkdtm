"""Kiểm thử ETL trên PostgreSQL thật (cục bộ). Bỏ qua nếu không kết nối được CSDL.

Mỗi bài chạy trong một giao dịch và hoàn tác ở cuối nên không để lại dữ liệu.
Dữ liệu thử là mẫu tự tạo, dùng nguồn riêng `test_src` để không lẫn với dữ liệu thật.
"""

import csv
import sys
from pathlib import Path

import pytest

ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ETL_DIR))
sys.path.insert(0, str(ETL_DIR / "load"))

from common import connect  # noqa: E402
from load_clean import load_clean  # noqa: E402
from load_dw import load_dw  # noqa: E402
from load_news import load_news  # noqa: F401,E402
from load_raw import load_raw  # noqa: E402

COLUMNS = [
    "source", "product", "review_id", "author_hash", "rating", "text", "lang_guess", "created_at",
    "app_version", "thumbs_up", "reply_text", "crawled_at", "platform_group", "source_type",
]


def _row(review_id, product, rating, text, created_at, thumbs_up="0"):
    return {
        "source": "test_src", "product": product, "review_id": review_id, "author_hash": "abc123abc123",
        "rating": rating, "text": text, "lang_guess": "vi", "created_at": created_at,
        "app_version": "1.0", "thumbs_up": thumbs_up, "reply_text": "", "crawled_at": "2025-01-05T00:00:00+00:00",
        "platform_group": "trong_nuoc", "source_type": "kho_ung_dung",
    }


SAMPLE = [
    _row("a1", "ELSA Speak", "5", "Học rất tốt", "2025-01-02T03:00:00+00:00", "3"),
    _row("a2", "VUIHOC", "", "Hay quá", "2025-01-02T18:30:00+00:00"),
    _row("a3", "ELSA Speak", "4", "Gọi 0912345678 nhé", "2025-01-03T01:00:00+00:00"),
    _row("a1", "ELSA Speak", "1", "Dòng trùng khóa", "2025-01-04T01:00:00+00:00"),   # trùng (source, review_id)
    _row("a4", "ELSA Speak", "3", "   ", "2025-01-04T01:00:00+00:00"),                # rỗng sau làm sạch
    _row("a5", "ELSA Speak", "3", "Không có ngày", ""),                              # thiếu created_at
    _row("a6", "KHONG_CO_NEN_TANG", "3", "Nền tảng lạ", "2025-01-04T01:00:00+00:00"),  # nền tảng không có trong cấu hình
]


@pytest.fixture()
def conn():
    try:
        connection = connect(connect_timeout=3)
    except Exception as exc:  # không có CSDL cục bộ thì bỏ qua, không làm hỏng bộ kiểm thử
        pytest.skip(f"Không kết nối được PostgreSQL cục bộ: {type(exc).__name__}")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _write_csv(tmp_path: Path) -> Path:
    path = tmp_path / "sample.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(SAMPLE)
    return path


def _count(conn, sql, params=None):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def test_pipeline_loads_cleans_and_is_idempotent(conn, tmp_path):
    csv_path = _write_csv(tmp_path)

    raw = load_raw(conn, csv_path)
    assert raw["read"] == 7
    assert raw["inserted"] == 6            # dòng trùng a1 bị bỏ
    clean = load_clean(conn)
    assert clean["inserted"] >= 5          # a4 rỗng bị loại
    dw = load_dw(conn)
    assert dw["platforms"] >= 9

    assert _count(conn, "SELECT count(*) FROM raw.review_raw WHERE source = 'test_src'") == 6
    assert _count(conn, "SELECT count(*) FROM clean.review_text WHERE source = 'test_src'") == 5
    # fact: a1, a2, a3 (a5 thiếu ngày, a6 nền tảng lạ bị loại)
    fact_sql = """
        SELECT count(*) FROM dw.fact_review f JOIN clean.review_text c USING (review_key)
        WHERE c.source = 'test_src'
    """
    assert _count(conn, fact_sql) == 3

    # số điện thoại đã bị che ở lớp clean nhưng còn nguyên ở lớp raw
    masked = _count(conn, "SELECT count(*) FROM clean.review_text WHERE source='test_src' AND text LIKE '%[SDT]%'")
    assert masked == 1
    assert _count(conn, "SELECT count(*) FROM clean.review_text WHERE source='test_src' AND text LIKE '%0912%'") == 0

    # giờ Việt Nam: 2025-01-02 18:30 UTC thuộc ngày 3
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT f.time_key, f.rating, f.thumbs_up FROM dw.fact_review f
            JOIN clean.review_text c USING (review_key) WHERE c.source='test_src' AND c.review_id IN ('a1','a2')
            ORDER BY c.review_id
            """
        )
        (a1_time, a1_rating, a1_thumbs), (a2_time, a2_rating, _) = cur.fetchall()
    assert (a1_time, a1_rating, a1_thumbs) == (20250102, 5, 3)
    assert a2_time == 20250103 and a2_rating is None   # bình luận không có sao

    # chạy lại: không sinh thêm dòng nào
    raw_again = load_raw(conn, csv_path)
    clean_again = load_clean(conn)
    dw_again = load_dw(conn)
    assert raw_again["inserted"] == 0
    assert clean_again["inserted"] == 0 or _count(
        conn, "SELECT count(*) FROM clean.review_text WHERE source = 'test_src'") == 5
    assert dw_again["inserted"] == 0
    assert _count(conn, "SELECT count(*) FROM raw.review_raw WHERE source = 'test_src'") == 6
    assert _count(conn, fact_sql) == 3


def test_load_raw_rejects_file_missing_columns(conn, tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("source,product\ngoogle_play,ELSA Speak\n", encoding="utf-8")
    with pytest.raises(ValueError, match="thiếu cột"):
        load_raw(conn, bad)


NEWS_COLUMNS = ["platform", "origin", "title", "outlet", "link", "published_at", "collected_at", "title_hash"]


def _news(platform, title, title_hash, published="2025-02-01T07:00:00+00:00", outlet="Báo mẫu"):
    return {
        "platform": platform, "origin": "google_news", "title": title, "outlet": outlet,
        "link": "https://example.org/bai-" + title_hash, "published_at": published,
        "collected_at": "2025-02-02T00:00:00+00:00", "title_hash": title_hash,
    }


NEWS_SAMPLE = [
    _news("ELSA Speak", "  ELSA   ra mắt tính năng mới ", "tn0001"),
    _news("DUOLINGO", "Duolingo tăng giá gói Plus", "tn0002"),
    _news("ELSA Speak", "ELSA ra mắt tính năng mới (trùng)", "tn0001"),   # trùng (mã bài, nền tảng)
    _news("DUOLINGO", "Cùng một bài nhắc hai nền tảng", "tn0003"),
    _news("ELSA Speak", "Cùng một bài nhắc hai nền tảng", "tn0003"),       # cùng mã bài, nền tảng khác: giữ cả hai
    _news("NenTangLa", "Nền tảng không có trong cấu hình", "tn0004"),
    _news("DUOLINGO", "   ", "tn0005"),                                    # tiêu đề rỗng
    _news("DUOLINGO", "Thiếu ngày đăng", "tn0006", published=""),
]


def _write_news_csv(tmp_path: Path) -> Path:
    path = tmp_path / "news_sample.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=NEWS_COLUMNS)
        writer.writeheader()
        writer.writerows(NEWS_SAMPLE)
    return path


def test_load_news_filters_dedupes_and_is_idempotent(conn, tmp_path):
    from load_news import load_news

    news_csv = _write_news_csv(tmp_path)
    first = load_news(conn, news_csv)
    assert first["read"] == 8
    assert first["unknown_platform"] == 1
    assert first["empty_title"] == 1
    assert first["inserted"] == 5   # tn0001, tn0002, tn0003 x2, tn0006

    ids = "('tn0001','tn0002','tn0003','tn0004','tn0005','tn0006')"
    assert _count(conn, f"SELECT count(*) FROM clean.news_article WHERE article_id IN {ids}") == 5
    with conn.cursor() as cur:
        cur.execute("SELECT title, outlet, link FROM clean.news_article WHERE article_id = 'tn0001'")
        title, outlet, link = cur.fetchone()
        cur.execute("SELECT published_at FROM clean.news_article WHERE article_id = 'tn0006'")
        missing_date = cur.fetchone()[0]
    assert title == "ELSA ra mắt tính năng mới"          # chuẩn hóa khoảng trắng, giữ dòng đầu của cặp trùng
    assert outlet == "Báo mẫu" and link.startswith("https://")
    assert missing_date is None                            # thiếu ngày vẫn lưu, ngày để trống

    again = load_news(conn, news_csv)
    assert again["inserted"] == 0
    assert _count(conn, f"SELECT count(*) FROM clean.news_article WHERE article_id IN {ids}") == 5


def test_load_news_rejects_file_missing_columns(conn, tmp_path):
    from load_news import load_news

    bad = tmp_path / "bad_news.csv"
    bad.write_text("platform,title\nELSA Speak,abc\n", encoding="utf-8")
    with pytest.raises(ValueError, match="thiếu cột"):
        load_news(conn, bad)

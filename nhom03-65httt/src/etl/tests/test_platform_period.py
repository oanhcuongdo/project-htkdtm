"""Kiểm thử tổng hợp fact_platform_period (T3) trên PostgreSQL cục bộ. Bỏ qua nếu không kết nối được CSDL.

Mỗi bài chạy trong một giao dịch và hoàn tác ở cuối. Dữ liệu thử là mẫu tự tạo ở tháng 05/2010 (nguồn `test_src`),
tháng không có trong dữ liệu thật nên số liệu tính tay đối chiếu được chính xác.
"""

import csv
import sys
from pathlib import Path

import pytest

ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ETL_DIR))
sys.path.insert(0, str(ETL_DIR / "load"))
sys.path.insert(0, str(ETL_DIR.parent / "bi"))

from bhi import compute_bhi  # noqa: E402
from common import connect  # noqa: E402
from load_clean import load_clean  # noqa: E402
from load_dw import load_dw  # noqa: E402
from load_platform_period import PlatformPeriodError, build_platform_period  # noqa: E402
from load_raw import load_raw  # noqa: E402

COLUMNS = ["source", "product", "review_id", "author_hash", "rating", "text", "lang_guess", "created_at",
           "app_version", "thumbs_up", "reply_text", "crawled_at"]
MONTH_KEY = 20100501


def _row(review_id, product, rating, day=10):
    return {"source": "test_src", "product": product, "review_id": review_id, "author_hash": "abc",
            "rating": rating, "text": f"nội dung {review_id}", "lang_guess": "vi",
            "created_at": f"2010-05-{day:02d}T03:00:00+00:00", "app_version": "1", "thumbs_up": "0",
            "reply_text": "", "crawled_at": "2026-11-25T00:00:00+00:00"}


# ELSA Speak (trong_nuoc) 7 đánh giá: sao 5,5,4,3,1,2 và một bình luận không có sao
# VUIHOC (trong_nuoc) 3 đánh giá: 5,5,5; DUOLINGO (quoc_te) 2 đánh giá: 1,1
SAMPLE = (
    [_row(f"e{i}", "ELSA Speak", r) for i, r in enumerate(["5", "5", "4", "3", "1", "2", ""])]
    + [_row(f"v{i}", "VUIHOC", "5") for i in range(3)]
    + [_row(f"d{i}", "DUOLINGO", "1") for i in range(2)]
)


@pytest.fixture()
def conn():
    try:
        connection = connect(connect_timeout=3)
    except Exception as exc:
        pytest.skip(f"Không kết nối được PostgreSQL cục bộ: {type(exc).__name__}")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture()
def loaded(conn, tmp_path):
    path = tmp_path / "sample.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(SAMPLE)
    load_raw(conn, path)
    load_clean(conn)
    load_dw(conn)
    return conn


def _period(conn, platform):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT f.new_review_count, f.positive_rate, f.negative_rate, f.avg_rating, f.sentiment_index,
                   f.bhi, f.review_share_in_group
            FROM dw.fact_platform_period f JOIN dw.dim_platform p USING (platform_key)
            WHERE p.platform_name = %s AND f.time_key = %s
            """, (platform, MONTH_KEY))
        return cur.fetchone()


def _snapshot(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT platform_key, time_key, new_review_count, positive_rate, negative_rate, avg_rating, "
                    "sentiment_index, bhi, review_share_in_group FROM dw.fact_platform_period ORDER BY 1, 2")
        return cur.fetchall()


def test_rating_mode_matches_hand_calculation(loaded):
    result = build_platform_period(loaded)
    assert result["sentiment_source"] == "rating"

    count, pos_rate, neg_rate, avg, si, bhi, share = _period(loaded, "ELSA Speak")
    assert count == 7                                   # gồm cả bình luận không có sao
    assert float(pos_rate) == pytest.approx(3 / 6, abs=1e-4)   # 5,5,4 trên 6 đánh giá có sao
    assert float(neg_rate) == pytest.approx(2 / 6, abs=1e-4)   # 1,2
    assert float(avg) == pytest.approx(20 / 6, abs=0.01)       # (5+5+4+3+1+2)/6 = 3,33
    assert float(si) == pytest.approx(100 * (3 - 2) / 6, abs=0.001)
    assert float(share) == pytest.approx(7 / 10, abs=1e-4)     # 7 trên (7 + 3) trong nhóm trong nước

    count, pos_rate, neg_rate, avg, si, bhi_v, share = _period(loaded, "VUIHOC")
    assert (count, float(pos_rate), float(neg_rate), float(avg), float(si)) == (3, 1.0, 0.0, 5.0, 100.0)
    assert float(bhi_v) == 100.0 and float(share) == pytest.approx(3 / 10, abs=1e-4)

    count, pos_rate, neg_rate, avg, si, bhi_d, share = _period(loaded, "DUOLINGO")
    assert (count, float(neg_rate), float(si), float(avg)) == (2, 1.0, -100.0, 1.0)
    assert float(bhi_d) == 0.0 and float(share) == 1.0         # một mình trong nhóm quốc tế


def test_bhi_in_sql_equals_python_function(loaded):
    build_platform_period(loaded)
    _count, _p, _n, avg, si, bhi, _share = _period(loaded, "ELSA Speak")
    # cùng đầu vào CHƯA làm tròn (3 tích cực, 2 tiêu cực, 6 có sao, tổng sao 20): SQL và Python phải trùng
    exact_si, exact_avg = 100 * (3 - 2) / 6, 20 / 6
    assert float(bhi) == pytest.approx(compute_bhi(exact_si, exact_avg, 7)["bhi"], abs=0.006)
    # tính lại từ giá trị ĐÃ LÀM TRÒN lưu trong bảng thì lệch nhẹ (dưới 0,05), không phải lỗi công thức
    assert float(bhi) == pytest.approx(compute_bhi(float(si), float(avg), 7)["bhi"], abs=0.05)


def test_is_idempotent_and_adds_month_start_dates(loaded):
    first = build_platform_period(loaded)
    assert first["month_dates_added"] >= 1                     # 2010-05-01 chưa có trong dim_time
    snapshot = _snapshot(loaded)
    second = build_platform_period(loaded)
    assert second["month_dates_added"] == 0
    assert _snapshot(loaded) == snapshot                       # chạy lại không đổi kết quả
    assert second["rows_in_table"] == first["rows_in_table"]


def test_total_reviews_counted_equals_fact_review(loaded):
    result = build_platform_period(loaded)
    assert result["reviews_counted"] == result["fact_review_total"]


def test_month_with_only_unrated_reviews_has_null_rates_and_bhi(conn, tmp_path):
    rows = [_row(f"y{i}", "MONKEY", "") for i in range(4)]
    path = tmp_path / "unrated.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    load_raw(conn, path)
    load_clean(conn)
    load_dw(conn)
    build_platform_period(conn)
    count, pos_rate, neg_rate, avg, si, bhi, share = _period(conn, "MONKEY")
    assert count == 4 and pos_rate is None and neg_rate is None and avg is None and si is None and bhi is None
    assert float(share) == 1.0


def test_model_mode_uses_model_labels(loaded):
    with loaded.cursor() as cur:
        # bảng tạm (mất khi hết phiên) để không phụ thuộc việc dw.fact_review_sentiment của migration 0004 đã có hay chưa
        cur.execute("""CREATE TEMP TABLE t3_sentiment (
                           review_key bigint PRIMARY KEY, sentiment_label text NOT NULL)""")
        # mô hình gán khác số sao: 4 tích cực, 1 trung tính, 2 tiêu cực trên 7 đánh giá của ELSA Speak
        cur.execute("""
            INSERT INTO t3_sentiment (review_key, sentiment_label)
            SELECT f.review_key,
                   (ARRAY['tich_cuc','tich_cuc','tich_cuc','tich_cuc','trung_tinh','tieu_cuc','tieu_cuc'])[
                       row_number() OVER (ORDER BY c.review_id)]
            FROM dw.fact_review f
            JOIN clean.review_text c USING (review_key)
            JOIN dw.dim_platform p USING (platform_key)
            WHERE c.source = 'test_src' AND p.platform_name = 'ELSA Speak'""")
    result = build_platform_period(loaded, "model", "pg_temp.t3_sentiment")
    assert result["sentiment_source"] == "model"
    count, pos_rate, neg_rate, avg, si, bhi, share = _period(loaded, "ELSA Speak")
    assert count == 7
    assert float(pos_rate) == pytest.approx(4 / 7, abs=1e-4) and float(neg_rate) == pytest.approx(2 / 7, abs=1e-4)
    assert float(si) == pytest.approx(100 * (4 - 2) / 7, abs=0.001)
    assert float(avg) == pytest.approx(20 / 6, abs=0.01)        # số sao trung bình vẫn lấy từ rating
    # nền tảng không có nhãn M1: tỷ lệ để trống thay vì bịa
    assert _period(loaded, "VUIHOC")[1] is None


def test_model_mode_without_table_gives_clear_error(loaded):
    with pytest.raises(PlatformPeriodError, match="Chưa có bảng"):
        build_platform_period(loaded, "model", "dw.khong_ton_tai")


def test_rejects_unsafe_table_name_and_unknown_source(loaded):
    with pytest.raises(PlatformPeriodError, match="không hợp lệ"):
        build_platform_period(loaded, "model", "dw.fact_review_sentiment; DROP TABLE dw.fact_review")
    with pytest.raises(PlatformPeriodError, match="không hợp lệ"):
        build_platform_period(loaded, "model", "khong_co_schema")
    with pytest.raises(PlatformPeriodError):
        build_platform_period(loaded, "khong_ro")
    # bảng dw.fact_review vẫn nguyên vẹn sau các lần bị từ chối
    with loaded.cursor() as cur:
        cur.execute("SELECT count(*) FROM dw.fact_review")
        assert cur.fetchone()[0] >= 12


def _has_results_table(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('dw.fact_review_sentiment') IS NOT NULL")
        return cur.fetchone()[0]


def test_model_mode_with_empty_results_table_gives_clear_error(loaded):
    """Bảng nhãn M1 của migration 0004 đã có nhưng chưa có nhãn nào: báo lỗi, không ghi toàn giá trị rỗng."""
    if not _has_results_table(loaded):
        pytest.skip("Chưa chạy migration 0004 (thiếu dw.fact_review_sentiment)")
    with loaded.cursor() as cur:
        cur.execute("DELETE FROM dw.fact_review_sentiment")
    with pytest.raises(PlatformPeriodError, match="rỗng"):
        build_platform_period(loaded, "model")


def test_model_mode_reads_the_real_results_table_from_migration_0004(loaded):
    if not _has_results_table(loaded):
        pytest.skip("Chưa chạy migration 0004 (thiếu dw.fact_review_sentiment)")
    with loaded.cursor() as cur:
        cur.execute("DELETE FROM dw.fact_review_sentiment")
        cur.execute("""
            INSERT INTO dw.fact_review_sentiment (review_key, model_key, sentiment_label)
            SELECT f.review_key, (SELECT model_key FROM dw.dim_model WHERE model_name = 'M1_phobert'), 'tieu_cuc'
            FROM dw.fact_review f JOIN clean.review_text c USING (review_key)
            JOIN dw.dim_platform p USING (platform_key)
            WHERE c.source = 'test_src' AND p.platform_name = 'DUOLINGO'""")
    build_platform_period(loaded, "model")
    count, pos_rate, neg_rate, avg, si, bhi, share = _period(loaded, "DUOLINGO")
    assert count == 2 and float(neg_rate) == 1.0 and float(pos_rate) == 0.0 and float(si) == -100.0

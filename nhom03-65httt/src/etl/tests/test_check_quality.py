"""Kiểm thử check_quality.py trên PostgreSQL thật (cục bộ). Bỏ qua nếu không kết nối được CSDL.

Mỗi bài chạy trong một giao dịch và hoàn tác ở cuối nên không để lại dữ liệu.
Lỗi được chèn cố tình vào nguồn riêng `qa_src` (số sao 7, trùng khóa, văn bản rỗng, ngày ngoài miền...)
rồi kiểm tra mỗi lỗi được ghi đúng loại, đúng lớp, đúng số dòng.
"""

import sys
from pathlib import Path

import pytest

ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ETL_DIR))
sys.path.insert(0, str(ETL_DIR / "quality"))

from check_quality import run_checks  # noqa: E402
from common import connect  # noqa: E402

SRC = "qa_src"


@pytest.fixture()
def conn():
    try:
        connection = connect(connect_timeout=3)
    except Exception as exc:
        pytest.skip(f"Không kết nối được PostgreSQL cục bộ: {type(exc).__name__}")
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT to_regclass('dw.data_quality_log')")
            if cur.fetchone()[0] is None:
                pytest.skip("Chưa chạy migration 0004 (thiếu dw.data_quality_log)")
        yield connection
    finally:
        connection.rollback()
        connection.close()


def _one(cur, sql, params=None):
    cur.execute(sql, params)
    return cur.fetchone()[0]


def _seed_errors(conn):
    """Chèn dữ liệu thô, văn bản sạch và fact có lỗi cố tình cho nguồn qa_src."""
    with conn.cursor() as cur:
        cur.execute("INSERT INTO dw.dim_source (source_name, source_type) VALUES (%s, 'khac') RETURNING source_key", (SRC,))
        source_key = cur.fetchone()[0]
        cur.execute("SELECT platform_key FROM dw.dim_platform ORDER BY platform_key LIMIT 1")
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO dw.dim_platform (platform_name, platform_group) VALUES ('QA_PLATFORM', 'trong_nuoc') RETURNING platform_key")
            row = cur.fetchone()
        platform_key = row[0]
        for d in ("2025-01-02", "2999-01-01", "2005-06-01"):
            cur.execute(
                """
                INSERT INTO dw.dim_time (time_key, full_date, week, month, quarter, year)
                VALUES (to_char(%s::date, 'YYYYMMDD')::int, %s::date, 1, extract(month FROM %s::date),
                        extract(quarter FROM %s::date), extract(year FROM %s::date))
                ON CONFLICT (time_key) DO NOTHING
                """,
                (d, d, d, d, d),
            )

        # raw: 7 dòng; lỗi: 1 trùng khóa, 1 sao 7, 2 văn bản thiếu, 2 ngày ngoài miền
        raw = [
            ("d1", 5, "ok", "2025-01-02"), ("d1", 3, "ok", "2025-01-02"),   # trùng khóa
            ("r3", 7, "ok", "2025-01-02"),                                   # sao 7
            ("r4", 4, "", "2025-01-02"), ("r5", 3, None, "2025-01-02"),     # văn bản rỗng và null
            ("r6", 3, "ok", "2999-01-01"), ("r7", 3, "ok", "2005-06-01"),   # ngày tương lai và quá cũ
        ]
        for review_id, rating, text, created in raw:
            cur.execute(
                "INSERT INTO raw.review_raw (source, review_id, rating, text, created_at) VALUES (%s, %s, %s, %s, %s)",
                (SRC, review_id, rating, text, f"{created}T03:00:00+00:00"),
            )

        # clean + dw: 4 dòng; c1 và c2 trùng nội dung, c3 văn bản rỗng, c3 ngày 2999, c4 ngày 2005
        clean = [
            ("c1", "noi dung a", "h1", "2025-01-02"), ("c2", "noi dung a", "h1", "2025-01-02"),
            ("c3", "", "h3", "2999-01-01"), ("c4", "noi dung b", "h4", "2005-06-01"),
        ]
        for review_id, text, text_hash, d in clean:
            cur.execute(
                "INSERT INTO clean.review_text (review_id, source, text, text_hash) VALUES (%s, %s, %s, %s) RETURNING review_key",
                (review_id, SRC, text, text_hash),
            )
            review_key = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO dw.fact_review (review_key, time_key, platform_key, source_key, rating) "
                "VALUES (%s, to_char(%s::date, 'YYYYMMDD')::int, %s, %s, 5)",
                (review_key, d, platform_key, source_key),
            )
    return source_key, platform_key


def _by_type_layer(results):
    return {(r["check_type"], r["layer"]): (r["rows_checked"], r["rows_failed"]) for r in results}


def test_each_error_is_logged_with_right_type_and_count(conn):
    _seed_errors(conn)
    results = run_checks(conn, source=SRC, run_id="test-run-1")
    got = _by_type_layer(results)

    assert got[("trung_khoa", "raw")] == (7, 1)
    assert got[("thieu_van_ban", "raw")] == (7, 2)
    assert got[("thieu_van_ban", "clean")] == (4, 1)
    assert got[("sao_ngoai_mien", "raw")] == (7, 1)
    assert got[("sao_ngoai_mien", "dw")] == (4, 0)
    assert got[("ngay_ngoai_mien", "raw")] == (7, 2)
    assert got[("ngay_ngoai_mien", "dw")] == (4, 2)
    assert got[("mo_coi_khoa_ngoai", "dw")] == (4, 0)
    assert got[("trung_noi_dung", "dw")] == (4, 1)

    # kết quả đã nằm trong bảng, đủ 6 loại kiểm tra
    with conn.cursor() as cur:
        cur.execute(
            "SELECT check_type, sum(rows_failed) FROM dw.data_quality_log WHERE run_id = 'test-run-1' GROUP BY check_type"
        )
        logged = dict(cur.fetchall())
        assert _one(cur, "SELECT count(*) FROM dw.data_quality_log WHERE run_id = 'test-run-1' AND source_name = %s", (SRC,)) == len(results)
    assert logged == {
        "trung_khoa": 1, "thieu_van_ban": 3, "sao_ngoai_mien": 1,
        "ngay_ngoai_mien": 4, "mo_coi_khoa_ngoai": 0, "trung_noi_dung": 1,
    }


def test_orphan_foreign_key_is_logged(conn):
    source_key, platform_key = _seed_errors(conn)
    with conn.cursor() as cur:
        try:
            cur.execute("SET LOCAL session_replication_role = replica")  # tắt kiểm tra khóa ngoại trong giao dịch này
        except Exception:
            pytest.skip("Tài khoản CSDL không có quyền tắt kiểm tra khóa ngoại")
        cur.execute(
            "INSERT INTO dw.fact_review (review_key, time_key, platform_key, source_key, rating) "
            "VALUES (-5, 20250102, %s, %s, 4)",
            (platform_key, source_key),
        )
        cur.execute("SET LOCAL session_replication_role = origin")
    got = _by_type_layer(run_checks(conn, source=SRC, run_id="test-run-orphan"))
    assert got[("mo_coi_khoa_ngoai", "dw")] == (5, 1)


def test_rerun_adds_new_batch_and_dry_run_writes_nothing(conn):
    _seed_errors(conn)
    with conn.cursor() as cur:
        before = _one(cur, "SELECT count(*) FROM dw.data_quality_log")
    first = run_checks(conn, source=SRC, run_id="test-run-a")
    second = run_checks(conn, source=SRC, run_id="test-run-b")
    dry = run_checks(conn, source=SRC, run_id="test-run-dry", dry_run=True)
    with conn.cursor() as cur:
        after = _one(cur, "SELECT count(*) FROM dw.data_quality_log")
        dry_rows = _one(cur, "SELECT count(*) FROM dw.data_quality_log WHERE run_id = 'test-run-dry'")
    assert after - before == len(first) + len(second)  # mỗi lần chạy thêm một đợt dòng mới
    assert dry_rows == 0                               # dry-run hoàn tác
    assert _by_type_layer(dry) == _by_type_layer(first)  # nhưng vẫn tính ra cùng kết quả


def test_run_on_real_data_without_error(conn):
    results = run_checks(conn, dry_run=True)
    assert len(results) == 9
    assert all(r["rows_failed"] <= r["rows_checked"] for r in results)

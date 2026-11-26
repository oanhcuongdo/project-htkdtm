"""Kiểm tra chất lượng dữ liệu trên raw, clean, dw và ghi kết quả vào dw.data_quality_log.

Sáu loại kiểm tra: trung_khoa, thieu_van_ban, sao_ngoai_mien, ngay_ngoai_mien, mo_coi_khoa_ngoai, trung_noi_dung.
Mỗi loại ghi một dòng cho mỗi lớp được kiểm (details bắt đầu bằng [raw], [clean] hoặc [dw]).
Mỗi lần chạy ghi một đợt dòng mới (cùng run_id) nên chạy lại được. --dry-run: tính rồi hoàn tác, không ghi.

Cách chạy (từ thư mục nhom03-65httt, mật khẩu lấy từ .env hoặc biến môi trường):
    python src/etl/quality/check_quality.py [--dry-run] [--source TEN_NGUON] [--run-id MA]
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import psycopg

_ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ETL_DIR))

from common import connect  # noqa: E402

MIN_DATE = "2011-01-01"  # trước ngày này là ngoài miền (dữ liệu thật bắt đầu 10/2011)
TODAY_VN = "(now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date"
# %(src)s rỗng = kiểm toàn bộ nguồn; có giá trị = chỉ kiểm nguồn đó.
RAW_SRC = "(%(src)s::text IS NULL OR r.source = %(src)s)"
CLEAN_SRC = "(%(src)s::text IS NULL OR c.source = %(src)s)"
DW_SRC = "(%(src)s::text IS NULL OR s.source_name = %(src)s)"

# fact_review nối nguồn và văn bản (LEFT JOIN để thấy cả dòng mồ côi)
DW_FROM = """
    FROM dw.fact_review f
    JOIN dw.dim_source s ON s.source_key = f.source_key
    JOIN dw.dim_time t ON t.time_key = f.time_key
"""


@dataclass(frozen=True)
class Check:
    check_type: str
    layer: str
    description: str
    total_sql: str   # đếm số dòng được kiểm
    failed_sql: str  # đếm số dòng lỗi


CHECKS: list[Check] = [
    Check(
        "trung_khoa", "raw", "dòng thô trùng khóa (source, review_id); đếm số dòng thừa ngoài dòng đầu",
        f"SELECT count(*) FROM raw.review_raw r WHERE r.source IS NOT NULL AND r.review_id IS NOT NULL AND {RAW_SRC}",
        f"""SELECT coalesce(sum(n - 1), 0) FROM (
                SELECT count(*) AS n FROM raw.review_raw r
                WHERE r.source IS NOT NULL AND r.review_id IS NOT NULL AND {RAW_SRC}
                GROUP BY r.source, r.review_id HAVING count(*) > 1) d""",
    ),
    Check(
        "thieu_van_ban", "raw", "đánh giá thô không có văn bản (rỗng hoặc chỉ khoảng trắng)",
        f"SELECT count(*) FROM raw.review_raw r WHERE {RAW_SRC}",
        f"SELECT count(*) FROM raw.review_raw r WHERE {RAW_SRC} AND (r.text IS NULL OR btrim(r.text) = '')",
    ),
    Check(
        "thieu_van_ban", "clean", "văn bản đã làm sạch bị rỗng",
        f"SELECT count(*) FROM clean.review_text c WHERE {CLEAN_SRC}",
        f"SELECT count(*) FROM clean.review_text c WHERE {CLEAN_SRC} AND (c.text IS NULL OR btrim(c.text) = '')",
    ),
    Check(
        "sao_ngoai_mien", "raw", "số sao thô ngoài 1 đến 5 (rỗng không tính là lỗi)",
        f"SELECT count(*) FROM raw.review_raw r WHERE r.rating IS NOT NULL AND {RAW_SRC}",
        f"SELECT count(*) FROM raw.review_raw r WHERE r.rating IS NOT NULL AND r.rating NOT BETWEEN 1 AND 5 AND {RAW_SRC}",
    ),
    Check(
        "sao_ngoai_mien", "dw", "số sao trong fact_review ngoài 1 đến 5",
        f"SELECT count(*) {DW_FROM} WHERE f.rating IS NOT NULL AND {DW_SRC}",
        f"SELECT count(*) {DW_FROM} WHERE f.rating IS NOT NULL AND f.rating NOT BETWEEN 1 AND 5 AND {DW_SRC}",
    ),
    Check(
        "ngay_ngoai_mien", "raw", f"ngày đăng thô sau hôm nay hoặc trước {MIN_DATE}",
        f"SELECT count(*) FROM raw.review_raw r WHERE r.created_at IS NOT NULL AND {RAW_SRC}",
        f"""SELECT count(*) FROM raw.review_raw r
            WHERE r.created_at IS NOT NULL AND {RAW_SRC}
              AND ((r.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date > {TODAY_VN}
                   OR (r.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date < DATE '{MIN_DATE}')""",
    ),
    Check(
        "ngay_ngoai_mien", "dw", f"ngày của fact_review sau hôm nay hoặc trước {MIN_DATE}",
        f"SELECT count(*) {DW_FROM} WHERE {DW_SRC}",
        f"""SELECT count(*) {DW_FROM}
            WHERE {DW_SRC} AND (t.full_date > {TODAY_VN} OR t.full_date < DATE '{MIN_DATE}')""",
    ),
    Check(
        "mo_coi_khoa_ngoai", "dw", "fact_review trỏ tới clean.review_text không còn",
        f"SELECT count(*) FROM dw.fact_review f JOIN dw.dim_source s ON s.source_key = f.source_key WHERE {DW_SRC}",
        f"""SELECT count(*) FROM dw.fact_review f
            JOIN dw.dim_source s ON s.source_key = f.source_key
            LEFT JOIN clean.review_text c ON c.review_key = f.review_key
            WHERE c.review_key IS NULL AND {DW_SRC}""",
    ),
    Check(
        "trung_noi_dung", "dw", "đánh giá trùng nội dung (cùng text_hash) trong cùng nền tảng; đếm số dòng thừa",
        f"""SELECT count(*) FROM dw.fact_review f
            JOIN dw.dim_source s ON s.source_key = f.source_key
            JOIN clean.review_text c ON c.review_key = f.review_key
            WHERE c.text_hash IS NOT NULL AND {DW_SRC}""",
        f"""SELECT coalesce(sum(n - 1), 0) FROM (
                SELECT count(*) AS n FROM dw.fact_review f
                JOIN dw.dim_source s ON s.source_key = f.source_key
                JOIN clean.review_text c ON c.review_key = f.review_key
                WHERE c.text_hash IS NOT NULL AND {DW_SRC}
                GROUP BY f.platform_key, c.text_hash HAVING count(*) > 1) d""",
    ),
]


def run_checks(
    conn: psycopg.Connection,
    source: str | None = None,
    run_id: str | None = None,
    dry_run: bool = False,
) -> list[dict]:
    """Chạy toàn bộ kiểm tra, ghi vào dw.data_quality_log và trả về kết quả. Hàm không commit.

    dry_run: vẫn tính và ghi trong một giao dịch con rồi hoàn tác giao dịch con đó.
    """
    run_id = run_id or "quality-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    source_name = source or "all"
    params = {"src": source}
    results: list[dict] = []
    with conn.transaction(force_rollback=dry_run):
        with conn.cursor() as cur:
            for check in CHECKS:
                cur.execute(check.total_sql, params)
                checked = int(cur.fetchone()[0])
                cur.execute(check.failed_sql, params)
                failed = int(cur.fetchone()[0])
                details = f"[{check.layer}] {check.description}"
                cur.execute(
                    """
                    INSERT INTO dw.data_quality_log
                        (run_id, source_name, check_type, rows_checked, rows_failed, details)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (run_id, source_name, check.check_type, checked, failed, details),
                )
                results.append({
                    "run_id": run_id, "source_name": source_name, "check_type": check.check_type,
                    "layer": check.layer, "rows_checked": checked, "rows_failed": failed, "details": details,
                })
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kiểm tra chất lượng dữ liệu và ghi dw.data_quality_log")
    parser.add_argument("--dry-run", action="store_true", help="tính và in kết quả rồi hoàn tác, không ghi")
    parser.add_argument("--source", help="chỉ kiểm một nguồn (ví dụ google_play); mặc định kiểm tất cả")
    parser.add_argument("--run-id", help="mã đợt kiểm tra; mặc định quality-<thời điểm UTC>")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # console Windows mặc định không in được tiếng Việt

    with connect() as conn:
        results = run_checks(conn, source=args.source, run_id=args.run_id, dry_run=args.dry_run)
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()

    print(f"run_id={results[0]['run_id']} nguồn={results[0]['source_name']} {'(dry-run, đã hoàn tác)' if args.dry_run else '(đã ghi)'}")
    for r in results:
        print(f"  {r['check_type']:<18} [{r['layer']:<5}] kiểm={r['rows_checked']:>8} lỗi={r['rows_failed']:>8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

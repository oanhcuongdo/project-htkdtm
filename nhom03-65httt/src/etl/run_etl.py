"""ETL: CSV đánh giá -> raw -> clean -> dw; CSV tin báo chí -> clean.news_article.

Ví dụ (chạy từ thư mục gốc nhom03-65httt):
    python src/etl/run_etl.py --input data/raw/reviews.csv
    python src/etl/run_etl.py --input data/raw/reviews.csv --dry-run     # chạy thử rồi hoàn tác
    python src/etl/run_etl.py --steps news                                 # chỉ nạp tin báo chí

Kết nối lấy từ DATABASE_URL, hoặc POSTGRES_* trong môi trường, hoặc tệp .env (không commit).
Chạy lại nhiều lần không sinh dòng trùng. Nhật ký mỗi lần chạy ghi vào data/logs/etl_runs.jsonl (ngoài Git).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ETL_DIR))
sys.path.insert(0, str(ETL_DIR / "load"))

from common import connect, project_root  # noqa: E402
from load_clean import load_clean  # noqa: E402
from load_dw import load_dw  # noqa: E402
from load_news import load_news  # noqa: E402
from load_raw import load_raw  # noqa: E402

STEPS = ("raw", "clean", "dw", "news")


def summarize(conn) -> dict:
    """Số liệu kiểm tra sau khi chạy: theo nguồn, theo nhóm nền tảng, số đánh giá tiếng Việt."""
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM raw.review_raw")
        raw_total = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM clean.review_text")
        clean_total = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM dw.fact_review")
        fact_total = cur.fetchone()[0]
        cur.execute(
            """
            SELECT s.source_name, count(*) FROM dw.fact_review f
            JOIN dw.dim_source s USING (source_key) GROUP BY 1 ORDER BY 1
            """
        )
        by_source = dict(cur.fetchall())
        cur.execute(
            """
            SELECT p.platform_group, count(*) FROM dw.fact_review f
            JOIN dw.dim_platform p USING (platform_key) GROUP BY 1 ORDER BY 1
            """
        )
        by_group = dict(cur.fetchall())
        cur.execute("SELECT count(DISTINCT platform_key) FROM dw.fact_review")
        platforms = cur.fetchone()[0]
        cur.execute("SELECT to_regclass('clean.news_article') IS NOT NULL")
        news_total = None
        if cur.fetchone()[0]:
            cur.execute("SELECT count(*) FROM clean.news_article")
            news_total = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM clean.review_text WHERE lang_guess = 'vi'")
        vietnamese = cur.fetchone()[0]
        cur.execute(
            "SELECT count(DISTINCT text_hash) FROM clean.review_text WHERE lang_guess = 'vi'"
        )
        vietnamese_unique = cur.fetchone()[0]
    return {
        "raw_total": raw_total,
        "clean_total": clean_total,
        "fact_total": fact_total,
        "by_source": by_source,
        "by_platform_group": by_group,
        "platforms_in_fact": platforms,
        "news_articles": news_total,
        "vietnamese_clean": vietnamese,
        "vietnamese_unique_text": vietnamese_unique,
    }


def write_run_log(entry: dict) -> Path:
    log_dir = project_root() / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "etl_runs.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    return log_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ETL đánh giá: CSV -> raw -> clean -> dw")
    parser.add_argument("--input", type=Path, default=project_root() / "data" / "raw" / "reviews.csv",
                        help="Tệp CSV đánh giá thô (mặc định data/raw/reviews.csv)")
    parser.add_argument("--news", type=Path, default=project_root() / "data" / "raw" / "news" / "news.csv",
                        help="Tệp CSV tin báo chí (mặc định data/raw/news/news.csv)")
    parser.add_argument("--steps", default=",".join(STEPS),
                        help="Các bước chạy, cách nhau bằng dấu phẩy (raw, clean, dw, news)")
    parser.add_argument("--env-file", type=Path, default=None, help="Tệp .env chứa POSTGRES_*")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử rồi hoàn tác, không ghi vào CSDL")
    args = parser.parse_args(argv)

    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    unknown = [s for s in steps if s not in STEPS]
    if unknown:
        parser.error(f"Bước không hợp lệ: {', '.join(unknown)} (hợp lệ: {', '.join(STEPS)})")
    if "raw" in steps and not args.input.is_file():
        parser.error(f"Không thấy tệp đầu vào: {args.input}")

    if "news" in steps and not args.news.is_file():
        if args.steps == ",".join(STEPS):
            print(f"Bỏ qua bước news: không thấy {args.news}")
            steps.remove("news")
        else:
            parser.error(f"Không thấy tệp tin báo chí: {args.news}")

    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    entry: dict = {"started_at": started.isoformat(), "input": str(args.input.name), "steps": steps,
                   "dry_run": args.dry_run, "status": "running"}
    try:
        with connect(args.env_file) as conn:
            if "raw" in steps:
                entry["raw"] = load_raw(conn, args.input)
                print("raw  :", entry["raw"])
            if "clean" in steps:
                entry["clean"] = load_clean(conn)
                print("clean:", entry["clean"])
            if "dw" in steps:
                entry["dw"] = load_dw(conn)
                print("dw   :", entry["dw"])
            if "news" in steps:
                entry["news"] = load_news(conn, args.news)
                print("news :", entry["news"])
            entry["summary"] = summarize(conn)
            if args.dry_run:
                conn.rollback()
                entry["status"] = "dry_run"
            else:
                conn.commit()
                entry["status"] = "success"
    except Exception as exc:  # ghi nhật ký rồi báo lỗi rõ ràng, không nuốt lỗi
        entry["status"] = "failed"
        entry["error"] = f"{type(exc).__name__}: {exc}"
        entry["seconds"] = round(time.monotonic() - clock, 2)
        write_run_log(entry)
        print("LỖI:", entry["error"], file=sys.stderr)
        return 1

    entry["seconds"] = round(time.monotonic() - clock, 2)
    log_file = write_run_log(entry)
    print("Tổng hợp:", json.dumps(entry["summary"], ensure_ascii=False))
    print(f"Trạng thái: {entry['status']} ({entry['seconds']} giây). Nhật ký: {log_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

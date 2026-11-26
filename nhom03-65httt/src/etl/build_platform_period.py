"""Tổng hợp dw.fact_platform_period (một nền tảng x một tháng) từ dw.fact_review (T3).

Ví dụ (chạy từ thư mục gốc nhom03-65httt):
    python src/etl/build_platform_period.py                         # cảm xúc tạm tính theo số sao
    python src/etl/build_platform_period.py --dry-run               # tính thử rồi hoàn tác
    python src/etl/build_platform_period.py --sentiment-source model   # dùng nhãn M1 khi đã có dw.fact_review_sentiment

Chạy lại nhiều lần cho cùng kết quả. Nhật ký mỗi lần chạy ghi vào data/logs/etl_runs.jsonl (ngoài Git).
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
from load_platform_period import (  # noqa: E402
    MODEL_TABLE_DEFAULT, SENTIMENT_SOURCES, build_platform_period,
)


def write_log(entry: dict) -> None:
    log_dir = project_root() / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "etl_runs.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tổng hợp fact_platform_period (nền tảng x tháng)")
    parser.add_argument("--sentiment-source", choices=SENTIMENT_SOURCES, default="rating",
                        help="rating: tạm tính theo số sao (mặc định); model: nhãn M1 trong --model-table")
    parser.add_argument("--model-table", default=MODEL_TABLE_DEFAULT,
                        help=f"Bảng nhãn M1 khi dùng model (mặc định {MODEL_TABLE_DEFAULT})")
    parser.add_argument("--env-file", type=Path, default=None, help="Tệp .env chứa POSTGRES_*")
    parser.add_argument("--dry-run", action="store_true", help="Tính thử rồi hoàn tác, không ghi vào CSDL")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # console Windows mặc định không in được tiếng Việt

    entry: dict = {"started_at": datetime.now(timezone.utc).isoformat(), "step": "platform_period",
                   "dry_run": args.dry_run, "status": "running"}
    clock = time.monotonic()
    try:
        with connect(args.env_file) as conn:
            entry["result"] = build_platform_period(conn, args.sentiment_source, args.model_table)
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
        write_log(entry)
        print("LỖI:", entry["error"], file=sys.stderr)
        return 1

    entry["seconds"] = round(time.monotonic() - clock, 2)
    write_log(entry)
    result = entry["result"]
    print("Kết quả:", json.dumps(result, ensure_ascii=False))
    if result["reviews_counted"] != result["fact_review_total"]:
        print(f"CẢNH BÁO: tổng new_review_count ({result['reviews_counted']}) khác số dòng fact_review "
              f"({result['fact_review_total']})", file=sys.stderr)
        return 1
    if args.sentiment_source == "rating":
        print("Lưu ý: cảm xúc đang tạm tính theo số sao (docs/kpi_bhi.md); đổi sang nhãn M1 bằng --sentiment-source model.")
    print(f"Trạng thái: {entry['status']} ({entry['seconds']} giây)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

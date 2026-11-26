"""Chạy trọn một vòng pipeline: thu thập đánh giá mới, nạp ETL, ghi nhật ký (T8a).

Ví dụ (chạy từ thư mục gốc nhom03-65httt):
    python src/etl/run_pipeline.py                      # một vòng đầy đủ cho 9 nền tảng
    python src/etl/run_pipeline.py --only "ELSA Speak" --count 20
    python src/etl/run_pipeline.py --skip-collect       # chỉ nạp các tệp đã thu thập trong thư mục incoming
    python src/etl/run_pipeline.py --report             # xem bằng chứng "tự chạy N ngày liên tiếp"

Mỗi vòng:
  1. Gọi collector Google Play và App Store cho từng nền tảng trong config/platforms.yml
     (giãn cách tối thiểu 2 giây, không đổi IP, không proxy: theo docs/dao_duc_phap_ly.md).
  2. Nạp các CSV vừa thu thập qua raw -> clean -> dw (loại trùng theo (source, review_id), chạy lại không sinh trùng).
  3. Ghi một bản ghi vào data/logs/pipeline_runs.jsonl (ngoài Git).

Một collector lỗi không làm hỏng vòng: các nền tảng khác vẫn chạy, trạng thái vòng là `partial`.
Không sửa mã collector của người khác; chỉ gọi chúng qua dòng lệnh.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ETL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ETL_DIR))
sys.path.insert(0, str(ETL_DIR / "load"))

from common import connect, load_platforms, project_root  # noqa: E402
from load_clean import load_clean  # noqa: E402
from load_dw import load_dw  # noqa: E402
from load_raw import load_raw  # noqa: E402

VN_TZ = timezone(timedelta(hours=7))
COLLECTORS = ("google_play_collector.py", "app_store_collector.py")
LOCK_STALE_SECONDS = 3 * 3600


# ---------------------------------------------------------------- nhật ký và khóa chạy
def log_path() -> Path:
    override = os.environ.get("EDUVISION_LOG_DIR")  # dùng cho kiểm thử, tránh ghi vào nhật ký thật
    path = Path(override) if override else project_root() / "data" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path / "pipeline_runs.jsonl"


def append_log(entry: dict) -> None:
    with log_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


def read_log() -> list[dict]:
    path = log_path()
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def acquire_lock() -> Path | None:
    """Không cho hai vòng chạy chồng nhau. Khóa cũ hơn 3 giờ được coi là treo và bị bỏ qua."""
    lock = log_path().parent / "pipeline.lock"
    if lock.exists() and time.time() - lock.stat().st_mtime < LOCK_STALE_SECONDS:
        return None
    lock.write_text(f"{os.getpid()} {datetime.now(timezone.utc).isoformat()}", encoding="utf-8")
    return lock


# ---------------------------------------------------------------- báo cáo bằng chứng
def consecutive_days(entries: list[dict]) -> tuple[list[str], int]:
    """Các ngày (giờ Việt Nam) có ít nhất một vòng ETL thành công, và số ngày liên tiếp tính đến ngày gần nhất."""
    days = set()
    for entry in entries:
        if entry.get("status") in ("success", "partial") and not entry.get("dry_run"):
            started = datetime.fromisoformat(entry["started_at"]).astimezone(VN_TZ)
            days.add(started.date())
    ordered = sorted(days)
    if not ordered:
        return [], 0
    streak = 1
    for prev, cur in zip(reversed(ordered[:-1]), reversed(ordered[1:])):
        if (cur - prev).days == 1:
            streak += 1
        else:
            break
    return [d.isoformat() for d in ordered], streak


def print_report(min_days: int) -> int:
    entries = read_log()
    days, streak = consecutive_days(entries)
    print(f"Số vòng đã ghi: {len(entries)}")
    for entry in entries[-10:]:
        summary = entry.get("summary", {})
        print(
            f"  {entry['started_at'][:19]}  {entry['status']:<8} thu thập lỗi: "
            f"{summary.get('collectors_failed', '-')}/{summary.get('collectors_total', '-')}  "
            f"dòng mới ở raw: {summary.get('raw_inserted', '-')}"
        )
    print(f"Các ngày có vòng thành công: {', '.join(days) if days else '(chưa có)'}")
    print(f"Số ngày liên tiếp gần nhất: {streak} (yêu cầu tối thiểu {min_days})")
    print("ĐẠT" if streak >= min_days else "CHƯA ĐẠT: ghi số ngày thật vào báo cáo")
    return 0 if streak >= min_days else 3


def count_csv_rows(path: Path) -> int:
    """Số bản ghi (không tính dòng tiêu đề). Dùng bộ đọc CSV vì một đánh giá có thể xuống dòng trong ô văn bản."""
    csv.field_size_limit(10**9)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return max(sum(1 for _ in csv.reader(handle)) - 1, 0)


# ---------------------------------------------------------------- thu thập
def run_collectors(platform_ids: list[str], out_dir: Path, count: int, sleep: float, timeout: int) -> list[dict]:
    results = []
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for platform_id in platform_ids:
        for script in COLLECTORS:
            started = time.monotonic()
            command = [
                sys.executable, str(ETL_DIR / "collectors" / script), "--only", platform_id,
                "--count", str(count), "--out", str(out_dir), "--sleep", str(sleep),
            ]
            item = {"collector": script.replace("_collector.py", ""), "platform": platform_id}
            try:
                done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                      errors="replace", timeout=timeout, env=env)
                item["returncode"] = done.returncode
                if done.returncode != 0:
                    tail = (done.stderr or done.stdout or "").strip().splitlines()
                    item["error"] = tail[-1][:300] if tail else "không rõ lỗi"
            except subprocess.TimeoutExpired:
                item["returncode"] = -1
                item["error"] = f"quá {timeout} giây"
            item["seconds"] = round(time.monotonic() - started, 1)
            results.append(item)
            print(f"  thu thập {item['collector']:<10} {platform_id:<14} "
                  f"{'ok' if item['returncode'] == 0 else 'LỖI: ' + item.get('error', '')}")
            time.sleep(sleep)  # giãn cách giữa các lần gọi nguồn
    return results


# ---------------------------------------------------------------- một vòng
def run_cycle(args: argparse.Namespace) -> int:
    all_ids = [p["id"] for p in load_platforms()]
    platform_ids = args.only or all_ids
    unknown = [p for p in platform_ids if p not in all_ids]
    if unknown:
        print(f"Nền tảng không có trong config/platforms.yml: {', '.join(unknown)}", file=sys.stderr)
        return 2

    lock = acquire_lock()
    if lock is None:
        print("Đang có vòng khác chạy (pipeline.lock còn mới). Bỏ qua vòng này.", file=sys.stderr)
        return 4

    started = datetime.now(timezone.utc)
    clock = time.monotonic()
    entry: dict = {"run_id": uuid.uuid4().hex[:12], "started_at": started.isoformat(),
                   "dry_run": args.dry_run, "platforms": platform_ids, "count": args.count,
                   "status": "running"}
    summary: dict = {}
    try:
        stamp = datetime.now(VN_TZ).strftime("%Y%m%d_%H%M%S")
        out_dir = args.incoming / stamp
        if args.skip_collect:
            # chỉ nạp các tệp có sẵn: lấy mọi CSV trong thư mục incoming
            files = sorted(args.incoming.rglob("*.csv"))
            collector_results: list[dict] = []
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            print(f"Thu thập {len(platform_ids)} nền tảng, mỗi nền tảng tối đa {args.count} đánh giá mỗi kho:")
            collector_results = run_collectors(platform_ids, out_dir, args.count, args.sleep, args.timeout)
            files = sorted(out_dir.glob("*.csv"))
        failed = sum(1 for r in collector_results if r["returncode"] != 0)
        # collector thoát mã 0 nhưng CSV rỗng (ví dụ nguồn cấp RSS của Apple trả 0 mục): báo rõ, không im lặng
        csv_rows = {path.name: count_csv_rows(path) for path in files}
        empty_files = sorted(name for name, n in csv_rows.items() if n == 0)
        summary.update(collectors_total=len(collector_results), collectors_failed=failed,
                       csv_files=len(files), csv_rows=csv_rows, empty_csv=empty_files)
        if empty_files:
            print(f"Cảnh báo: {len(empty_files)} tệp CSV không có dòng nào (nguồn trả rỗng): {', '.join(empty_files)}")
        entry["collectors"] = collector_results

        if not args.skip_collect and collector_results and failed == len(collector_results):
            raise RuntimeError("Mọi collector đều lỗi: không có dữ liệu mới để nạp (kiểm tra mạng hoặc nguồn bị chặn)")

        raw_inserted = raw_read = 0
        with connect(args.env_file) as conn:
            for path in files:
                stats = load_raw(conn, path)
                raw_read += stats["read"]
                raw_inserted += stats["inserted"]
            clean_stats = load_clean(conn)
            dw_stats = load_dw(conn)
            if args.dry_run:
                conn.rollback()
            else:
                conn.commit()
        summary.update(raw_read=raw_read, raw_inserted=raw_inserted, clean_inserted=clean_stats["inserted"],
                       clean_dropped_empty=clean_stats["dropped_empty"], fact_inserted=dw_stats["inserted"],
                       fact_total=dw_stats["fact_total"])
        entry["status"] = "dry_run" if args.dry_run else ("partial" if failed else "success")
        entry["summary"] = summary
        code = 0
    except Exception as exc:  # ghi nhật ký rồi báo lỗi rõ ràng, không nuốt lỗi
        entry["status"] = "failed"
        entry["error"] = f"{type(exc).__name__}: {exc}"
        entry["summary"] = summary
        print("LỖI:", entry["error"], file=sys.stderr)
        code = 1
    finally:
        entry["finished_at"] = datetime.now(timezone.utc).isoformat()
        entry["seconds"] = round(time.monotonic() - clock, 1)
        append_log(entry)
        lock.unlink(missing_ok=True)

    print(f"Trạng thái: {entry['status']} ({entry['seconds']} giây). Tóm tắt: "
          f"{json.dumps(summary, ensure_ascii=False)}")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Một vòng pipeline: thu thập, ETL, ghi nhật ký")
    parser.add_argument("--only", action="append", metavar="ID",
                        help="Chỉ chạy nền tảng này (lặp lại được); mặc định tất cả nền tảng trong platforms.yml")
    parser.add_argument("--count", type=int, default=100, help="Số đánh giá mỗi nền tảng mỗi kho (mặc định 100)")
    parser.add_argument("--sleep", type=float, default=2.0, help="Giây nghỉ giữa các lần gọi nguồn (tối thiểu 2)")
    parser.add_argument("--timeout", type=int, default=900, help="Giây tối đa cho mỗi lần gọi collector")
    parser.add_argument("--incoming", type=Path, default=project_root() / "data" / "raw" / "incoming",
                        help="Thư mục chứa CSV thu thập theo từng vòng (ngoài Git)")
    parser.add_argument("--skip-collect", action="store_true", help="Không thu thập, chỉ nạp CSV có sẵn trong incoming")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử, hoàn tác ETL, vòng không tính vào bằng chứng")
    parser.add_argument("--env-file", type=Path, default=None, help="Tệp .env chứa POSTGRES_*")
    parser.add_argument("--report", action="store_true", help="In bằng chứng tự chạy liên tiếp rồi thoát")
    parser.add_argument("--min-days", type=int, default=3, help="Số ngày liên tiếp tối thiểu khi --report (mặc định 3)")
    args = parser.parse_args(argv)

    if args.sleep < 2:
        parser.error("--sleep phải từ 2 giây trở lên (docs/dao_duc_phap_ly.md)")
    if args.count < 1:
        parser.error("--count phải lớn hơn 0")
    if args.report:
        return print_report(args.min_days)
    return run_cycle(args)


if __name__ == "__main__":
    raise SystemExit(main())

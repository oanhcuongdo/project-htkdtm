"""Kiểm thử bộ lập lịch pipeline (T8a): bằng chứng nhiều ngày, bí danh nguồn, một vòng nạp CSV có sẵn."""

import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ETL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ETL_DIR))
sys.path.insert(0, str(ETL_DIR / "load"))

import run_pipeline  # noqa: E402
from common import canonical_source, connect  # noqa: E402

VN = timezone(timedelta(hours=7))


def _entry(day: str, status="success", dry_run=False, hour=2):
    moment = datetime.fromisoformat(f"{day}T{hour:02d}:00:00").replace(tzinfo=VN)
    return {"started_at": moment.astimezone(timezone.utc).isoformat(), "status": status, "dry_run": dry_run}


def test_canonical_source_merges_app_store_alias() -> None:
    assert canonical_source("app_store") == "app_store_vn"
    assert canonical_source(" app_store ") == "app_store_vn"
    assert canonical_source("google_play") == "google_play"
    assert canonical_source(None) is None


def test_consecutive_days_counts_streak_ending_at_latest_day() -> None:
    entries = [_entry("2026-11-25"), _entry("2026-11-26"), _entry("2026-11-27"), _entry("2026-11-27", hour=14)]
    days, streak = run_pipeline.consecutive_days(entries)
    assert days == ["2026-11-25", "2026-11-26", "2026-11-27"]
    assert streak == 3


def test_consecutive_days_breaks_on_gap_and_ignores_failed_and_dry_run() -> None:
    entries = [
        _entry("2026-11-24"),
        _entry("2026-11-26"),                       # thiếu ngày 25: chuỗi bị ngắt
        _entry("2026-11-27", status="failed"),      # vòng lỗi không tính
        _entry("2026-11-28", dry_run=True, status="dry_run"),
    ]
    days, streak = run_pipeline.consecutive_days(entries)
    assert days == ["2026-11-24", "2026-11-26"]
    assert streak == 1


def test_consecutive_days_counts_partial_runs_and_uses_vietnam_date() -> None:
    # 01:30 ngày 26 giờ Việt Nam là 18:30 ngày 25 theo UTC; phải tính vào ngày 26
    entries = [_entry("2026-11-25"), _entry("2026-11-26", status="partial", hour=1)]
    days, streak = run_pipeline.consecutive_days(entries)
    assert days == ["2026-11-25", "2026-11-26"] and streak == 2


def test_consecutive_days_empty() -> None:
    assert run_pipeline.consecutive_days([]) == ([], 0)


def test_report_exit_code_depends_on_min_days(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("EDUVISION_LOG_DIR", str(tmp_path))
    log = tmp_path / "pipeline_runs.jsonl"
    log.write_text("\n".join(json.dumps(_entry(d)) for d in ("2026-11-25", "2026-11-26")) + "\n", encoding="utf-8")
    assert run_pipeline.main(["--report", "--min-days", "2"]) == 0
    assert run_pipeline.main(["--report", "--min-days", "3"]) == 3
    assert "CHƯA ĐẠT" in capsys.readouterr().out


def test_sleep_below_two_seconds_is_rejected() -> None:
    with pytest.raises(SystemExit):
        run_pipeline.main(["--sleep", "1"])


def test_unknown_platform_is_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EDUVISION_LOG_DIR", str(tmp_path))
    assert run_pipeline.main(["--only", "KhongTonTai", "--skip-collect", "--dry-run"]) == 2


def test_cycle_with_existing_csv_dry_run_logs_and_does_not_persist(tmp_path, monkeypatch) -> None:
    try:
        connect(connect_timeout=3).close()
    except Exception as exc:
        pytest.skip(f"Không kết nối được PostgreSQL cục bộ: {type(exc).__name__}")
    monkeypatch.setenv("EDUVISION_LOG_DIR", str(tmp_path / "logs"))
    incoming = tmp_path / "incoming"
    incoming.mkdir()
    columns = ["source", "product", "review_id", "author_hash", "rating", "text", "lang_guess", "created_at",
               "app_version", "thumbs_up", "reply_text", "crawled_at"]
    with (incoming / "app_store_sample.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow({
            "source": "app_store", "product": "ELSA Speak", "review_id": "pipeline-test-1", "author_hash": "aaa",
            "rating": "5", "text": "Rất tốt", "lang_guess": "vi", "created_at": "2026-11-20T03:00:00+00:00",
            "app_version": "1", "thumbs_up": "0", "reply_text": "", "crawled_at": "2026-11-21T00:00:00+00:00",
        })

    code = run_pipeline.main(["--skip-collect", "--dry-run", "--incoming", str(incoming)])
    assert code == 0

    entries = [json.loads(line) for line in (tmp_path / "logs" / "pipeline_runs.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(entries) == 1
    assert entries[0]["status"] == "dry_run" and entries[0]["dry_run"] is True
    assert entries[0]["summary"]["raw_inserted"] == 1
    assert not (tmp_path / "logs" / "pipeline.lock").exists()   # khóa đã được gỡ

    # dry-run đã hoàn tác: dòng thử không nằm lại trong CSDL
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM raw.review_raw WHERE review_id = 'pipeline-test-1'")
        assert cur.fetchone()[0] == 0


def test_second_cycle_is_skipped_while_lock_is_fresh(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EDUVISION_LOG_DIR", str(tmp_path))
    (tmp_path / "pipeline.lock").write_text("12345", encoding="utf-8")
    assert run_pipeline.main(["--skip-collect", "--dry-run", "--incoming", str(tmp_path)]) == 4


def test_count_csv_rows_ignores_newlines_inside_quoted_text(tmp_path) -> None:
    path = tmp_path / "multi.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["review_id", "text"])
        writer.writerow(["a", "dòng một\ndòng hai\ndòng ba"])   # một đánh giá chiếm 3 dòng văn bản
        writer.writerow(["b", "một dòng"])
    assert run_pipeline.count_csv_rows(path) == 2
    header_only = tmp_path / "empty.csv"
    header_only.write_text("review_id,text\n", encoding="utf-8")
    assert run_pipeline.count_csv_rows(header_only) == 0

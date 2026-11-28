import csv
from datetime import datetime, timezone
from pathlib import Path

from .storage import sha256_file, utc_now, write_json_atomic, write_jsonl_new


def _source_name(url):
    if not url:
        return None
    from urllib.parse import urlsplit

    host = (urlsplit(url).hostname or "").casefold()
    return "udemy" if host == "udemy.com" or host.endswith(".udemy.com") else None


def ingest_legacy_csv(source_csv: Path, raw_root: Path) -> tuple[str, Path]:
    if not source_csv.exists():
        raise FileNotFoundError(f"Không tìm thấy CSV nguồn cũ: {source_csv}")
    started_at = utc_now()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch_id = f"legacy-{stamp}-{sha256_file(source_csv)[:8]}"
    batch_dir = raw_root / batch_id
    temporary_dir = raw_root / f".{batch_id}.tmp"
    temporary_dir.mkdir(parents=True, exist_ok=False)
    records_path = temporary_dir / "records.jsonl"
    total = 0
    failed = 0
    with source_csv.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"CSV không có dòng tiêu đề cột: {source_csv}")
        records = []
        for row_number, row in enumerate(reader, 1):
            total += 1
            if None in row:
                failed += 1
            source_url = row.get("url") or ""
            records.append({
                "record_number": row_number,
                "source_name": _source_name(source_url),
                "source_url": source_url or None,
                "crawled_at": row.get("scraped_at") or None,
                "http_status": None,
                "raw_payload": row,
                "ingestion_kind": "legacy_parsed_csv",
            })
    write_jsonl_new(records_path, records)
    manifest = {
        "batch_id": batch_id,
        "source_name": "udemy",
        "started_at": started_at,
        "finished_at": utc_now(),
        "total_pages": None,
        "total_records": total,
        "successful_records": total - failed,
        "failed_records": failed,
        "parser_errors": failed,
        "network_errors": 0,
        "status": "SUCCESS" if failed == 0 else "PARTIAL",
        "ingestion_kind": "legacy_parsed_csv_not_original_source_payload",
        "input_file": str(source_csv),
        "input_sha256": sha256_file(source_csv),
        "raw_html_or_source_json_retained": False,
    }
    write_json_atomic(temporary_dir / "manifest.json", manifest)
    temporary_dir.rename(batch_dir)
    return batch_id, batch_dir

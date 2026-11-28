import csv
from pathlib import Path

from .storage import read_jsonl, utc_now, write_json_atomic, write_jsonl_new
from .normalize import COURSE_FIELDS


REQUIRED = ("course_id", "source_name", "source_course_id", "title", "canonical_url", "offer_type", "quality_status")


def validate_approved(record: dict):
    missing = [field for field in REQUIRED if not record.get(field)]
    if missing:
        return False, f"Thiếu các trường bắt buộc: {', '.join(missing)}"
    if record["quality_status"] != "approved_candidate":
        return False, "Bản ghi chưa phải là ứng viên được duyệt"
    if not record.get("description") or not record.get("skills") or not record.get("level"):
        return False, "Thiếu description, skills hoặc level bắt buộc"
    if record.get("quality_flags"):
        return False, "Vẫn còn cờ chất lượng chưa được xử lý"
    if record.get("duplicate_status") != "unique":
        return False, "Trạng thái trùng lặp không phải unique"
    if record["offer_type"] not in {"EXTERNAL_REFERENCE", "INTERNAL"}:
        return False, "offer_type không hợp lệ"
    return True, ""


def create_release(approved_root: Path, releases_root: Path, version: str, batch_id: str | None = None, reviewer: str | None = None):
    destination = releases_root / version
    if destination.exists():
        raise FileExistsError(f"Bản phát hành dataset đã tồn tại: {destination}")
    batches = [approved_root / batch_id] if batch_id else sorted(path for path in approved_root.iterdir() if path.is_dir()) if approved_root.exists() else []
    records = []
    for batch in batches:
        file = batch / "courses.jsonl"
        if file.exists():
            records.extend(read_jsonl(file))
    seen = set()
    for record in records:
        valid, reason = validate_approved(record)
        if not valid:
            raise ValueError(f"Từ chối bản ghi chưa được duyệt {record.get('course_id')}: {reason}")
        key = (record["source_name"], record["source_course_id"], record["canonical_url"])
        if key in seen:
            raise ValueError(f"Mã định danh bị trùng trong bản phát hành: {key}")
        seen.add(key)

    destination.mkdir(parents=True)
    jsonl_path = destination / "courses.jsonl"
    csv_path = destination / "courses.csv"
    write_jsonl_new(jsonl_path, records)
    columns = list(records[0]) if records else list(COURSE_FIELDS)
    with csv_path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: _csv_value(value) for key, value in record.items()})
    metadata = {
        "dataset_version": version,
        "created_at": utc_now(),
        "total_records": len(records),
        "approved_records": len(records),
        "source_statistics": _counts(records, "source_name"),
        "quality_statistics": _counts(records, "quality_status"),
        "schema_version": "1.0",
        "pipeline_version": "0.1.0",
        "reviewer": reviewer,
        "collection_limitations": [
            "Chỉ đưa các bản ghi ứng viên đã được duyệt vào bản phát hành.",
            "Không crawl thêm Udemy khi chưa có văn bản cho phép.",
            "CSV nguồn cũ thiếu description và skills; bản ghi thiếu trường bắt buộc không được đưa vào bản phát hành.",
        ],
        "release_status": "EMPTY" if not records else "RELEASED",
    }
    write_json_atomic(destination / "metadata.json", metadata)
    return metadata


def _csv_value(value):
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        import json

        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return value


def _counts(records, key):
    counts = {}
    for record in records:
        value = record.get(key) or "unknown"
        counts[value] = counts.get(value, 0) + 1
    return counts

from pathlib import Path

from .release import REQUIRED, validate_approved
from .storage import read_jsonl


def load_release(release_dir: Path, database_config: dict, dry_run: bool = True) -> dict:
    source = release_dir / "courses.jsonl"
    if not source.exists():
        raise FileNotFoundError(f"Không tìm thấy dữ liệu bản phát hành: {source}")
    records = list(read_jsonl(source))
    invalid = []
    identities = set()
    for index, record in enumerate(records, 1):
        valid, reason = validate_approved(record)
        if not valid:
            invalid.append({"row": index, "course_id": record.get("course_id"), "reason": reason})
        if any(field not in record for field in REQUIRED):
            invalid.append({"row": index, "course_id": record.get("course_id"), "reason": "schema field missing"})
        identity = record.get("course_id")
        if identity in identities:
            invalid.append({"row": index, "course_id": identity, "reason": "duplicate course_id"})
        identities.add(identity)
    if invalid:
        raise ValueError(f"Bản phát hành không đạt kiểm tra schema: {invalid[:5]}")
    adapter = database_config.get("adapter")
    if dry_run:
        return {"status": "DRY_RUN", "records_validated": len(records), "records_written": 0, "adapter": adapter, "configured": bool(adapter)}
    if not adapter:
        raise ValueError("Chưa cấu hình adapter cơ sở dữ liệu; không tự giả định endpoint hoặc schema.")
    raise NotImplementedError(f"Adapter cơ sở dữ liệu '{adapter}' chưa được triển khai vì chưa có schema/thông tin xác thực.")

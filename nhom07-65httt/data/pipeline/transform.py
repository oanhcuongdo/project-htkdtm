import json
from collections import Counter
from pathlib import Path

from .deduplicate import deduplicate
from .normalize import normalize_course
from .quality_check import check_quality
from .skill_mapping import load_taxonomy, map_skills
from .storage import read_jsonl, utc_now, write_json_atomic, write_jsonl_new


def transform_batch(batch_dir: Path, staging_root: Path, approved_root: Path, reports_root: Path, taxonomy_path: Path | None = None):
    batch_id = batch_dir.name
    raw_file = batch_dir / "records.jsonl"
    staging_dir = staging_root / batch_id
    approved_dir = approved_root / batch_id
    if staging_dir.exists() or approved_dir.exists():
        raise FileExistsError(f"Lô staging/approved đã tồn tại: {batch_id}")
    taxonomy = load_taxonomy(taxonomy_path)
    records = []
    for raw in read_jsonl(raw_file):
        record = normalize_course(raw)
        record = map_skills(record, taxonomy)
        records.append(record)
    records, near_pairs = deduplicate(records)
    records = [check_quality(record) for record in records]
    approved = [record for record in records if record["quality_status"] == "approved_candidate"]
    staging_dir.mkdir(parents=True)
    approved_dir.mkdir(parents=True)
    write_jsonl_new(staging_dir / "courses.jsonl", records)
    write_jsonl_new(approved_dir / "courses.jsonl", approved)
    statuses = Counter(record["quality_status"] for record in records)
    duplicates = Counter(record["duplicate_status"] for record in records)
    flag_counts = Counter(flag for record in records for flag in record["quality_flags"])
    source_coverage = Counter()
    for record in records:
        for key in ("title", "description", "skills", "level", "price_amount", "duration_minutes"):
            source_coverage[key] += record.get(key) is not None
    summary = {
        "batch_id": batch_id,
        "generated_at": utc_now(),
        "records_in": len(records),
        "records_staged": len(records),
        "approved_candidates": len(approved),
        "quality_status_counts": dict(statuses),
        "duplicate_status_counts": dict(duplicates),
        "quality_flag_counts": dict(flag_counts),
        "near_duplicate_pair_count": len(near_pairs),
        "field_non_null_counts": dict(source_coverage),
        "taxonomy_loaded": taxonomy is not None,
        "external_source_accuracy": None,
        "note": "Chưa xác minh trực tiếp với nguồn; xem sources.md.",
    }
    write_json_atomic(staging_dir / "manifest.json", summary)
    write_json_atomic(approved_dir / "manifest.json", {**summary, "approved_candidates": len(approved)})
    reports_root.mkdir(parents=True, exist_ok=True)
    report_path = reports_root / f"dq_{batch_id}.md"
    lines = [
        f"# Báo cáo chất lượng dữ liệu: {batch_id}",
        "",
        f"Thời điểm tạo: {summary['generated_at']}",
        "",
        f"- Bản ghi đưa vào bước rà soát: {len(records)}",
        f"- Ứng viên được duyệt: {len(approved)}",
        f"- Bản ghi trùng hoàn toàn: {duplicates.get('exact_duplicate', 0)}",
        f"- Bản ghi gần trùng: {duplicates.get('near_duplicate', 0)}",
        f"- Cặp gần trùng: {len(near_pairs)}",
        "- Độ chính xác so với nguồn: chưa đo; kiểm tra tự động bị tắt khi chưa có cho phép.",
        "",
        "## Trạng thái chất lượng",
        "",
        "| Trạng thái | Số bản ghi |",
        "|---|---:|",
    ]
    lines.extend(f"| {status} | {count} |" for status, count in sorted(statuses.items()))
    lines.extend(["", "## Cờ chất lượng", "", "| Cờ | Số bản ghi |", "|---|---:|"])
    lines.extend(f"| {flag} | {count} |" for flag, count in sorted(flag_counts.items()))
    lines.extend(["", "## Mức độ đầy đủ của trường", "", "| Trường | Có dữ liệu | Tổng số | Tỷ lệ đầy đủ |", "|---|---:|---:|---:|"])
    for field, count in source_coverage.items():
        percentage = count / len(records) * 100 if records else 0
        lines.append(f"| {field} | {count} | {len(records)} | {percentage:.2f}% |")
    lines.extend(["", "Dataset chưa được xác minh với nguồn bên ngoài. Giá trị thiếu vẫn là null; không tự tạo giá, cấp độ, thời lượng, mô tả hoặc kỹ năng.", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    (reports_root / f"near_duplicates_{batch_id}.json").write_text(json.dumps(near_pairs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary

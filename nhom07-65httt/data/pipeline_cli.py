import argparse
import json
from pathlib import Path

from pipeline.baseline import analyze_csv, write_baseline_report
from pipeline.config import load_settings, resolve_path
from pipeline.console import configure_utf8_console
from pipeline.database_loader import load_release
from pipeline.raw_ingest import ingest_legacy_csv
from pipeline.release import create_release
from pipeline.transform import transform_batch


def _latest_batch(root: Path) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục lô dữ liệu: {root}")
    batches = sorted(path for path in root.iterdir() if path.is_dir())
    if not batches:
        raise FileNotFoundError(f"Không có lô dữ liệu nào trong {root}")
    return batches[-1]


def main(argv=None):
    configure_utf8_console()
    parser = argparse.ArgumentParser(description="Pipeline xử lý dữ liệu khóa học SmartEdu chạy ngoại tuyến")
    parser.add_argument("--config", default="data/config.yaml")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit", help="Kiểm toán CSV hiện có, không truy cập mạng")
    subparsers.add_parser("ingest", help="Tạo lô dữ liệu gốc bất biến từ CSV hiện tại")
    transform = subparsers.add_parser("transform", help="Chuẩn hóa, ánh xạ kỹ năng, phát hiện trùng lặp và kiểm tra chất lượng")
    transform.add_argument("--batch-id")
    release = subparsers.add_parser("release", help="Tạo bản phát hành phiên bản từ các bản ghi đã duyệt")
    release.add_argument("--batch-id")
    release.add_argument("--version")
    db_load = subparsers.add_parser("db-load", help="Kiểm tra bản phát hành; mặc định chạy mô phỏng")
    db_load.add_argument("--version", required=True)
    db_load.add_argument("--write", action="store_true", help="Thử dùng adapter đã cấu hình (hiện chưa khả dụng nếu thiếu schema/thông tin xác thực)")
    args = parser.parse_args(argv)

    settings, root = load_settings(args.config)
    paths = settings.get("paths", {})
    legacy_csv = resolve_path(root, settings.get("sources", {}).get("legacy_csv"), "data/udemy_courses.csv")
    raw_root = resolve_path(root, paths.get("raw"), "data/raw")
    staging_root = resolve_path(root, paths.get("staging"), "data/staging")
    approved_root = resolve_path(root, paths.get("approved"), "data/approved")
    releases_root = resolve_path(root, paths.get("releases"), "data/releases")
    reports_root = resolve_path(root, paths.get("reports"), "data/reports")
    taxonomy_path = resolve_path(root, paths.get("taxonomy"))

    if args.command == "audit":
        stats = analyze_csv(legacy_csv)
        output = reports_root / "baseline_report.md"
        write_baseline_report(stats, output)
        print(json.dumps({"report": str(output), **{key: stats[key] for key in ("rows", "duplicate_urls", "duplicate_ids", "invalid_shapes")}}, indent=2))
    elif args.command == "ingest":
        batch_id, batch_dir = ingest_legacy_csv(legacy_csv, raw_root)
        print(json.dumps({"batch_id": batch_id, "raw_dir": str(batch_dir), "source_file_preserved": True}, indent=2))
    elif args.command == "transform":
        batch = raw_root / args.batch_id if args.batch_id else _latest_batch(raw_root)
        summary = transform_batch(batch, staging_root, approved_root, reports_root, taxonomy_path)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    elif args.command == "release":
        version = args.version or settings.get("project", {}).get("dataset_version", "0.1.0")
        metadata = create_release(approved_root, releases_root, version, args.batch_id, settings.get("project", {}).get("reviewer"))
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
    elif args.command == "db-load":
        release_dir = releases_root / args.version
        database = dict(settings.get("database", {}))
        result = load_release(release_dir, database, dry_run=not args.write)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

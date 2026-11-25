"""
Đóng gói Superset Dashboard-as-Code Bundle (.zip)
Phụ trách: Nguyễn Quang Đức (Data Warehouse & BI)

Tạo tệp training_analytics_dashboards.zip chuẩn Superset Export v1.0.0
để import trực tiếp qua CLI (`superset import-dashboards`) hoặc UI Superset.
"""

import os
import zipfile

BI_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BI_DIR, "superset_dashboards")
OUTPUT_ZIP = os.path.join(ASSETS_DIR, "training_analytics_dashboards.zip")


def build_bundle():
    if not os.path.exists(ASSETS_DIR):
        raise FileNotFoundError(f"Không tìm thấy thư mục assets: {ASSETS_DIR}")

    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(ASSETS_DIR):
            for fname in sorted(files):
                if not fname.endswith(".yaml"):
                    continue
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, ASSETS_DIR)
                arc_name = os.path.join("training_analytics_dashboards", rel_path).replace("\\", "/")
                zf.write(full_path, arc_name)
                file_count += 1

    print(f"[OK] Đã đóng gói {file_count} tệp YAML vào: {OUTPUT_ZIP}")
    return OUTPUT_ZIP


if __name__ == "__main__":
    build_bundle()

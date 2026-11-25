"""Tiện ích dùng chung cho ETL: kết nối PostgreSQL, đọc cấu hình nền tảng.

Mật khẩu và thông tin kết nối lấy từ biến môi trường hoặc tệp .env cục bộ (đã bị .gitignore chặn),
không viết cứng trong mã.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
import yaml

# Nguồn dữ liệu nào thuộc loại nào trong dw.dim_source (source_type phải thuộc: kho_ung_dung, youtube, bao_chi, khac).
SOURCE_TYPES = {
    "google_play": "kho_ung_dung",
    "app_store_vn": "kho_ung_dung",
    "app_store": "kho_ung_dung",
    "youtube": "youtube",
    "news": "bao_chi",
    "google_news": "bao_chi",
}


def project_root() -> Path:
    """Thư mục nhom03-65httt (chứa config/platforms.yml)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "config" / "platforms.yml").is_file():
            return parent
    raise FileNotFoundError("Không tìm thấy config/platforms.yml khi đi ngược lên từ src/etl")


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_dsn(env_file: Path | None = None) -> str:
    """Ưu tiên DATABASE_URL, sau đó POSTGRES_* trong môi trường, cuối cùng tệp .env ở gốc nhóm."""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    file_values = read_env_file(env_file or (project_root() / ".env"))

    def pick(name: str, default: str = "") -> str:
        return os.environ.get(name) or file_values.get(name) or default

    user = pick("POSTGRES_USER", "eduvision")
    password = pick("POSTGRES_PASSWORD")
    db = pick("POSTGRES_DB", "eduvision")
    host = pick("POSTGRES_HOST", "127.0.0.1")
    port = pick("POSTGRES_PORT", "5432")
    if not password:
        raise RuntimeError(
            "Thiếu mật khẩu CSDL: đặt DATABASE_URL hoặc POSTGRES_PASSWORD (xem .env.example), không viết vào mã."
        )
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def connect(env_file: Path | None = None, connect_timeout: int = 10) -> psycopg.Connection:
    return psycopg.connect(get_dsn(env_file), connect_timeout=connect_timeout)


def load_platforms(path: Path | None = None) -> list[dict]:
    """Đọc danh sách nền tảng chính từ config/platforms.yml (id, platform_group, play_id, ios_id)."""
    config_path = path or (project_root() / "config" / "platforms.yml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return list(data.get("platforms", []))

"""Cấu hình ứng dụng, đọc từ biến môi trường (hoặc tệp .env khi chạy cục bộ không dùng Docker)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    # Ví dụ: postgresql://user:matkhau@localhost:5432/eduvision. Để trống nếu chưa kết nối CSDL.
    database_url: str = ""
    # Đường dẫn tới config/platforms.yml; để trống thì tự tìm ngược lên từ thư mục mã nguồn.
    platforms_file: str = ""
    # Các nguồn được phép gọi API (website), cách nhau bằng dấu phẩy.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def resolve_platforms_file(self) -> Path | None:
        """Trả về đường dẫn tới platforms.yml, hoặc None nếu không tìm thấy."""
        if self.platforms_file:
            path = Path(self.platforms_file)
            return path if path.is_file() else None
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "config" / "platforms.yml"
            if candidate.is_file():
                return candidate
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()

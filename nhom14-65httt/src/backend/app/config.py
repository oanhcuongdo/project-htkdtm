"""Cấu hình ứng dụng – đọc từ biến môi trường (.env)."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "viviet"
    POSTGRES_USER: str = "viviet"
    POSTGRES_PASSWORD: str = "changeme"
    DATABASE_URL: str = ""
    DATA_DIR: Path = Path(__file__).resolve().parents[2] / "database"

    # Auth
    SECRET_KEY: str = "changeme-generate-a-random-secret-key"
    ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0, le=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0, le=30)

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # Google Maps
    GOOGLE_MAPS_API_KEY: str = ""

    # AI
    RECOMMENDATION_ALGORITHM_VERSION: str = "content_v1"

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return URL.create(
            "postgresql+psycopg2",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)


settings = Settings()

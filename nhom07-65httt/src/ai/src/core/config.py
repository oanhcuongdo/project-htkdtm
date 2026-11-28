"""Settings for AI service."""

from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[3] / ".env", extra="ignore")

    DEBUG: bool = False

    INTERNAL_API_KEY: str = ""

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_URL: str | None = None
    QDRANT_API_KEY: str | None = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = ""
    AI_CHAT_RATE_LIMIT_PER_MINUTE: int = 20

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        weak_values = {
            "", "secret", "changeme", "your_internal_api_key", "your_internal_key",
            "change_me", "change_me_api_key",
        }
        if not self.DEBUG and (
            not self.INTERNAL_API_KEY
            or self.INTERNAL_API_KEY.lower() in weak_values
            or len(self.INTERNAL_API_KEY) < 16
        ):
            raise ValueError("INTERNAL_API_KEY must be a secure, non-default string (min 16 chars) in production")
        return self


settings = Settings()

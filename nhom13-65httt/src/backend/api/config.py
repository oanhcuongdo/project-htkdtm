import os
from pathlib import Path


def _load_env_file():
    """Tự động đọc file .env bằng thư viện chuẩn Python."""
    current_dir = Path(__file__).resolve().parent
    env_path = current_dir.parent.parent.parent / ".env"

    if env_path.is_file():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        os.environ.setdefault(key, val)
        except Exception:
            pass


_load_env_file()


class Settings:
    PROJECT_NAME: str = "Personal Finance Intelligence API"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "htkdtm-nhom13-super-secret-jwt-key-2026!")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 ngày

    # Google Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

    # Cấu hình CSDL PostgreSQL Data Warehouse
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "finance_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "SecurePassword123!")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres_db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "personal_finance_dw")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

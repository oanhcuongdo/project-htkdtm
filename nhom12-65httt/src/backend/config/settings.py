import os
from pathlib import Path
from dotenv import load_dotenv

# Tìm và nạp file .env từ thư mục gốc dự án
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "Hệ Thống Tìm Kiếm Nhà Thuê Thông Minh - Nhóm 12"
    
    # Cấu hình Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://ttcydkbefqiqacygjohj.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR0Y3lka2JlZnFpcWFjeWdqb2hqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTUxNzEwMTUsImV4cCI6MjExMDc0NzAxNX0.IVNgnK_o6hH1UGxNI1XlI8YT6oLgEYLgg4FsXl3dN50")
    
    # Cấu hình AI Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    # Cấu hình Scheduler & Scraper
    SCHEDULER_INTERVAL_HOURS: int = int(os.getenv("SCHEDULER_INTERVAL_HOURS", "12"))
    SCRAPER_REQUEST_TIMEOUT: int = int(os.getenv("SCRAPER_REQUEST_TIMEOUT", "15"))
    SCRAPER_DELAY_SECONDS: float = float(os.getenv("SCRAPER_DELAY_SECONDS", "1.5"))
    DEFAULT_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

settings = Settings()

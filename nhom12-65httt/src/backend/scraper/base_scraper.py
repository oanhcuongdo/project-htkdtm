import abc
import time
import logging
from typing import List, Dict, Any, Optional
import requests
from src.backend.config.settings import settings

logger = logging.getLogger(__name__)

class BaseScraper(abc.ABC):
    """Lớp cơ sở cho các công cụ cào dữ liệu phòng trọ."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.timeout = settings.SCRAPER_REQUEST_TIMEOUT
        self.delay = settings.SCRAPER_DELAY_SECONDS

    def sleep_rate_limit(self):
        """Tạm dừng giữa các request để tuân thủ rate limit và tránh bị chặn IP."""
        if self.delay > 0:
            time.sleep(self.delay)

    @abc.abstractmethod
    def fetch_listings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Thu thập danh sách tin đăng thô từ nguồn."""
        pass

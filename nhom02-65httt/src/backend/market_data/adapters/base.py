from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import random
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd

class CompetitorSourceAdapter(ABC):
    """Adapter contract: fetch returns rows using the shared market-data schema."""
    marketplace: str = "UNKNOWN"

    def __init__(self, timeout: int = 12, min_delay: float = 2.0, max_delay: float = 4.0):
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.session = requests.Session()
        retry = Retry(total=3, connect=3, read=2, status=3,
                      backoff_factor=1.0, status_forcelist=(429, 500, 502, 503, 504),
                      allowed_methods=frozenset(["GET", "HEAD"]))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.headers.update({"User-Agent": "SmartPricingAcademicCrawler/1.0 (+course project)"})

    def polite_wait(self):
        if self.max_delay > 0:
            time.sleep(random.uniform(self.min_delay, self.max_delay))

    def request(self, url: str, **kwargs) -> requests.Response:
        self.polite_wait()
        response = self.session.get(url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response

    @staticmethod
    def record(**kwargs) -> dict:
        kwargs.setdefault("observed_at", datetime.now(timezone.utc).isoformat())
        kwargs.setdefault("confidence", 0.7)
        return kwargs

    @abstractmethod
    def fetch(self, **kwargs) -> pd.DataFrame:
        raise NotImplementedError

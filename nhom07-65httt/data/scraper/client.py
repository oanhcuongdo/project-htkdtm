import logging
import time
import gzip
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .robots import RobotsGuard


class UdemyClient:
    def __init__(self, config):
        self.config = config
        self.robots = RobotsGuard(config.start_url, config.user_agent, config.respect_robots_txt)
        self._last_request = 0.0

    def _wait(self):
        wait = self.config.request_delay - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)

    def get(self, url: str) -> str:
        if not self.robots.allowed(url):
            raise PermissionError(f"robots.txt không cho phép truy cập URL này: {url}")
        error = None
        for attempt in range(1, self.config.retries + 1):
            try:
                self._wait()
                request = Request(
                    url,
                    headers={
                        "User-Agent": self.config.user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                )
                with urlopen(request, timeout=self.config.timeout) as response:
                    body = response.read()
                    encoding = response.headers.get_content_charset() or "utf-8"
                if urlsplit(url).path.casefold().endswith(".gz"):
                    body = gzip.decompress(body)
                self._last_request = time.monotonic()
                return body.decode(encoding, errors="replace")
            except Exception as exc:
                error = exc
                logging.warning("Lần gửi request %s/%s thất bại: %s", attempt, self.config.retries, exc)
                if attempt < self.config.retries:
                    time.sleep(min(2 ** (attempt - 1), 8))
        raise RuntimeError(f"Không tải được {url}: {error}")

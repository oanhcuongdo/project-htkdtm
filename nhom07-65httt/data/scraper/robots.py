from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


class RobotsGuard:
    def __init__(self, start_url: str, user_agent: str, enabled: bool = True):
        self.enabled = enabled
        self.user_agent = user_agent
        parts = urlsplit(start_url)
        self.parser = RobotFileParser(f"{parts.scheme}://{parts.netloc}/robots.txt")
        self.loaded = False

    def load(self):
        if self.enabled:
            try:
                request = Request(
                    self.parser.url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/plain,*/*;q=0.8",
                    },
                )
                with urlopen(request, timeout=15) as response:
                    content = response.read().decode("utf-8", errors="replace")
                self.parser.parse(content.splitlines())
                self.loaded = True
            except Exception:
                self.loaded = False

    def allowed(self, url: str) -> bool:
        if not self.enabled:
            return True
        if not self.loaded:
            self.load()
        return self.parser.can_fetch(self.user_agent, url) if self.loaded else False

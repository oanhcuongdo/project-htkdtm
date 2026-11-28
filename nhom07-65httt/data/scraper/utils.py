import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, urlunsplit


def clean_text(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def absolute_url(value: str, base: str = "https://www.udemy.com") -> str:
    return urljoin(base, value or "") if value else ""


def canonical_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

import html
import re
import unicodedata
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = html.unescape(str(value))
    parser = _TextExtractor()
    parser.feed(text)
    text = " ".join(parser.parts) if "<" in text and ">" in text else text
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def normalize_key(value: str | None) -> str:
    text = clean_text(value) or ""
    return re.sub(r"[^\w]+", " ", text.casefold(), flags=re.UNICODE).strip()

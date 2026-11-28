import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .cleaner import clean_text


LEVELS = {
    "beginner": "Beginner",
    "beginner level": "Beginner",
    "intermediate": "Intermediate",
    "intermediate level": "Intermediate",
    "advanced": "Advanced",
    "advanced level": "Advanced",
    "all levels": "All Levels",
    "all-levels": "All Levels",
}
LANGUAGES = {
    "arabic": "ar", "chinese": "zh", "dutch": "nl", "english": "en",
    "french": "fr", "german": "de", "hindi": "hi", "indonesian": "id",
    "italian": "it", "japanese": "ja", "korean": "ko", "portuguese": "pt",
    "russian": "ru", "spanish": "es", "thai": "th", "turkish": "tr",
    "vietnamese": "vi",
}
COURSE_FIELDS = (
    "course_id", "source_name", "source_course_id", "title", "canonical_url", "source_url",
    "description", "raw_description", "clean_description", "provider", "language", "level",
    "skills", "direct_skills", "inferred_skills", "prerequisites", "duration_minutes",
    "price_amount", "price_currency", "image_url", "rating", "rating_count", "student_count",
    "category", "subcategory", "lecture_count", "section_count", "last_updated", "subtitle",
    "captions", "original_price", "discount", "learning_objectives", "target_audience",
    "certificate", "offer_type", "crawled_at", "quality_status", "quality_flags",
    "duplicate_status", "dataset_version", "source_metadata",
)


def _number(value, integer=False):
    text = clean_text(value)
    if text is None:
        return None
    text = text.replace(",", "").replace("%", "")
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    if integer:
        return int(number) if number == number.to_integral_value() else None
    return float(number)


def duration_to_minutes(value):
    text = clean_text(value)
    if not text:
        return None
    match = re.fullmatch(r"\s*(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?\s*", text, re.I)
    if not match or not any(match.groups()):
        return None
    return int(match.group(1) or 0) * 60 + int(match.group(2) or 0)


def canonical_course_url(value):
    text = clean_text(value)
    if not text:
        return None
    try:
        parts = urlsplit(text)
    except ValueError:
        return None
    host = (parts.hostname or "").casefold()
    if parts.scheme.casefold() not in {"http", "https"}:
        return None
    if host != "udemy.com" and not host.endswith(".udemy.com"):
        return None
    match = re.fullmatch(r"/course/([^/]+)/?", parts.path, re.I)
    if not match:
        return None
    slug = match.group(1)
    return urlunsplit(("https", "www.udemy.com", f"/course/{slug}/", "", ""))


def _as_list(value):
    value = clean_text(value)
    if value is None:
        return None
    try:
        decoded = json.loads(value)
        if isinstance(decoded, list):
            return [item for item in (clean_text(x) for x in decoded) if item]
    except (TypeError, ValueError):
        pass
    return [item.strip() for item in re.split(r"[,;|\n]", value) if item.strip()]


def normalize_course(raw_record: dict) -> dict:
    source = raw_record.get("raw_payload") or {}
    source_url = source.get("url") or raw_record.get("source_url")
    canonical = canonical_course_url(source_url)
    source_id = clean_text(source.get("course_id"))
    if not source_id and canonical:
        source_id = urlsplit(canonical).path.strip("/").rsplit("/", 1)[-1]
    title = clean_text(source.get("title"))
    raw_description = source.get("raw_description") or source.get("description")
    raw_description = str(raw_description) if raw_description not in (None, "") else None
    description = clean_text(source.get("description") or raw_description)
    instructors = clean_text(source.get("instructors"))
    level_value = clean_text(source.get("level"))
    language_value = clean_text(source.get("language"))
    language_key = language_value.casefold() if language_value else ""
    language = LANGUAGES.get(language_key, language_key if re.fullmatch(r"[a-z]{2}", language_key, re.I) else None)
    provider = instructors
    return {
        "course_id": f"udemy:{source_id}" if source_id else None,
        "source_name": "udemy" if canonical else None,
        "source_course_id": source_id,
        "title": title,
        "canonical_url": canonical,
        "source_url": source_url,
        "description": description,
        "raw_description": raw_description,
        "clean_description": clean_text(description),
        "provider": provider,
        "language": language,
        "level": LEVELS.get(level_value.casefold(), level_value) if level_value else None,
        "skills": None,
        "direct_skills": _as_list(source.get("direct_skills") or source.get("skills")),
        "inferred_skills": None,
        "prerequisites": clean_text(source.get("requirements")),
        "duration_minutes": duration_to_minutes(source.get("duration")),
        "price_amount": _number(source.get("price")),
        "price_currency": clean_text(source.get("currency")) or None,
        "image_url": clean_text(source.get("image_url")),
        "rating": _number(source.get("rating")),
        "rating_count": _number(source.get("rating_count"), integer=True),
        "student_count": _number(source.get("student_count"), integer=True),
        "category": clean_text(source.get("category")),
        "subcategory": clean_text(source.get("subcategory")),
        "lecture_count": _number(source.get("lecture_count"), integer=True),
        "section_count": _number(source.get("section_count"), integer=True),
        "last_updated": clean_text(source.get("last_updated")),
        "subtitle": clean_text(source.get("subtitle")),
        "captions": clean_text(source.get("captions")),
        "original_price": _number(source.get("original_price")),
        "discount": clean_text(source.get("discount")),
        "learning_objectives": clean_text(source.get("learning_objectives")),
        "target_audience": clean_text(source.get("target_audience")),
        "certificate": clean_text(source.get("certificate")),
        "offer_type": "EXTERNAL_REFERENCE",
        "crawled_at": clean_text(source.get("scraped_at") or raw_record.get("crawled_at")),
        "quality_status": None,
        "quality_flags": [],
        "duplicate_status": "unique",
        "dataset_version": None,
        "source_metadata": dict(source),
    }

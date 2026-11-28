import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from .udemy_models import Course
from .utils import canonical_url, clean_text, utc_now


def _is_udemy_host(host: str) -> bool:
    host = (host or "").casefold()
    return host == "udemy.com" or host.endswith(".udemy.com")


def discover_course_urls(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html or "", "html.parser")
    urls = []
    for anchor in soup.select('a[href*="/course/"]'):
        url = canonical_url(urljoin(base_url, anchor.get("href", "")))
        parts = urlsplit(url)
        if _is_udemy_host(parts.netloc) and re.fullmatch(r"/course/[^/]+/?", parts.path):
            if url not in urls:
                urls.append(url)
    return urls


def discover_sitemap_entries(xml_text: str, base_url: str) -> tuple[list[str], list[str]]:
    """Return child sitemap URLs and course URLs from a sitemap document."""
    try:
        root = ET.fromstring(xml_text or "")
    except ET.ParseError:
        return [], []

    sitemaps = []
    courses = []
    is_index = root.tag.rsplit("}", 1)[-1].casefold() == "sitemapindex"
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1].casefold() != "loc" or not node.text:
            continue
        url = canonical_url(urljoin(base_url, node.text.strip()))
        parts = urlsplit(url)
        if not _is_udemy_host(parts.netloc):
            continue
        if re.fullmatch(r"/course/[^/]+/?", parts.path):
            if url not in courses:
                courses.append(url)
        elif is_index and parts.path.casefold().endswith((".xml", ".xml.gz")) and url not in sitemaps:
            sitemaps.append(url)
    return sitemaps, courses


def _json_nodes(soup):
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.string or node.get_text())
        except (ValueError, TypeError):
            continue
        values = data if isinstance(data, list) else [data]
        while values:
            item = values.pop(0)
            if isinstance(item, dict):
                yield item
                graph = item.get("@graph", [])
                values.extend(graph if isinstance(graph, list) else [graph])


def _text(value):
    if isinstance(value, list):
        return ", ".join(dict.fromkeys(filter(None, (_text(v) for v in value))))
    if isinstance(value, dict):
        return clean_text(value.get("name") or value.get("value") or value.get("text") or "")
    return clean_text(value)


def _meta(soup, *keys):
    for key in keys:
        node = soup.select_one(f'meta[property="{key}"], meta[name="{key}"]')
        if node and node.get("content"):
            return clean_text(node["content"])
    return ""


def _first(soup, selectors):
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            value = clean_text(node.get_text(" ", strip=True))
            if value:
                return value
    return ""


def _ld_by_type(nodes, type_name):
    for item in nodes:
        types = item.get("@type", [])
        types = types if isinstance(types, list) else [types]
        if type_name in types:
            return item
    return {}


def _price(offers):
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    if not isinstance(offers, dict):
        return "", ""
    return _text(offers.get("price")), _text(offers.get("priceCurrency"))


def _page_stats(soup):
    text = clean_text(soup.get_text(" ", strip=True))
    match = re.search(r"(\d+)\s+sections?\s*[\u2022\u00b7]\s*(\d+)\s+lectures?\s*[\u2022\u00b7]\s*(.+?)\s+total length", text, re.I)
    return (match.group(1), match.group(2), match.group(3)) if match else ("", "", "")


def parse_course(html: str, course_url: str) -> Course:
    soup = BeautifulSoup(html or "", "html.parser")
    nodes = list(_json_nodes(soup))
    course = _ld_by_type(nodes, "Course")
    product = _ld_by_type(nodes, "Product")
    data = course or product
    aggregate = data.get("aggregateRating") or {}
    if not isinstance(aggregate, dict):
        aggregate = {}
    offers = data.get("offers") or product.get("offers") or {}
    price, currency = _price(offers)
    instructors = data.get("instructor") or data.get("creator") or []
    if not isinstance(instructors, list):
        instructors = [instructors]
    instructor_names = [_text(item) for item in instructors]
    image = data.get("image") or product.get("image") or _meta(soup, "og:image")
    if isinstance(image, list):
        image = image[0] if image else ""
    identifier = _text(data.get("productID") or data.get("sku") or data.get("identifier"))
    path_match = re.search(r"/course/([^/]+)/?", course_url)
    course_id = identifier or (path_match.group(1) if path_match else "")
    title = _text(data.get("name")) or _meta(soup, "og:title") or _first(soup, ["h1"])
    section_count, lecture_count, duration = _page_stats(soup)
    breadcrumbs = [_text(node.get_text(" ", strip=True)) for node in soup.select('nav[aria-label*="breadcrumb"] a, ol[aria-label*="breadcrumb"] a')]
    price = price or _first(soup, ['[data-purpose="course-price-text"]'])
    rating_count = _text(aggregate.get("ratingCount") or aggregate.get("reviewCount")) or _first(soup, ['[data-purpose="rating-count"]', '[data-purpose="rating"] + span'])

    return Course(
        course_id=course_id,
        title=title,
        url=canonical_url(course_url),
        subtitle=_meta(soup, "udemy:course:headline") or _first(soup, ['[data-purpose="lead-headline"]']),
        instructors=", ".join(filter(None, dict.fromkeys(instructor_names))) or _first(soup, ['[data-purpose="instructor-name"]']),
        category=_meta(soup, "udemy:course:category") or (breadcrumbs[-2] if len(breadcrumbs) > 1 else ""),
        subcategory=_meta(soup, "udemy:course:subcategory") or (breadcrumbs[-1] if breadcrumbs else ""),
        rating=_text(aggregate.get("ratingValue")) or _meta(soup, "udemy:course:rating") or _first(soup, ['[data-purpose="rating"]']),
        rating_count=rating_count,
        student_count=_meta(soup, "udemy:course:students") or _first(soup, ['[data-purpose="enrollment"]']),
        price=price or _meta(soup, "udemy:course:price"),
        currency=currency,
        original_price=_meta(soup, "udemy:course:original-price"),
        discount=_meta(soup, "udemy:course:discount"),
        level=_meta(soup, "udemy:course:level") or _first(soup, ['[data-purpose="course-level"]']),
        language=_meta(soup, "udemy:course:language") or _first(soup, ['[data-purpose="language"]']),
        captions=_meta(soup, "udemy:course:captions") or _first(soup, ['[data-purpose="captions"]']),
        last_updated=_text(data.get("dateModified")) or _meta(soup, "udemy:course:last-updated") or _first(soup, ['[data-purpose="last-update-date"]']),
        duration=_text(data.get("timeRequired")) or _meta(soup, "udemy:course:duration") or duration or _first(soup, ['[data-purpose="curriculum-stats"]']),
        lecture_count=_meta(soup, "udemy:course:lecture-count") or lecture_count,
        section_count=_meta(soup, "udemy:course:section-count") or section_count,
        certificate=_meta(soup, "udemy:course:certificate"),
        image_url=_text(image),
        requirements=_meta(soup, "udemy:course:requirements"),
        learning_objectives=_meta(soup, "udemy:course:objectives"),
        target_audience=_meta(soup, "udemy:course:audience"),
        scraped_at=utc_now(),
    )

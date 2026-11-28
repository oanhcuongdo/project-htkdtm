import argparse
import json
import logging
from collections import deque
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from scraper.client import UdemyClient
from scraper.config import Config
from scraper.udemy_exporter import append_course_csv, count_course_rows, existing_course_urls, export_courses_csv
from scraper.udemy_parser import discover_course_urls, discover_sitemap_entries, parse_course
from pipeline.console import configure_utf8_console


def page_url(url: str, page: int) -> str:
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query["p"] = str(page)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def iter_sitemap_course_urls(client, sitemap_url: str, existing_urls: set[str], limit: int = 0):
    pending = deque([sitemap_url])
    seen_sitemaps = set()
    seen_courses = set()
    yielded = 0
    while pending and (not limit or yielded < limit):
        current = pending.popleft()
        if current in seen_sitemaps:
            continue
        seen_sitemaps.add(current)
        logging.info("Đọc sitemap %s", current)
        try:
            child_sitemaps, course_urls = discover_sitemap_entries(client.get(current), current)
        except Exception:
            logging.exception("Bỏ qua sitemap lỗi: %s", current)
            continue
        pending.extend(url for url in child_sitemaps if url not in seen_sitemaps)
        for url in course_urls:
            if url in existing_urls or url in seen_courses:
                continue
            seen_courses.add(url)
            yield url
            yielded += 1
            if limit and yielded >= limit:
                return


def iter_listing_course_urls(client, config, existing_urls: set[str], limit: int = 0):
    page = max(1, config.start_page)
    seen_urls = set(existing_urls)
    yielded = 0
    while config.max_pages <= 0 or page < config.start_page + config.max_pages:
        listing_url = page_url(config.start_url, page)
        logging.info("Đọc danh sách khóa học %s", listing_url)
        try:
            found = discover_course_urls(client.get(listing_url), listing_url)
        except Exception:
            logging.exception("Bỏ qua trang danh sách lỗi")
            return
        new_urls = [url for url in found if url not in seen_urls]
        if not new_urls:
            return
        for url in new_urls:
            seen_urls.add(url)
            yield url
            yielded += 1
            if limit and yielded >= limit:
                return
        page += 1


def run(config: Config):
    if not config.source_authorized or not config.authorization_reference:
        raise PermissionError("Crawler Udemy đang bị khóa vì chưa có văn bản cho phép; chưa gửi request nào.")
    max_total = max(0, config.max_total_courses)
    existing_count = count_course_rows(config.output_file) if config.append else 0
    if max_total and existing_count >= max_total:
        logging.info("Đã đạt giới hạn tổng %s khóa học; không gửi request mới.", max_total)
        return Path(config.output_file)

    seen_urls = existing_course_urls(config.output_file) if config.append else set()
    limit = max(0, config.max_courses)
    if max_total:
        remaining = max_total - existing_count
        limit = min(limit, remaining) if limit else remaining
    if not config.append:
        export_courses_csv([], config.output_file, append=False)
    client = UdemyClient(config)
    if config.crawl_mode.casefold() == "sitemap":
        urls = iter_sitemap_course_urls(client, config.sitemap_url, seen_urls, limit)
    else:
        urls = iter_listing_course_urls(client, config, seen_urls, limit)
    for index, url in enumerate(urls, 1):
        try:
            logging.info("[%s] %s", index, url)
            course = parse_course(client.get(url), url)
            append_course_csv(course, config.output_file)
        except Exception:
            logging.exception("Bỏ qua khóa học lỗi: %s", url)
    return Path(config.output_file)


if __name__ == "__main__":
    configure_utf8_console()
    parser = argparse.ArgumentParser(description="Thu thập metadata khóa học Udemy và xuất ra CSV")
    parser.add_argument("--config", default="config.udemy.yaml", help="Đường dẫn tệp cấu hình (mặc định: config.udemy.yaml)")
    parser.add_argument("--source", choices=["udemy"], default="udemy", help="Nguồn dữ liệu")
    parser.add_argument("--max-pages", type=int, help="Số trang danh sách tối đa trong lần chạy này")
    parser.add_argument("--max-courses", type=int, help="Số khóa học mới tối đa trong lần chạy này")
    parser.add_argument("--dry-run", action="store_true", help="Xem cấu hình mà không gửi request mạng")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    config = Config.load(config_path)
    if args.max_pages is not None:
        config.max_pages = args.max_pages
    if args.max_courses is not None:
        config.max_courses = args.max_courses
    output = Path(config.output_file)
    if not output.is_absolute():
        config.output_file = str(root / output)
    (root / "logs").mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[logging.FileHandler(root / "logs/udemy_scraper.log", encoding="utf-8"), logging.StreamHandler()])
    if args.dry_run:
        print(json.dumps({"source": args.source, "authorized": config.source_authorized and bool(config.authorization_reference), "max_pages": config.max_pages, "max_courses": config.max_courses, "max_total_courses": config.max_total_courses, "network_requests": 0}, indent=2))
        raise SystemExit(0)
    result = run(config)
    logging.info("Đã xuất CSV: %s", result)

"""Thu thập đánh giá công khai từ RSS Customer Reviews của Apple."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml


REPO_ROOT = Path(__file__).resolve().parents[4]
PLATFORMS_FILE = REPO_ROOT / "nhom03-65httt" / "config" / "platforms.yml"
DEFAULT_OUT = REPO_ROOT / "nhom03-65httt" / "data" / "raw"
CSV_COLUMNS = [
    "source",
    "product",
    "review_id",
    "author_hash",
    "rating",
    "text",
    "lang_guess",
    "created_at",
    "app_version",
    "thumbs_up",
    "reply_text",
    "crawled_at",
]
MAX_RETRIES = 5
MAX_PAGES = 10
REVIEWS_PER_PAGE = 50
MAX_FEED_REVIEWS = MAX_PAGES * REVIEWS_PER_PAGE
VIETNAMESE_DIACRITICS = set(
    "àáảãạăằắẳẵặâầấẩẫậđ"
    "èéẻẽẹêềếểễệ"
    "ìíỉĩị"
    "òóỏõọôồốổỗộơờớởỡợ"
    "ùúủũụưừứửữự"
    "ỳýỷỹỵ"
)
VIETNAMESE_DIACRITICS |= {character.upper() for character in VIETNAMESE_DIACRITICS}


class CollectorError(RuntimeError):
    """Lỗi cấu hình hoặc lỗi không thể phục hồi khi thu thập."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thu thập đánh giá App Store cho một nền tảng trong platforms.yml."
    )
    parser.add_argument(
        "--only", required=True, metavar="ID", help="ID nền tảng khớp platforms.yml"
    )
    parser.add_argument(
        "--count", type=int, default=200, help="Số đánh giá cần lấy (mặc định: 200)"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Thư mục lưu CSV (mặc định: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--sleep", type=float, default=2, help="Thời gian nghỉ giữa các trang, tối thiểu 2 giây"
    )
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count phải lớn hơn 0")
    if args.sleep < 2:
        parser.error("--sleep phải từ 2 giây trở lên")
    return args


def load_platform(platform_id: str) -> dict[str, str]:
    try:
        with PLATFORMS_FILE.open("r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
    except (OSError, yaml.YAMLError) as exc:
        raise CollectorError(f"Không đọc được cấu hình {PLATFORMS_FILE}: {exc}") from exc

    platforms = config.get("platforms") if isinstance(config, dict) else None
    if not isinstance(platforms, list):
        raise CollectorError('Cấu hình phải có danh sách "platforms".')

    for platform in platforms:
        if not isinstance(platform, dict) or platform.get("id") != platform_id:
            continue
        required = ("id", "play_id", "ios_id", "platform_group")
        missing = [key for key in required if not platform.get(key)]
        if missing:
            raise CollectorError(
                f"Nền tảng {platform_id!r} thiếu trường: {', '.join(missing)}."
            )
        return {key: str(platform[key]) for key in required}

    available = [
        str(item.get("id"))
        for item in platforms
        if isinstance(item, dict) and item.get("id")
    ]
    raise CollectorError(
        f"Không tìm thấy --only {platform_id!r} trong platforms.yml. "
        f"Các ID hiện có: {', '.join(available)}"
    )


def output_file(out_dir: Path, platform_id: str) -> Path:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", platform_id).strip("._-").lower()
    if not slug:
        slug = hashlib.sha256(platform_id.encode("utf-8")).hexdigest()[:12]
    return out_dir / f"app_store_{slug}.csv"


def read_existing_ids(csv_path: Path) -> set[str]:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != CSV_COLUMNS:
            raise CollectorError(
                f"Tệp {csv_path} không có đúng tiêu đề CSV của collector; "
                "hãy kiểm tra tệp trước khi chạy lại."
            )
        return {row["review_id"] for row in reader if row.get("review_id")}


def write_rows(csv_path: Path, rows: list[dict[str, Any]]) -> None:
    is_new_or_empty = not csv_path.exists() or csv_path.stat().st_size == 0
    encoding = "utf-8-sig" if is_new_or_empty else "utf-8"
    mode = "w" if is_new_or_empty else "a"
    with csv_path.open(mode, encoding=encoding, newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if is_new_or_empty:
            writer.writeheader()
        writer.writerows(rows)


def label_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("label") or "")
    return str(value or "")


def review_id(entry: dict[str, Any]) -> str:
    value = entry.get("id")
    if isinstance(value, dict):
        attributes = value.get("attributes")
        if isinstance(attributes, dict) and attributes.get("im:id"):
            return str(attributes["im:id"])
        return label_value(value)
    return str(value or "")


def int_or_blank(value: Any) -> int | str:
    label = label_value(value)
    try:
        return int(label)
    except (TypeError, ValueError):
        return ""


def normalize_review(entry: dict[str, Any], product_id: str, crawled_at: str) -> dict[str, Any]:
    review_text = label_value(entry.get("content"))
    if not review_text:
        review_text = label_value(entry.get("title"))

    author = entry.get("author")
    author_name = label_value(author.get("name")) if isinstance(author, dict) else ""
    author_hash = (
        hashlib.sha256(author_name.encode("utf-8")).hexdigest()[:12]
        if author_name
        else ""
    )
    diacritic_count = sum(character in VIETNAMESE_DIACRITICS for character in review_text)

    return {
        "source": "app_store",
        "product": product_id,
        "review_id": review_id(entry),
        "author_hash": author_hash,
        "rating": int_or_blank(entry.get("im:rating")),
        "text": review_text,
        "lang_guess": "vi" if diacritic_count >= 2 else "other",
        "created_at": label_value(entry.get("updated")),
        "app_version": label_value(entry.get("im:version")),
        "thumbs_up": int_or_blank(entry.get("im:voteSum")),
        "reply_text": "",
        "crawled_at": crawled_at,
    }


def request_bytes(
    url: str,
    base_delay: float,
    source_label: str,
    headers: dict[str, str],
) -> bytes:
    request = Request(url, headers=headers)
    for retry_number in range(MAX_RETRIES + 1):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read()
        except HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code <= 599
            if not retryable:
                raise CollectorError(f"Apple trả HTTP {exc.code} ở {source_label}.") from exc
            if retry_number >= MAX_RETRIES:
                raise CollectorError(
                    f"Apple tiếp tục trả HTTP {exc.code} sau {MAX_RETRIES} lần thử lại."
                ) from exc
            delay = base_delay * (2**retry_number)
            print(
                f"App Store gặp HTTP {exc.code}; thử lại sau {delay:g} giây "
                f"({retry_number + 1}/{MAX_RETRIES}).",
                file=sys.stderr,
            )
            time.sleep(delay)
        except (URLError, TimeoutError, OSError) as exc:
            if retry_number >= MAX_RETRIES:
                raise CollectorError(
                    f"Kết nối tới Apple tiếp tục thất bại sau {MAX_RETRIES} lần thử lại."
                ) from exc
            delay = base_delay * (2**retry_number)
            print(
                f"Kết nối App Store thất bại; thử lại sau {delay:g} giây "
                f"({retry_number + 1}/{MAX_RETRIES}).",
                file=sys.stderr,
            )
            time.sleep(delay)

    raise CollectorError(f"Không đọc được {source_label}.")


def request_page(
    app_id: str, page: int, base_delay: float
) -> list[dict[str, Any]]:
    url = (
        "https://itunes.apple.com/vn/rss/customerreviews/"
        f"page={page}/id={quote(app_id, safe='')}/sortby=mostrecent/json"
    )
    body = request_bytes(
        url,
        base_delay,
        f"RSS trang {page}",
        {
            "Accept": "application/json",
            "User-Agent": "EduVisionBI-Collector/1.0",
        },
    )
    try:
        payload = json.loads(body.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CollectorError(f"Apple trả dữ liệu JSON không hợp lệ ở trang {page}.") from exc

    feed = payload.get("feed") if isinstance(payload, dict) else None
    entries = feed.get("entry", []) if isinstance(feed, dict) else []
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list):
        raise CollectorError(f"Cấu trúc RSS không hợp lệ ở trang {page}.")
    # RSS có thể đặt thông tin ứng dụng ở entry đầu; chỉ giữ các entry là review.
    review_entries = [
        entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("im:rating") is not None
    ]
    return review_entries


def collect(args: argparse.Namespace) -> tuple[Path, int, int]:
    platform = load_platform(args.only)
    csv_path = output_file(args.out, platform["id"])
    args.out.mkdir(parents=True, exist_ok=True)
    seen_ids = read_existing_ids(csv_path)

    crawled_at = datetime.now(timezone.utc).isoformat()
    requested_count = min(args.count, MAX_FEED_REVIEWS)
    fetched_count = 0
    added_count = 0
    app_id = platform["ios_id"]

    for page in range(1, MAX_PAGES + 1):
        if fetched_count >= requested_count:
            break
        entries = request_page(app_id, page, args.sleep)
        if not entries:
            write_rows(csv_path, [])
            break

        remaining = requested_count - fetched_count
        page_entries = entries[:remaining]
        fetched_count += len(page_entries)
        new_rows: list[dict[str, Any]] = []
        for entry in page_entries:
            current_id = review_id(entry)
            if not current_id or current_id in seen_ids:
                continue
            new_rows.append(normalize_review(entry, platform["id"], crawled_at))
            seen_ids.add(current_id)

        write_rows(csv_path, new_rows)
        added_count += len(new_rows)
        if fetched_count < requested_count and page < MAX_PAGES:
            time.sleep(args.sleep)

    return csv_path, added_count, requested_count


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args()
    try:
        csv_path, added_count, requested_count = collect(args)
    except CollectorError as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Lỗi đọc/ghi tệp: {exc}", file=sys.stderr)
        return 1

    print(f"Đã thêm {added_count} đánh giá mới vào {csv_path}.")
    if args.count > requested_count:
        print(
            f"RSS công khai của Apple giới hạn tối đa {requested_count} đánh giá mỗi lần chạy."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

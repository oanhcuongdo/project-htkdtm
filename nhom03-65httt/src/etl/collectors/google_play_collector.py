"""Thu thập đánh giá công khai của một ứng dụng Google Play mỗi lần chạy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import re
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError

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
MAX_PAGE_SIZE = 200
VIETNAMESE_DIACRITICS = set(
    "àáảãạăằắẳẵặâầấẩẫậđ"
    "èéẻẽẹêềếểễệ"
    "ìíỉĩị"
    "òóỏõọôồốổỗộơờớởỡợ"
    "ùúủũụưừứửữự"
    "ỳýỷỹỵ"
)
VIETNAMESE_DIACRITICS |= {char.upper() for char in VIETNAMESE_DIACRITICS}


class CollectorError(RuntimeError):
    """Lỗi cấu hình hoặc lỗi không thể phục hồi khi thu thập."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thu thập đánh giá Google Play cho một nền tảng trong platforms.yml."
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
        if not isinstance(platform, dict):
            continue
        if platform.get("id") == platform_id:
            required = ("id", "play_id", "platform_group")
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
    return out_dir / f"google_play_{slug}.csv"


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


def iso_timestamp(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def normalize_review(review: dict[str, Any], product_id: str, crawled_at: str) -> dict[str, Any]:
    text = review.get("content") or ""
    # Tên hiển thị chỉ được đọc tạm thời để tạo mã băm; không được ghi vào CSV.
    display_name = str(review.get("userName") or "")
    author_hash = (
        hashlib.sha256(display_name.encode("utf-8")).hexdigest()[:12]
        if display_name
        else ""
    )
    diacritic_count = sum(character in VIETNAMESE_DIACRITICS for character in text)

    return {
        "source": "google_play",
        "product": product_id,
        "review_id": review.get("reviewId") or "",
        "author_hash": author_hash,
        "rating": review.get("score"),
        "text": text,
        "lang_guess": "vi" if diacritic_count >= 2 else "other",
        "created_at": iso_timestamp(review.get("at")),
        "app_version": review.get("appVersion") or review.get("reviewCreatedVersion") or "",
        "thumbs_up": review.get("thumbsUpCount", 0),
        "reply_text": review.get("replyContent") or "",
        "crawled_at": crawled_at,
    }


def transient_status(error: Exception) -> int | None:
    match = re.search(r"\bStatus code\s+(\d{3})\b", str(error), re.IGNORECASE)
    if not match:
        return None
    status = int(match.group(1))
    return status if status == 429 or 500 <= status <= 599 else None


def transient_network_error(error: Exception) -> bool:
    """Nhận diện lỗi kết nối có thể hồi phục mà không thử lách cơ chế chặn."""
    retryable_types = (
        http.client.RemoteDisconnected,
        ConnectionError,
        TimeoutError,
        socket.timeout,
    )
    if isinstance(error, retryable_types):
        return True

    if isinstance(error, URLError):
        reason = error.reason
        if isinstance(reason, retryable_types):
            return True
        message = str(reason).lower()
    else:
        message = str(error).lower()

    retryable_messages = (
        "remote end closed connection without response",
        "connection reset",
        "connection aborted",
        "connection timed out",
        "timed out",
        "temporary failure in name resolution",
    )
    return any(fragment in message for fragment in retryable_messages)


def fetch_page(
    app_id: str,
    count: int,
    continuation_token: Any,
    base_delay: float,
) -> tuple[list[dict[str, Any]], Any]:
    """Gọi API thư viện và khôi phục lỗi HTTP mà thư viện vốn âm thầm nuốt."""
    try:
        from google_play_scraper import Sort, reviews
        from google_play_scraper.features import reviews as reviews_feature
        from google_play_scraper.utils import request as request_utils
    except ImportError as exc:
        raise CollectorError(
            "Thiếu google-play-scraper. Cài các gói bằng lệnh "
            "pip install -r nhom03-65httt/src/etl/collectors/requirements.txt."
        ) from exc

    original_fetch = reviews_feature._fetch_review_items
    original_retry_limit = request_utils.MAX_RETRIES

    # Thư viện lưu số lượng trong continuation token và ưu tiên giá trị đó ở
    # lần gọi tiếp theo. Cập nhật để trang cuối không lấy vượt --count.
    if continuation_token is not None and hasattr(continuation_token, "count"):
        continuation_token.count = count

    for retry_number in range(MAX_RETRIES + 1):
        captured_errors: list[Exception] = []

        def capture_fetch_error(*args: Any, **kwargs: Any) -> Any:
            try:
                return original_fetch(*args, **kwargs)
            except Exception as exc:
                captured_errors.append(exc)
                raise

        # reviews() trong thư viện bắt Exception và trả về danh sách rỗng. Ghi nhận
        # lỗi ở điểm gọi nội bộ để phân biệt lỗi HTTP với trang thực sự đã hết dữ liệu.
        reviews_feature._fetch_review_items = capture_fetch_error
        request_utils.MAX_RETRIES = 1
        try:
            result, next_token = reviews(
                app_id,
                lang="vi",
                country="vn",
                sort=Sort.NEWEST,
                count=count,
                continuation_token=continuation_token,
            )
        finally:
            reviews_feature._fetch_review_items = original_fetch
            request_utils.MAX_RETRIES = original_retry_limit

        if not captured_errors:
            return result, next_token

        error = captured_errors[-1]
        status = transient_status(error)
        network_failure = status is None and transient_network_error(error)
        if status is None and not network_failure:
            raise CollectorError(f"Không lấy được trang đánh giá: {error}") from error
        if retry_number >= MAX_RETRIES:
            if status is not None:
                message = (
                    f"Google Play tiếp tục trả HTTP {status} "
                    f"sau {MAX_RETRIES} lần thử lại."
                )
            else:
                message = (
                    "Kết nối tới Google Play tiếp tục thất bại "
                    f"sau {MAX_RETRIES} lần thử lại ({type(error).__name__})."
                )
            raise CollectorError(message) from error

        delay = base_delay * (2**retry_number)
        reason = f"HTTP {status}" if status is not None else "lỗi kết nối tạm thời"
        print(
            f"Google Play gặp {reason}; thử lại sau {delay:g} giây "
            f"({retry_number + 1}/{MAX_RETRIES}).",
            file=sys.stderr,
        )
        time.sleep(delay)

    raise CollectorError("Không lấy được trang đánh giá.")


def collect(args: argparse.Namespace) -> tuple[Path, int]:
    platform = load_platform(args.only)
    csv_path = output_file(args.out, platform["id"])
    args.out.mkdir(parents=True, exist_ok=True)
    seen_ids = read_existing_ids(csv_path)

    crawled_at = datetime.now(timezone.utc).isoformat()
    continuation_token = None
    fetched_count = 0
    added_count = 0

    while fetched_count < args.count:
        page_count = min(MAX_PAGE_SIZE, args.count - fetched_count)
        reviews, next_token = fetch_page(
            platform["play_id"],
            page_count,
            continuation_token,
            args.sleep,
        )
        if not reviews:
            # Nếu ứng dụng chưa có đánh giá, vẫn tạo CSV hợp lệ chỉ có tiêu đề.
            write_rows(csv_path, [])
            break

        fetched_count += len(reviews)
        new_rows = []
        for review in reviews:
            review_id = str(review.get("reviewId") or "")
            if not review_id or review_id in seen_ids:
                continue
            new_rows.append(normalize_review(review, platform["id"], crawled_at))
            seen_ids.add(review_id)

        write_rows(csv_path, new_rows)
        added_count += len(new_rows)
        continuation_token = next_token

        if fetched_count >= args.count or getattr(continuation_token, "token", None) is None:
            break
        time.sleep(args.sleep)

    return csv_path, added_count


def main() -> int:
    # Tránh lỗi in ký tự tiếng Việt trên terminal Windows dùng bảng mã cũ.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")

    args = parse_args()
    try:
        csv_path, added_count = collect(args)
    except CollectorError as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Lỗi đọc/ghi tệp: {exc}", file=sys.stderr)
        return 1

    print(f"Đã thêm {added_count} đánh giá mới vào {csv_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

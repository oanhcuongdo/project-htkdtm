import argparse
import logging
import sys
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.config.settings import settings
from src.backend.etl.pipeline import ETLPipeline
from src.backend.scraper.chotot_scraper import ChototScraper
from src.backend.scraper.phongtro123_scraper import Phongtro123Scraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("SmartRentScheduler")


def run_scheduled_job(limit_per_source: int = 20, check_active_limit: int = 30, use_gemini: bool = True):
    """
    Tác vụ định kỳ:
    1. Thu thập tin mới nhất từ Chợ Tốt & Phongtro123
    2. Chạy ETL làm sạch, bóc tách phí và nạp Star Schema
    3. Kiểm tra vòng đời tin cũ để cập nhật closed_at (Days on Market)
    """
    logger.info("Bắt đầu chu kỳ thu thập & cập nhật dữ liệu định kỳ...")
    pipeline = ETLPipeline(use_gemini=use_gemini)
    chotot = ChototScraper()
    pt123 = Phongtro123Scraper(fetch_details=True)

    listings = []
    listings.extend(chotot.fetch_listings(limit=limit_per_source, start_offset=0))
    listings.extend(pt123.fetch_listings(limit=limit_per_source, start_page=1))

    if listings:
        pipeline.save_raw_listings(listings)
        pipeline.process_and_load_star_schema(listings)

    pipeline.refresh_listing_active_status(sample_limit=check_active_limit)
    logger.info("Hoàn tất chu kỳ cập nhật định kỳ.")


def main():
    parser = argparse.ArgumentParser(description="Bộ lập lịch chạy định kỳ Scraper + ETL")
    parser.add_argument("--interval-hours", type=int, default=settings.SCHEDULER_INTERVAL_HOURS, help="Chu kỳ chạy (giờ)")
    parser.add_argument("--limit", type=int, default=20, help="Số tin mới mỗi nguồn mỗi lượt")
    parser.add_argument("--check-active", type=int, default=30, help="Số tin kiểm tra hết hạn mỗi lượt")
    parser.add_argument("--run-once", action="store_true", help="Chạy ngay 1 lần rồi thoát (phù hợp cron/CI)")
    parser.add_argument("--skip-gemini", action="store_true", help="Dùng Regex fallback nếu không gọi Gemini")
    args = parser.parse_args()

    if args.run_once:
        run_scheduled_job(
            limit_per_source=args.limit,
            check_active_limit=args.check_active,
            use_gemini=not args.skip_gemini,
        )
        return

    scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")
    scheduler.add_job(
        run_scheduled_job,
        "interval",
        hours=args.interval_hours,
        kwargs={
            "limit_per_source": args.limit,
            "check_active_limit": args.check_active,
            "use_gemini": not args.skip_gemini,
        },
        id="rental_etl_periodic_job",
        replace_existing=True,
    )
    logger.info("Scheduler đã khởi động (chu kỳ mỗi %d giờ). Nhấn Ctrl+C để dừng.", args.interval_hours)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler đã dừng.")


if __name__ == "__main__":
    main()

import argparse
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.backend.database.supabase_client import get_supabase_client, test_connection
from src.backend.etl.pipeline import ETLPipeline
from src.backend.scraper.chotot_scraper import ChototScraper
from src.backend.scraper.phongtro123_scraper import Phongtro123Scraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("SmartRentCrawler")


def main():
    parser = argparse.ArgumentParser(description="Thu thập và Lưu trữ dữ liệu Nhà Thuê Thông Minh lên Supabase")
    parser.add_argument("--source", choices=["chotot", "phongtro123", "all"], default="all", help="Nguồn cào dữ liệu")
    parser.add_argument("--limit", type=int, default=20, help="Số lượng tin thu thập cho mỗi lượt")
    parser.add_argument("--offset", type=int, default=0, help="Vị trí offset bắt đầu cho Chợ Tốt")
    parser.add_argument("--page", type=int, default=1, help="Trang bắt đầu cho Phongtro123")
    parser.add_argument("--target", type=int, default=None, help="Mục tiêu tổng số tin cần đạt trong Fact table (vd: 250)")
    parser.add_argument("--backfill", action="store_true", help="Làm giàu lại dữ liệu hiện có từ staging_raw_listings")
    parser.add_argument("--check-active", type=int, default=0, help="Kiểm tra trạng thái còn/hết hạn của N tin đang active")
    parser.add_argument("--skip-gemini", action="store_true", help="Chạy ETL bằng Regex fallback, bỏ qua gọi API Gemini")
    parser.add_argument("--fast-pt123", action="store_true", help="Không truy cập trang chi tiết Phongtro123 (cào nhanh)")
    args = parser.parse_args()

    print("=" * 70)
    print(" HỆ THỐNG TÌM KIẾM NHÀ THUÊ THÔNG MINH - PIPELINE DỮ LIỆU & SUPABASE")
    print("=" * 70)

    logger.info("Bước 1: Kiểm tra kết nối Supabase...")
    if not test_connection():
        logger.error("Không thể kết nối đến Supabase. Vui lòng kiểm tra file .env!")
        return

    client = get_supabase_client()
    pipeline = ETLPipeline(use_gemini=not args.skip_gemini)

    if args.backfill:
        logger.info("Chạy Backfill làm giàu dữ liệu từ staging_raw_listings...")
        stats = pipeline.backfill_from_staging()
        print(f"Hoàn tất Backfill: {stats}")
        return

    if args.check_active > 0:
        logger.info("Kiểm tra trạng thái hoạt động của %d tin...", args.check_active)
        res = pipeline.refresh_listing_active_status(sample_limit=args.check_active)
        print(f"Hoàn tất kiểm tra vòng đời tin: {res}")
        return

    chotot = ChototScraper()
    pt123 = Phongtro123Scraper(fetch_details=not args.fast_pt123)

    if args.target:
        current_count = client.table("fact_rental_listings").select("fact_id", count="exact").execute().count
        logger.info(f"Mục tiêu cần đạt: {args.target} tin. Hiện có: {current_count} tin.")

        if current_count >= args.target:
            print(f"\n[THÔNG BÁO] Kho dữ liệu đã đạt/vượt mục tiêu ({current_count}/{args.target} tin).")
            return

        chotot_offset = args.offset if args.offset > 0 else 25
        pt123_page = args.page if args.page > 1 else 3
        round_no = 1

        while current_count < args.target:
            needed = args.target - current_count
            batch_limit = min(35, max(15, (needed // 2) + 5))
            pct = (current_count / args.target) * 100
            print("\n" + "-" * 70)
            logger.info(f"[VÒNG CÀO {round_no}] Tiến độ: {current_count}/{args.target} ({pct:.1f}%). Cần thêm: {needed} tin.")
            print("-" * 70)

            round_listings = []
            if args.source in ["chotot", "all"]:
                logger.info(f"Cào Chợ Tốt (offset={chotot_offset}, limit={batch_limit})...")
                c_ads = chotot.fetch_listings(limit=batch_limit, start_offset=chotot_offset)
                round_listings.extend(c_ads)
                chotot_offset += len(c_ads) if c_ads else batch_limit

            if args.source in ["phongtro123", "all"]:
                logger.info(f"Cào Phongtro123 (page={pt123_page}, limit={batch_limit})...")
                p_ads = pt123.fetch_listings(limit=batch_limit, start_page=pt123_page)
                round_listings.extend(p_ads)
                pt123_page += max(1, (len(p_ads) + 15) // 20)

            if not round_listings:
                logger.warning("Không còn tin mới nào từ các nguồn thu thập. Kết thúc vòng lặp.")
                break

            pipeline.save_raw_listings(round_listings)
            loaded = pipeline.process_and_load_star_schema(round_listings)

            current_count = client.table("fact_rental_listings").select("fact_id", count="exact").execute().count
            logger.info(f"Vòng {round_no} hoàn thành: nạp thêm {loaded} tin mới. Tổng hiện tại: {current_count}/{args.target}")
            round_no += 1

        print("\n" + "=" * 70)
        print(f" HOÀN TẤT MỤC TIÊU: KHO DỮ LIỆU ĐÃ ĐẠT {current_count} TIN (MỤC TIÊU: {args.target})")
        print("=" * 70)
        return

    all_listings = []
    if args.source in ["chotot", "all"]:
        all_listings.extend(chotot.fetch_listings(limit=args.limit, start_offset=args.offset))

    if args.source in ["phongtro123", "all"]:
        all_listings.extend(pt123.fetch_listings(limit=args.limit, start_page=args.page))

    if not all_listings:
        return

    saved_staging = pipeline.save_raw_listings(all_listings)
    loaded_facts = pipeline.process_and_load_star_schema(all_listings)

    fact_count = client.table("fact_rental_listings").select("fact_id", count="exact").execute().count
    print(f"Đã lưu Staging: {saved_staging} | Fact: {loaded_facts} (Tổng: {fact_count})")


if __name__ == "__main__":
    main()

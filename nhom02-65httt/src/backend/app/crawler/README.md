# Bộ Công Cụ Crawler Đa Nền Tảng (`app/crawler`)

Thư mục này chứa bộ mã nguồn thu thập dữ liệu thị trường thật từ **Shopee, Lazada, TikTok Shop, Tiki và các chuỗi bán lẻ**, được đưa vào dự án từ bộ kiểm chứng PoC để phục vụ phát triển tiếp Module 2 (Crawler Pipeline & Entity Resolution).

## 1. Cài đặt thư viện bổ sung

- Các thư viện cho **Mode A & Mode B** (`httpx`, `beautifulsoup4`) đã có sẵn trong `requirements.txt`.
- Để dùng **Entity Resolution (`rapidfuzz`)** hoặc chạy **Mode C (`playwright`)** trên máy cục bộ, cài thêm:

```powershell
cd nhom02-65httt\src\backend
.venv\Scripts\pip install -r requirements-crawler.txt
```

## 2. Kiến trúc 3 Chế độ (3-Mode Hybrid Crawling)

1. **Mode A & Mode B (`multi_platform_crawler.py`) — Chạy nền tự động (không cần trình duyệt):**
   - **Lazada Direct PDP:** Crawl `lazada.vn/products/*.html`, bóc tách `pdpTrackingData`, `JSON-LD` và `__moduleData__`.
   - **Shopee Keyword Discovery + Price History (32–56+ điểm quá khứ):** Truy vấn `lichsugia.com/api/similar-products.php`, `lichsugia.net/backend-api/api/public/products/platform/{shop_id}/{item_id}` và `lichsugia.com/api/price-history.php`.
   - **Tiki Open API v2:** Truy vấn `https://tiki.vn/api/v2/products`.
   - **GiaReVN & Retail Benchmarks:** Bóc tách biểu đồ giá `giarevn.com`, giá chính hãng `cellphones.com.vn` và `websosanh.vn`.

   Chạy thử từ `nhom02-65httt/src/backend/`:
   ```powershell
   python -m app.crawler.multi_platform_crawler
   ```
   Kết quả mẫu được lưu tại `app/crawler/samples/verified_crawl_output.json`.

2. **Mode C (`chrome_cdp_collector.py` + `start_chrome_cdp.bat`) — Chrome Headful CDP (có cửa sổ thật):**
   - Khởi chạy Chrome ở cổng debug `9222` với profile riêng (`%LOCALAPPDATA%\ERP_SmartPricing_ChromeProfile`), không ảnh hưởng trình duyệt cá nhân.
   - Chạy từ `nhom02-65httt/src/backend/`:
     ```powershell
     python -m app.crawler.chrome_cdp_collector --open-login
     python -m app.crawler.chrome_cdp_collector --diagnose
     python -m app.crawler.chrome_cdp_collector --auto-crawl --source all --max-items 3
     python -m app.crawler.chrome_cdp_collector --listen 60
     ```
   - Lưu ý: Output tạm `cdp_captured_payloads.json` đã được đưa vào `.gitignore`, không commit lên Git.

## 3. Hướng phát triển tiếp cho thành viên phụ trách (Nghiêm Xuân Trường)

1. Tách các hàm crawl trong `multi_platform_crawler.py` thành 5 Adapter chuẩn ghi dữ liệu thật vào bảng `competitor_prices` và `competitor_price_history`.
2. Cài đặt bước chuẩn hóa & khớp nối SKU (`RapidFuzz` ngưỡng `>= 85%` tự động khớp, `65%–84%` gắn `NEEDS_REVIEW`, `< 65%` bỏ qua) và gắn cờ `fake_sale_warning`.
3. Xây dựng các API `GET/POST /api/v1/competitors`, `GET /api/v1/competitor-prices`, `POST /api/v1/crawler/run`, `POST /api/v1/crawler/ingest-cdp` và đăng ký lịch chạy định kỳ trong `app/worker/celery_app.py`.

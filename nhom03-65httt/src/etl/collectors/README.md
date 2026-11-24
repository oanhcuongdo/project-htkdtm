# Collector Google Play và App Store

## Mục đích

Hai collector thu thập đánh giá công khai cho một nền tảng mỗi lần chạy. Danh sách nền tảng và mã ứng dụng được đọc từ `nhom03-65httt/config/platforms.yml` (`id`, `play_id`, `ios_id`, `platform_group`). Google Play dùng thư viện `google-play-scraper`. App Store chỉ đọc RSS Customer Reviews công khai của Apple. Tên hiển thị người đánh giá chỉ được dùng tạm để tạo `author_hash`, không được ghi vào CSV.

## Cài đặt

Từ thư mục gốc của kho dự án:

```bash
pip install -r nhom03-65httt/src/etl/collectors/requirements.txt
```

## Chạy

Lấy 50 đánh giá mới nhất của ELSA Speak từ Google Play:

```bash
python nhom03-65httt/src/etl/collectors/google_play_collector.py --only "ELSA Speak" --count 50
```

Lấy 50 đánh giá mới nhất của ELSA Speak từ App Store Việt Nam:

```bash
python nhom03-65httt/src/etl/collectors/app_store_collector.py --only "ELSA Speak" --count 50
```

Các tham số của cả hai collector:

- `--only`: ID nền tảng phải khớp với một mục trong `platforms.yml`.
- `--count`: số đánh giá cần lấy, mặc định `200`.
- `--out`: thư mục lưu CSV, mặc định `nhom03-65httt/data/raw`.
- `--sleep`: thời gian nghỉ giữa các trang, mặc định `2` giây; giá trị nhỏ hơn `2` bị từ chối.

Collector Google Play lấy theo trang mới nhất bằng continuation token. RSS App Store thường chỉ cung cấp tối đa khoảng 500 đánh giá gần nhất cho mỗi nền tảng, ít hơn Google Play; vì vậy dữ liệu App Store là một mẫu, không đại diện cho toàn bộ người dùng. Collector giới hạn tối đa 500 đánh giá mỗi lần chạy. Gặp HTTP 429, 5xx hoặc lỗi kết nối tạm thời, collector thử lại tối đa 5 lần với thời gian chờ tăng theo cấp số nhân. Không dùng proxy hoặc đổi IP, không cần token.

Mỗi nguồn có tệp riêng: `google_play_<id>.csv` hoặc `app_store_<id>.csv`. Nếu tệp đã có, collector chỉ thêm `review_id` chưa xuất hiện trong tệp đó. RSS App Store đôi khi không có review công khai cho một storefront; khi đó collector vẫn tạo CSV có tiêu đề và báo 0 review mới.

## Các cột CSV

CSV có cùng thứ tự cột ở cả hai nguồn, dùng UTF-8 có BOM:

| Cột | Nội dung |
|---|---|
| `source` | `google_play` hoặc `app_store`. |
| `product` | ID nền tảng trong `platforms.yml`. |
| `review_id` | Mã đánh giá do cửa hàng cung cấp. |
| `author_hash` | 12 ký tự đầu của SHA-256 tên hiển thị; không lưu tên, ảnh đại diện hoặc đường dẫn hồ sơ. |
| `rating` | Điểm đánh giá. |
| `text` | Nội dung đánh giá. |
| `lang_guess` | `vi` nếu nội dung có ít nhất hai ký tự tiếng Việt có dấu, nếu không là `other`. |
| `created_at` | Thời điểm đánh giá theo ISO 8601. |
| `app_version` | Phiên bản ứng dụng ghi nhận cùng đánh giá. |
| `thumbs_up` | Số lượt hữu ích nếu nguồn cung cấp; để trống nếu không có. |
| `reply_text` | Phản hồi của nhà phát triển nếu nguồn cung cấp; để trống nếu không có. |
| `crawled_at` | Thời điểm collector chạy theo ISO 8601. |

Dữ liệu đánh giá là đầu ra cục bộ: **không commit CSV hoặc dữ liệu đánh giá thật lên Git**.

# Collector Google Play

## Mục đích

Thu thập đánh giá công khai trên Google Play cho một nền tảng mỗi lần chạy. ID ứng dụng được đọc từ `nhom03-65httt/config/platforms.yml`; không khai báo ID ứng dụng trong mã. Tên hiển thị của người đánh giá chỉ được dùng tạm thời để tạo `author_hash`, không được lưu vào CSV.

## Cài đặt

Từ thư mục gốc của kho dự án, cài các thư viện:

```bash
pip install -r nhom03-65httt/src/etl/collectors/requirements.txt
```

## Chạy

Ví dụ lấy 20 đánh giá mới nhất của ELSA Speak:

```bash
python nhom03-65httt/src/etl/collectors/google_play_collector.py --only "ELSA Speak" --count 20
```

Các tham số:

- `--only`: ID nền tảng phải khớp với một mục trong `platforms.yml`.
- `--count`: số đánh giá cần lấy, mặc định `200`.
- `--out`: thư mục lưu CSV, mặc định `nhom03-65httt/data/raw`.
- `--sleep`: thời gian nghỉ giữa các trang, mặc định `2` giây; giá trị nhỏ hơn `2` bị từ chối. Khi gặp HTTP 429, 5xx hoặc lỗi kết nối tạm thời (như timeout hay máy chủ đóng kết nối), collector thử lại tối đa 5 lần với thời gian chờ tăng theo cấp số nhân. Không dùng proxy hoặc đổi IP.

Mỗi nền tảng được lưu vào một tệp `google_play_<id>.csv`. Nếu tệp đã có, collector bỏ qua các `review_id` đã ghi.

## Các cột CSV

| Cột | Nội dung |
|---|---|
| `source` | Luôn là `google_play`. |
| `product` | ID nền tảng trong `platforms.yml`. |
| `review_id` | Mã đánh giá từ Google Play. |
| `author_hash` | 12 ký tự đầu của SHA-256 tên hiển thị; không lưu tên, ảnh đại diện hoặc đường dẫn hồ sơ. |
| `rating` | Điểm đánh giá. |
| `text` | Nội dung đánh giá. |
| `lang_guess` | `vi` nếu có ít nhất hai ký tự tiếng Việt có dấu, nếu không là `other`. |
| `created_at` | Thời điểm đánh giá theo ISO 8601. |
| `app_version` | Phiên bản ứng dụng ghi nhận cùng đánh giá. |
| `thumbs_up` | Số lượt hữu ích. |
| `reply_text` | Nội dung phản hồi của nhà phát triển, nếu có. |
| `crawled_at` | Thời điểm collector chạy theo ISO 8601. |

Tệp CSV dùng UTF-8 có BOM để thuận tiện mở bằng bảng tính. Dữ liệu đánh giá là dữ liệu đầu ra cục bộ: **không commit CSV hoặc dữ liệu đánh giá thật lên Git**.

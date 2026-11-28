# Từ điển dữ liệu khóa học SmartEdu (schema v1.0)

CSV dùng UTF-8 BOM để mở thuận tiện bằng bảng tính. JSONL dùng UTF-8; giá trị chưa biết được lưu bằng JSON `null`. CSV nguồn cũ được giữ nguyên, còn bản ghi chuẩn hóa tuân theo schema dưới đây.

| Trường | Kiểu | Bắt buộc | Ý nghĩa và cách chuẩn hóa | Nguồn suy ra |
|---|---|---:|---|---|
| `course_id` | string | có | Khóa ổn định của dataset: `<source_name>:<source_course_id>` | ID xác định, không đổi |
| `source_name` | string | có | Nguồn dữ liệu; hiện là `udemy` với các dòng cũ | Suy ra từ URL nguồn đã kiểm tra |
| `source_course_id` | string | có | ID hoặc slug của khóa học trên nguồn | Trường từ nguồn |
| `title` | string | có | Giải mã HTML, bỏ thẻ, chuẩn hóa Unicode NFC và khoảng trắng | Không sửa nghĩa |
| `canonical_url` | string | có | URL HTTPS của khóa học, bỏ tham số theo dõi | Chỉ chuẩn hóa URL |
| `source_url` | string | có | URL gốc như được lưu trong CSV cũ | Không suy diễn |
| `description` | string/null | không | Mô tả khóa học công khai nếu được phép và có trong nguồn | Không tự tạo |
| `raw_description` | string/null | không | Mô tả nguyên bản trước khi làm sạch | Không tự tạo |
| `clean_description` | string/null | không | Mô tả đã bỏ HTML và chuẩn hóa | Chỉ tạo từ mô tả gốc |
| `provider` | string/null | không | Giảng viên hoặc đơn vị cung cấp | Chỉ lấy từ nguồn |
| `language` | string/null | không | Mã ISO 639-1 nếu được ánh xạ rõ ràng | Không đoán |
| `level` | string/null | không | Beginner / Intermediate / Advanced / All Levels / Unknown | Không đoán; thiếu thì để null |
| `skills` | array/null | không | Danh sách kỹ năng ánh xạ theo taxonomy | Dữ liệu dẫn xuất; giữ lại dữ liệu gốc |
| `direct_skills` | array/null | không | Kỹ năng được nguồn cung cấp trực tiếp | Không suy diễn |
| `inferred_skills` | array/null | không | Ứng viên kỹ năng từ quy tắc taxonomy đã cấu hình | Phải có độ tin cậy và cờ rà soát |
| `prerequisites` | string/array/null | không | Điều kiện tiên quyết được nguồn nêu rõ | Không đoán |
| `duration_minutes` | integer/null | không | Thời lượng quy đổi sang phút khi đơn vị nguồn rõ ràng | Quy đổi xác định |
| `price_amount` | number/null | không | Giá trị số theo tiền tệ gốc | Không quy đổi; thiếu thì null, không phải 0 |
| `price_currency` | string/null | không | Mã tiền tệ ISO nếu nguồn cung cấp | Không đoán |
| `image_url` | string/null | không | URL ảnh khóa học | Trường từ nguồn |
| `rating` | number/null | không | Điểm đánh giá từ nguồn | Chỉ phân tích kiểu số |
| `rating_count` | integer/null | không | Số lượt đánh giá | Chỉ phân tích kiểu số |
| `student_count` | integer/null | không | Số học viên đăng ký | Chỉ phân tích kiểu số |
| `category`, `subcategory` | string/null | không | Nhãn phân loại từ nguồn | Chỉ lấy từ nguồn |
| `lecture_count`, `section_count` | integer/null | không | Số bài giảng và chương | Chỉ phân tích kiểu số |
| `last_updated` | string/null | không | Ngày cập nhật do nguồn cung cấp | Không đoán |
| `offer_type` | enum | có | `EXTERNAL_REFERENCE` hoặc `INTERNAL` | Phân loại nguồn rõ ràng |
| `crawled_at` | ISO-8601 string/null | không | Thời điểm crawl gốc nếu có | Không tạo lại khi nhập dữ liệu |
| `quality_status` | enum | có | `approved_candidate`, `needs_review`, `rejected` | Quy tắc chất lượng |
| `quality_flags` | array | có | Các cờ thiếu, sai hoặc cần rà soát | Quy tắc chất lượng |
| `duplicate_status` | enum | có | `unique`, `exact_duplicate`, `near_duplicate` | Bước phát hiện trùng lặp |
| `dataset_version` | string/null | không | Phiên bản dataset phát hành | Quy trình release |
| `source_metadata` | object | có | Các cột nguồn khác, được giữ lại không mất dữ liệu | Giá trị nguyên bản |

## Ghi chú ánh xạ dữ liệu cũ

Trường `course_id` trong CSV cũ là slug URL và được ánh xạ sang `source_course_id`. `course_id` chuẩn mới có tiền tố `udemy:`. Các dòng cũ không có mô tả hoặc kỹ năng; những trường đó giữ giá trị null và tạo cờ cần rà soát. Giá trị CSV cũ là chuỗi; JSON chuẩn hóa dùng kiểu số khi có thể phân tích rõ ràng.

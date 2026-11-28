# Crawler và pipeline dữ liệu khóa học Udemy

Dự án thu thập metadata khóa học Udemy ra CSV và cung cấp pipeline ngoại tuyến để kiểm toán, chuẩn hóa, rà soát chất lượng, tạo bản phát hành và kiểm tra nạp dữ liệu.

## Quyền thu thập và dữ liệu hiện có

CSV cũ `data/udemy_courses.csv` có 3.001 dòng. Cấu hình hiện đặt giới hạn tổng ở 3.001 và `source_authorized: false`. Vì vậy crawler chưa gửi request; lệnh crawl thật sẽ bị chặn cho đến khi có văn bản cho phép hoặc API được phê duyệt. Robots.txt không thay thế sự cho phép đó.

Trước khi crawl, tạo cấu hình cá nhân từ mẫu và kiểm tra không truy cập mạng:

```powershell
Copy-Item config.udemy.example.yaml config.udemy.yaml
python data/crawl.py --config config.udemy.yaml --max-pages 1 --max-courses 10 --dry-run
```

Dry-run cần hiển thị `network_requests: 0`. Không bật `source_authorized` khi chưa có căn cứ cho phép.

## Crawl tối đa một số lượng khóa học

`--max-courses N` đặt số khóa học mới tối đa trong lần chạy; số thực tế có thể thấp hơn nếu sitemap không còn URL mới hoặc một số trang lỗi. Dùng tệp đầu ra mới để không ghi đè CSV 3.001 dòng hiện tại.

Ví dụ lấy tối đa 100 khóa học sau khi nguồn đã được cho phép:

```powershell
Copy-Item config.udemy.example.yaml config.udemy.100.yaml
notepad config.udemy.100.yaml
```

Trong `config.udemy.100.yaml`, đặt các giá trị sau:

```yaml
output_file: "data/udemy_courses_100.csv"
max_courses: 100
max_total_courses: 100
append: false
source_authorized: true
authorization_reference: "MA-VAN-BAN-HOAC-API"
```

Thay `authorization_reference` bằng mã hoặc liên kết văn bản cho phép thực tế, rồi chạy:

```powershell
python data/crawl.py --config config.udemy.100.yaml --max-courses 100
```

`append: false` phù hợp với tên tệp đầu ra mới. Nếu tệp đó đã tồn tại, hãy chọn tên khác hoặc sao lưu trước vì crawler có thể ghi lại tệp.

## Crawl toàn bộ khóa học được sitemap phát hiện

Với `crawl_mode: "sitemap"`, `--max-courses 0` và `max_total_courses: 0` bỏ giới hạn số lượng; crawler đi qua các URL khóa học tìm thấy trong sitemap. Sitemap có thể không liệt kê toàn bộ catalog Udemy. Crawl toàn bộ có thể mất nhiều thời gian và tạo tệp lớn.

Tạo cấu hình riêng để giữ nguyên CSV cũ:

```powershell
Copy-Item config.udemy.example.yaml config.udemy.all.yaml
notepad config.udemy.all.yaml
```

Trong `config.udemy.all.yaml`, đặt:

```yaml
output_file: "data/udemy_courses_all.csv"
max_courses: 0
max_total_courses: 0
append: false
source_authorized: true
authorization_reference: "MA-VAN-BAN-HOAC-API"
```

Sau khi có quyền thu thập, chạy:

```powershell
python data/crawl.py --config config.udemy.all.yaml --max-courses 0
```

Giới hạn `--max-pages` chỉ áp dụng cho `crawl_mode: "listing"`; chế độ sitemap dùng `--max-courses` để giới hạn số khóa học.

## Cài đặt

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Pipeline ngoại tuyến

Chạy các lệnh sau từ thư mục gốc dự án. Dùng mã lô được in ra từ `ingest` cho các bước tiếp theo:

```powershell
python pipeline_cli.py audit
python pipeline_cli.py ingest
python pipeline_cli.py transform --batch-id <ma-lo>
python pipeline_cli.py release --batch-id <ma-lo> --version 0.1.0
python pipeline_cli.py db-load --version 0.1.0
```

Dữ liệu cũ thiếu mô tả, kỹ năng, cấp độ và nhiều trường khác. Các bản ghi thiếu thông tin được đánh dấu `needs_review`, không tự động làm giàu hay đưa vào bản phát hành. Vì vậy release hiện tại dự kiến rỗng cho đến khi dữ liệu bắt buộc được rà soát và bổ sung từ nguồn được phép. Chưa có taxonomy, schema cơ sở dữ liệu bên ngoài, endpoint hay thông tin xác thực; bước nạp database chỉ chạy mô phỏng.

Dữ liệu khóa học mẫu do dự án tự tạo nằm riêng trong `data/internal/courses.json`. Danh mục nguồn và từ điển trường dữ liệu nằm trong `data/sources.md` và `data/schema_dictionary.md`.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

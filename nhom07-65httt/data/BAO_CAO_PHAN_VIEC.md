# Báo cáo phần việc: Crawler và pipeline dữ liệu khóa học Udemy

## 1. Mục tiêu

Xây dựng công cụ thu thập metadata khóa học Udemy và quy trình xử lý dataset có thể kiểm tra lại. Crawler không lấy mô tả khóa học. Dữ liệu thiếu được để trống, không tự tạo giá, cấp độ, kỹ năng hoặc thông tin khác.

## 2. Phần việc đã thực hiện

### Crawler Udemy

- Tạo crawler Python đọc URL khóa học từ sitemap hoặc trang danh sách Udemy.
- Thu thập các trường: mã khóa học, tiêu đề, URL, tiêu đề phụ, giảng viên, danh mục, điểm đánh giá và số lượt đánh giá, số học viên, giá, tiền tệ, cấp độ, ngôn ngữ, phụ đề, ngày cập nhật, thời lượng, số bài giảng/chương, chứng chỉ, URL ảnh, yêu cầu, mục tiêu học tập và đối tượng học.
- Xuất CSV UTF-8 BOM; hỗ trợ giới hạn số khóa mới, giới hạn tổng dòng, nối thêm dữ liệu và bỏ qua URL đã có.
- Kiểm tra `robots.txt`, đặt độ trễ giữa request và thử lại khi lỗi.
- Đặt `source_authorized: false` mặc định. Crawl thật bị khóa nếu chưa có văn bản cho phép hoặc API được phê duyệt. Dry-run dùng để xem cấu hình mà không gửi request.

### Pipeline xử lý dataset

- Kiểm toán CSV hiện có và ghi báo cáo về số dòng, cột, dữ liệu thiếu, URL/mã trùng và tiêu đề lặp.
- Nhập CSV thành lô dữ liệu gốc có manifest và mã SHA-256, không sửa CSV nguồn.
- Chuẩn hóa URL, văn bản và trường số; ánh xạ kỹ năng chỉ khi có taxonomy cấu hình.
- Gắn cờ bản ghi trùng chính xác/gần trùng và lỗi chất lượng để rà soát; không tự xóa bản ghi gần trùng.
- Chỉ đưa bản ghi đạt điều kiện vào release. Tích hợp database hiện ở chế độ dry-run vì chưa có schema, endpoint và thông tin xác thực.

### Tổ chức dữ liệu và tài liệu

- Viết README tiếng Việt hướng dẫn crawl tối đa N khóa hoặc các khóa tìm được qua sitemap, đồng thời nêu cách dùng file đầu ra riêng để giữ nguyên CSV cũ.
- Bổ sung danh mục nguồn, từ điển schema và báo cáo chất lượng bằng tiếng Việt.
- Dọn các artifact pipeline có thể tạo lại khỏi thư mục dữ liệu trên branch PR; giữ CSV Udemy, cấu hình, dữ liệu mẫu và tài liệu cần thiết. Thêm quy tắc `.gitignore` cho các thư mục sinh tự động.

## 3. Kết quả kiểm toán dữ liệu hiện có

CSV nguồn có **3.001 dòng và 27 cột**. Báo cáo kiểm toán ghi nhận:

| Chỉ số | Kết quả |
|---|---:|
| URL trùng | 0 |
| Mã nguồn trùng | 0 |
| Nhóm tiêu đề lặp | 15 nhóm, thừa 16 dòng |
| Tiêu đề có HTML entity | 326 |
| Có điểm đánh giá | 1.623 dòng |
| Có số lượt đánh giá | 2.997 dòng |
| Có thời lượng/số bài/số chương | 2.009 dòng |

Trong bước kiểm tra chất lượng, 3.001 bản ghi được đưa vào staging; 0 bản ghi đủ điều kiện duyệt. Tất cả đang ở trạng thái `needs_review` vì CSV cũ thiếu mô tả, kỹ năng, cấp độ và các trường khác. Bộ phát hành hiện rỗng; đây là kết quả đúng theo quy tắc chất lượng, không phải lỗi xuất dữ liệu.

Hệ thống phát hiện 207 bản ghi gần trùng thuộc 162 cặp để rà soát. Các bản ghi vẫn được giữ nguyên, không tự động gộp hoặc xóa.

## 4. Kiểm tra đã thực hiện

- Chạy 14 unit test của pipeline; tất cả đạt.
- Chạy `--help` cho crawler và pipeline để kiểm tra hướng dẫn tiếng Việt trên Windows.
- Chạy dry-run: kết quả `authorized: false`, `network_requests: 0`.
- Chạy kiểm toán CSV: 3.001 dòng, không có URL trùng, mã trùng hoặc dòng sai cấu trúc.

## 5. Giới hạn và hướng tiếp tục

- Chưa crawl bổ sung vì cấu hình nguồn đang khóa và chưa có văn bản cho phép/API được phê duyệt.
- Sitemap có thể không liệt kê mọi khóa học Udemy; “crawl toàn bộ” chỉ có nghĩa là lấy hết URL được sitemap phát hiện.
- Dataset hiện có thiếu nhiều trường; muốn tạo release không rỗng cần bổ sung dữ liệu từ nguồn được phép rồi rà soát các bản ghi `needs_review`.
- Muốn nạp database cần schema, endpoint và thông tin xác thực được cung cấp rõ ràng.

## 6. Lệnh chạy

Kiểm tra cấu hình crawler không gửi request mạng:

```powershell
Copy-Item config.udemy.example.yaml config.udemy.yaml
python data/crawl.py --config config.udemy.yaml --max-pages 1 --max-courses 10 --dry-run
```

Chạy pipeline ngoại tuyến từ thư mục gốc dự án:

```powershell
python pipeline_cli.py audit
python pipeline_cli.py ingest
python pipeline_cli.py transform --batch-id <ma-lo>
python pipeline_cli.py release --batch-id <ma-lo> --version 0.1.0
python pipeline_cli.py db-load --version 0.1.0
```

## 7. Thay đổi trên GitHub

Các thay đổi crawler, tài liệu tiếng Việt và dọn artifact đã được chuẩn bị trên branch PR hướng vào `dev`. Việc merge PR do người có quyền trên repo thực hiện.

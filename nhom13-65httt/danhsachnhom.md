# Danh sách nhóm và phân chia nhiệm vụ

**Đề tài:** Hệ thống Quản lý Tài chính Cá nhân Thông minh tích hợp thu thập dữ liệu tự động, AI phân loại và dự báo, trực quan hóa bằng Apache Superset.

## Thành viên và nhiệm vụ

| STT | Thành viên | Vai trò | Nhiệm vụ chính | Sản phẩm phụ trách |
| :-: | :--- | :--- | :--- | :--- |
| 1 | Thiều Quang Gia Bảo | Nhóm trưởng | Điều phối công việc và quản lý nhánh GitHub của nhóm; thiết kế kiến trúc tổng thể, mô hình dữ liệu Star Schema trên PostgreSQL và môi trường Docker Compose; tích hợp các thành phần, tổng hợp báo cáo cuối kỳ. | Sơ đồ kiến trúc và ERD, cấu hình PostgreSQL/FastAPI/Superset, mã nguồn đã tích hợp và báo cáo tổng kết. |
| 2 | Trần Minh Giang | Thành viên | Xây dựng luồng thu thập giao dịch từ email thông báo biến động số dư và tệp sao kê CSV/PDF; viết bộ phân tích dữ liệu đầu vào và thiết lập lịch chạy pipeline. | Module đọc email và sao kê, dữ liệu giao dịch được trích xuất, cấu hình chạy tự động. |
| 3 | Nguyễn Thu Giang | Thành viên | Xây dựng luồng nhận ảnh biên lai qua Telegram Bot và OCR; chuẩn hóa ngày giờ, số tiền, nội dung giao dịch; xử lý giao dịch trùng lặp trước khi nạp vào PostgreSQL. | Module OCR và làm sạch dữ liệu, quy tắc khử trùng lặp cùng nhật ký xử lý, dữ liệu sạch trong kho dữ liệu. |
| 4 | Trương Quốc Thái | Thành viên | Xây dựng các chức năng AI: phân loại danh mục giao dịch từ mô tả tiếng Việt, phát hiện giao dịch bất thường và dự báo dòng tiền; cung cấp kết quả qua API để tích hợp. | Module AI và API, kết quả phân loại/dự báo/cảnh báo, báo cáo đánh giá độ chính xác và sai số mô hình. |
| 5 | Nguyễn Thị Khanh | Thành viên | Kết nối PostgreSQL với Apache Superset; định nghĩa các chỉ số và bộ dữ liệu phân tích; xây dựng dashboard tổng quan dòng tiền, hành vi chi tiêu, dự báo và cảnh báo; chuẩn bị nội dung trình bày và demo. | Ba dashboard Superset, cấu hình cảnh báo/báo cáo, slide và kịch bản demo. |

## Phối hợp và nghiệm thu

- Các thành viên thống nhất định dạng giao dịch và các trường dữ liệu trước khi ghép module thu thập, xử lý, AI và Superset. Mỗi người cập nhật mã nguồn, tài liệu và kết quả kiểm thử thuộc phần mình phụ trách lên nhánh làm việc của nhóm.
- Cả nhóm kiểm thử luồng từ giao dịch giả lập đến dashboard, đối chiếu kết quả với năm câu hỏi nghiệp vụ trong đề cương và sửa lỗi tích hợp. Nhóm trưởng tổng hợp kết quả, lịch sử đóng góp trên GitHub và báo cáo cuối kỳ.

# Kế hoạch thực hiện và đánh giá

Kế hoạch dự kiến 8 tuần, tính từ ngày bắt đầu được giảng viên chấp thuận. Đây là phân rã công việc từ đề cương, chưa phải nhật ký hoàn thành. Phân công theo tên tại [danhsachnhom.md](../danhsachnhom.md) cần nhóm xác nhận.

## 1. Các mốc thực hiện

| Tuần | Công việc | Đầu ra và điều kiện chuyển bước |
| :-: | :--- | :--- |
| 1 | Khảo sát 30 khách dự kiến, phỏng vấn 3–5 chủ quán, chốt khu vực và nhu cầu | Báo cáo nhu cầu, câu hỏi nghiên cứu, phạm vi và chức năng ưu tiên; ghi rõ dữ liệu nào là quan sát, dữ liệu nào là giả thuyết |
| 2 | Kiểm tra và làm sạch ViFoodRec; chuẩn hóa món; thiết kế ERD, use case, giao diện và ca kiểm thử | Từ điển dữ liệu, khoảng 100 món chuẩn, kế hoạch 20 quán/200 mục món; bản thiết kế và quy tắc dữ liệu |
| 3 | Xác thực, phân quyền, quản lý quán và thực đơn | API ba vai trò, nhập được dữ liệu hợp lệ, chặn truy cập ngoài quyền |
| 4 | Giao diện, vị trí, giỏ hàng, đơn hàng và trạng thái | Chạy được đặt–xác nhận–hoàn tất và hủy/từ chối; gửi lặp không tạo đơn trùng |
| 5 | Hồ sơ khẩu vị, gợi ý theo nội dung, lọc, xếp hạng, đa dạng và giải thích | Có Top 5 và đối chứng trên cùng tập món đủ điều kiện; tham số được chọn bằng tập phát triển |
| 6 | Sự kiện hành vi, ETL, bảng phân tích, dashboard và tích hợp | Đối soát số liệu nguồn; cố định mô hình/phiên bản trước thử nghiệm đánh giá |
| 7 | Đánh giá với người dùng, kiểm thử chức năng và hiệu năng, sửa lỗi | Báo cáo 150 tình huống dự kiến, so sánh đối chứng và ghi nhận các mục chưa đạt |
| 8 | Kiểm thử lại, tài liệu cài đặt, báo cáo, slide và demo | Bộ bàn giao tái chạy được; nguồn dữ liệu rõ ràng và kết quả thực tế được báo cáo |

Phụ thuộc chính: dữ liệu món đủ chất lượng trước khi chốt mô hình; ghi sự kiện trước khi đối soát BI; cố định mô hình trước thử nghiệm người dùng. Chức năng tự nấu, chatbot và điều phối tài xế chỉ xem xét sau khi phần cốt lõi ổn định.

## 2. Tiêu chí đánh giá dự kiến

| Nội dung | Cách đo | Mục tiêu |
| :--- | :--- | :--- |
| Chất lượng dữ liệu gợi ý | Kiểm tra trường bắt buộc, nhãn, tọa độ và trạng thái | 100% món đưa vào gợi ý có trường bắt buộc hợp lệ; thiếu thông tin bị chặn theo điều kiện |
| Mức phù hợp | Precision@5 trung bình trên các trường hợp đủ 5 ứng viên | Ít nhất 0,60; cao hơn đối chứng ít nhất 0,05 điểm tuyệt đối, tức 5 điểm phần trăm |
| Ràng buộc | 100 ca kiểm tra nguyên liệu, phạm vi phục vụ, trạng thái món/quán | Không vi phạm trong bộ ca thử |
| Giao dịch | 30 ca cốt lõi, gồm tạo/hủy/từ chối, gửi lặp, sai trạng thái và phân quyền | Toàn bộ ca cốt lõi đạt |
| Trải nghiệm | Tỷ lệ hoàn thành nhiệm vụ và hài lòng thang 1–5 | Ít nhất 90% hoàn thành; hài lòng trung bình ít nhất 4/5 |
| Hiệu năng | 100 yêu cầu sau khởi động, 10 người dùng đồng thời; ghi cấu hình máy | p95 phản hồi gợi ý dưới 2 giây, không tính API bản đồ ngoài |
| BI | Đối soát 100 đơn kiểm thử và các sự kiện liên quan | Số đơn, trạng thái và lượt hiển thị khớp 100% với nguồn sau ETL |

Precision@5 bằng số món được đánh giá phù hợp trong Top 5 chia 5. Trường hợp ít hơn 5 ứng viên báo cáo riêng Precision@k và tỷ lệ thiếu ứng viên. Báo cáo riêng người mới và người đã có lịch sử.

## 3. Thiết kế thử nghiệm

Dự kiến 30 người, mỗi người đánh giá 5 tình huống, tổng 150 trường hợp. Cá nhân hóa và đối chứng dùng cùng tập món đủ điều kiện; ẩn tên thuật toán, xáo trộn hiển thị và loại trùng trước khi chấm. Độ phổ biến của đối chứng chỉ lấy từ giai đoạn trước thử nghiệm; nếu chưa có lịch sử, dùng thứ tự khám phá cố định và ghi rõ.

Không đưa phản hồi kiểm tra vào huấn luyện/chọn tham số rồi dùng lại để tuyên bố kết quả độc lập. Tính khoảng tin cậy theo người dùng vì mỗi người đánh giá nhiều trường hợp. Nếu không đạt mục tiêu, ghi số đo thực tế và nguyên nhân; không thay số liệu bằng mục tiêu.

## 4. Sản phẩm bàn giao

- Báo cáo phân tích thiết kế và bản mẫu website ba vai trò.
- Cơ sở dữ liệu, từ điển dữ liệu và hướng dẫn tạo dữ liệu.
- Bộ xử lý đặc trưng, mô hình gợi ý và đối chứng.
- Dashboard BI và định nghĩa KPI có thể đối soát.
- Bộ ca kiểm thử, kết quả đánh giá, hướng dẫn cài đặt và kịch bản demo.


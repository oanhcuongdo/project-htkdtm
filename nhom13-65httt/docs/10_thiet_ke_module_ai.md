# THIẾT KẾ MODULE AI – NHÓM 13

## 1. Thông tin chung

- Đề tài: Hệ thống Quản lý Tài chính Cá nhân Thông minh
- Thành viên phụ trách: Trương Quốc Thái
- Học phần: Hệ thống Kinh doanh Thông minh
- Trạng thái: Đặc tả thiết kế, chưa xác nhận triển khai

## 2. Mục tiêu

Xây dựng module AI hỗ trợ người dùng quản lý tài chính cá nhân thông qua:

1. Tự động phân loại giao dịch.
2. Phát hiện giao dịch chi tiêu bất thường.
3. Dự báo dòng tiền trong kỳ tiếp theo.
4. Cung cấp kết quả cho API và Apache Superset.

## 3. Dữ liệu đầu vào

Dữ liệu giao dịch được các thành viên phụ trách thu thập và làm sạch, dự kiến gồm:

| Trường           | Mô tả                       |
| ---------------- | --------------------------- |
| transaction_id   | Mã giao dịch                |
| transaction_date | Ngày giao dịch              |
| amount           | Số tiền                     |
| description      | Nội dung giao dịch          |
| transaction_type | Thu hoặc chi                |
| category         | Danh mục giao dịch (nếu có) |

Nguồn dữ liệu dự kiến:

- Sao kê CSV/PDF đã được xử lý.
- Thông báo giao dịch từ email.
- Dữ liệu biên lai đã được OCR.
- Dữ liệu giao dịch mẫu phục vụ kiểm thử.

Không sử dụng thông tin tài chính thật nếu chưa được cho phép và bảo vệ phù hợp.

## 4. Các chức năng AI dự kiến

### 4.1. Phân loại giao dịch

Mục tiêu: Phân loại nội dung giao dịch vào các nhóm như ăn uống, đi lại, mua sắm, hóa đơn và học tập.

Phương pháp đề xuất:

- Baseline: Quy tắc từ khóa.
- Mô hình thử nghiệm: TF-IDF kết hợp Logistic Regression.

Đánh giá: Precision, Recall, F1-score.

### 4.2. Phát hiện bất thường

Mục tiêu: Nhận diện những giao dịch có số tiền hoặc tần suất khác biệt so với lịch sử chi tiêu.

Phương pháp đề xuất:

- Baseline: IQR hoặc ngưỡng thống kê.
- Mô hình thử nghiệm: Isolation Forest.

Đánh giá: Kiểm tra các giao dịch bất thường được gắn nhãn hoặc bộ tình huống kiểm thử.

Lưu ý: Cảnh báo bất thường không đồng nghĩa giao dịch gian lận.

### 4.3. Dự báo dòng tiền

Mục tiêu: Ước tính tổng thu, chi hoặc số dư dự kiến cho kỳ tiếp theo.

Phương pháp đề xuất:

- Baseline: Trung bình trượt.
- Thử nghiệm: Mô hình hồi quy hoặc chuỗi thời gian nếu dữ liệu đủ điều kiện.

Đánh giá: MAE, RMSE.

Không tuyên bố mô hình dự báo chính xác khi chưa có dữ liệu kiểm thử.

## 5. Tích hợp API

Các endpoint dự kiến:

- POST /api/ai/classify
- POST /api/ai/anomaly
- GET /api/ai/forecast

Đầu ra cần có cấu trúc rõ ràng, xử lý lỗi và không trả về dữ liệu nhạy cảm không cần thiết.

Tên endpoint và schema sẽ thống nhất với nhóm backend trước khi triển khai.

## 6. Tích hợp BI

Kết quả phân tích AI được lưu vào cơ sở dữ liệu để Apache Superset hiển thị:

- Chi tiêu theo danh mục.
- Số lượng và giá trị giao dịch bất thường.
- Biểu đồ so sánh thu/chi thực tế với dự báo.

## 7. Kế hoạch thực hiện

1. Thống nhất schema dữ liệu với nhóm backend.
2. Chuẩn bị dữ liệu và bộ kiểm thử.
3. Xây dựng mô hình baseline.
4. Thử nghiệm mô hình AI và đánh giá.
5. Xây dựng API và kiểm thử tích hợp.
6. Cung cấp đầu ra cho dashboard BI.

## 8. Kết quả cần bàn giao

- Mã nguồn module AI.
- Các API đã được kiểm thử.
- Dữ liệu mẫu và hướng dẫn chạy.
- Báo cáo chỉ số đánh giá.
- Minh chứng tích hợp với hệ thống.

Các mục trên là kế hoạch và tiêu chí nghiệm thu, chưa phải kết quả đã hoàn thành.

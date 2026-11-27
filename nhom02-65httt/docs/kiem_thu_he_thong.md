# Kế Hoạch Kiểm Thử Hệ Thống

Tài liệu này mô tả tiêu chí nghiệm thu ban đầu cho hệ thống ERP Smart Pricing đa kênh.

## 1. Kiểm thử chức năng ERP

- Thêm, sửa, tìm kiếm và phân trang danh mục sản phẩm.
- Kiểm tra khóa ngoại khi tạo bản ghi giá vốn, tồn kho hoặc kênh bán.
- Xác nhận dữ liệu bắt buộc không được để trống.
- Kiểm tra phân quyền truy cập của vai trò quản trị và nhân viên.

## 2. Kiểm thử Rule Engine và AI

- Tính đúng giá sàn Pmin theo cấu trúc chi phí và margin tối thiểu.
- Cảnh báo hoặc khóa các đề xuất có giá thấp hơn Pmin.
- Kiểm tra mô hình baseline khi dự đoán đầu vào ngoài tập huấn luyện.
- Ghi nhận MAE và RMSE trên tập kiểm thử mô hình XGBoost.
- Đảm bảo cùng một SKU cho ra kết quả nhất quán giữa các lần chạy.

## 3. Kiểm thử quy trình phê duyệt

- Người đề xuất không được tự phê duyệt theo chính sách RBAC.
- Giá đã phê duyệt phải được ghi lịch sử thay đổi.
- Giá bị từ chối phải được lưu lý do và hiển thị cho người đề xuất.
- Hệ thống không áp dụng giá khi adapter kênh bán trả lỗi.

## 4. Kiểm thử dữ liệu và BI

- SKU của dữ liệu ERP phải khớp với dữ liệu ngoài trên crawler/API.
- Giá trị doanh thu, tồn kho và doanh số phải đồng nhất sau khi làm sạch.
- Dashboard hiển thị đúng bộ lọc theo thời gian, kênh và danh mục.
- Kiểm tra toàn vẹn dữ liệu sau khi làm mới nguồn Superset.

## 5. Tiêu chí đạt

1. Không có lỗi nghiêm trọng trong luồng tạo dữ liệu, đề xuất và phê duyệt giá.
2. API trả mã trạng thái và thông báo nhất quán.
3. Kết quả kiểm thử AI được lưu kèm MAE, RMSE và tập dữ liệu đánh giá.
4. Mọi thao tác thay đổi giá quan trọng có audit log.

# Frontend Vị Việt

Thư mục dành cho giao diện web khi bắt đầu triển khai. Hiện chưa có ứng dụng hoặc lệnh khởi chạy.

## Các màn hình dự kiến

| Vai trò | Nhóm màn hình |
| :--- | :--- |
| Khách hàng | Đăng nhập, khai báo khẩu vị, chọn vị trí, tìm món/quán, danh sách gợi ý có lý do, thực đơn, giỏ hàng, tạo và theo dõi đơn, phản hồi |
| Chủ quán | Hồ sơ quán, giờ mở/phạm vi phục vụ, thực đơn/nguyên liệu/trạng thái, danh sách đơn, cập nhật trạng thái và thống kê quán |
| Quản trị viên | Duyệt quán, danh mục món chuẩn và nhãn, tài khoản, kiểm tra dữ liệu và dashboard |

## Các tình huống phải thể hiện

- Người dùng có thể nhập địa chỉ khi không cấp quyền vị trí.
- Quán xuất hiện trên bản đồ nhưng chưa tham gia hệ thống không có thao tác đặt món qua Vị Việt.
- Hiển thị lý do gợi ý, danh sách ngắn khi ít ứng viên và thông báo chưa cá nhân hóa khi khách bỏ qua khai báo.
- Thông báo khi món hết bán, ngoài phạm vi phục vụ, đơn bị từ chối hoặc trạng thái thay đổi.
- Khóa thao tác gửi lặp trên giao diện kết hợp kiểm soát ở backend; không dựa riêng vào việc ẩn nút để phân quyền.

## Công nghệ và đầu ra khi lập trình

Dự kiến React. Cần bổ sung `package.json`, cấu hình mẫu, danh sách biến môi trường, lệnh cài phụ thuộc/chạy/biên dịch đã kiểm tra và tài liệu tích hợp API. Không đưa khóa bí mật vào mã nguồn trình duyệt.

Xem [README nhóm](../../README.md) và [kế hoạch](../../docs/KE_HOACH_THUC_HIEN.md).


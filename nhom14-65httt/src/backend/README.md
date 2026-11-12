# Backend Vị Việt

Thư mục dành cho mã nguồn backend khi bắt đầu triển khai. Hiện chỉ có tài liệu định hướng, chưa có API hay ứng dụng chạy được.

## Phạm vi dự kiến

- Xác thực và phân quyền khách hàng, chủ quán, quản trị viên.
- Hồ sơ quán, giờ mở cửa, phạm vi phục vụ, thực đơn, nguyên liệu và trạng thái món.
- Giỏ hàng, kiểm tra khả dụng khi đặt, xử lý đơn và lịch sử trạng thái.
- Hồ sơ khẩu vị, lọc ứng viên, gợi ý theo nội dung và giải thích bằng đặc trưng thực.
- Ghi nhận yêu cầu gợi ý, lượt hiển thị, nhấp, đặt và phản hồi; cấp dữ liệu cho ETL/BI.

## Quy tắc nghiệp vụ cần giữ

- Mỗi đơn thuộc một quán; kiểm tra lại giá và khả dụng ở thời điểm đặt.
- Yêu cầu gửi lặp không tạo thêm đơn; chỉ cho phép chuyển trạng thái hợp lệ.
- Chủ quán chỉ xử lý dữ liệu và đơn thuộc quán mình.
- Phải lọc điều kiện bắt buộc trước xếp hạng; không suy diễn nguyên liệu còn thiếu hoặc tự nới điều kiện để đủ 5 gợi ý.
- Phản hồi đánh giá sau đơn hoàn tất; không coi dữ liệu người dùng ViFoodRec là tài khoản khách hàng website.

## Công nghệ và đầu ra khi lập trình

Dự kiến FastAPI/Python, PostgreSQL và scikit-learn. Khi triển khai cần bổ sung mã nguồn, dependency manifest, cấu hình mẫu không có khóa bí mật, tài liệu API, lệnh chạy và hướng dẫn kiểm tra. Phiên bản công nghệ sẽ được chốt khi thực hiện.

Xem [README nhóm](../../README.md), [nguồn dữ liệu](../../docs/NGUON_DU_LIEU.md) và [kế hoạch](../../docs/KE_HOACH_THUC_HIEN.md).


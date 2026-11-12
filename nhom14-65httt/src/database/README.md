# Cơ sở dữ liệu Vị Việt

Thư mục dành cho thiết kế chi tiết, migration, dữ liệu mẫu và mô hình phân tích khi triển khai. Hiện chưa có script SQL hoặc cơ sở dữ liệu chạy được. Hệ quản trị dự kiến là PostgreSQL.

## Dữ liệu giao dịch dự kiến

| Nhóm | Thực thể chính |
| :--- | :--- |
| Tài khoản và khẩu vị | User, Preference |
| Quán và người quản lý | Restaurant, RestaurantMembership |
| Món và nguyên liệu | CanonicalDish, MenuItem, Ingredient, MenuItemIngredient |
| Giao dịch | Order, OrderItem, OrderStatusHistory |
| Gợi ý và hành vi | RecommendationRequest, RecommendationImpression, InteractionEvent |

`CanonicalDish` là món chuẩn; `MenuItem` là món bán cụ thể tại một quán. Lưu thông tin món tại thời điểm đặt để dữ liệu đơn không thay đổi theo lần cập nhật thực đơn sau đó. Sự kiện cần mã duy nhất và thời điểm để chống đếm trùng, đối soát và hạn chế sử dụng dữ liệu tương lai.

## Dữ liệu phân tích dự kiến

| Bảng Fact | Mức chi tiết một dòng | Số đo hoặc thuộc tính chính |
| :--- | :--- | :--- |
| Fact_OrderItem | Một mục món trong một đơn | Số lượng, mã đơn, cờ hoàn tất, liên kết quy thuộc gợi ý khi có |
| Fact_RecImpression | Một mục món hiển thị trong một yêu cầu gợi ý | Vị trí xếp hạng, cờ nhấp/đặt, phiên bản thuật toán |
| Fact_Session | Một phiên truy cập đã kết thúc | Cờ nhấp gợi ý, cờ có đơn, thời gian chọn món |

Các chiều dùng chung: ngày, người dùng đã ẩn danh, quán và món; có thể bổ sung khu vực, thuật toán khi cần. Đếm đơn bằng `OrderID` duy nhất, không lấy số dòng món làm số đơn.

## Định nghĩa KPI cần thống nhất trước triển khai

- CTR gợi ý: số lượt hiển thị có ít nhất một lần nhấp chia tổng lượt hiển thị hợp lệ.
- Tỷ lệ phiên đặt từ gợi ý: số phiên có đơn hợp lệ được quy thuộc gợi ý chia số phiên có hiển thị gợi ý.
- Quy thuộc: lần nhấp cùng món bán gần nhất trước đặt trong 30 phút, cùng phiên; loại đơn hủy/từ chối, chờ cửa sổ quan sát kết thúc trước khi chốt.
- Theo dõi riêng tỷ lệ đơn hoàn tất, lý do từ chối và món được xem nhiều nhưng ít được đặt; các chênh lệch quan sát không tự chứng minh quan hệ nhân quả.

## Đầu ra cần bổ sung

- ERD, ràng buộc và từ điển dữ liệu đã thống nhất.
- Migration có thứ tự và hướng dẫn tạo schema.
- Seed có phân biệt dữ liệu mô phỏng và dữ liệu thật.
- Quy trình nhập dữ liệu, ánh xạ nguồn, báo cáo làm sạch và cách chạy ETL.
- Truy vấn hoặc mô hình phục vụ BI, quy tắc quy thuộc và đối soát.

Không đưa thông tin giao hàng chi tiết vào dashboard công khai. Xem [nguồn dữ liệu](../../docs/NGUON_DU_LIEU.md), [kế hoạch đánh giá](../../docs/KE_HOACH_THUC_HIEN.md) và [README nhóm](../../README.md).


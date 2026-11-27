# Cơ sở dữ liệu Vị Việt

Thư mục dành cho tài liệu dữ liệu, seed, ánh xạ nguồn, truy vấn BI và tài liệu Power BI. Migration được quản lý duy nhất tại `src/backend/alembic/versions/`, không đặt ở đây. Đã có [revision 001](../backend/alembic/versions/001_initial_schema.py) tạo 15 bảng OLTP của F.5; chưa có seed hoặc SQL BI. Hệ quản trị chính là PostgreSQL; migration đã thử trên SQLite và sinh SQL PostgreSQL, chưa chạy PostgreSQL thực tế.

## Dữ liệu giao dịch hiện có

[ERD](../../docs/ERD.md) mô tả đủ 15 bảng và 24 khóa ngoại của revision `001`. [Từ điển dữ liệu](../../docs/TU_DIEN_DU_LIEU.md) ghi từng cột, kiểu, NULL, mặc định, khóa, CHECK, index và những kiểm tra thuộc ORM/service.

| Nhóm | Thực thể chính |
| :--- | :--- |
| Tài khoản và khẩu vị | User, Preference |
| Quán và người quản lý | Restaurant, RestaurantMembership |
| Món và nguyên liệu | CanonicalDish, MenuItem, Ingredient, MenuItemIngredient |
| Giao dịch | Order, OrderItem, OrderStatusHistory |
| Đánh giá món đã mua | Review |
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

- ERD/từ điển dữ liệu F.7 đã có theo revision `001`; cần cập nhật cùng mỗi revision mở rộng.
- Migration hiện có: `001_initial_schema.py` trong backend; hướng dẫn tạo schema tại [hướng dẫn cài đặt](../../docs/HUONG_DAN_CAI_DAT.md). Các phần mở rộng sẽ có revision kế tiếp.
- Seed có phân biệt dữ liệu mô phỏng và dữ liệu thật.
- Quy trình nhập dữ liệu, ánh xạ nguồn, báo cáo làm sạch và cách chạy ETL.
- Truy vấn hoặc mô hình phục vụ BI, quy tắc quy thuộc và đối soát.

Không đưa thông tin giao hàng chi tiết vào dashboard công khai. Xem [nguồn dữ liệu](../../docs/NGUON_DU_LIEU.md), [kế hoạch đánh giá](../../docs/KE_HOACH_THUC_HIEN.md) và [README nhóm](../../README.md).


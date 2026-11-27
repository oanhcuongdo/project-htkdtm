# Backend Vị Việt

Đã có nền tảng FastAPI: `/health`, tài liệu OpenAPI tại `/docs`, cấu hình môi trường, SQLAlchemy, Alembic, middleware request ID/CORS/logging và định dạng lỗi thống nhất. Đã có models F.5, migration `001`, auth F.8, API hồ sơ/duyệt quán F.10.1, thực đơn/món chuẩn/nguyên liệu F.10.2 và tìm kiếm F.10.3. API đơn COD đã có ở F.10.5; API tiếp nhận sự kiện tracking F.10.8 đã có, còn API sinh gợi ý chưa triển khai.

## Auth backend

`app/auth/` có router, schema, service, dependency và tiện ích theo F.8. Chi tiết request/response, mã lỗi, cấu hình JWT và giới hạn refresh nằm trong [API contract](../../docs/API_CONTRACT.md).

| Endpoint | Chức năng |
| :--- | :--- |
| `POST /api/v1/auth/register` | Tạo customer/vendor, chuẩn hóa email, băm mật khẩu, trả UserOut 201 |
| `POST /api/v1/auth/login` | Kiểm tra mật khẩu, trả access/refresh token và UserOut |
| `POST /api/v1/auth/refresh` | Kiểm tra refresh token và cấp cặp token mới |
| `GET /api/v1/auth/me` | Kiểm tra Bearer access token và đọc User hiện tại từ DB |

Mật khẩu dùng Passlib PBKDF2-SHA256 với 600.000 vòng và salt ngẫu nhiên; không phụ thuộc bcrypt. Đăng ký công khai không nhận admin hoặc trường ngoài schema. Email kiểm tra theo định dạng cơ bản, chưa xác minh hộp thư. JWT chỉ dùng HS256, có hạn dùng và phân biệt access/refresh; thay SECRET_KEY mẫu trước khi dùng token. Chưa có giới hạn tần suất đăng nhập/khôi phục mật khẩu.

Dependency `get_current_user`, `require_role(*roles)`, `require_vendor_owner` có thể import từ `app.auth.dependencies` hoặc `app.dependencies`. Guard đọc lại vai trò/membership từ DB; admin không tự bỏ qua quyền sở hữu quán của vendor. Router vendor/admin hiện có hồ sơ/duyệt quán, thực đơn và danh mục; đơn hàng và các chức năng quản trị khác sẽ bổ sung sau.

## API hồ sơ và duyệt quán

`restaurants/` có schema, service và API công khai; `vendor/` quản lý quán lấy từ membership của người đăng nhập; `admin/` có danh sách, duyệt và tạm ngừng. Các endpoint, request đầy đủ và lỗi nằm ở [API contract F.10.1](../../docs/API_CONTRACT.md#hồ-sơ-quán-và-duyệt-quán--f101).

- Công khai: GET `/api/v1/restaurants/` có phân trang, GET `/api/v1/restaurants/{restaurant_id}`; chỉ trả quán approved.
- Vendor: POST/GET/PUT `/api/v1/vendor/restaurant`. Tạo quán và membership trong cùng transaction, mặc định pending và chưa nhận đơn. PUT yêu cầu toàn bộ hồ sơ; chỉ approved mới bật nhận đơn được. Không nhận ID quán/người dùng hoặc trạng thái duyệt từ client.
- Admin: GET `/api/v1/admin/restaurants`, PATCH `/{restaurant_id}/approve` hoặc `/suspend` dưới prefix đó. Tạm ngừng luôn tắt nhận đơn; duyệt không tự bật lại. Chưa có API thêm/chuyển membership, xóa quán hoặc tự cấp admin.

Service tính giờ mở theo `Asia/Ho_Chi_Minh`, hỗ trợ qua đêm và quy ước hai giờ bằng nhau là 24 giờ. Response có `is_open` và `can_receive_orders` (approved + cờ nhận đơn + giờ mở), chưa bao gồm điều kiện vị trí khách/khả dụng món. DB vẫn giữ TIME địa phương và không có cột tính toán mới. Quán pending/suspended bị ẩn ở công khai nhưng chủ quán vẫn xem/sửa hồ sơ của mình với cờ nhận đơn false.

Ghi dữ liệu có rollback và khóa hàng khi DB hỗ trợ; kiểm thử SQLite tạm chưa chứng minh cạnh tranh/khóa trên PostgreSQL. Không thay models hoặc migration `001`; giao diện hồ sơ/duyệt quán sẽ triển khai theo F.12.

## API thực đơn, món chuẩn và nguyên liệu

`menu/` có schema/service/router đọc công khai; `vendor/` quản lý món của quán lấy từ membership; `admin/` quản lý catalog. Chi tiết 17 thao tác, body và response ở [API contract F.10.2](../../docs/API_CONTRACT.md#thực-đơn-món-chuẩn-và-nguyên-liệu--f102).

- Công khai: GET `/api/v1/restaurants/{restaurant_id}/menu`, `/menu-items/{item_id}`, `/canonical-dishes`, `/ingredients`. Món phải đang bán và thuộc quán approved; quán đóng cửa/tắt nhận đơn vẫn cho đọc thực đơn.
- Vendor: GET/POST `/api/v1/vendor/menu-items`, GET/PUT/DELETE `/{item_id}` dưới prefix đó. PUT thay toàn bộ sáu trường; DELETE ngừng bán, giữ ID/liên kết/lịch sử, PUT có thể bật lại. Món ngoài quán hoặc chưa có membership trả 404.
- Admin: GET/POST `/api/v1/admin/canonical-dishes` và `/ingredients`, PUT/DELETE `/{entry_id}` dưới từng prefix. Xóa mục còn được sử dụng trả 409, kể cả món đã ngừng bán. Chuẩn hóa tên nguyên liệu, kiểm tra UNIQUE tên/source_id và cấm client tự gán cờ mô phỏng.

Giá là số nguyên VNĐ; các cờ nhận đúng Boolean JSON. Xác nhận nguyên liệu yêu cầu danh sách ID thực tế không rỗng; không suy thành phần thực tế từ JSON món chuẩn. Ghi món và thay liên kết nguyên liệu có tính nguyên tử/rollback. Menu quán trả mảng; các danh sách khác trả page có total/offset/limit. Chưa có frontend thực đơn hoặc kiểm tra điều kiện đặt đơn; không đổi schema.

## API tìm kiếm món và quán

`app/search/` có schema, service và router theo C.5/F.10. GET công khai `/api/v1/search/dishes` và `/api/v1/search/restaurants` nhận lat/lng bắt buộc, q tùy chọn, radius mặc định 5 km (tối đa 50), offset/limit như các API danh sách. Xem [API contract F.10.3](../../docs/API_CONTRACT.md#tìm-kiếm-món-và-quán--f103).

Tìm chữ tiếng Việt có/không dấu, không phân biệt hoa/thường; mọi từ phải khớp trong tên món bán/món chuẩn/quán, hoặc tên/địa chỉ khi tìm quán. Chỉ trả quán approved, món đang bán và trong cả bán kính khách lẫn phạm vi giao của quán. Quán đóng cửa/tắt nhận đơn vẫn xuất hiện cùng trạng thái công khai. Không áp bộ lọc AI/khẩu vị vào tìm kiếm.

Khoảng cách Haversine đường chim bay; sắp theo khoảng cách chưa làm tròn rồi ID, lọc trước total/phân trang. SQL giới hạn vùng ứng viên, Python chuẩn hóa Unicode và tính khoảng cách; phù hợp tập dữ liệu MVP, chưa có chỉ mục không gian/tìm kiếm cho dữ liệu lớn. Trả public DTO cùng distance_km, món có thêm restaurant để hiển thị giờ/trạng thái. Không ghi vị trí khách, không gọi Maps/geocode, không đổi schema/dependencies hoặc frontend.

Refresh dùng JWT không lưu trạng thái: token cũ vẫn còn hiệu lực đến hạn, chưa có thu hồi từng phiên/thiết bị hoặc logout phía máy chủ. Không gọi việc cấp token mới là rotation có chống dùng lại. Frontend auth đã tích hợp token trong localStorage hoặc sessionStorage theo lựa chọn ghi nhớ, tải lại User từ `/me`, tự refresh một lần và logout cục bộ; backend chưa cấp cookie HttpOnly. Phần auth không thay đổi schema hoặc revision `001`.

## Model tài khoản đã bổ sung

`app/users/models.py` định nghĩa bảng `users` và enum `UserRole`:

| Trường | Nội dung |
| :--- | :--- |
| `id` | Khóa chính tự tăng |
| `email` | Bắt buộc, duy nhất; ORM bỏ khoảng trắng đầu/cuối và chuyển chữ thường trước khi lưu |
| `full_name` | Họ tên bắt buộc; ORM loại khoảng trắng đầu/cuối, không nhận chuỗi rỗng |
| `hashed_password` | Chuỗi băm mật khẩu bắt buộc; module auth tạo/kiểm tra PBKDF2-SHA256 |
| `role` | `customer`, `vendor`, `admin`; mặc định `customer`, có CHECK constraint ở DB |
| `is_simulated` | Phân biệt tài khoản mô phỏng; mặc định `false` |
| `created_at` | Thời điểm tạo; mặc định UTC phía Python, có mặc định phía DB |

Alembic đã import model để nhận metadata và User nằm trong migration `001`. Cần chạy `alembic upgrade head` để tạo bảng trong DB ứng dụng. Kiểm thử dùng DB SQLite riêng, không thay đổi DB ứng dụng. Enum vai trò ở model giới hạn dữ liệu; dependency trong module auth thực hiện kiểm tra quyền API.

## Model khẩu vị đã bổ sung

`app/preferences/models.py` định nghĩa bảng `preferences`. `user_id` vừa là khóa chính vừa tham chiếu `users.id`, nên mỗi tài khoản có tối đa một hồ sơ. Xóa tài khoản sẽ xóa hồ sơ khẩu vị đi kèm. Người bỏ qua khai báo chưa có bản ghi Preference; không tự tạo hồ sơ rỗng khi tạo User.

API GET/PUT `/api/v1/preferences/` dành cho customer đã đăng nhập. GET chưa khai báo trả 404; PUT yêu cầu đủ năm câu hỏi và thay toàn bộ hồ sơ, lấy user_id từ token. Danh sách trim/loại trùng, nguyên liệu chuyển chữ thường; mức cay/khám phá là số nguyên nghiêm ngặt. Ghi transaction, rollback lỗi DB và xử lý tranh chấp tạo lần đầu. Xem [API contract F.10.7](../../docs/API_CONTRACT.md#hồ-sơ-khẩu-vị--f107); chưa có giao diện PreferencePage.

Năm câu hỏi được đối chiếu với [đặc tả frontend](../frontend/README.md), mục bản đồ route và luồng khách mới. Bản thiết kế cấu trúc yêu cầu năm câu hỏi nhưng chưa chốt từng cột; các quy ước chi tiết được ghi dưới đây để dùng thống nhất ở API và giao diện sau này.

| Câu hỏi | Trường | Quy ước dữ liệu |
| :--- | :--- | :--- |
| Thích hương vị vùng nào? | `regions` | Danh sách nhãn vùng miền; mặc định `[]` |
| Mức cay mong muốn? | `spice_level` | Số nguyên 0–3: không cay, ít cay, vừa cay, rất cay; mặc định 0 |
| Nguyên liệu yêu thích? | `liked_ingredients` | Danh sách nguyên liệu; mặc định `[]` |
| Nguyên liệu cần tránh? | `avoided_ingredients` | Danh sách nguyên liệu cần loại; mặc định `[]` |
| Sẵn sàng thử món mới đến đâu? | `exploration_level` | Số nguyên 0–2: món quen, cân bằng, ưu tiên khám phá; mặc định 1 |

Gán danh sách qua ORM sẽ bỏ khoảng trắng đầu/cuối và loại trùng không phân biệt hoa/thường; tên nguyên liệu được chuyển chữ thường. Các danh sách dùng MutableList để lưu được thay đổi tại chỗ như `append`/`remove`. Mức cay và mức khám phá có CHECK constraint ở DB. Việc kiểm tra API, mã hóa vector và áp dụng nguyên liệu cần tránh khi gợi ý sẽ được triển khai ở các phần sau; chưa có trong model này.

## API ghi nhận tương tác

`app/tracking/` có schema, service và POST `/api/v1/tracking/events` cho customer. Batch 1–100 sự kiện được ghi cùng transaction; `event_id` UUID v4 cho phép gửi lại cùng nội dung mà không tạo dòng trùng. Server đối chiếu chủ request, phiên và món trong danh sách gợi ý; chỉ ghi `displayed_at` khi nhận sự kiện `impression`. Xem [API contract F.10.8](../../docs/API_CONTRACT.md#ghi-nhận-sự-kiện-tương-tác--f108). API sinh gợi ý và giao diện phát sự kiện chưa có.

## Models quán và liên kết quản lý đã bổ sung

Theo mục C.5 và F.5 của [thiết kế](../../docs/THIET_KE_CAU_TRUC.md), `app/restaurants/models.py` định nghĩa `Restaurant`, `RestaurantMembership` và enum `RestaurantStatus`. Các giới hạn, kiểu dữ liệu và mặc định dưới đây là quy ước triển khai chi tiết để API/UI dùng thống nhất.

| Trường Restaurant | Quy ước |
| :--- | :--- |
| `id` | Khóa chính tự tăng |
| `name`, `address` | Bắt buộc; bỏ khoảng trắng đầu/cuối; tối đa 160/500 ký tự |
| `latitude`, `longitude` | Số hữu hạn; trong khoảng [-90, 90] và [-180, 180] |
| `delivery_radius_km` | Lớn hơn 0 và không quá 50 km; mặc định 5 km |
| `opens_at`, `closes_at` | Kiểu TIME theo giờ địa phương Việt Nam (UTC+7); ORM nhận `time` hoặc chuỗi `HH:MM` |
| `accepting_orders` | Cờ nhận đơn; mặc định `false` để quán mới chưa tự nhận đơn |
| `status` | `pending`, `approved`, `suspended`; mặc định `pending`, có CHECK constraint |
| `is_simulated` | Cờ dữ liệu mô phỏng; mặc định `false` |

Giờ phục vụ có độ chính xác đến phút. Chấp nhận khoảng qua đêm, ví dụ 22:00–02:00; hai mốc bằng nhau được quy ước là phục vụ 24 giờ. Mặc định cả hai là 00:00. Service F.10.1 đã tính giờ mở theo Việt Nam và kết hợp trạng thái duyệt/cờ nhận đơn trong response; model chỉ lưu giờ và các cờ.

`RestaurantMembership.user_id` vừa là khóa chính vừa tham chiếu `users.id`: mỗi tài khoản quản lý tối đa một quán, phù hợp API `/vendor/restaurant` trong bản thiết kế. `restaurant_id` tham chiếu `restaurants.id`, có index và cho phép nhiều tài khoản cùng liên kết một quán. Đây là quy ước MVP; chưa mở rộng một tài khoản quản lý chuỗi nhiều quán.

Khóa ngoại chặn xóa tài khoản/quán đang có membership để không làm mất liên kết ngoài ý muốn; cần xử lý membership trước khi xóa. FK chỉ kiểm tra đối tượng tồn tại; auth/vendor đã kiểm tra vai trò và suy ra đúng quán của tài khoản ở API hồ sơ. Hai model đã có trong migration `001`; bảng trong DB ứng dụng được tạo khi chạy upgrade.

## Models món chuẩn, thực đơn và nguyên liệu đã bổ sung

Theo mục C.5, D.16/33/34 và F.5 của [thiết kế](../../docs/THIET_KE_CAU_TRUC.md), `app/menu/models.py` có bốn model. Các giới hạn chi tiết dưới đây được ghi để API và dữ liệu nhập dùng thống nhất.

| Model | Nội dung |
| :--- | :--- |
| `CanonicalDish` | Món chuẩn: tên duy nhất, vùng miền, mức cay 0–3, cách chế biến, nguyên liệu đặc trưng và nhãn JSON; `source_id` tùy chọn/duy nhất để truy vết nguồn |
| `MenuItem` | Món bán tại một quán, tham chiếu Restaurant và CanonicalDish; có tên, giá, khả dụng và xác nhận nguyên liệu riêng |
| `Ingredient` | Danh mục nguyên liệu: tên tối đa 100 ký tự, chuẩn hóa chữ thường và duy nhất |
| `MenuItemIngredient` | Liên kết nguyên liệu thực tế của món bán; khóa chính ghép ngăn liên kết trùng một nguyên liệu |

Tên món tối đa 180 ký tự; vùng miền/cách chế biến tối đa 40 ký tự; mã nguồn tối đa 120 ký tự khi có. Tên được bỏ khoảng trắng đầu/cuối. Nguyên liệu đặc trưng và nhãn dùng MutableList để lưu cập nhật tại chỗ; khi gán danh sách qua ORM sẽ loại phần tử trùng, chuỗi rỗng và dữ liệu sai kiểu.

Giá dùng số nguyên VNĐ, lớn hơn 0 và không quá 10.000.000. Món mới mặc định `is_available=false`, `ingredients_verified=false`; API vendor cho chủ quán đặt các cờ và yêu cầu danh sách nguyên liệu khi xác nhận. CanonicalDish, MenuItem và Ingredient đều có `is_simulated`, mặc định false.

Nguyên liệu JSON của món chuẩn là đặc trưng tham khảo, không tự thay thế nguyên liệu thực tế trong MenuItemIngredient. API vendor đã nhận danh sách nguyên liệu thực tế và cờ xác nhận; nhập nguồn và lọc theo nguyên liệu cần tránh sẽ triển khai ở phần sau. Model chưa chứng minh một món đáp ứng điều kiện lọc chỉ từ cờ xác nhận.

Một món chuẩn có thể được nhiều quán bán với tên và giá khác nhau. FK chặn xóa quán/món chuẩn còn MenuItem và nguyên liệu còn được liên kết. Nếu xóa MenuItem trực tiếp khi chưa có tham chiếu khác, các liên kết nguyên liệu bị xóa theo và danh mục vẫn còn. API vendor luôn ngừng bán bằng cờ, giữ cả món lẫn liên kết; OrderItem có FK bảo vệ món từng được đặt và snapshot giữ tên/giá lần mua.

## Models đơn hàng, chi tiết và lịch sử đã bổ sung

Theo mục C.5, D.10–13, E.2/E.4/E.5 và F.5 của [thiết kế](../../docs/THIET_KE_CAU_TRUC.md), `app/orders/models.py` định nghĩa ba model và `OrderStatus` với đủ bảy giá trị: `pending`, `confirmed`, `preparing`, `delivering`, `completed`, `cancelled`, `rejected`.

| Model | Dữ liệu/ràng buộc |
| :--- | :--- |
| `Order` | Tham chiếu khách và một quán; trạng thái mặc định pending, tổng tiền, địa chỉ/tọa độ giao, session, idempotency key, hash nội dung yêu cầu, thời điểm tạo, cờ mô phỏng |
| `OrderItem` | Tham chiếu Order và MenuItem; lưu `snapshot_name`, `snapshot_price`, số lượng; mỗi MenuItem xuất hiện tối đa một dòng trong cùng đơn |
| `OrderStatusHistory` | Trạng thái, tài khoản thao tác, thời điểm, lý do tùy chọn; từ chối đơn bắt buộc có lý do ở DB |

Theo E.4, `Order.idempotency_key` có UNIQUE toàn bảng. Key và session nhận UUID v4 từ client, được chuẩn hóa qua kiểu UUID; backend không tự cấp key cho mỗi lần nhận request. `payload_hash` là trường bổ sung chứa SHA-256 dạng hex để service sau này phát hiện cùng key nhưng khác nội dung. Chính sách trả lại đơn cũ, kiểm tra người gửi và cửa sổ 24 giờ chưa được triển khai ở model.

Tổng tiền là số nguyên VNĐ dương dùng BIGINT để không tràn số khi cộng nhiều món. Giá chụp mỗi món trong (0, 10.000.000], số lượng 1–99, tên chụp tối đa 180 ký tự; đây là giới hạn triển khai chi tiết. Địa chỉ dài 5–500 ký tự; tọa độ nằm trong giới hạn địa lý hợp lệ. Các thời điểm mặc định UTC; thời điểm gán trực tiếp qua ORM phải có múi giờ và được đổi về UTC. `is_simulated` của Order mặc định false.

FK chặn xóa khách/quán/món bán đang được giao dịch tham chiếu và chặn xóa Order còn chi tiết hoặc lịch sử. Thay đổi tên/giá trong MenuItem không tự thay đổi snapshot đã lưu ở OrderItem. Lịch sử được đọc theo thời điểm rồi ID để giữ thứ tự ổn định.

Service đã tạo snapshot từ menu, tính tổng, kiểm tra cùng quán/khả dụng/giá/giờ/phạm vi và ghi lịch sử pending cùng transaction. API tạo, đọc, hủy và xử lý đơn đã tích hợp ở F.10.5; schema vẫn migration `001`.

### API đơn COD và idempotency

`orders/router.py` có 11 thao tác customer/vendor dưới `/api/v1`: POST/GET `/orders/`, GET `/orders/{order_id}`, PATCH cancel; GET `/vendor/orders`, GET chi tiết và PATCH confirm/reject/preparing/delivering/complete. Danh sách trả mảng phân trang, chỉ đơn của khách/quán từ membership. Chi tiết body/response/mã lỗi ở [API contract F.10.5](../../docs/API_CONTRACT.md#đơn-cod-và-chống-gửi-lặp--f105).

Body tạo gồm restaurant_id, items (menu_item_id/quantity/expected_price), địa chỉ/tọa độ giao, session_id và idempotency_key UUID v4. Backend xác minh giá và lưu snapshot/tổng tiền từ DB. Mã gửi lặp cùng khách/cùng payload trong dưới 24 giờ trả đơn cũ 200; khác payload/chủ sở hữu hoặc hết hạn trả 409, không tái sử dụng key. Khóa hàng khách/quán/món khi DB hỗ trợ; UNIQUE xử lý tranh chấp key, rollback khi lỗi. Chưa có frontend đơn hàng, review hoặc kiểm chứng cạnh tranh PostgreSQL thực tế.

### Chuyển trạng thái và lịch sử đơn

`orders/state_machine.py` thực hiện đúng E.2: vendor chuyển pending → confirmed/rejected, confirmed → preparing, preparing → delivering, delivering → completed; customer chỉ hủy pending → cancelled. Completed/cancelled/rejected là trạng thái kết thúc; không có chuyển về trước hoặc chuyển lặp cùng trạng thái. Admin không có quyền chuyển trạng thái thay người mua/chủ quán.

`orders/service.py::transition_order(db, order_id, actor_id, target, reason=...)` đã được API sử dụng. Caller lấy actor_id từ dependency xác thực và dùng session của request, không nhận ID người thao tác từ body. Service đọc lại User/membership/trạng thái từ DB; khách chỉ thao tác đơn của mình, vendor chỉ thao tác đơn thuộc quán liên kết. Đơn ngoài quyền và đơn không tồn tại cùng trả NotFoundError; tài khoản mất vai trò hợp lệ bị từ chối.

Từ chối bắt buộc lý do trim 1–500 ký tự; các thao tác khác không nhận lý do ở phiên bản này. Service khóa hàng Order khi DB hỗ trợ, UPDATE có điều kiện trạng thái cũ rồi ghi OrderStatusHistory cùng transaction. Chỉ commit khi cả hai thành công; lỗi nghiệp vụ/DB rollback. Không thay tổng tiền, snapshot hoặc dữ liệu giao hàng. Các quán tạm ngừng/đóng cửa vẫn có thể xử lý đơn đã tồn tại; điều kiện nhận đơn mới được kiểm tra trong create_order.

Service sở hữu commit/rollback nên không ghép các thay đổi không liên quan vào cùng session. Service tạo đơn ghi lịch sử pending cùng lúc tạo đơn; transition_order không tự bổ sung lịch sử cũ còn thiếu. Chưa có UI hoặc kiểm chứng khóa hàng cạnh tranh trên PostgreSQL.

## Model đánh giá món đã bổ sung

Theo mục C.5, D.14 và F.5 của [thiết kế](../../docs/THIET_KE_CAU_TRUC.md), `app/reviews/models.py` định nghĩa `Review`. Đây là đánh giá món đã mua, tách khỏi phản hồi phù hợp/không phù hợp của danh sách gợi ý.

| Trường | Quy ước |
| :--- | :--- |
| `id` | Khóa chính tự tăng |
| `order_id`, `menu_item_id` | Tham chiếu Order/MenuItem và có FK ghép tới cặp `(order_id, menu_item_id)` trong OrderItem; món phải thực sự xuất hiện trong đơn |
| `user_id` | Tài khoản gửi đánh giá; service sẽ gán từ người đang đăng nhập |
| `rating` | Số nguyên 1–5, có CHECK constraint ở DB |
| `comment` | Nhận xét tùy chọn, mặc định chuỗi rỗng, tối đa 2000 ký tự sau khi bỏ khoảng trắng đầu/cuối |
| `created_at` | Thời điểm tạo, mặc định UTC; giá trị gán qua ORM phải có múi giờ và được đổi về UTC |
| `is_simulated` | Phân biệt đánh giá mô phỏng với đánh giá thật; mặc định false |

UNIQUE trên `(order_id, menu_item_id)` ngăn đánh giá trùng một món trong cùng đơn. Cùng món bán được đánh giá lại khi có đơn mua khác. Quan hệ `order_item` chỉ đọc giúp lấy tên/giá snapshot đã mua dù thực đơn sau đó thay đổi. FK chặn xóa dữ liệu giao dịch đang được Review tham chiếu.

`reviews/service.py` đã kiểm tra người gửi sở hữu đơn, trạng thái completed và món thực sự có trong OrderItem; router cung cấp POST `/api/v1/orders/{order_id}/review`. Mỗi món trong một đơn chỉ đánh giá một lần, duplicate trả 409. Response dùng tên/giá snapshot và không lộ cờ mô phỏng; xem [API contract F.10.6](../../docs/API_CONTRACT.md#đánh-giá-món-đã-mua--f106). Bảng Review đã có trong migration `001`; chưa có frontend ReviewForm hoặc API đọc/sửa/xóa đánh giá.

## Models yêu cầu gợi ý, hiển thị và tương tác đã bổ sung

Theo mục C.5, D.6/7/20/21, E.5 và F.5 của [thiết kế](../../docs/THIET_KE_CAU_TRUC.md), `app/tracking/models.py` định nghĩa ba model. API F.10.8 đã tiếp nhận sự kiện; ETL/KPI chưa triển khai.

| Model | Dữ liệu/ràng buộc |
| :--- | :--- |
| `RecommendationRequest` | ID UUID v4 được backend/ORM sinh, tài khoản, session UUID v4, phiên bản thuật toán bắt buộc tối đa 40 ký tự, thời điểm tạo |
| `RecommendationImpression` | Request, món được trả về, thứ hạng 1–5; không lặp món hoặc thứ hạng trong cùng request; `displayed_at` mặc định NULL |
| `InteractionEvent` | `event_id` UUID v4 do client cấp là khóa chính chống trùng; tài khoản/session, loại sự kiện, request/món tùy ngữ cảnh, giá trị feedback, thời điểm phát sinh/tiếp nhận |

Mã sự kiện được lưu thống nhất: `impression`, `click`, `add_to_cart`, `feedback`, `session_start`, `session_end`. Các tên `rec_*` ở bản đặc tả frontend trước đây được thống nhất về các mã trên; chưa có API chuyển đổi alias. `impression`/`click`/`feedback` cần request và món; `add_to_cart` cần món nhưng có thể không đến từ gợi ý; sự kiện phiên không mang request/món. Chỉ feedback có giá trị, nhận số nguyên 0 hoặc 1. Các quy tắc ngữ cảnh có CHECK constraint ở DB.

FK ghép đảm bảo sự kiện có request phải khớp tài khoản/session của request, và món thuộc danh sách đã trả về trong request đó. Request và Impression được truy cập từ event qua quan hệ chỉ đọc để tránh tự sửa chủ sở hữu khi gán quan hệ. FK chặn xóa các bản ghi đang được tracking tham chiếu. Mỗi model có `is_simulated`, mặc định false.

Việc tạo dòng RecommendationImpression khi trả danh sách chưa chứng minh món đã hiện trên màn hình. Chỉ khi service nhận sự kiện hiển thị hợp lệ mới ghi `displayed_at`; KPI sau này phải loại các dòng chưa có giá trị này. Nhiều click khác `event_id` vẫn được lưu riêng; CTR sẽ đếm impression có click, không lấy số dòng click làm mẫu số hoặc số lần hiển thị.

`occurred_at` là thời điểm phát sinh do client gửi kèm múi giờ; `received_at` do máy chủ/ORM cấp mặc định. Thời điểm gán qua ORM được chuẩn hóa UTC. Service F.10.8 kiểm tra cửa sổ tiếp nhận, thứ tự hiển thị trước click/feedback, người gửi và xử lý HTTP khi gửi lại. Model chỉ bảo vệ cấu trúc dữ liệu; chưa kiểm tra cặp bắt đầu/kết thúc phiên hoặc quy thuộc đơn hàng.

## Migration khởi tạo

`alembic/versions/001_initial_schema.py` là revision gốc, tạo đúng 15 bảng OLTP ở F.5 cùng PK, FK, UNIQUE, CHECK, index và mặc định phía DB. Chưa tạo bảng fact, BI views, dữ liệu mẫu hoặc bảng đánh giá mù của các phần sau. Migration dùng các thao tác cố định, không import models đang phát triển để tạo schema.

Sau khi cài dependencies và có DB theo `.env`, chạy từ thư mục backend:

```powershell
python -m alembic upgrade head
python -m alembic current
python -m alembic check
```

`current` cần báo `001 (head)`. `check` dùng để phát hiện thay đổi schema/model mà Alembic hỗ trợ so sánh, gồm kiểu cột và mặc định. Bổ sung constraint phức tạp vẫn cần review/test; không dựa riêng vào autogenerate. Lệnh nâng tới head lần nữa không tạo lại bảng hoặc xóa dữ liệu.

`alembic.ini` dùng đường dẫn theo vị trí file cấu hình, nên cũng có thể gọi từ thư mục nhóm với `python -m alembic -c src/backend/alembic.ini upgrade head`. URL kết nối được truyền nguyên dạng đã mã hóa từ Settings, không escape `%` hai lần. SQLite bật kiểm tra FK trong migration; mặc định Boolean được viết bằng biểu thức SQLAlchemy để sinh đúng SQL theo từng hệ quản trị.

`migration_support.py` so sánh các giá trị mặc định JSON dạng literal khi kiểm tra schema PostgreSQL, tránh phép so sánh bằng không được hỗ trợ cho kiểu `json`. Các kiểu dữ liệu khác vẫn do Alembic so sánh.

Đã kiểm thử nâng/hạ/nâng lại, schema lệch model, dữ liệu/constraint trên DB tạo từ migration và sinh SQL PostgreSQL offline. Chưa chạy PostgreSQL hoặc Docker thực tế trong môi trường này. Các bài test chỉ dùng DB tạm. Hạ về `base` sẽ xóa các bảng và dữ liệu, chỉ dùng trên DB kiểm thử có thể bỏ; không chạy trên DB cần giữ dữ liệu.

Khi revision đã được commit/áp dụng, thay đổi schema bằng revision kế tiếp thay vì sửa hoặc sinh lại `001`. Xem hướng dẫn cài đặt để chạy migration local/Docker. [ERD](../../docs/ERD.md) và [từ điển dữ liệu](../../docs/TU_DIEN_DU_LIEU.md) ở F.7 đối chiếu đủ 15 bảng, các cột và ràng buộc hiện có.

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

Python >=3.11, FastAPI, SQLAlchemy, PostgreSQL và scikit-learn. Phụ thuộc được khai báo trong `requirements.txt` và `requirements-dev.txt`. Chạy từ thư mục này: `python -m uvicorn app.main:app --reload`; kiểm tra: `python -m pytest tests -q`. Xem [hướng dẫn cài đặt](../../docs/HUONG_DAN_CAI_DAT.md) để tạo môi trường trước khi chạy.

Các phần F.5–F.9 và nghiệp vụ/API F.10.1–F.10.7 đã được bổ sung đến hồ sơ khẩu vị. Các phần backend tiếp theo thuộc yêu cầu gợi ý/tracking và quản trị; triển khai từng phần để commit riêng. Alembic trong backend là nguồn schema duy nhất; các model BI hoặc đánh giá mù của phần sau sẽ dùng revision bổ sung khi được triển khai.

Xem [README nhóm](../../README.md), [nguồn dữ liệu](../../docs/NGUON_DU_LIEU.md) và [kế hoạch](../../docs/KE_HOACH_THUC_HIEN.md).


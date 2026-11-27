# Hợp đồng API Vị Việt

Tài liệu hiện mô tả auth F.8 và các API quán, thực đơn, tìm kiếm, đơn COD, đánh giá, khẩu vị, tracking trong F.10. OpenAPI tại `http://localhost:8000/docs` phản ánh request/response đang chạy.

Frontend đã có types và tám hàm gọi GET công khai cho quán, thực đơn, danh mục, tìm kiếm ở F.11.1; xem [bảng hàm API frontend](../src/frontend/README.md#api-công-khai-đã-chuẩn-bị--f111). Chúng dùng chung API client auth nhưng đặt `authenticated: false`; màn hình nghiệp vụ sẽ được nối ở F.12.

## Quy ước chung

Nghiệp vụ đơn hàng dùng state machine E.2 và API COD ở F.10.5 bên dưới. Xem [README backend](../src/backend/README.md#chuyển-trạng-thái-và-lịch-sử-đơn) về quyền sở hữu và transaction.

- Base URL local: `http://localhost:8000/api/v1`. Gửi body JSON với `Content-Type: application/json`.
- Endpoint yêu cầu đăng nhập nhận `Authorization: Bearer <access_token>`. Refresh token chỉ gửi trong body `/auth/refresh`, không dùng thay access token.
- ID người dùng là số nguyên; timestamp response dùng ISO 8601. Thời điểm phía ứng dụng dùng UTC; SQLite demo có thể trả timestamp không kèm offset khi đọc lại từ DB.
- Lỗi theo dạng `{"error":{"code":"...","message":"...","details":{}}}`. Với 422, `details` là danh sách trường lỗi; không chứa giá trị input hoặc body mật khẩu. Mọi response có `X-Request-ID`.
- Response đăng nhập/refresh có `Cache-Control: no-store`. Lỗi xác thực 401 có `WWW-Authenticate: Bearer`.

## `POST /auth/register`

Không cần token. Tạo tài khoản và trả UserOut, không tự đăng nhập.

```json
{
  "email": "khach@example.vn",
  "password": "Mat khau demo 123!",
  "full_name": "Nguyễn Văn A",
  "role": "customer"
}
```

| Trường | Bắt buộc | Quy tắc |
| :--- | :--- | :--- |
| `email` | Có | Bỏ khoảng trắng đầu/cuối, chuyển chữ thường, tối đa 254 ký tự; kiểm tra cơ bản dạng `ten@mien.duoi`, không xác minh hộp thư |
| `password` | Có | 8–128 ký tự, không chỉ gồm khoảng trắng; giữ nguyên khoảng trắng đầu/cuối |
| `full_name` | Có | Bỏ khoảng trắng đầu/cuối, dài 1–120 ký tự |
| `role` | Không | Mặc định `customer`; chỉ nhận `customer` hoặc `vendor` |

Các trường ngoài schema bị từ chối 422, bao gồm `is_simulated`, `hashed_password` và thông tin tự cấp quyền. Vai trò `admin` không được tạo qua đăng ký công khai. Đăng ký vendor chưa tạo quán hoặc membership; các bước đó thuộc module quán sau này.

Thành công **201**, body UserOut:

```json
{
  "id": 1,
  "email": "khach@example.vn",
  "full_name": "Nguyễn Văn A",
  "role": "customer",
  "is_simulated": false,
  "created_at": "2026-11-26T10:00:00Z"
}
```

`created_at` trong ví dụ chỉ minh họa định dạng. Response không có mật khẩu hoặc chuỗi băm. Email đã tồn tại sau chuẩn hóa trả **409** `EMAIL_EXISTS`; ràng buộc UNIQUE vẫn bảo vệ khi hai yêu cầu tạo trùng chạy đồng thời.

## `POST /auth/login`

Không cần token. Body:

```json
{
  "email": "khach@example.vn",
  "password": "Mat khau demo 123!"
}
```

Email chuẩn hóa giống đăng ký; password dài 1–128 ký tự và được kiểm tra nguyên dạng. Không nhận trường thừa. Thành công **200**, TokenResponse:

```json
{
  "access_token": "<JWT access>",
  "refresh_token": "<JWT refresh>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "khach@example.vn",
    "full_name": "Nguyễn Văn A",
    "role": "customer",
    "is_simulated": false,
    "created_at": "2026-11-26T10:00:00Z"
  }
}
```

`expires_in` là số giây sống của access token, lấy từ cấu hình. Email không tồn tại và sai mật khẩu đều trả **401** `INVALID_CREDENTIALS` với cùng thông báo. Email không tồn tại vẫn chạy bước kiểm tra mật khẩu qua hash giả; đây không phải cam kết thời gian phản hồi giống hệt nhau.

Mật khẩu được băm bằng Passlib PBKDF2-SHA256, 600.000 vòng và salt ngẫu nhiên. Không dùng hoặc lưu mật khẩu rõ. Chưa có xác minh email, khôi phục mật khẩu, giới hạn tần suất đăng nhập hoặc chức năng đổi mật khẩu.

## `POST /auth/refresh`

Không cần header Bearer. Body:

```json
{
  "refresh_token": "<JWT refresh>"
}
```

`refresh_token` bắt buộc, dài 1–4096 ký tự; không nhận trường thừa. Thành công **200**, trả TokenResponse với hai token mới và thông tin tài khoản hiện tại. Token access gửi nhầm, token không hợp lệ/hết hạn hoặc tài khoản không còn tồn tại trả **401** `UNAUTHENTICATED`.

Refresh hiện **không lưu trạng thái ở DB**: cấp token mới chưa thu hồi token cũ; token cũ còn dùng được đến hạn. Chưa có denylist, phát hiện dùng lại, thu hồi từng thiết bị hoặc endpoint logout phía máy chủ. `jti` giúp phân biệt token, chưa được lưu để chống phát lại. Logout phía giao diện sau này chỉ xóa token cục bộ; không được mô tả thành thu hồi phiên trên máy chủ. Khi cần thu hồi từng phiên phải bổ sung lưu trữ phiên/token bằng migration mới và cập nhật contract.

## `GET /auth/me`

Yêu cầu access token hợp lệ. Thành công **200** trả UserOut giống response đăng ký. Token không có, sai loại, sai chữ ký, sai thuật toán, sai issuer/audience, thiếu claim bắt buộc, hết hạn hoặc tài khoản đã bị xóa trả **401** `UNAUTHENTICATED`.

Không tin vai trò nằm trong token: backend đọc User từ DB mỗi request. Thay đổi `User.role` có hiệu lực với guard ở lần gọi tiếp theo mà không phải chờ token hết hạn. Model User hiện chưa có trạng thái khóa tài khoản.

## JWT và cấu hình

| Biến | Mặc định | Quy tắc |
| :--- | :--- | :--- |
| `SECRET_KEY` | Placeholder trong `.env.example` | Thay bằng chuỗi ngẫu nhiên; backend từ chối cấp/kiểm tra JWT nếu khóa dưới 32 byte hoặc bắt đầu bằng `changeme` |
| `ALGORITHM` | `HS256` | Chỉ hỗ trợ HS256; cấu hình thuật toán khác không hợp lệ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Số nguyên 1–1440 phút |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Số nguyên 1–30 ngày |

Token có `sub` là ID User dạng chuỗi, `iss=viviet`, `aud=viviet-api`, `iat`, `exp`, `jti` và `token_type=access|refresh`. Không đặt mật khẩu, hash hoặc vai trò trong token. `iat` không được nằm trong tương lai; `exp` phải lớn hơn thời điểm hiện tại và `iat`. Chữ ký được kiểm tra với thuật toán cấu hình cố định, không lấy thuật toán tùy ý từ client.

Khi SECRET_KEY chưa cấu hình hợp lệ, thao tác cần ký/kiểm tra token trả **503** `AUTH_NOT_CONFIGURED`; `/health` và tài liệu API vẫn chạy. Thay khóa sẽ làm token đã ký bằng khóa cũ không hợp lệ. Hướng dẫn tạo khóa ở [cài đặt](HUONG_DAN_CAI_DAT.md); không đưa khóa vào trình duyệt, Git hoặc log.

## Dependency phân quyền cho các router tiếp theo

| Dependency | Điều kiện | Kết quả |
| :--- | :--- | :--- |
| `get_current_user` | Access token hợp lệ, User còn tồn tại | Trả User từ DB, lỗi 401 khi không xác thực được |
| `require_role(*roles)` | User có một trong các vai trò cho phép | Trả User, lỗi 403 khi không đủ quyền |
| `require_vendor_owner` | Vai trò vendor và membership trùng `restaurant_id` trên route | Trả ID quán, lỗi 403 nếu sai vai trò/chưa có membership/khác quán |

Admin không tự vượt qua guard sở hữu của vendor; router admin dùng guard riêng. Các API hồ sơ, thực đơn và đơn hàng đã áp dụng guard thật; API quản lý tài khoản admin chưa triển khai.

## Phạm vi kiểm chứng

API auth được kiểm thử với FastAPI TestClient và SQLite tạm có schema tạo bằng migration `001`, gồm dữ liệu tài khoản, token và phân quyền. Frontend F.8 đã tích hợp và được kiểm tra bằng Playwright/Edge với backend thật trên DB SQLite tạm: đăng ký/đăng nhập, tải lại, route theo vai trò và logout. Chưa chạy PostgreSQL/Docker thực tế.

Frontend lưu hai token dưới khóa `viviet.auth.v1`: `localStorage` khi bật “Ghi nhớ đăng nhập”, `sessionStorage` của tab khi tắt. Refresh giữ nguyên nơi lưu, logout xóa cả hai. Không lưu password hoặc dùng User/role trong storage để cấp quyền. Sau tải lại, frontend gọi `/auth/me`; nếu access hết hạn thì gọi `/auth/refresh` và thử lại request một lần. Refresh bị từ chối xóa phiên; lỗi mạng/5xx cho phép thử lại. Request đồng thời dùng chung một refresh; phản hồi từ phiên trước không khôi phục được phiên sau logout/đổi tài khoản. Các phiên localStorage được đồng bộ giữa tab; sessionStorage theo phiên riêng của tab. Backend vẫn nhận token qua JSON/Bearer, chưa có cookie HttpOnly hoặc thu hồi token phía máy chủ.

Giao diện đăng ký yêu cầu đọc/đồng ý nội dung điều khoản và bảo mật của bản thử nghiệm; đây là điều kiện phía client, API hiện chưa nhận/lưu trường chấp thuận. “Quên mật khẩu?” chỉ mở hướng dẫn hỗ trợ; chưa có endpoint reset mật khẩu hoặc đăng nhập Google. Các lỗi validation được hiển thị tiếng Việt tại trường tương ứng; password/confirm không bị xóa khi gửi lỗi.

## Hồ sơ quán và duyệt quán — F.10.1

Prefix chung vẫn là `/api/v1`. Đây là phần API backend; màn hình hồ sơ/duyệt quán sẽ triển khai ở F.12. Endpoint thực đơn và tìm kiếm được mô tả ở F.10.2–F.10.3 bên dưới.

| Method | Đường dẫn | Quyền | Kết quả |
| :--- | :--- | :--- | :--- |
| GET | `/restaurants/` | Công khai | Trang danh sách quán đã duyệt |
| GET | `/restaurants/{restaurant_id}` | Công khai | Hồ sơ quán đã duyệt, hoặc 404 |
| POST | `/vendor/restaurant` | vendor | Tạo quán pending cùng membership, trả 201 |
| GET | `/vendor/restaurant` | vendor | Hồ sơ quán của tài khoản hiện tại |
| PUT | `/vendor/restaurant` | vendor | Thay toàn bộ hồ sơ quán của tài khoản hiện tại |
| GET | `/admin/restaurants` | admin | Trang danh sách quán ở mọi trạng thái |
| PATCH | `/admin/restaurants/{restaurant_id}/approve` | admin | Duyệt/quyết định hoạt động trở lại, trả 200 |
| PATCH | `/admin/restaurants/{restaurant_id}/suspend` | admin | Tạm ngừng và tắt cờ nhận đơn, trả 200 |

### Tạo quán của vendor

Body `POST /vendor/restaurant`:

```json
{
  "name": "Bếp Vị Việt",
  "address": "Hà Nội",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "delivery_radius_km": 5,
  "opens_at": "08:00",
  "closes_at": "22:00"
}
```

`name`, `address`, `latitude`, `longitude` bắt buộc. Tên/địa chỉ trim trước khi kiểm tra, dài 1–160 và 1–500 ký tự. Tọa độ nhận số JSON hữu hạn trong [-90, 90] và [-180, 180], không nhận chuỗi hoặc Boolean. Bán kính trong (0, 50] km, mặc định 5. Giờ phải đúng chuỗi `HH:MM` địa phương Việt Nam, mặc định cả hai `00:00`; không nhận giây hoặc offset.

Server lấy vendor từ access token, tạo Restaurant và RestaurantMembership trong cùng transaction. Quán mới luôn `status=pending`, `accepting_orders=false`, `is_simulated=false`; không nhận các trường tự gán quyền như `user_id`, `restaurant_id`, `status`, `is_simulated` hoặc `accepting_orders` trong body tạo. Mỗi tài khoản tối đa một membership; tạo lần nữa trả 409, không thay liên kết cũ hoặc tạo quán mồ côi khi thất bại.

### Xem/cập nhật hồ sơ của mình

GET/PUT `/vendor/restaurant` suy ra quán từ membership của người đăng nhập, không nhận ID quán từ body/query để đổi mục tiêu. Chưa có membership trả 404. Nhiều tài khoản được liên kết cùng quán có thể cùng quản lý quán đó theo model hiện tại; chưa có API thêm/chuyển membership giữa tài khoản.

PUT là thay toàn bộ hồ sơ: gửi đủ bảy trường trong ví dụ tạo và thêm `accepting_orders` dạng Boolean. Không dùng PATCH hoặc bỏ trường để sửa từng phần.

```json
{
  "name": "Bếp Vị Việt",
  "address": "Hà Nội",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "delivery_radius_km": 5,
  "opens_at": "08:00",
  "closes_at": "22:00",
  "accepting_orders": true
}
```

Chỉ quán approved mới bật nhận đơn được; pending/suspended gửi `true` trả 409 `RESTAURANT_NOT_APPROVED` và không ghi phần hồ sơ còn lại. Vendor vẫn sửa hồ sơ của quán pending/suspended khi gửi `false`. Sửa hồ sơ không tự thay trạng thái duyệt; vendor không được gửi `status` hoặc cờ mô phỏng. Chưa có thao tác xóa quán qua API; sử dụng trạng thái/cờ nhận đơn để quản lý hoạt động, giữ các tham chiếu lịch sử.

### Duyệt/tạm ngừng

Admin PATCH approve/suspend không cần body. Approve đổi trạng thái sang approved và giữ nguyên cờ nhận đơn; không tự bật nhận đơn cho quán mới hoặc quán vừa tạm ngừng. Suspend đổi sang suspended và đặt `accepting_orders=false`. Gọi lặp cùng thao tác trả 200; có thể approve lại quán suspended, sau đó vendor chủ động bật nhận đơn. Quán không tồn tại trả 404. Vai trò admin được đọc lại từ DB như auth; chưa có API tự cấp admin hoặc seed tài khoản quản trị.

Quán pending/suspended không xuất hiện trong danh sách công khai và chi tiết công khai đều trả cùng 404 với quán không tồn tại. Quán approved vẫn xuất hiện khi đóng cửa hoặc tạm tắt nhận đơn; trạng thái giờ/cờ trong response cho biết điều kiện hiện tại.

### Response và phân trang

`RestaurantPublic` chỉ có các trường sau; ví dụ minh họa một quán được duyệt, đang tắt nhận đơn:

```json
{
  "id": 1,
  "name": "Bếp Vị Việt",
  "address": "Hà Nội",
  "latitude": 21.0285,
  "longitude": 105.8542,
  "delivery_radius_km": 5,
  "opens_at": "08:00",
  "closes_at": "22:00",
  "accepting_orders": false,
  "is_open": true,
  "can_receive_orders": false
}
```

`is_open` được tính tại thời điểm request theo `Asia/Ho_Chi_Minh`: gồm giờ mở, không gồm giờ đóng; qua đêm hợp lệ, hai mốc bằng nhau nghĩa là 24 giờ. `can_receive_orders = approved AND accepting_orders AND is_open` chỉ phản ánh điều kiện của quán, chưa kiểm tra vị trí khách, món bán hoặc nguyên liệu cần tránh. Các kiểm tra đặt đơn/lọc khoảng cách được làm ở phần tiếp theo. Hai trường tính toán không phải cột DB.

Response quản lý (`RestaurantDetail`) thêm `status` và `is_simulated`. API công khai không trả membership/tài khoản chủ quán, trạng thái nội bộ hoặc cờ mô phỏng. Giờ response luôn là `HH:MM`.

Hai endpoint danh sách nhận `offset` mặc định 0, trong 0–2147483647; `limit` mặc định 20, trong 1–100. Sắp xếp tăng dần theo ID, response `{"items":[...],"total":3,"offset":0,"limit":20}`; offset vượt số dòng trả danh sách rỗng, total vẫn là tổng số quán phù hợp. Admin còn nhận filter `status=pending|approved|suspended`; công khai luôn lọc approved. ID trên path trong 1–2147483647; tham số sai trả 422.

| HTTP | Mã lỗi | Trường hợp |
| :--- | :--- | :--- |
| 401 | `UNAUTHENTICATED` | Thiếu/sai/hết hạn access token ở endpoint quản lý |
| 403 | `FORBIDDEN` | Vai trò không đúng; admin cũng không dùng endpoint vendor |
| 404 | `NOT_FOUND` | Chưa liên kết quán, quán không tồn tại hoặc không công khai |
| 409 | `RESTAURANT_ALREADY_LINKED` | Vendor đã có membership |
| 409 | `RESTAURANT_NOT_APPROVED` | Bật nhận đơn khi quán chưa approved |
| 422 | `VALIDATION_ERROR` | Trường thiếu/thừa, kiểu/giới hạn/giờ không hợp lệ |

Phần này không đổi schema/revision `001`. Ghi hồ sơ và trạng thái dùng khóa hàng `FOR UPDATE` khi hệ quản trị hỗ trợ; PK membership vẫn bảo vệ liên kết duy nhất. Kiểm thử hiện dùng SQLite tạm và có ca mô phỏng race/lỗi ghi để kiểm tra rollback; chưa xác nhận khóa hàng hoặc cạnh tranh thực tế trên PostgreSQL.

## Thực đơn, món chuẩn và nguyên liệu — F.10.2

Prefix `/api/v1`. Đây là API backend, chưa có giao diện quản lý thực đơn. Bổ sung 17 thao tác API; danh mục nguyên liệu và các thao tác sửa/xóa món chuẩn cụ thể hóa yêu cầu CRUD của thiết kế, không thêm bảng mới.

| Method | Đường dẫn | Quyền | Kết quả |
| :--- | :--- | :--- | :--- |
| GET | `/restaurants/{restaurant_id}/menu` | Công khai | Mảng món đang bán của quán approved |
| GET | `/menu-items/{item_id}` | Công khai | Chi tiết món đang bán của quán approved |
| GET | `/canonical-dishes` | Công khai | Trang danh mục món chuẩn để tra cứu/chọn món |
| GET | `/ingredients` | Công khai | Trang danh mục nguyên liệu |
| GET | `/vendor/menu-items` | vendor | Trang thực đơn của mình, gồm cả món ngừng bán |
| GET | `/vendor/menu-items/{item_id}` | vendor | Chi tiết món của mình |
| POST | `/vendor/menu-items` | vendor | Tạo món của mình, trả 201 |
| PUT | `/vendor/menu-items/{item_id}` | vendor | Thay toàn bộ dữ liệu món của mình, trả 200 |
| DELETE | `/vendor/menu-items/{item_id}` | vendor | Ngừng bán, trả 204 không body |
| GET | `/admin/canonical-dishes` | admin | Trang món chuẩn có thông tin nội bộ |
| POST | `/admin/canonical-dishes` | admin | Tạo món chuẩn, trả 201 |
| PUT | `/admin/canonical-dishes/{entry_id}` | admin | Thay toàn bộ món chuẩn, trả 200 |
| DELETE | `/admin/canonical-dishes/{entry_id}` | admin | Xóa mục chưa được dùng, trả 204 |
| GET | `/admin/ingredients` | admin | Trang nguyên liệu có thông tin nội bộ |
| POST | `/admin/ingredients` | admin | Tạo nguyên liệu, trả 201 |
| PUT | `/admin/ingredients/{entry_id}` | admin | Đổi tên nguyên liệu, trả 200 |
| DELETE | `/admin/ingredients/{entry_id}` | admin | Xóa mục chưa được dùng, trả 204 |

### Quản lý món bán

POST/PUT vendor nhận cùng cấu trúc sau:

```json
{
  "canonical_dish_id": 1,
  "name": "Phở bò tái",
  "price": 45000,
  "is_available": true,
  "ingredients_verified": true,
  "ingredient_ids": [1, 2]
}
```

POST bắt buộc `canonical_dish_id`, `name`, `price`; mặc định hai cờ false và `ingredient_ids=[]`. PUT yêu cầu đủ sáu trường; danh sách nguyên liệu thay toàn bộ liên kết trong cùng transaction với tên/giá/cờ. Danh sách có thể rỗng nếu `ingredients_verified=false`; `true` bắt buộc khai báo ít nhất một nguyên liệu thực tế. Cờ này là xác nhận của vendor, không bảo đảm an toàn thực phẩm hoặc thay thế kiểm tra nguyên liệu cần tránh.

Tên trim dài 1–180. Giá là số nguyên JSON trong 1–10.000.000 VNĐ; không nhận chuỗi, số thập phân hoặc Boolean. Các ID body là số nguyên JSON trong 1–2147483647; `ingredient_ids` tối đa 100 ID khác nhau. Cờ nhận đúng Boolean JSON. Món chuẩn hoặc nguyên liệu không tồn tại trả 404 và không lưu dở dang. Mọi body ghi đều cấm trường thừa, gồm `restaurant_id`, `user_id`, `id`, `is_simulated`.

Server lấy quán từ membership của vendor; không cho chọn quán đích. Vendor chưa có membership trả 404. Món ngoài quán của mình và món không tồn tại cùng trả 404; admin không được dùng API vendor. Nhiều vendor cùng membership quán có thể quản lý chung. Chủ quán pending/suspended vẫn chuẩn bị thực đơn nhưng món chưa được công khai.

DELETE vendor chỉ đặt `is_available=false`, giữ ID, nguyên liệu, dữ liệu đơn hàng/đánh giá/tracking. Gọi lặp trả 204; GET vendor vẫn xem được, PUT có thể bật bán lại. Không có API xóa vĩnh viễn MenuItem. Thay tên/giá không sửa snapshot của đơn đã có.

### Quản lý danh mục

POST món chuẩn nhận ví dụ sau; PUT yêu cầu đủ cả bảy trường (kể cả `source_id` với giá trị null nếu không có):

```json
{
  "name": "Phở bò",
  "region": "Bắc",
  "method": "nước",
  "spice_level": 0,
  "ingredients": ["bò", "bánh phở"],
  "labels": ["Truyền thống"],
  "source_id": null
}
```

`name`, `region`, `method` bắt buộc khi POST; bốn trường còn lại mặc định lần lượt 0, [], [], null. Tên trim 1–180; vùng/cách chế biến trim 1–40; mức cay số nguyên 0–3. `source_id` tùy chọn, khi có trim 1–120. Tên và source_id có UNIQUE riêng; tên giữ hoa/thường theo model hiện có, không tự gộp các tên gần giống. Cho phép nhiều dòng có source_id null.

`ingredients`/`labels` là mảng tối đa 100 chuỗi; từng chuỗi trim 1–100 ký tự, loại trùng không phân biệt hoa/thường. Nguyên liệu chuyển chữ thường, nhãn giữ cách viết đầu tiên sau trim. Đây là đặc trưng dùng chung; nguyên liệu thực tế của món bán lấy từ `ingredient_ids`, không suy ra từ JSON món chuẩn.

POST/PUT nguyên liệu chỉ nhận `{"name":"hành"}`; trim/chuyển chữ thường, dài 1–100, tên duy nhất. Các mục tạo mới luôn `is_simulated=false`; API không cho sửa cờ mô phỏng. Sửa catalog có hiệu lực ở lần đọc món tiếp theo; không sửa snapshot giao dịch.

DELETE catalog xóa vật lý mục chưa được tham chiếu. Món chuẩn có bất kỳ MenuItem nào, hoặc nguyên liệu còn trong MenuItemIngredient, trả 409 `CATALOG_IN_USE`, kể cả món đã ngừng bán. Mục không tồn tại trả 404. Không tự xóa các liên kết để vượt qua ràng buộc tham chiếu.

### Response và phạm vi công khai

MenuItem công khai trả `id`, `restaurant_id`, `restaurant_name`, `canonical_dish_id`, `name`, `price`, `is_available`, `ingredients_verified`, đối tượng `canonical_dish` và mảng `ingredients` thực tế. `canonical_dish` gồm id/name/region/method/spice_level/ingredients/labels; mỗi nguyên liệu thực tế chỉ gồm id/name, sắp xếp theo ID. Response vendor thêm `is_simulated` của món bán. Response catalog admin thêm `is_simulated` và `source_id` của món chuẩn; catalog công khai và mọi catalog lồng trong MenuItem không trả các trường nội bộ đó.

Món công khai phải đang bán và quán approved. Món ngừng bán, quán pending/suspended và ID không tồn tại đều trả 404 ở chi tiết. Menu quán chưa công khai/không tồn tại trả 404; quán approved không còn món trả []. Quán approved đóng cửa hoặc tắt nhận đơn vẫn cho đọc món đang bán; API này chưa kiểm tra khoảng cách, vị trí, khẩu vị hoặc điều kiện đặt đơn.

Mọi danh sách nhận `offset=0` trong 0–2147483647, `limit=20` trong 1–100; sắp xếp tăng theo ID. Menu quán công khai trả **mảng** theo thiết kế; các danh sách catalog/vendor/admin trả `{"items":[...],"total":3,"offset":0,"limit":20}`. Offset vượt dữ liệu trả mảng rỗng nhưng total giữ tổng số mục phù hợp. ID path trong 1–2147483647.

| HTTP | Mã lỗi | Trường hợp |
| :--- | :--- | :--- |
| 401 | `UNAUTHENTICATED` | Thiếu/sai/hết hạn access token ở API quản lý |
| 403 | `FORBIDDEN` | Sai vai trò |
| 404 | `NOT_FOUND` | Không có membership, món/danh mục không tồn tại, món ngoài quyền hoặc chưa công khai |
| 409 | `DISH_NAME_EXISTS` | Trùng tên món chuẩn |
| 409 | `DISH_SOURCE_EXISTS` | Trùng mã nguồn món chuẩn |
| 409 | `INGREDIENT_EXISTS` | Trùng tên nguyên liệu đã chuẩn hóa |
| 409 | `CATALOG_IN_USE` | Danh mục còn được món bán tham chiếu |
| 422 | `VALIDATION_ERROR` | Thiếu/thừa trường, sai kiểu/giới hạn, lặp ID hoặc xác nhận khi chưa có nguyên liệu |

Không thay schema/revision `001`. Ghi món và liên kết nguyên liệu cùng transaction, rollback khi lỗi SQLAlchemy; khóa các hàng liên quan khi DB hỗ trợ. Kiểm thử chạy production app trên SQLite tạm được tạo bằng migration; chưa kiểm chứng PostgreSQL thực tế hoặc khóa hàng cạnh tranh. Tìm kiếm, đơn hàng, đánh giá và tracking được mô tả ở các mục F.10.3/F.10.5/F.10.6/F.10.8 riêng.

## Tìm kiếm món và quán — F.10.3

Hai endpoint công khai, không yêu cầu token:

| Method | Đường dẫn | Kết quả |
| :--- | :--- | :--- |
| GET | `/api/v1/search/dishes` | `DishSearchPage`: món đang bán của quán approved trong phạm vi |
| GET | `/api/v1/search/restaurants` | `RestaurantSearchPage`: quán approved trong phạm vi |

Hai endpoint nhận cùng query:

| Tham số | Bắt buộc | Quy tắc |
| :--- | :--- | :--- |
| `lat` | Có | Vĩ độ khách, số hữu hạn trong [-90, 90] |
| `lng` | Có | Kinh độ khách, số hữu hạn trong [-180, 180] |
| `radius` | Không | Bán kính km trong (0, 50], mặc định 5 |
| `q` | Không | Mặc định chuỗi rỗng; gộp khoảng trắng, tối đa 180 ký tự sau chuẩn hóa khoảng trắng |
| `offset` | Không | Số nguyên trong 0–2147483647, mặc định 0 |
| `limit` | Không | Số nguyên trong 1–100, mặc định 20 |

Thiếu tọa độ, NaN/Infinity, giá trị sai kiểu/giới hạn hoặc tham số ngoài schema trả 422 `VALIDATION_ERROR` theo envelope chung. Không tự dùng tọa độ mặc định ở Hà Nội khi client chưa chọn vị trí. Request không lưu vị trí vào hồ sơ người dùng và không có hành vi geocode địa chỉ.

Ví dụ:

```http
GET /api/v1/search/dishes?q=pho%20bo&lat=21.0285&lng=105.8542&radius=5&offset=0&limit=20
GET /api/v1/search/restaurants?q=ha%20noi&lat=21.0285&lng=105.8542
```

### Từ khóa và điều kiện lọc

- Tìm không phân biệt hoa/thường hoặc dấu tiếng Việt, gồm `đ`/`d` và chuỗi Unicode dựng sẵn/tổ hợp. Mỗi từ trong q phải xuất hiện dưới dạng chuỗi con trong các trường được tìm; thứ tự các từ không bắt buộc. q rỗng/toàn khoảng trắng trả kết quả gần vị trí khách.
- Tìm món đối chiếu **tên món bán, tên món chuẩn và tên quán**; tìm quán đối chiếu **tên quán và địa chỉ**. Không tìm trong thành phần nguyên liệu/nhãn, source_id hoặc tài khoản chủ quán. `%`, `_`, dấu nháy được tìm như ký tự bình thường, không là wildcard/cú pháp SQL.
- Quán phải approved. Món còn phải `is_available=true`; không gộp các MenuItem cùng món chuẩn, vì mỗi món bán có quán/giá riêng. Tìm quán có thể trả quán chưa có món đang bán.
- Khoảng cách đường chim bay dùng Haversine, bán kính Trái Đất quy ước 6371,0088 km. Kết quả phải có `distance_km <= radius` **và** `distance_km <= delivery_radius_km` của quán. Hai biên đều được tính; lọc/sắp xếp dùng số chưa làm tròn. Đây không phải khoảng cách đường bộ hoặc thời gian giao dự kiến.
- Quán approved đang đóng cửa/tắt nhận đơn vẫn xuất hiện kèm `is_open`, `accepting_orders`, `can_receive_orders` như API hồ sơ. Tìm kiếm là luồng khám phá; chưa cá nhân hóa theo khẩu vị, lọc nguyên liệu cần tránh hoặc bảo đảm đặt đơn thành công. `ingredients_verified` là khai báo của vendor, không phải chứng nhận an toàn.

### Response và phân trang

Cả hai trả `{"items":[...],"total":3,"offset":0,"limit":20}`. Lọc đủ điều kiện và sắp theo khoảng cách tăng dần trước khi phân trang; nếu cùng khoảng cách thì theo ID món bán/quán tăng dần. `total` là tổng sau lọc, không phải số mục trên trang. Không có kết quả hoặc offset vượt tổng trả 200 với items rỗng; total vẫn phản ánh toàn bộ kết quả phù hợp.

`RestaurantSearchResult` gồm toàn bộ `RestaurantPublic` ở F.10.1 và thêm `distance_km`. Giờ mở, trạng thái nhận đơn được tính tại cùng một thời điểm cho toàn trang theo giờ Việt Nam. `can_receive_orders` vẫn chỉ phản ánh trạng thái quán; chưa chứng minh có món/khả năng tạo đơn.

`DishSearchResult` gồm toàn bộ `MenuItemPublic` ở F.10.2 và thêm `distance_km`, `restaurant` là `RestaurantPublic` của quán bán. ID của kết quả là ID MenuItem dùng cho trang chi tiết/giỏ hàng sau này. `canonical_dish` là đặc trưng dùng chung, `ingredients` là nguyên liệu thực tế của MenuItem; không trộn hai nguồn. Không trả membership, source_id, cờ mô phỏng hoặc dữ liệu tài khoản trong kết quả hay các đối tượng lồng.

### Phạm vi triển khai

SQL lọc quán approved/món available và hộp tọa độ bao quanh bán kính; Python kiểm tra Haversine chính xác, chuẩn hóa chữ Unicode và sắp xếp/phân trang. Hộp tọa độ xử lý kinh tuyến 180° và vùng cực để không loại nhầm ứng viên hợp lệ. Nguyên liệu chỉ nạp theo lô cho trang món trả về, tránh truy vấn riêng từng món.

Cách triển khai phù hợp tập dữ liệu MVP quanh trường; vẫn phải đọc toàn bộ ứng viên trong hộp tọa độ để tính đúng total/thứ tự, chưa có chỉ mục tìm kiếm không dấu hoặc chỉ mục không gian. Không cắt ngầm số ứng viên và không công bố cam kết hiệu năng cho dữ liệu lớn. Khi mở rộng cần đo tải và đưa tìm chữ/khoảng cách vào cơ chế chỉ mục thích hợp. Không cần extension DB, đổi model/migration hoặc thêm thư viện ở phần này. Chưa có giao diện SearchPage hoặc tích hợp bản đồ; API đặt đơn mô tả bên dưới.

## Đơn COD và chống gửi lặp — F.10.5

Prefix `/api/v1`, tất cả endpoint yêu cầu access token đúng vai trò. Admin không thay thế customer/vendor. COD là thanh toán khi nhận hàng; chưa có thanh toán trực tuyến hoặc cột trạng thái thanh toán riêng.

| Method | Đường dẫn | Vai trò | Kết quả |
| :--- | :--- | :--- | :--- |
| POST | `/orders/` | customer | OrderDetail 201 khi tạo, 200 khi gửi lại hợp lệ |
| GET | `/orders/` | customer | Mảng đơn của mình |
| GET | `/orders/{order_id}` | customer | Chi tiết đơn của mình |
| PATCH | `/orders/{order_id}/cancel` | customer | Hủy đơn pending, trả OrderDetail |
| GET | `/vendor/orders` | vendor | Mảng đơn của quán từ membership |
| GET | `/vendor/orders/{order_id}` | vendor | Chi tiết đơn của quán |
| PATCH | `/vendor/orders/{order_id}/confirm` | vendor | pending → confirmed |
| PATCH | `/vendor/orders/{order_id}/reject` | vendor | pending → rejected; body reason bắt buộc |
| PATCH | `/vendor/orders/{order_id}/preparing` | vendor | confirmed → preparing |
| PATCH | `/vendor/orders/{order_id}/delivering` | vendor | preparing → delivering |
| PATCH | `/vendor/orders/{order_id}/complete` | vendor | delivering → completed |

### Tạo đơn

```json
{
  "restaurant_id": 1,
  "items": [{"menu_item_id": 1, "quantity": 2, "expected_price": 40000}],
  "delivery_address": "Số 1 Hà Nội",
  "latitude": 21,
  "longitude": 105,
  "session_id": "59738c0b-55c7-4423-b530-9fcabda63168",
  "idempotency_key": "f03f7b22-54eb-4c08-9438-ba829b874da8"
}
```

Tất cả trường trong ví dụ bắt buộc. Mỗi lần đặt mới client sinh UUID v4 mới; retry giữ nguyên session_id, key và payload. Items có 1–100 dòng không trùng menu_item_id; quantity nguyên JSON 1–99, expected_price nguyên JSON 1–10.000.000 VNĐ. ID body nguyên JSON 1–2147483647; không nhận Boolean/chuỗi thay số nguyên. Địa chỉ trim dài 5–500; tọa độ số JSON hữu hạn đúng phạm vi vĩ độ/kinh độ. Body tạo/từ chối và từng dòng món cấm trường thừa; không nhận user_id, total, status, snapshot hoặc is_simulated từ client.

Quán phải approved, đang mở theo giờ Việt Nam và bật accepting_orders. Khoảng cách Haversine từ tọa độ giao đến quán phải ≤ delivery_radius_km; không áp bán kính tìm kiếm của khách khi đặt. Mọi món phải thuộc cùng quán, đang bán và giá hiện tại bằng expected_price. Backend lấy tên/giá từ MenuItem, lưu snapshot, tính tổng quantity × giá và ghi lịch sử pending cùng transaction. Không tự sửa giá khách đang xem hoặc ghi đơn dở dang khi một dòng không hợp lệ. Địa chỉ dạng chữ chưa được geocode/đối chiếu với tọa độ; client chịu trách nhiệm chọn đúng điểm giao. Không có phí giao/thuế riêng trong bản mẫu.

### Idempotency

UNIQUE idempotency_key toàn hệ thống. Cùng khách, cùng nội dung trong vòng **dưới 24 giờ** kể từ tạo trả 200 với đơn đã có và trạng thái hiện tại; không tạo dòng món/lịch sử mới, không kiểm tra lại giá/khả dụng hiện tại. Hash payload gồm restaurant_id, items, địa chỉ đã trim, tọa độ và session_id; thứ tự các dòng món không ảnh hưởng. Giá kỳ vọng/số lượng/địa chỉ/session thay đổi là nội dung khác. Tọa độ -0 và 0 được coi như nhau.

Key của khách khác hoặc payload khác trả 409 IDEMPOTENCY_CONFLICT, không tiết lộ đơn cũ. Từ đúng mốc 24 giờ trả 409 IDEMPOTENCY_EXPIRED; không xóa/reuse key hoặc tạo thêm đơn. Client phải kiểm tra lịch sử trước khi chủ động đặt mới bằng key mới. Lỗi trước commit không tiêu thụ key. Khóa hàng khách/quán/món khi DB hỗ trợ và UNIQUE bảo vệ khi ghi cạnh tranh; kiểm thử hiện có mô phỏng tranh chấp, chưa xác nhận chạy đồng thời PostgreSQL thực tế.

### Đọc và xử lý đơn

OrderDetail có id, restaurant_id, status, total, delivery_address, latitude, longitude, created_at, items và history. Mỗi item có menu_item_id/quantity/snapshot_price/snapshot_name, sắp theo menu_item_id. History có status/reason/created_at, sắp thời điểm rồi ID; actor_id được lưu DB để truy vết nhưng không trả trong DTO. Không trả hash/key/session/cờ mô phỏng hoặc thông tin tài khoản. Timestamp là ISO 8601; SQLite có thể bỏ offset khi đọc lại như quy ước chung.

GET danh sách trả **mảng** theo thiết kế, mới nhất trước theo ID giảm dần; offset mặc định 0 trong 0–2147483647, limit mặc định 20 trong 1–100. Offset vượt dữ liệu trả []; không có total wrapper. ID path trong 1–2147483647. Khách chỉ thấy đơn của mình, vendor chỉ thấy đơn quán từ membership; đơn ngoài quyền và không tồn tại cùng 404, vendor chưa liên kết quán cũng 404. Chi tiết vendor bổ sung để xem địa chỉ giao/lịch sử khi xử lý đơn.

PATCH reject nhận `{"reason":"Hết nguyên liệu"}`, trim 1–500; các PATCH khác không cần body. Mỗi thao tác thành công trả 200 với OrderDetail, ghi đúng một dòng lịch sử. Sai thứ tự, gọi lặp hoặc đổi trạng thái cuối trả 409; không tự coi lặp PATCH là thành công. Khách chỉ hủy pending; confirmed/preparing/delivering không được hủy. Quán đóng cửa/tạm ngừng vẫn xử lý được đơn đã nhận trước đó. Snapshot/tổng/địa chỉ giữ nguyên khi chuyển trạng thái; không có API sửa/xóa đơn.

| HTTP | Mã lỗi | Trường hợp |
| :--- | :--- | :--- |
| 401 / 403 | UNAUTHENTICATED / FORBIDDEN | Thiếu/sai token hoặc sai vai trò |
| 404 | NOT_FOUND | Quán không approved/tồn tại, đơn ngoài quyền/không tồn tại, thiếu membership |
| 400 | OUTSIDE_DELIVERY_AREA | Tọa độ giao nằm ngoài phạm vi quán |
| 400 | ORDER_ITEM_INVALID | Món không tồn tại hoặc thuộc quán khác |
| 409 | RESTAURANT_UNAVAILABLE | Quán đóng cửa hoặc tắt nhận đơn |
| 409 | ORDER_ITEM_UNAVAILABLE | Món ngừng bán |
| 409 | ORDER_PRICE_CHANGED | Giá khác expected_price; details có menu_item_id/current_price |
| 409 | IDEMPOTENCY_CONFLICT / IDEMPOTENCY_EXPIRED | Key đã dùng khác nội dung/chủ sở hữu hoặc hết 24 giờ |
| 409 | INVALID_STATE_TRANSITION / ORDER_STATE_CHANGED | Sai thứ tự hoặc trạng thái thay đổi cạnh tranh |
| 422 | VALIDATION_ERROR | Body/query/path sai giới hạn/kiểu hoặc thiếu/thừa trường |

Schema vẫn revision 001. API review được mô tả ở F.10.6; chưa có giao diện giỏ hàng/checkout/xử lý đơn hoặc thu phí trực tuyến. Không cam kết xử lý tải lớn hoặc khóa hàng PostgreSQL trước khi kiểm chứng môi trường thật.

## Đánh giá món đã mua — F.10.6

`POST /api/v1/orders/{order_id}/review` yêu cầu Bearer access token vai trò customer; thành công trả 201 với ReviewOut. Body:

```json
{"menu_item_id": 1, "rating": 5, "comment": "Rất ngon"}
```

`menu_item_id` và `rating` bắt buộc. ID nguyên JSON 1–2147483647; rating nguyên JSON 1–5, không nhận Boolean/chuỗi/thập phân. Comment tùy chọn, mặc định chuỗi rỗng, trim và dài tối đa 2000 ký tự sau trim; không nhận giá trị null/số. Body cấm trường thừa, gồm user_id/order_id/is_simulated. ID path phải trong 1–2147483647.

Chỉ người mua đúng đơn ở trạng thái completed mới gửi được; món phải là OrderItem của **đơn đó**. Đơn ngoài quyền hoặc không tồn tại trả cùng 404, món không thuộc đơn trả 404; đơn chưa completed trả 409 `ORDER_NOT_COMPLETED`. Mỗi cặp order_id/menu_item_id được đánh giá tối đa một lần, gửi lại trả 409 `REVIEW_ALREADY_EXISTS` kể cả khi thay nội dung. Món có thể được đánh giá lại sau một đơn mua khác. API ghi cờ mô phỏng false; không liên quan feedback phù hợp của gợi ý.

Response gồm `id`, `order_id`, `menu_item_id`, `snapshot_name`, `snapshot_price`, `rating`, `comment`, `created_at`. Tên/giá lấy từ OrderItem lúc mua, không bị đổi khi quán sửa thực đơn/ngừng bán. Không trả actor/user_id hoặc cờ mô phỏng. Review được lưu cùng transaction, rollback khi lỗi; UNIQUE ghép và FK ghép ở revision 001 bảo vệ chống trùng/món chưa mua ở tầng DB. Kiểm thử dùng SQLite tạm; chưa kiểm chứng PostgreSQL cạnh tranh thực tế. Chưa có API liệt kê/sửa/xóa đánh giá hoặc frontend ReviewForm; sẽ làm riêng nếu cần theo giao diện F.12.

## Hồ sơ khẩu vị — F.10.7

GET và PUT `/api/v1/preferences/` yêu cầu access token vai trò `customer`. Khách bỏ qua năm câu hỏi sẽ không có bản ghi; GET trả 404 `NOT_FOUND`. PUT tạo hồ sơ nếu chưa có hoặc thay toàn bộ năm câu trả lời nếu đã có, trả 200. ID người dùng lấy từ token; không nhận `user_id` hay cờ mô phỏng trong body. Vendor/admin nhận 403.

```json
{
  "regions": ["Bắc", "Nam"],
  "spice_level": 2,
  "liked_ingredients": ["bò", "hành"],
  "avoided_ingredients": ["đậu phộng"],
  "exploration_level": 1
}
```

PUT yêu cầu đủ năm trường. Hai mức là số nguyên JSON: spice_level 0–3 (không/ít/vừa/rất cay), exploration_level 0–2 (món quen/cân bằng/khám phá); không nhận Boolean, thập phân hoặc chuỗi số. Ba danh sách cho phép rỗng, mỗi danh sách tối đa 100 chuỗi, mỗi chuỗi sau trim dài 1–100 ký tự. Loại trùng không phân biệt hoa/thường; vùng miền giữ cách viết đầu tiên, nguyên liệu chuyển chữ thường. Danh sách 101 phần tử bị từ chối dù trùng nhau. Trường thừa/thiếu, phần tử rỗng/sai kiểu và mức sai trả 422 `VALIDATION_ERROR`. GET/PUT chỉ trả đúng năm trường.

Ghi năm câu trả lời cùng transaction, rollback khi lỗi; khóa hàng User và Preference khi DB hỗ trợ. PK user_id bảo đảm tối đa một hồ sơ; tranh chấp tạo lần đầu được xử lý sau rollback. Chưa kiểm tra danh sách thích/tránh giao nhau; lọc món cần tránh thuộc pipeline gợi ý riêng. API không lưu tọa độ hoặc lịch sử đồng ý điều khoản. Chưa có màn hình PreferencePage.

## Ghi nhận sự kiện tương tác — F.10.8

POST `/api/v1/tracking/events` yêu cầu Bearer access token vai trò `customer`. Body gồm `events`, mảng 1–100 sự kiện. Mỗi sự kiện cần `event_id` và `session_id` là UUID v4, `event_type` thuộc sáu mã bên dưới, `occurred_at` là thời điểm có múi giờ. `request_id`, `menu_item_id`, `value` chỉ dùng theo ngữ cảnh. ID người dùng, thời điểm tiếp nhận và cờ mô phỏng lấy từ máy chủ; body không nhận trường thừa.

```json
{
  "events": [
    {
      "event_id": "9e54e6a0-66c6-45ba-b532-d257bf87e004",
      "session_id": "45d20d74-fb7c-45d9-840d-3a29e3b24451",
      "event_type": "impression",
      "request_id": "b5ee0e38-b818-4fa8-9871-5e56fa42d685",
      "menu_item_id": 1,
      "occurred_at": "2026-11-27T10:00:00+07:00"
    }
  ]
}
```

| `event_type` | `request_id` | `menu_item_id` | `value` |
| :--- | :--- | :--- | :--- |
| `impression`, `click` | Bắt buộc | Bắt buộc | Không gửi |
| `feedback` | Bắt buộc | Bắt buộc | 0 hoặc 1 |
| `add_to_cart` | Tùy chọn | Bắt buộc | Không gửi |
| `session_start`, `session_end` | Không gửi | Không gửi | Không gửi |

Request gợi ý phải thuộc đúng tài khoản và phiên; món có `request_id` phải nằm trong danh sách gợi ý đó. `impression` đầu tiên ghi `displayed_at` theo `occurred_at`; tạo dòng gợi ý chưa được tính là hiển thị. `click` và `feedback` chỉ được nhận sau khi món đã hiển thị, kể cả khi hai sự kiện nằm cùng batch theo đúng thứ tự. `add_to_cart` không có request vẫn được nhận cho món tồn tại. Giá trị feedback 0 nghĩa là không phù hợp, 1 là phù hợp.

Sự kiện mới chỉ được nhận nếu `occurred_at` nằm trong 24 giờ trước đến 5 phút sau thời điểm máy chủ tiếp nhận. Gửi lại cùng `event_id` và nội dung sau thời hạn vẫn được tính là bản trùng, không tạo thêm dòng. Cả batch là một transaction: lỗi ở một sự kiện sẽ rollback mọi sự kiện và mốc hiển thị trong batch đó. Thành công trả 200 với `{"accepted":1,"duplicates":0}`; `accepted` là số dòng mới, `duplicates` là số lần gửi lại cùng nội dung. Gửi cùng `event_id` với nội dung khác trả 409 `EVENT_ID_CONFLICT`.

| HTTP | Mã lỗi | Khi nào |
| :--- | :--- | :--- |
| 401 / 403 | `UNAUTHENTICATED` / `FORBIDDEN` | Thiếu/sai token hoặc không phải customer |
| 404 | `NOT_FOUND` | Request ngoài quyền/phiên, món không tồn tại hoặc không thuộc danh sách gợi ý |
| 400 | `EVENT_TIME_INVALID` | Thời điểm sự kiện mới ngoài cửa sổ tiếp nhận |
| 409 | `IMPRESSION_NOT_DISPLAYED` / `EVENT_ID_CONFLICT` | Chưa hiển thị trước click/feedback; dùng lại ID khác nội dung hoặc xung đột ghi |
| 422 | `VALIDATION_ERROR` | Body, UUID, mã sự kiện, ngữ cảnh hoặc số lượng sai |

API sinh request/danh sách gợi ý và giao diện gửi sự kiện sẽ tích hợp ở phần riêng; API này chỉ tiếp nhận request đã được tạo hợp lệ. Không đổi migration `001`. Kiểm thử hiện dùng SQLite tạm; chưa xác nhận hành vi cạnh tranh trên PostgreSQL thực tế.

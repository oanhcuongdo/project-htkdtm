# Từ điển dữ liệu Vị Việt

Phạm vi: 15 bảng OLTP của models F.5 và [migration `001`](../src/backend/alembic/versions/001_initial_schema.py), tương ứng bước F.7 của [thiết kế](THIET_KE_CAU_TRUC.md). [ERD](ERD.md) trình bày quan hệ, lực lượng và danh mục đầy đủ 24 FK cùng quy tắc xóa. Chưa có bảng fact, BI view, Session hoặc đánh giá mù. Bảng kỹ thuật `alembic_version` do Alembic quản lý, không phải thực thể nghiệp vụ.

## Quy ước

- Kiểu trong bảng là kiểu SQL hướng PostgreSQL: `TIMESTAMPTZ` viết gọn cho `TIMESTAMP WITH TIME ZONE`; `TIME` là `TIME WITHOUT TIME ZONE`; `FLOAT` theo khai báo SQLAlchemy. Enum được lưu `VARCHAR` kèm CHECK, không tạo PostgreSQL enum type.
- `NULL = Có` cho phép SQL NULL; các cột còn lại bắt buộc có giá trị. `—` trong cột mặc định nghĩa là không có server default, không có nghĩa cho phép NULL. PK số nguyên `id` được DB cấp tự động (PostgreSQL dùng SERIAL trong revision này); PK lấy từ FK không tự cấp.
- Mặc định ghi dưới đây là mặc định phía DB. Các timestamp `CURRENT_TIMESTAMP` cũng có mặc định UTC từ ORM; `recommendation_requests.id` được ORM cấp UUID v4 nhưng không có mặc định phía DB. Ghi SQL trực tiếp phải tự cấp UUID này.
- Tiền là số nguyên VNĐ, không dùng số thực. Giờ phục vụ là giờ địa phương Việt Nam UTC+7. ORM cấp thời điểm mặc định UTC; validator của orders/reviews/tracking yêu cầu timestamp gán trực tiếp có múi giờ và chuẩn hóa UTC. `User.created_at` chưa có validator tương ứng. PostgreSQL lưu thời điểm tuyệt đối, cách hiển thị phụ thuộc múi giờ kết nối. SQLite trong kiểm thử không bảo toàn đầy đủ ngữ nghĩa múi giờ như PostgreSQL.
- JSON hiện dùng kiểu `JSON`, không phải `JSONB`. Các danh sách mặc định `[]` dùng MutableList ở ORM; DB chưa CHECK cấu trúc mảng, kiểu phần tử hoặc danh sách giá trị hợp lệ.
- `is_simulated=false` là giá trị mặc định, không tự chứng minh dữ liệu thật. Bộ seed/nhập dữ liệu sau này phải gán `true` cho dữ liệu mô phỏng. Cờ có trên 10 bảng được ghi bên dưới; các bảng liên kết, khẩu vị, dòng đơn và lịch sử không có cờ riêng.
- Mọi FK dùng `ON DELETE RESTRICT`, ngoại trừ `preferences.user_id` và `menu_item_ingredients.menu_item_id` dùng CASCADE. Chi tiết FK ghép xem ERD. Các index được liệt kê là index khai báo riêng, không liệt kê lại index do PK/UNIQUE tạo.

## 1. `users` — Tài khoản

Model: [`User`](../src/backend/app/users/models.py). Một dòng cho một tài khoản chung của ba vai trò.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `email` | VARCHAR(254) | Không | — | Email, UNIQUE |
| `full_name` | VARCHAR(120) | Không | — | Họ tên |
| `hashed_password` | VARCHAR(256) | Không | — | Chuỗi băm Passlib PBKDF2-SHA256 do module auth tạo/kiểm tra |
| `role` | VARCHAR(20) | Không | `'customer'` | Vai trò |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |
| `created_at` | TIMESTAMPTZ | Không | CURRENT_TIMESTAMP | Thời điểm tạo |

Ràng buộc DB: `uq_users_email` UNIQUE `(email)`; `ck_users_role` chỉ nhận `customer`, `vendor`, `admin`. Không có index khai báo riêng.

ORM bỏ khoảng trắng, chuyển email về chữ thường và chặn email rỗng; họ tên bỏ khoảng trắng và chặn rỗng. DB chưa có CHECK cho định dạng email/họ tên hoặc index không phân biệt hoa thường: ghi trực tiếp có thể bỏ qua chuẩn hóa. Module auth xử lý đăng nhập, băm/kiểm tra mật khẩu và dependency phân quyền; schema không tự bảo đảm một chuỗi được ghi trực tiếp là hash hợp lệ. Xem [API contract](API_CONTRACT.md).

## 2. `preferences` — Hồ sơ khẩu vị

Model: [`Preference`](../src/backend/app/preferences/models.py). Tối đa một hồ sơ trên mỗi tài khoản; chưa có dòng nghĩa là người dùng chưa khai báo.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | INTEGER | Không | — | PK, FK → `users.id`, xóa CASCADE |
| `regions` | JSON | Không | `'[]'` | Danh sách vùng miền ưa thích |
| `spice_level` | INTEGER | Không | 0 | Mức cay 0–3 |
| `liked_ingredients` | JSON | Không | `'[]'` | Danh sách nguyên liệu thích |
| `avoided_ingredients` | JSON | Không | `'[]'` | Danh sách nguyên liệu cần tránh |
| `exploration_level` | INTEGER | Không | 1 | Mức sẵn sàng thử món mới 0–2 |

CHECK: `ck_preferences_spice_level` trong 0–3; `ck_preferences_exploration_level` trong 0–2. Không có UNIQUE/index khai báo riêng ngoài PK.

Mức cay: 0 không cay, 1 ít, 2 vừa, 3 rất cay. Mức khám phá: 0 món quen, 1 cân bằng, 2 ưu tiên khám phá. Khi gán danh sách qua ORM, phần tử phải là chuỗi không rỗng, được bỏ khoảng trắng và loại trùng không phân biệt hoa thường; nguyên liệu chuyển chữ thường. Chưa kiểm tra danh sách thích/tránh giao nhau hoặc áp dụng lọc gợi ý. Thao tác sửa danh sách tại chỗ được MutableList theo dõi nhưng không tự chạy lại toàn bộ validator khi gán thuộc tính.

API F.10.7 cho customer GET/PUT toàn bộ năm câu trả lời của mình; bỏ qua không tạo bản ghi. Mỗi danh sách tối đa 100 chuỗi 1–100 ký tự sau trim; hai mức là số nguyên đúng khoảng. Không có cột đồng ý điều khoản hoặc lịch sử thay đổi hồ sơ; gợi ý chưa dùng hồ sơ này.

## 3. `restaurants` — Quán

Model: [`Restaurant`](../src/backend/app/restaurants/models.py). Hồ sơ và điều kiện phục vụ của một quán.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `name` | VARCHAR(160) | Không | — | Tên quán |
| `address` | VARCHAR(500) | Không | — | Địa chỉ quán |
| `latitude` | FLOAT | Không | — | Vĩ độ |
| `longitude` | FLOAT | Không | — | Kinh độ |
| `delivery_radius_km` | FLOAT | Không | 5 | Bán kính giao hàng, km |
| `opens_at` | TIME | Không | `'00:00:00'` | Giờ mở cửa địa phương |
| `closes_at` | TIME | Không | `'00:00:00'` | Giờ đóng cửa địa phương |
| `accepting_orders` | BOOLEAN | Không | false | Cờ nhận đơn |
| `status` | VARCHAR(20) | Không | `'pending'` | Trạng thái duyệt |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |

CHECK: `ck_restaurants_name` và `ck_restaurants_address` giới hạn độ dài sau trim lần lượt 1–160, 1–500; `ck_restaurants_latitude` trong [-90, 90]; `ck_restaurants_longitude` trong [-180, 180]; `ck_restaurants_delivery_radius` lớn hơn 0 và không quá 50; `ck_restaurants_status` nhận `pending`, `approved`, `suspended`. Không có UNIQUE/index khai báo riêng.

ORM trim tên/địa chỉ, chặn tọa độ/bán kính không hữu hạn, nhận giờ không kèm múi giờ với độ chính xác phút (`time` hoặc chuỗi `HH:MM`). API F.10.1 kiểm tra giờ đúng `HH:MM`; service tính `is_open` và `can_receive_orders` từ giờ Việt Nam, trạng thái duyệt và cờ nhận đơn. Khoảng qua đêm hợp lệ; hai mốc bằng nhau là 24 giờ. Các trường tính toán không thêm cột DB; DB chưa CHECK độ chính xác phút. Search F.10.3 tính distance_km từ vị trí khách trong query, lọc theo cả bán kính khách và delivery_radius_km của quán; không lưu vị trí khách vào bảng. API tạo đơn F.10.5 đã kiểm tra phạm vi giao tại thời điểm đặt.

## 4. `restaurant_memberships` — Liên kết người quản lý quán

Model: [`RestaurantMembership`](../src/backend/app/restaurants/models.py). Mỗi tài khoản tối đa một quán, một quán có thể có nhiều tài khoản.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `user_id` | INTEGER | Không | — | PK, FK → `users.id` |
| `restaurant_id` | INTEGER | Không | — | FK → `restaurants.id` |

Index: `ix_restaurant_memberships_restaurant_id` trên `(restaurant_id)`. Không có CHECK/UNIQUE riêng ngoài PK. Membership không tự cấp vai trò `vendor`; API hồ sơ quán hiện kiểm tra vai trò và lấy đúng quán từ membership. POST vendor tạo quán/membership cùng transaction; chưa có API gán/chuyển membership sang tài khoản khác. Xóa cha có membership bị chặn; cần xử lý liên kết trước.

## 5. `canonical_dishes` — Danh mục món chuẩn

Model: [`CanonicalDish`](../src/backend/app/menu/models.py). Đặc trưng món dùng chung, tách khỏi giá và khả dụng từng quán.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `name` | VARCHAR(180) | Không | — | Tên món chuẩn, UNIQUE |
| `region` | VARCHAR(40) | Không | — | Nhãn vùng miền |
| `spice_level` | INTEGER | Không | 0 | Mức cay 0–3 |
| `method` | VARCHAR(40) | Không | — | Cách chế biến |
| `ingredients` | JSON | Không | `'[]'` | Nguyên liệu đặc trưng; không phải FK |
| `labels` | JSON | Không | `'[]'` | Nhãn đặc trưng |
| `source_id` | VARCHAR(120) | Có | — | Mã truy vết nguồn, UNIQUE khi có |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |

UNIQUE: `uq_canonical_dishes_name` trên `(name)`, `uq_canonical_dishes_source_id` trên `(source_id)`; cho phép nhiều dòng không có `source_id`. CHECK: `ck_canonical_dishes_name` trim dài 1–180; `ck_canonical_dishes_region` và `ck_canonical_dishes_method` trim dài 1–40; `ck_canonical_dishes_source_id` NULL hoặc trim dài 1–120; `ck_canonical_dishes_spice_level` trong 0–3. Không có index khai báo riêng.

ORM trim các chuỗi, chuẩn hóa danh sách như khẩu vị; nguyên liệu chuyển chữ thường, nhãn giữ cách viết sau trim. Tên món không tự chuyển chữ thường, UNIQUE không phải quy tắc gộp tên tương đương. JSON nguyên liệu đặc trưng không chứng minh thành phần thực tế của món bán. API F.10.2 giới hạn mỗi danh sách 100 chuỗi, mỗi chuỗi trim 1–100 ký tự; admin quản lý catalog, xóa mục còn có MenuItem trả 409. source_id/cờ mô phỏng chỉ trả trong catalog admin; API không cho client sửa cờ mô phỏng.

## 6. `ingredients` — Danh mục nguyên liệu

Model: [`Ingredient`](../src/backend/app/menu/models.py).

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `name` | VARCHAR(100) | Không | — | Tên nguyên liệu, UNIQUE |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |

`uq_ingredients_name` UNIQUE `(name)`; `ck_ingredients_name` trim dài 1–100. Không có index riêng. ORM và API F.10.2 trim/chuyển tên về chữ thường; ghi SQL trực tiếp chưa tự chuẩn hóa tên. Admin CRUD danh mục; xóa nguyên liệu còn được MenuItemIngredient sử dụng trả 409.

## 7. `menu_items` — Món bán tại quán

Model: [`MenuItem`](../src/backend/app/menu/models.py).

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `restaurant_id` | INTEGER | Không | — | FK → `restaurants.id` |
| `canonical_dish_id` | INTEGER | Không | — | FK → `canonical_dishes.id` |
| `name` | VARCHAR(180) | Không | — | Tên hiển thị trên thực đơn |
| `price` | INTEGER | Không | — | Giá một phần, VNĐ |
| `is_available` | BOOLEAN | Không | false | Cờ đang bán/có sẵn |
| `ingredients_verified` | BOOLEAN | Không | false | Cờ đã xác nhận nguyên liệu thực tế |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |

CHECK: `ck_menu_items_name` trim dài 1–180; `ck_menu_items_price` trong (0, 10.000.000]. Index: `ix_menu_items_restaurant_id` trên `(restaurant_id)`, `ix_menu_items_canonical_dish_id` trên `(canonical_dish_id)`. Không có UNIQUE tên hoặc UNIQUE cặp quán/món chuẩn.

ORM trim tên, chặn giá không phải số nguyên hợp lệ. API F.10.2 lấy quán từ membership vendor, lưu món và liên kết nguyên liệu cùng transaction; ingredients_verified=true cần ít nhất một ID nguyên liệu thực tế. Cờ xác nhận không bảo đảm an toàn với nguyên liệu cần tránh. DELETE vendor chỉ đặt is_available=false, giữ bản ghi/liên kết và các tham chiếu giao dịch/tracking; PUT có thể bật bán lại. Chỉ món đang bán của quán approved được đọc công khai; đóng cửa/tắt nhận đơn không ẩn thực đơn. Không thêm cột hoặc sửa migration cho các quy tắc API này.

## 8. `menu_item_ingredients` — Nguyên liệu thực tế của món bán

Model: [`MenuItemIngredient`](../src/backend/app/menu/models.py).

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `menu_item_id` | INTEGER | Không | — | Thành phần PK ghép, FK → `menu_items.id`, xóa CASCADE |
| `ingredient_id` | INTEGER | Không | — | Thành phần PK ghép, FK → `ingredients.id` |

PK `(menu_item_id, ingredient_id)` chống lặp nguyên liệu trong cùng món bán. Không có CHECK/UNIQUE/index riêng. Xóa món khi được phép sẽ xóa liên kết, không xóa danh mục nguyên liệu. Bảng chưa lưu định lượng nguyên liệu.

## 9. `orders` — Đơn hàng COD

Model: [`Order`](../src/backend/app/orders/models.py). Một đơn tham chiếu một khách và một quán; không có cột thanh toán trực tuyến.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `user_id` | INTEGER | Không | — | FK → `users.id`, người đặt |
| `restaurant_id` | INTEGER | Không | — | FK → `restaurants.id`, quán nhận |
| `status` | VARCHAR(20) | Không | `'pending'` | Trạng thái hiện tại |
| `total` | BIGINT | Không | — | Tổng tiền nguyên VNĐ, dương |
| `delivery_address` | VARCHAR(500) | Không | — | Địa chỉ giao hàng |
| `latitude` | FLOAT | Không | — | Vĩ độ giao hàng |
| `longitude` | FLOAT | Không | — | Kinh độ giao hàng |
| `session_id` | UUID | Không | — | Mã phiên client, không phải FK |
| `idempotency_key` | UUID | Không | — | Khóa gửi lặp do client cấp, UNIQUE toàn bảng |
| `payload_hash` | VARCHAR(64) | Không | — | SHA-256 hex của nội dung yêu cầu |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |
| `created_at` | TIMESTAMPTZ | Không | CURRENT_TIMESTAMP | Thời điểm tạo |

UNIQUE: `uq_orders_idempotency_key` trên `(idempotency_key)`. CHECK: `ck_orders_total` lớn hơn 0; `ck_orders_delivery_address` trim dài 5–500; `ck_orders_latitude` trong [-90, 90]; `ck_orders_longitude` trong [-180, 180]; `ck_orders_payload_hash` dài đúng 64; `ck_orders_status` nhận bảy trạng thái ở bảng dưới. Index: `ix_orders_user_id` trên `(user_id)`, `ix_orders_restaurant_id` trên `(restaurant_id)`, `ix_orders_session_id` trên `(session_id)`.

| Mã trạng thái | Ý nghĩa |
| :--- | :--- |
| `pending` | Chờ quán xác nhận |
| `confirmed` | Đã xác nhận |
| `preparing` | Đang chuẩn bị |
| `delivering` | Đang giao |
| `completed` | Đã hoàn tất |
| `cancelled` | Đã hủy |
| `rejected` | Quán từ chối |

ORM yêu cầu UUID v4 cho session/key; hash gồm 64 ký tự hex; tổng tiền nguyên dương BIGINT; trim địa chỉ, chặn tọa độ không hữu hạn. API F.10.5 xác thực người gửi và tính hash từ payload, trả đơn cũ nếu cùng khách/nội dung dưới 24 giờ. Khác nội dung/chủ sở hữu hoặc hết hạn trả 409, không tái sử dụng key. DB chưa CHECK phiên bản UUID/nội dung hex; API/ORM thực hiện kiểm tra đó.

API tạo đơn bắt buộc 1–100 dòng, kiểm tra cùng quán/khả dụng/giá/phạm vi và tính tổng từ snapshot DB. `orders/state_machine.py` kiểm tra luồng E.2; service và API đổi trạng thái/ghi lịch sử cùng transaction sau khi kiểm tra vai trò/quyền sở hữu. UPDATE có điều kiện trạng thái cũ để chặn ghi đè cạnh tranh; ghi SQL trực tiếp không được các kiểm tra service bảo vệ.

## 10. `order_items` — Dòng món và thông tin tại lúc đặt

Model: [`OrderItem`](../src/backend/app/orders/models.py).

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `order_id` | INTEGER | Không | — | FK → `orders.id` |
| `menu_item_id` | INTEGER | Không | — | FK → `menu_items.id` |
| `quantity` | INTEGER | Không | — | Số lượng phần, 1–99 |
| `snapshot_price` | INTEGER | Không | — | Giá một phần tại lúc đặt, VNĐ |
| `snapshot_name` | VARCHAR(180) | Không | — | Tên món tại lúc đặt |

UNIQUE: `uq_order_items_order_menu_item` trên `(order_id, menu_item_id)`. CHECK: `ck_order_items_quantity` trong 1–99; `ck_order_items_snapshot_price` trong (0, 10.000.000]; `ck_order_items_snapshot_name` trim dài 1–180. Index: `ix_order_items_order_id` trên `(order_id)`, `ix_order_items_menu_item_id` trên `(menu_item_id)`.

ORM kiểm tra số nguyên cho số lượng/giá và trim tên. API tạo đơn đọc giá/tên từ MenuItem đã khóa, kiểm tra expected_price và lưu snapshot tại thời điểm tạo đơn. Thành tiền dòng được tính bằng `quantity * snapshot_price`, chưa có cột riêng. Không tự cập nhật snapshot theo thực đơn và chưa có trigger chặn sửa snapshot bằng SQL.

## 11. `order_status_history` — Lịch sử trạng thái đơn

Model: [`OrderStatusHistory`](../src/backend/app/orders/models.py).

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `order_id` | INTEGER | Không | — | FK → `orders.id` |
| `status` | VARCHAR(20) | Không | — | Trạng thái được ghi nhận |
| `actor_id` | INTEGER | Không | — | FK → `users.id`, tài khoản thao tác |
| `reason` | VARCHAR(500) | Có | — | Lý do; bắt buộc khi từ chối |
| `created_at` | TIMESTAMPTZ | Không | CURRENT_TIMESTAMP | Thời điểm ghi lịch sử |

CHECK: `ck_order_history_status` dùng cùng bảy mã trạng thái Order; `ck_order_history_reason` NULL hoặc trim dài 1–500; `ck_order_history_rejection_reason` yêu cầu `reason IS NOT NULL` khi `status='rejected'`. Index: `ix_order_status_history_order_id` trên `(order_id)`, `ix_order_status_history_actor_id` trên `(actor_id)`.

ORM trim lý do nếu có; quan hệ `Order.history` đọc theo `(created_at, id)`. Service chuyển trạng thái đã kiểm tra actor và ghi một dòng lịch sử cùng transaction với trạng thái mới; từ chối cần lý do 1–500 ký tự, các thao tác khác không nhận lý do. Không có trigger bảo vệ khi ghi SQL trực tiếp. Service tạo đơn đã ghi lịch sử pending ban đầu cùng transaction; chưa có API sửa/xóa lịch sử.

## 12. `reviews` — Đánh giá món đã mua

Model: [`Review`](../src/backend/app/reviews/models.py). Tách khỏi feedback phù hợp/không phù hợp của gợi ý.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `order_id` | INTEGER | Không | — | FK → `orders.id`; thuộc FK ghép món đã mua |
| `menu_item_id` | INTEGER | Không | — | FK → `menu_items.id`; thuộc FK ghép món đã mua |
| `user_id` | INTEGER | Không | — | FK → `users.id`, người gửi đánh giá |
| `rating` | INTEGER | Không | — | Điểm nguyên 1–5 |
| `comment` | VARCHAR(2000) | Không | `''` | Nhận xét, không nhập thì chuỗi rỗng |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |
| `created_at` | TIMESTAMPTZ | Không | CURRENT_TIMESTAMP | Thời điểm tạo |

UNIQUE: `uq_reviews_order_menu_item` trên `(order_id, menu_item_id)`. FK ghép `fk_reviews_purchased_item` tới `order_items(order_id, menu_item_id)`. CHECK: `ck_reviews_rating` trong 1–5; `ck_reviews_comment` dài không quá 2000. Index: `ix_reviews_order_id` trên `(order_id)`, `ix_reviews_menu_item_id` trên `(menu_item_id)`, `ix_reviews_user_id` trên `(user_id)`.

ORM kiểm tra điểm nguyên, trim nhận xét; quan hệ `order_item` chỉ đọc để truy xuất snapshot. DB bảo đảm món có trong đơn và chưa có đánh giá cùng cặp; service F.10.6 kiểm tra customer sở hữu đơn completed trước khi ghi. Response dùng tên/giá snapshot; cùng món được đánh giá lại trong đơn mua khác. SQL ghi trực tiếp không được kiểm tra vai trò/trạng thái của service.

## 13. `recommendation_requests` — Yêu cầu gợi ý

Model: [`RecommendationRequest`](../src/backend/app/tracking/models.py).

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | UUID | Không | — | PK; ORM sinh UUID v4 |
| `user_id` | INTEGER | Không | — | FK → `users.id` |
| `session_id` | UUID | Không | — | Mã phiên client, không phải FK |
| `algorithm_version` | VARCHAR(40) | Không | — | Phiên bản thuật toán đã dùng |
| `created_at` | TIMESTAMPTZ | Không | CURRENT_TIMESTAMP | Thời điểm tạo request |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |

UNIQUE: `uq_rec_requests_owner_session` trên `(id, user_id, session_id)`, làm đích FK ghép kiểm tra Event. CHECK: `ck_rec_requests_algorithm_version` trim dài 1–40. Index: `ix_recommendation_requests_user_id` trên `(user_id)`, `ix_recommendation_requests_session_id` trên `(session_id)`.

ORM yêu cầu UUID v4 cho ID/session, trim phiên bản thuật toán. Chưa có thuật toán hoặc API sinh danh sách; `algorithm_version` là chuỗi, chưa có bảng danh mục thuật toán và chưa CHECK giá trị cụ thể.

## 14. `recommendation_impressions` — Món trong danh sách gợi ý

Model: [`RecommendationImpression`](../src/backend/app/tracking/models.py).

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `id` | INTEGER | Không | Tự cấp | PK |
| `request_id` | UUID | Không | — | FK → `recommendation_requests.id` |
| `menu_item_id` | INTEGER | Không | — | FK → `menu_items.id` |
| `rank` | INTEGER | Không | — | Thứ hạng trong Top 5, 1–5 |
| `displayed_at` | TIMESTAMPTZ | Có | — | NULL đến khi ghi nhận hiển thị thực tế |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |

UNIQUE: `uq_rec_impressions_request_item` trên `(request_id, menu_item_id)`; `uq_rec_impressions_request_rank` trên `(request_id, rank)`. CHECK: `ck_rec_impressions_rank` trong 1–5. Index: `ix_recommendation_impressions_request_id` trên `(request_id)`, `ix_recommendation_impressions_menu_item_id` trên `(menu_item_id)`.

ORM kiểm tra UUID v4 của request và thứ hạng nguyên. Giới hạn thứ hạng cùng UNIQUE cho phép tối đa năm dòng/request, chưa buộc đủ năm hoặc thứ hạng liên tiếp. Có dòng không đồng nghĩa đã hiển thị; API F.10.8 chỉ cập nhật `displayed_at` khi nhận sự kiện `impression` đầu tiên. KPI sau này phải phân biệt các dòng chưa hiển thị.

## 15. `interaction_events` — Sự kiện tương tác

Model: [`InteractionEvent`](../src/backend/app/tracking/models.py). Mỗi dòng là một sự kiện có ID duy nhất do client cấp.

| Cột | Kiểu | NULL | Mặc định DB | Ý nghĩa / khóa |
| :--- | :--- | :--- | :--- | :--- |
| `event_id` | UUID | Không | — | PK, client cấp để chống ghi trùng |
| `user_id` | INTEGER | Không | — | FK → `users.id`; thuộc FK ghép chủ request |
| `session_id` | UUID | Không | — | Mã phiên; thuộc FK ghép chủ request |
| `event_type` | VARCHAR(30) | Không | — | Một trong sáu mã bên dưới |
| `request_id` | UUID | Có | — | Thuộc hai FK ghép tới Request và Impression |
| `menu_item_id` | INTEGER | Có | — | FK → `menu_items.id`; thuộc FK ghép Impression |
| `value` | INTEGER | Có | — | Chỉ feedback có giá trị 0/1 |
| `occurred_at` | TIMESTAMPTZ | Không | — | Thời điểm phát sinh do client gửi |
| `received_at` | TIMESTAMPTZ | Không | CURRENT_TIMESTAMP | Thời điểm máy chủ tiếp nhận |
| `is_simulated` | BOOLEAN | Không | false | Cờ mô phỏng |

FK ghép `fk_interaction_events_request_owner`: `(request_id, user_id, session_id)` → `recommendation_requests(id, user_id, session_id)`. FK ghép `fk_interaction_events_impression`: `(request_id, menu_item_id)` → `recommendation_impressions(request_id, menu_item_id)`. FK không khai báo MATCH FULL; khi thành phần NULL, CHECK ngữ cảnh bên dưới và các FK riêng cùng quyết định dữ liệu hợp lệ.

| `event_type` | Ý nghĩa | `request_id` | `menu_item_id` | `value` |
| :--- | :--- | :--- | :--- | :--- |
| `impression` | Ghi nhận nhìn thấy món gợi ý | Bắt buộc | Bắt buộc | NULL |
| `click` | Nhấp món trong gợi ý | Bắt buộc | Bắt buộc | NULL |
| `add_to_cart` | Thêm món vào giỏ | Tùy chọn | Bắt buộc | NULL |
| `feedback` | Phù hợp/không phù hợp với gợi ý | Bắt buộc | Bắt buộc | 0 hoặc 1 |
| `session_start` | Bắt đầu phiên | NULL | NULL | NULL |
| `session_end` | Kết thúc phiên | NULL | NULL | NULL |

CHECK: `ck_interaction_events_type` giới hạn sáu mã; `ck_interaction_events_context` quy định request/món theo bảng trên; `ck_interaction_events_feedback` yêu cầu giá trị 0/1 cho feedback và NULL cho các mã khác. Quy ước feedback: 0 không phù hợp, 1 phù hợp; DB chỉ giới hạn số, không diễn giải ý nghĩa. Không có alias `rec_*` trong enum hiện tại.

Index: `ix_interaction_events_user_id` trên `(user_id)`, `ix_interaction_events_session_id` trên `(session_id)`, `ix_interaction_events_request_id` trên `(request_id)`, `ix_interaction_events_menu_item_id` trên `(menu_item_id)`.

ORM kiểm tra UUID v4 và giá trị feedback nguyên, chuẩn hóa timestamp UTC. API F.10.8 chỉ cho customer ghi sự kiện của mình, kiểm tra request/phiên/món, cửa sổ thời gian 24 giờ trước đến 5 phút sau, hiển thị trước click/feedback và gửi lại cùng event ID/nội dung. PK chặn ghi trùng ở DB; API nhận lại an toàn hoặc báo xung đột nếu nội dung khác. Chưa kiểm tra một cặp start/end cho phiên. Các click có ID khác nhau vẫn là các dòng riêng; tính CTR phải đếm impression có click thay vì cộng mọi dòng click.

## Đối chiếu và thay đổi schema

Đọc models để hiểu validator ORM, đọc revision `001` để biết schema thực sự được tạo. Sau khi cấu hình DB theo [hướng dẫn cài đặt](HUONG_DAN_CAI_DAT.md), có thể chạy từ `src/backend/`:

```bash
python -m alembic current
python -m alembic check
```

`check` hỗ trợ phát hiện khác biệt khi autogenerate; không thay thế kiểm tra thủ công toàn bộ CHECK/ràng buộc nghiệp vụ. Chưa chạy PostgreSQL thực tế trong môi trường hiện tại; kiểm thử migration dùng SQLite tạm và SQL PostgreSQL offline. Thay đổi dữ liệu/schema sau revision đã áp dụng cần revision mới và cập nhật đồng thời hai tài liệu F.7.

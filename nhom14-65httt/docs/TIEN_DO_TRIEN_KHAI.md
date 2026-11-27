# Tiến độ triển khai theo từng phần

Mỗi lượt triển khai chỉ thêm một phần để nhóm kiểm tra và commit riêng. Trình tự dưới đây theo phần F của [thiết kế](THIET_KE_CAU_TRUC.md). Có file khung không đồng nghĩa chức năng đã hoàn tất.

Các nhãn Phase 1.1–1.7 dưới đây là cách chia nhỏ **bước 5 của mục F** để commit riêng từng model, không phải tên mục nguyên bản của tài liệu. Migration dùng bước 6, ERD/từ điển dữ liệu dùng bước 7. Bảng tiến độ phản ánh trạng thái hiện tại; các mục kết quả bên dưới giữ mốc kiểm tra của từng lượt triển khai.

| Phần | Nội dung | Trạng thái trong mã nguồn hiện tại |
| :--- | :--- | :--- |
| Phase 0 | Cấu hình môi trường, Docker, backend/frontend chạy tối thiểu | Đã chuẩn bị; xem hướng dẫn cài đặt và kết quả kiểm tra |
| Phase 1.1 | `users/models.py`: tài khoản và vai trò | Có model, kiểm thử, migration 001 và API auth backend |
| Phase 1.2 | `preferences/models.py`: khẩu vị | Có model/migration và API GET/PUT F.10.7 |
| Phase 1.3 | `restaurants/models.py`: quán và thành viên quản lý | Có model/migration và API hồ sơ, duyệt/tạm ngừng ở F.10.1 |
| Phase 1.4 | `menu/models.py`: món chuẩn, món bán, nguyên liệu | Có bốn model/migration; API thực đơn và catalog ở F.10.2 |
| Phase 1.5 | `orders/models.py`: đơn, món đặt và lịch sử | Có model/migration, service và API đơn COD F.10.5 |
| Phase 1.6 | `reviews/models.py`: đánh giá món | Có model/migration và POST đánh giá món đã mua F.10.6 |
| Phase 1.7 | `tracking/models.py`: yêu cầu gợi ý, hiển thị, sự kiện | Có ba model, kiểm thử, migration 001; API nhận sự kiện ở F.10.8 |
| F.6 | Migration khởi tạo | Đã có revision 001 tạo 15 bảng; kiểm thử SQLite và SQL PostgreSQL offline |
| F.7 | ERD và từ điển dữ liệu | Đã mô tả 15 bảng, từng cột, ràng buộc và 24 FK theo revision 001 |
| F.8 — backend | Đăng ký, đăng nhập, JWT, refresh và guard | Đã có API, 84 kiểm thử auth và tích hợp giao diện |
| F.8 — frontend | AuthContext, useAuth, API client và trang/layout | Đã có auth; giao diện được hoàn thiện theo Material Design 3 |
| F.9 | Kiểm thử auth | Backend 84 ca; frontend 54 ca unit/UI và bốn kịch bản E2E đạt |
| F.10.1 | Hồ sơ quán vendor, duyệt/tạm ngừng admin và quán công khai | Đã có tám thao tác API, 92 kiểm thử mới; chưa có giao diện quản lý quán |
| F.10.2 | Thực đơn vendor, catalog admin và món công khai | Đã có 17 thao tác API, 167 kiểm thử mới; chưa có giao diện quản lý thực đơn |
| F.10.3 | Tìm món/quán theo chữ, Haversine và phạm vi giao | Đã có hai GET công khai, 99 kiểm thử mới; chưa có SearchPage/bản đồ |
| F.10.4 | Quy tắc chuyển trạng thái và lịch sử đơn | Có state machine/service và 167 kiểm thử, đã nối API F.10.5 |
| F.10.5 | Tạo đơn COD, idempotency và API đơn hàng | Có 11 thao tác API customer/vendor; chưa có UI |
| F.10.6 | Đánh giá món đã mua sau đơn hoàn tất | Có POST customer, 30 kiểm thử mới; chưa có ReviewForm |
| F.10.7 | Hồ sơ khẩu vị năm câu hỏi | Có GET/PUT customer, 36 kiểm thử mới; chưa có PreferencePage |
| F.10.8 | Tiếp nhận sự kiện tương tác | Có POST batch customer, 31 kiểm thử mới; chưa có API sinh gợi ý/UI |
| F.11.1 | Kiểu dữ liệu và API client công khai frontend | Có tám hàm đọc quán/món/danh mục/tìm kiếm và 15 kiểm thử mới; chưa có màn hình F.12 |
| F.10 còn lại | Các nghiệp vụ khác | Tiếp tục tách từng module để commit |
| Phase 2 | Nghiệp vụ giao dịch, vendor/admin và giao diện | Đã có backend hồ sơ/duyệt quán, thực đơn/catalog và tìm kiếm; đã có API đơn COD; chưa có màn hình nghiệp vụ |
| Phase 3 | AI, tracking và dữ liệu | Đã có model/API nhận tracking; AI, ETL và KPI chưa triển khai |
| Phase 4 | ETL, BI, Power BI và đánh giá | Chưa đưa vào mã nguồn hiện tại |
| Phase 5 | Tích hợp, kiểm thử và bàn giao | Chưa thực hiện |

Phần đã soạn trước cho các phase sau được lưu cục bộ trong `.runtime/pending-implementation/`, được `.gitignore` bỏ qua. Đây là bản nháp tham khảo, chưa phải thay đổi để commit ở lượt này; mỗi phần phải được kiểm tra lại khi đưa vào dự án.

Thư mục nháp cũng được Docker bỏ qua, chưa có file nào trong đó được Git theo dõi và mã ứng dụng trong `src/` không tham chiếu nó. Do không được commit/push, thư mục này không có trên GitHub hoặc khi clone mới. Xóa thư mục, mất máy hoặc dùng `git clean -fdx` có thể làm mất bản nháp; không coi đó là bản sao lưu dài hạn. Các file đã hoàn thiện phải nằm trong `src/` và được commit riêng, không phụ thuộc vào bản nháp. Bản nháp có thể cũ so với models hiện tại nên không chép đè nguyên trạng hoặc dùng `git add -f` để đưa cả `.runtime/` vào repo.

Không tạo file `.pbix` rỗng thay cho sản phẩm Power BI và không đánh dấu các khảo sát, thử nghiệm người dùng hay kết quả nghiệm thu là hoàn tất khi chưa thực hiện.

## Kết quả kiểm tra Phase 0

- Backend: 5 kiểm thử đạt (health/request ID, định dạng lỗi, CORS, cấu hình URL DB).
- Frontend: `npm run build` và `npm run format:check` đạt.
- Chưa kiểm chứng Docker/PostgreSQL vì môi trường phát triển không có Docker CLI.
- Bộ khung, phần hợp nhất tài liệu, toàn bộ models F.5, migration F.6, tài liệu dữ liệu F.7 và auth backend F.8 đã được commit. Frontend auth được triển khai riêng; tiếp theo là các API nghiệp vụ F.10.

## Phần tài khoản và vai trò

- Thêm `app/users/models.py` với `User` và `UserRole` (`customer`, `vendor`, `admin`).
- Email được chuẩn hóa ở ORM và có ràng buộc duy nhất; vai trò có CHECK constraint ở DB.
- Thêm `is_simulated`, thời điểm tạo và các mặc định ở ORM/DB.
- Alembic đã đăng ký metadata của User; chưa sinh migration hoặc tạo bảng trong DB ứng dụng.
- Kiểm thử ràng buộc dùng SQLite trong bộ nhớ. Chưa kiểm chứng trên PostgreSQL.
- Kết quả: 20 kiểm thử đạt, gồm 15 ca User model và 5 ca kiểm tra nền tảng.
- Phần User model đã được người dùng commit; không tự commit/push hoặc gộp module khác vào commit đó.

## Phần hồ sơ khẩu vị

- Theo đúng đường dẫn `src/backend/app/preferences/models.py` ở mục F.5; thêm package và đăng ký metadata với Alembic.
- Mục C.5 yêu cầu khẩu vị năm câu nhưng chưa định nghĩa các cột. Đối chiếu mục bản đồ route/luồng khách mới của `src/frontend/README.md`, chốt năm nội dung: vùng miền, mức cay, nguyên liệu thích, nguyên liệu cần tránh và mức sẵn sàng thử món mới.
- Các trường tương ứng là `regions`, `spice_level`, `liked_ingredients`, `avoided_ingredients`, `exploration_level`; quy ước mức cay 0–3 và khám phá 0–2 được ghi trong README backend để API/UI dùng thống nhất.
- `user_id` là khóa chính và khóa ngoại tới User: mỗi tài khoản tối đa một hồ sơ; xóa tài khoản sẽ xóa hồ sơ đi kèm. Bỏ qua khai báo được biểu diễn bằng việc chưa có hồ sơ.
- Các danh sách không dùng chung mặc định giữa tài khoản, được chuẩn hóa khi gán và lưu được cập nhật tại chỗ qua MutableList.
- Kết quả: 54 kiểm thử đạt, gồm 34 ca Preference và 20 ca User/nền tảng. Kiểm thử dữ liệu dùng SQLite; chưa kiểm chứng PostgreSQL.
- Chưa tạo migration, API khẩu vị, bộ mã hóa vector hoặc giao diện khẩu vị. Các nội dung đó vẫn ở phần sau theo Markdown.
- Phần Preference model đã được người dùng commit; các module soạn trước trong `.runtime/` tiếp tục được bỏ qua và không đưa vào cùng lượt.

## Phần quán và người quản lý

- Theo đúng mục F.5, bổ sung `Restaurant` và `RestaurantMembership` tại `src/backend/app/restaurants/models.py`; Alembic đã nhận metadata của cả hai.
- Theo mục C.5 và D.15/17/18/22, lưu hồ sơ quán, tọa độ, giờ mở cửa, bán kính giao, trạng thái duyệt, cờ nhận đơn và liên kết người quản lý.
- Chi tiết kiểu cột, trạng thái `pending`/`approved`/`suspended`, bán kính tối đa 50 km, cờ nhận đơn mặc định false, giờ phục vụ qua đêm/cả ngày được ghi trong README backend. Đây là quy ước triển khai bổ sung cho phần Markdown chưa mô tả từng cột.
- Với API `/vendor/restaurant` của bản thiết kế, MVP chọn mỗi tài khoản tối đa một quán; một quán có thể có nhiều tài khoản quản lý. PK/FK ngăn liên kết trùng và tham chiếu thiếu. Xóa tài khoản/quán đang có membership bị chặn, cần xử lý liên kết trước.
- Chưa kiểm tra quyền API hoặc tự gán quyền theo membership; auth/vendor sẽ kiểm tra vai trò và quyền sở hữu ở phần sau.
- Kết quả: 105 kiểm thử đạt, gồm 51 ca phần quán và 54 ca đã có. Kiểm thử dữ liệu dùng SQLite; chưa kiểm chứng PostgreSQL.
- Chưa tạo migration, API CRUD, kiểm tra đang mở cửa hoặc bộ lọc khoảng cách; chưa thêm models thực đơn ở lượt này.
- Phần quán/người quản lý đã được người dùng commit; không gộp thêm models thực đơn vào commit đó.

## Phần món chuẩn, thực đơn và nguyên liệu

- Theo mục F.5, thêm CanonicalDish, MenuItem, Ingredient và MenuItemIngredient tại `src/backend/app/menu/models.py`; Alembic đã nhận metadata.
- Theo mục C.5 và D.16/33/34, tách đặc trưng món chuẩn khỏi tên/giá/khả dụng của từng món bán và nguyên liệu thực tế của quán. Có mã nguồn truy vết và cờ dữ liệu mô phỏng.
- Giá là số nguyên VNĐ trong (0, 10.000.000]; mức cay 0–3; các giới hạn text và mặc định cờ bán/xác nhận nguyên liệu được ghi trong README backend. Đây là chi tiết triển khai bổ sung cho phần Markdown chưa định nghĩa từng cột.
- PK/FK bảo vệ liên kết quán, món chuẩn và nguyên liệu; khóa ghép chống lặp nguyên liệu của một món bán. Không tự sao chép nguyên liệu đặc trưng thành nguyên liệu thực tế.
- Kết quả: 155 kiểm thử đạt, gồm 50 ca thực đơn và 105 ca đã có. Kiểm thử dữ liệu dùng SQLite; chưa kiểm chứng PostgreSQL.
- Chưa tạo migration, seed, API quản lý thực đơn, kiểm tra quyền vendor hoặc thuật toán lọc nguyên liệu; các phần đó vẫn chờ đúng bước trong Markdown.
- Đã kiểm tra bản nháp cục bộ không bị theo dõi bởi Git hoặc tham chiếu từ mã nguồn chạy chính; ghi thêm README cảnh báo bản nháp có thể cũ ngay trong thư mục nháp.
- Phần thực đơn đã được người dùng commit; không gộp models đơn hàng vào commit đó.

## Phần đơn hàng, món đặt và lịch sử trạng thái

- Theo mục F.5, thêm Order, OrderItem và OrderStatusHistory tại `src/backend/app/orders/models.py`; Alembic đã nhận metadata.
- Theo C.5, D.10–13 và E.2, lưu dữ liệu giao dịch, tên/giá tại thời điểm đặt, đủ bảy trạng thái, lịch sử tài khoản thao tác/thời điểm/lý do. Từ chối đơn bắt buộc có lý do.
- Theo E.4/E.5, idempotency key có UNIQUE toàn bảng và cùng session sử dụng UUID v4; lưu thêm SHA-256 của nội dung yêu cầu để hỗ trợ service gửi lặp sau này. Model chưa thực hiện phản hồi HTTP hoặc cửa sổ 24 giờ.
- Tổng tiền dùng BIGINT, snapshot dùng số nguyên VNĐ, mỗi món tối đa một dòng/đơn. FK bảo vệ dữ liệu giao dịch đang có tham chiếu. Các giới hạn và phần kiểm tra nghiệp vụ chưa triển khai được ghi rõ trong README backend.
- Kết quả: 219 kiểm thử đạt, gồm 64 ca dữ liệu đơn hàng và 155 ca đã có. Kiểm thử dùng SQLite; chưa kiểm chứng PostgreSQL. Chưa thay thế các ca giao dịch/API và state machine trong Markdown.
- Chưa có migration, tạo đơn qua API, transaction đặt đơn, kiểm tra quyền, tính tổng/snapshot tự động hoặc state machine.
- Phần đơn hàng đã được người dùng commit; không gộp Review hoặc tracking vào commit đó.

## Phần đánh giá món đã mua

- Theo mục C.5, D.14 và F.5, thêm Review tại `src/backend/app/reviews/models.py`, đăng ký metadata với Alembic.
- Liên kết Review tới Order, MenuItem, User và dùng FK ghép tới đúng cặp OrderItem để không đánh giá một món chỉ tồn tại ở đơn khác.
- UNIQUE ngăn đánh giá trùng một món trong một đơn; điểm nguyên 1–5, nhận xét tùy chọn tối đa 2000 ký tự. Lưu thời điểm UTC và cờ dữ liệu mô phỏng; đây là quy ước dữ liệu chi tiết trong README backend.
- Quan hệ đọc OrderItem giữ liên kết với tên/giá snapshot của lần mua. FK bảo vệ dữ liệu giao dịch đang được đánh giá tham chiếu.
- Kết quả: 252 kiểm thử đạt, gồm 33 ca Review và 219 ca đã có. Kiểm thử dữ liệu dùng SQLite; chưa kiểm chứng PostgreSQL.
- Chưa có migration/API đánh giá hoặc kiểm tra đơn hoàn tất/người gửi sở hữu đơn; service/auth sẽ thực hiện ở mục F.10. Không trộn Review với feedback gợi ý.
- Phần Review đã được người dùng commit; không gộp tracking vào commit đó.

## Phần yêu cầu gợi ý, hiển thị và tương tác

- Theo C.5, D.6/7/20/21, E.5 và F.5, thêm đúng ba model RecommendationRequest, RecommendationImpression và InteractionEvent tại `src/backend/app/tracking/models.py`, đăng ký metadata với Alembic.
- Request có UUID do backend sinh và phiên bản thuật toán; Impression không lặp món/thứ hạng trong Top 5. `displayed_at` mặc định NULL để tách món được trả về khỏi món thực sự được nhìn thấy.
- `event_id` do client cấp là PK; FK ghép bảo vệ chủ sở hữu/session/request và món trong danh sách gợi ý. Cart ngoài gợi ý và sự kiện phiên không bắt buộc request. Feedback nhận 0/1, độc lập Review.
- Chốt sáu mã sự kiện theo nội dung tracking trong Markdown; thống nhất ba tên `rec_*` từng được đề xuất trong README frontend thành `impression`, `click`, `feedback`, và mô tả riêng occurred_at/received_at. Chưa có client hoặc API tracking thực thi.
- Kết quả: 318 kiểm thử đạt, gồm 66 ca tracking và 252 ca đã có. Kiểm thử dữ liệu dùng SQLite; chưa kiểm chứng PostgreSQL.
- Đã khai báo đủ các models liệt kê ở F.5. Chưa tạo migration F.6, API tiếp nhận, kiểm tra thời gian/hiển thị, ETL/quy thuộc/KPI hoặc model đánh giá mù ở phần AI sau.
- Phần models tracking đã được người dùng commit; migration được triển khai ở lượt riêng sau đó.

## Migration khởi tạo F.6

- Tạo `alembic/versions/001_initial_schema.py`, revision gốc `001`, đúng 15 bảng OLTP đã chốt ở F.5. Không nhập models đang phát triển trong file migration, không đưa bảng BI/đánh giá mù chưa triển khai vào schema ban đầu.
- Có PK, FK, UNIQUE, CHECK, index và mặc định phía DB; `downgrade` bỏ theo thứ tự ngược phụ thuộc. Mặc định Boolean dùng `sa.false()` để sinh SQL đúng cho cả PostgreSQL/SQLite.
- Cấu hình Alembic dùng `%(here)s` để không phụ thuộc thư mục chạy lệnh, bật so sánh kiểu/mặc định và bật FK khi migrate SQLite. Sửa lỗi escape URL kết nối hai lần với ký tự `%`.
- Thêm lệnh `migrate-status`, `migrate-check` và hướng dẫn nâng schema local/Docker; chưa chạy migration vào DB ứng dụng của người dùng. Chưa có seed/API/BI.
- Thêm hỗ trợ so sánh mặc định JSON dạng literal trên PostgreSQL để tránh dùng toán tử bằng không được hỗ trợ cho kiểu `json`; các kiểu khác tiếp tục dùng cơ chế Alembic.
- Toàn bộ 341 kiểm thử đạt, gồm 23 ca migration: nâng/hạ/nâng lại khi có dữ liệu, chạy head lặp không xóa dữ liệu, đối chiếu PK/FK/index/UNIQUE/CHECK, phát hiện schema lệch, ghi dữ liệu ORM trên schema do migration tạo, URL/đường dẫn, mặc định JSON và SQL PostgreSQL offline.
- PostgreSQL/Docker thực tế chưa được kiểm chứng vì môi trường không có CLI/server tương ứng. Các thao tác nâng/hạ kiểm thử dùng SQLite tạm; không sử dụng DB cần giữ dữ liệu.
- Migration đã được người dùng commit tại `c3b8c76`; ERD và từ điển dữ liệu F.7 được triển khai ở lượt riêng tiếp theo.

## ERD và từ điển dữ liệu F.7

- Thêm `docs/ERD.md` với ba sơ đồ Mermaid chia theo tài khoản/thực đơn, giao dịch/đánh giá và tracking; bao phủ đủ 15 bảng. Ghi rõ PK/FK/UNIQUE ghép, lực lượng quan hệ và danh mục 24 FK cùng ON DELETE.
- Thêm `docs/TU_DIEN_DU_LIEU.md` mô tả mọi cột, kiểu hướng PostgreSQL, NULL, mặc định DB, khóa, CHECK, UNIQUE và index của revision `001`.
- Phân biệt ràng buộc DB với chuẩn hóa/validator ORM và nghiệp vụ chưa triển khai; đặc biệt quyền đánh giá, tính tổng/cùng quán, state machine, UUID v4 và hiển thị thực tế trước khi tính KPI.
- Liên kết tài liệu từ README nhóm/backend/database. Không thay đổi schema, không đưa bảng BI/đánh giá mù hoặc API auth vào phần này.
- Đối chiếu tự động đủ 15 bảng, 103 cột (kiểu/NULL/mặc định), các tên constraint/index và 24 FK; kiểm tra cấu trúc ba sơ đồ Mermaid cùng 57 liên kết cục bộ. Đối chiếu danh sách bảng/cột/FK với revision `001`; không chạy lại kiểm thử nghiệp vụ vì chỉ thay đổi tài liệu. PostgreSQL thực tế vẫn chưa được kiểm chứng.
- Tài liệu F.7 đã được người dùng commit tại `bade3f3`; auth F.8 được triển khai ở lượt riêng tiếp theo.

## Auth backend F.8 và kiểm thử F.9

- Tạo đủ `app/auth/__init__.py`, `schemas.py`, `utils.py`, `service.py`, `dependencies.py`, `router.py`; mount dưới `/api/v1/auth`. Đăng ký trả UserOut 201, đăng nhập/refresh trả cặp JWT và UserOut, GET `/me` xác thực access token.
- Đăng ký chỉ nhận customer/vendor, mặc định customer; không cho tự đăng ký admin hoặc truyền trường thừa. Email trim/lower và UNIQUE chống tạo trùng kể cả trường hợp chạy đồng thời; rollback khi lỗi DB.
- Băm mật khẩu bằng Passlib PBKDF2-SHA256, 600.000 vòng và salt ngẫu nhiên, giữ nguyên mật khẩu Unicode/khoảng trắng. Requirements không còn cần extra bcrypt. Không trả password/hash hoặc input nhạy cảm trong lỗi validation.
- JWT HS256 có issuer/audience, thời điểm cấp/hết hạn, subject, jti và loại access/refresh. Chặn SECRET_KEY mẫu/ngắn khi sử dụng JWT, thêm cấu hình hạn refresh; health/docs vẫn hoạt động khi chưa cấu hình khóa.
- `get_current_user` đọc User từ DB; `require_role(*roles)` và `require_vendor_owner` kiểm tra vai trò hiện tại/membership đúng quán. Chưa công bố API nghiệp vụ vendor/admin; guard được thử qua route của ứng dụng kiểm thử.
- Refresh là JWT không lưu trạng thái; cấp mới không thu hồi token cũ, chưa có denylist/thu hồi thiết bị/logout phía máy chủ. Chưa có xác minh email, khôi phục mật khẩu hoặc giới hạn tần suất đăng nhập. Những giới hạn này được ghi trong API contract.
- Thêm `docs/API_CONTRACT.md`, cập nhật hướng dẫn SECRET_KEY và tài liệu liên quan. Không đổi schema hoặc sửa revision `001`; chưa đưa frontend auth vào cùng phần.
- Toàn bộ 425 kiểm thử đạt, gồm 84 ca auth và 341 ca đã có. Auth được thử trên SQLite tạm do migration thật tạo, gồm API, validation, token sai/hết hạn/thiếu claim, refresh, vai trò, quyền sở hữu quán và lỗi DB; Ruff đạt trên các file Python của phần thay đổi.
- Auth backend đã được người dùng commit tại `dd97505`. Ở mốc backend chưa thử frontend; kết quả tích hợp được bổ sung trong phần frontend riêng bên dưới. PostgreSQL/Docker thực tế chưa được kiểm chứng.

## Frontend auth F.8 và kiểm thử tích hợp

- Tạo `api/client.ts`, `api/auth.ts`, `contexts/AuthContext.tsx`, `hooks/useAuth.ts`, types auth, trang login/register và đủ bốn component layout theo Markdown. Có trang giới thiệu, thông tin tài khoản, 403/404; `/vendor` và `/admin` hiện chỉ có thông tin tài khoản với guard, chưa phải dashboard nghiệp vụ.
- Đăng ký customer/vendor, xác nhận mật khẩu và chuyển về login; đăng nhập chuyển theo vai trò hoặc đích nội bộ được cho phép. Không tự cấp admin. Form có nhãn/autocomplete, lỗi, trạng thái chờ và khóa gửi lặp.
- localStorage chỉ lưu hai token; User/role lấy lại qua `/me`. API client timeout 15 giây, refresh một lần khi 401, dùng chung refresh cho request đồng thời, xóa phiên khi refresh bị từ chối; lỗi mạng/5xx giữ phiên để thử lại. Đồng bộ storage giữa các tab; logout/đổi tài khoản chặn phản hồi cũ khôi phục phiên.
- Giao diện co giãn, điều hướng bàn phím, liên kết bỏ qua điều hướng và thông báo khi storage bị chặn. Không thêm khẩu vị, menu, giỏ hàng hoặc dashboard vào cùng phần auth.
- Thêm Vitest/Testing Library/jsdom và Playwright cùng lockfile, cấu hình/script kiểm thử. 43 ca unit/UI đạt (token, refresh, race, storage, validation, vai trò); ba kịch bản Playwright/Edge đạt với backend thật trên SQLite tạm tạo bằng migration `001` (customer/vendor, tải lại, chặn admin, logout và bố cục 1280px/390px). Đã xem ảnh desktop/mobile và sửa khoảng trắng tiêu đề mobile.
- Build/typecheck nguồn + tests/config, lint và format check đạt. Không đổi schema hoặc mã backend; 425 kiểm thử backend đạt tại commit trước. Chưa chạy PostgreSQL/Docker, chưa đánh giá trải nghiệm người dùng thật. npm audit còn bốn cảnh báo từ Vite 5/React Router 6 đã có; chưa nâng major trong phần này.
- Frontend auth ban đầu đã được người dùng commit tại `6c112c2`. Người dùng yêu cầu thiết kế lại login/register theo Material Design 3 trước khi thực hiện F.10.

## Hoàn thiện giao diện auth theo Material Design 3

- Giữ React/TypeScript và API auth hiện có. Tách khung auth khỏi điều hướng nghiệp vụ, bố cục desktop hai phần, mobile rút gọn thương hiệu; dùng design tokens màu MD3, card 28px, nút pill và minh họa SVG tối giản.
- Be Vietnam Pro và Material Symbols Rounded phục vụ cục bộ, kèm giấy phép; không thêm MUI hoặc đăng nhập Google. Có AuthField/AuthButton/AuthDialog dùng chung, loading/lỗi khôi phục phiên đồng bộ thiết kế.
- Nhãn luôn hiển thị, hiện/ẩn từng mật khẩu, validation tiếng Việt dưới trường, focus lỗi đầu tiên, giữ dữ liệu sau lỗi, chặn gửi lặp, autofill/Enter, vùng chạm 48px, transition 180ms và reduced motion. Đã thử Escape/khôi phục focus của dialog bằng trình duyệt.
- Ghi nhớ đăng nhập có hành vi thực: bật lưu localStorage, tắt lưu sessionStorage; refresh bảo toàn lựa chọn, logout xóa cả hai, lỗi ghi storage không để token tài khoản cũ tồn tại ngoài ý muốn.
- Checkbox đồng ý điều khoản/bảo mật chặn đăng ký khi chưa chọn; các liên kết mở nội dung cho bản thử nghiệm. Backend chưa lưu chấp thuận; quên mật khẩu chỉ mở hướng dẫn vì chưa có API reset. Không mô phỏng đăng nhập thành công.
- 54 kiểm thử unit/UI và bốn kịch bản Playwright/Edge đạt với backend thật trên SQLite tạm; kiểm tra login/register ở 360/390/768/1280px, trạng thái lỗi, bàn phím, checkbox ghi nhớ và reduced motion. Build/typecheck, lint, format check đạt; không đổi mã backend/schema.
- Giao diện auth đã được người dùng commit tại `981571d`; các phần F.10 được triển khai riêng bên dưới.

## Hồ sơ và duyệt quán F.10.1

- Tiếp tục phần F sau khi hoàn thiện giao diện auth. Theo yêu cầu người dùng, không triển khai reset mật khẩu hoặc lưu chấp thuận điều khoản trong lượt này.
- Thêm schema/service/router của `restaurants/`, và module `vendor/`, `admin/` cho hồ sơ/duyệt quán; đăng ký trong production app. Hai GET công khai chỉ trả approved và có phân trang; vendor POST/GET/PUT chỉ tác động quán lấy từ membership; admin GET/approve/suspend yêu cầu đúng vai trò.
- Tạo Restaurant và membership cùng transaction, chặn liên kết trùng và rollback khi ghi lỗi. Quán mới pending/không nhận đơn; pending/suspended không bật nhận đơn được. Suspend luôn tắt nhận đơn, approve không tự bật lại. Không cho client tự đặt trạng thái, chủ sở hữu hoặc cờ mô phỏng.
- Giờ chuẩn `HH:MM`, tính theo `Asia/Ho_Chi_Minh`, hỗ trợ qua đêm và hai mốc bằng nhau = 24 giờ. Response phân biệt `is_open`, `accepting_orders`, `can_receive_orders`; chưa thay thế lọc khoảng cách/khả dụng món khi đặt đơn.
- 517 kiểm thử backend đạt, gồm 92 ca mới và 425 ca đã có; Ruff/format đạt. Có kiểm thử vòng đời qua API thật trên SQLite tạm, phân quyền/cô lập quán, validation, giờ địa phương, lỗi commit, rollback membership và mô phỏng tranh chấp tạo quán. PostgreSQL thực tế/khóa hàng chưa kiểm chứng.
- Không sửa model/migration, không thêm menu/search/orders/reviews API hoặc frontend quản lý quán vào cùng phần. API contract, tài liệu dữ liệu và README đã cập nhật; phần tiếp theo là API thực đơn/nguyên liệu.
- Phần hồ sơ/duyệt quán đã được người dùng commit tại `822b98f`. Các bản nháp service/router chưa tích hợp vẫn được giữ trong `.runtime/` và không được mã chính tham chiếu.

## Thực đơn, món chuẩn và nguyên liệu F.10.2

- Tiếp tục mục F.10 theo thiết kế, tách riêng phần menu để người dùng commit. Thêm schema/service/router `menu/`; mở rộng vendor/admin và đăng ký router trong production app, tổng cộng 17 thao tác mới.
- Công khai đọc món đang bán của quán approved và catalog tra cứu. Menu quán trả mảng theo thiết kế; catalog và danh sách vendor/admin trả page. Quán approved đóng cửa/tắt nhận đơn vẫn cho xem thực đơn, chưa đánh giá điều kiện đặt đơn.
- Vendor chỉ quản lý món thuộc quán từ membership, gồm danh sách/chi tiết/tạo/PUT/ngừng bán. Món ngoài quyền và món không tồn tại cùng trả 404; không nhận ID quán/người dùng/cờ mô phỏng từ client. Pending/suspended có thể chuẩn bị menu nhưng chưa được đọc công khai.
- Tạo món mặc định chưa bán/chưa xác nhận nguyên liệu. Giá/ID là số nguyên nghiêm ngặt, cờ đúng Boolean, danh sách tối đa 100 ID không lặp; xác nhận cần ít nhất một nguyên liệu thực tế. Ghi món và thay liên kết trong cùng transaction, tái sử dụng liên kết còn giữ để tránh xung đột PK.
- DELETE vendor ngừng bán bằng cờ, giữ món/liên kết/snapshot giao dịch và các tham chiếu lịch sử, cho phép bật lại qua PUT. Admin CRUD món chuẩn/nguyên liệu; chuẩn hóa tên/danh sách và trả 409 khi trùng tên/source_id hoặc xóa catalog còn dùng.
- Toàn bộ 684 kiểm thử backend đạt, gồm 167 ca mới và 517 ca đã có; Ruff/format đạt. Kiểm thử API thật với SQLite tạm do migration tạo, phân quyền tất cả endpoint quản lý, cô lập quán, validation, visibility, phân trang, catalog UNIQUE/FK, thay nguyên liệu, snapshot sau ngừng bán và rollback cả món/liên kết khi lỗi ghi. OpenAPI bao phủ đủ 17 thao tác mới.
- Không đổi model/migration/frontend/dependencies; API contract, từ điển dữ liệu, hướng dẫn cài đặt và README đã cập nhật. PostgreSQL thực tế/khóa hàng cạnh tranh chưa được kiểm chứng. Frontend 54 unit/UI và bốn E2E là kết quả lượt auth trước, không chạy lại ở phần backend này.
- Phần thực đơn/catalog đã được người dùng commit tại `54c3811`; tìm kiếm được triển khai ở lượt riêng bên dưới. Hai nội dung reset mật khẩu/lưu chấp thuận backend tiếp tục hoãn theo yêu cầu người dùng.

## Tìm kiếm món và quán F.10.3

- Theo C.5, D.4–5 và F.10, thêm `app/search/__init__.py`, `schemas.py`, `service.py`, `router.py`, đăng ký hai GET `/api/v1/search/dishes` và `/api/v1/search/restaurants` trong production app. Chỉ triển khai backend, tách riêng để người dùng commit.
- Vị trí lat/lng bắt buộc và hữu hạn; radius mặc định 5 km/tối đa 50. Chỉ trả quán approved và món đang bán, khoảng cách Haversine phải nằm trong cả radius khách lẫn phạm vi giao của quán. Quán đóng cửa/tắt nhận đơn vẫn hiện trạng thái theo API hồ sơ; bộ lọc AI/khẩu vị chưa áp vào search.
- Cụ thể hóa quy tắc tìm chữ: bỏ dấu/casefold/đ→d, mọi token phải khớp tên món bán/món chuẩn/quán, hoặc tên/địa chỉ khi tìm quán. q rỗng duyệt gần vị trí; ký tự %, _ và nháy là literal. Không tìm trong thông tin nội bộ hoặc tự geocode địa chỉ.
- SQL lọc hộp tọa độ, Python kiểm tra khoảng cách và chữ; xử lý vùng cực/kinh tuyến 180°. Lọc và sắp theo khoảng cách chưa làm tròn rồi ID trước total/phân trang, không cắt ngầm ứng viên. Nguyên liệu nạp theo lô chỉ cho trang trả về, tránh N+1. Cách triển khai phù hợp dữ liệu MVP; chưa có chỉ mục không gian/tìm kiếm cho tập lớn.
- Response tái sử dụng public DTO, thêm distance_km; món kèm restaurant với trạng thái giờ/nhận đơn, không lộ source_id/cờ mô phỏng/membership. Không ghi DB hoặc lưu vị trí khách, không đổi model/migration/frontend/dependencies.
- Toàn bộ 783 kiểm thử backend đạt, gồm 99 ca search mới và 684 ca đã có; Ruff/format đạt. Bao phủ API thật trên SQLite tạm do migration tạo, tiếng Việt NFC/NFD/đ, literal %/_, tọa độ và query sai, radius kép/sát biên, cực/kinh tuyến 180°, phân trang sau lọc/thứ tự ổn định, metadata công khai, không ghi DB và truy vấn tránh N+1. OpenAPI có đúng hai GET công khai cùng schema query; 57 liên kết tài liệu cục bộ hợp lệ. Chưa kiểm chứng PostgreSQL thực tế hoặc tải lớn. Không chạy lại frontend; kết quả 54 unit/UI và bốn E2E vẫn là mốc auth trước.
- Phần tìm kiếm đã được người dùng commit tại `1fdf0ac`; nghiệp vụ đơn hàng triển khai riêng bên dưới.

## Chuyển trạng thái và lịch sử đơn F.10.4

- Tách nội dung `orders/state_machine.py` theo E.2/F.10 thành một phần commit riêng, kèm `orders/service.py` thực hiện quyền sở hữu và transaction. Chưa công bố endpoint đơn hàng.
- Đúng sáu chuyển trạng thái của thiết kế; chỉ khách sở hữu đơn mới hủy pending, vendor đúng quán mới xác nhận/từ chối và xử lý đến hoàn tất. Admin không có quyền thay thế. Đơn ngoài quyền và không tồn tại cùng 404; chuyển sai/lặp trả lỗi 409. Lý do từ chối bắt buộc, trim 1–500 ký tự; các thao tác khác không nhận lý do.
- Đọc lại vai trò/membership/trạng thái từ DB, khóa hàng Order khi DB hỗ trợ; UPDATE có điều kiện trạng thái cũ và ghi lịch sử trong cùng transaction. Lỗi ghi lịch sử/commit rollback cả hai. Không sửa snapshot/tổng tiền/địa chỉ; chưa xử lý tạo đơn, idempotency, API hoặc frontend trong phần này.
- 167 kiểm thử mới gồm toàn bộ tổ hợp trạng thái/vai trò, luồng hoàn tất/hủy/từ chối, quyền sở hữu, thành viên chung quán, dữ liệu cached cũ, lý do, rollback và mô phỏng cạnh tranh cập nhật. Kiểm thử DB dùng SQLite tạm tạo bằng migration; chưa kiểm chứng PostgreSQL/khóa hàng cạnh tranh thực tế.
- Toàn bộ 950 kiểm thử backend đạt (783 ca trước + 167 ca mới); Ruff/format và diff check đạt. Không chạy lại frontend vì không thay đổi giao diện.
- Phần chuyển trạng thái đã được người dùng commit tại `56f7cda`; API đơn hàng được triển khai ở lượt riêng bên dưới.

## Đơn COD, idempotency và API F.10.5

- Thêm schemas/router và mở rộng service orders; mount 11 thao tác customer/vendor theo E.1, thêm chi tiết vendor để xem địa chỉ/lịch sử. Dùng state machine E.2 đã commit; kiểm tra scope từ token/membership, không cho admin vượt quyền.
- Tạo đơn kiểm tra quán approved/giờ mở/nhận đơn/phạm vi giao, món cùng quán/đang bán và expected_price. Snapshot lấy từ DB, tổng tính phía server; ghi Order/OrderItem/lịch sử pending cùng transaction, rollback khi lỗi. Không đổi schema/dependencies, chỉ bỏ import thừa trong model.
- Key UUID v4 UNIQUE; hash payload chuẩn hóa thứ tự dòng/địa chỉ, gồm session và tọa độ. Cùng khách/nội dung dưới 24 giờ trả lại đơn 200; khác nội dung/chủ sở hữu hoặc key quá hạn trả 409. Không xóa hoặc tái sử dụng key. Có khóa hàng khi DB hỗ trợ và xử lý UNIQUE sau rollback.
- Danh sách đơn trả mảng theo thiết kế, offset/limit, mới nhất trước. Chi tiết gồm snapshot/lịch sử, không trả key/hash/session/cờ mô phỏng; đơn ngoài quyền và không tồn tại cùng 404. Gọi lặp chuyển trạng thái trả 409.
- Chưa có UI/review, PostgreSQL thực tế hoặc kiểm thử tải/cạnh tranh thực tế; các ca race dùng mô phỏng trên SQLite. Chưa stage/commit/push; phần tiếp theo là API đánh giá món đã mua.
- Toàn bộ 1036 kiểm thử backend đạt, gồm 86 ca API đơn hàng mới và 950 ca đã có. Ruff/format đạt; bao phủ vòng đời COD, snapshot, scope, tất cả guard, validation/phân trang, key 24 giờ/payload khác/chủ sở hữu khác, tranh chấp UNIQUE mô phỏng, rollback dòng món/lịch sử/commit và OpenAPI 11 thao tác. Không chạy lại frontend vì không đổi giao diện.

## Đánh giá món đã mua F.10.6

- Phần đơn COD đã được người dùng commit tại `de24e11`. Lượt này thêm `reviews/schemas.py`, `service.py`, `router.py` và mount POST `/api/v1/orders/{order_id}/review` theo E.1/D.14, tách riêng để commit.
- Customer phải sở hữu đơn completed và món phải thuộc OrderItem của đúng đơn. Rating nguyên 1–5, nhận xét tùy chọn tối đa 2000 ký tự sau trim. Một cặp đơn/món chỉ đánh giá một lần; UNIQUE/FK ghép ở migration 001 vẫn bảo vệ tầng DB. Không trộn review với feedback gợi ý.
- Response dùng snapshot_name/snapshot_price của lần mua, giữ đúng dù thực đơn đã đổi; không trả user_id/is_simulated. Lỗi ghi rollback, tranh chấp trùng được chuyển thành 409. Chưa có frontend ReviewForm hoặc API đọc/sửa/xóa đánh giá.
- 30 ca kiểm thử API mới đạt: quyền vai trò/chủ đơn, trạng thái, món đã mua, trùng, hai đơn cùng món, validation, snapshot, lỗi DB/rollback, tranh chấp UNIQUE và OpenAPI. Chưa kiểm chứng PostgreSQL thực tế; chưa stage/commit/push.
- Toàn bộ 1066 kiểm thử backend đạt (1036 trước + 30 mới); Ruff/format và diff check đạt. Không chạy lại frontend vì không sửa giao diện.

## Hồ sơ khẩu vị F.10.7

- Phần đánh giá đã được người dùng commit tại `1ef5c6b`. Lượt này thêm `preferences/schemas.py`, `service.py`, `router.py`, mount GET/PUT `/api/v1/preferences/` theo E.1/C.5, tách riêng để commit.
- Customer chỉ đọc/sửa hồ sơ của mình. Bỏ qua năm câu hỏi không tạo bản ghi; GET chưa có trả 404. PUT yêu cầu đủ năm câu, thay toàn bộ hồ sơ; danh sách trim/loại trùng, nguyên liệu chuyển chữ thường và hai mức dùng số nguyên nghiêm ngặt. Không nhận user_id/cờ mô phỏng từ client.
- Lưu cùng transaction, rollback khi lỗi; khóa hàng khi DB hỗ trợ và xử lý tranh chấp lần tạo đầu. PK user_id bảo vệ một hồ sơ/tài khoản. Chưa có frontend PreferencePage, lọc gợi ý hoặc lịch sử đồng ý điều khoản; không đổi schema/migration.
- 36 ca kiểm thử API mới đạt: quyền vai trò, cô lập tài khoản, tạo/ghi đè, validation đủ năm câu, chuẩn hóa, lỗi DB/rollback, tranh chấp PK và OpenAPI. Chưa stage/commit/push; chưa kiểm chứng PostgreSQL thực tế.
- Toàn bộ 1102 kiểm thử backend đạt (1066 trước + 36 mới); Ruff/format và diff check đạt. Frontend không thay đổi trong phần này.

## Ghi nhận sự kiện tương tác F.10.8

- Sau commit hồ sơ khẩu vị `b8aa5ff`, bổ sung `tracking/schemas.py`, `service.py`, `router.py` và mount POST `/api/v1/tracking/events` theo E.1/C.5; phần này để nhóm commit riêng.
- Customer gửi batch 1–100 sự kiện với `event_id` UUID v4. Server gắn người dùng từ token, kiểm tra request thuộc đúng người/phiên và món thuộc danh sách gợi ý. `impression` đầu tiên mới ghi `displayed_at`; click/feedback yêu cầu hiển thị trước. Sự kiện mới chỉ nhận trong khoảng 24 giờ trước đến 5 phút sau; gửi lại cùng ID/nội dung được tính trùng, ID khác nội dung trả 409.
- Ghi cả batch trong một transaction, rollback sự kiện và `displayed_at` khi lỗi. Có 31 ca kiểm thử API mới bao phủ quyền, ngữ cảnh sáu mã, thứ tự, idempotency, cửa sổ thời gian, rollback và OpenAPI. Không đổi schema/migration hoặc giao diện; API sinh gợi ý vẫn chờ phần AI, nên chưa có luồng người dùng tạo request thực tế.
- Toàn bộ 1133 kiểm thử backend đạt trên SQLite tạm; Ruff/format và diff check đạt. Chưa kiểm chứng PostgreSQL thực tế; chưa stage/commit/push.

## Kiểu dữ liệu và API công khai frontend F.11.1

- Tiếp tục bước 11 của mục F sau khi API tracking đã được commit. Thêm kiểu quán, món chuẩn, món bán, nguyên liệu, kết quả tìm kiếm và phân trang đúng schema backend hiện tại.
- Thêm tám hàm GET ở `api/restaurants.ts`, `menu.ts`, `search.ts`, dùng API client chung. Query mã hóa an toàn, giữ tọa độ/offset 0; hỗ trợ AbortSignal và giữ lỗi API. Endpoint công khai không gửi token và không yêu cầu phiên.
- Thực đơn trả mảng, tìm kiếm/danh mục trả Page; không thêm endpoint chưa có. Các client nghiệp vụ riêng như đơn hàng, vendor/admin sẽ tiếp tục ở từng phần của bước 11; màn hình khách hàng thuộc bước 12.
- Toàn bộ 69 kiểm thử frontend đạt (54 trước + 15 mới); TypeScript, ESLint, Prettier, production build và diff check đạt. Không thay backend; chưa stage/commit/push.

## Dọn bản nháp cục bộ

- Theo yêu cầu người dùng, chỉ dọn bản nháp khi bản chính tương ứng đã được tích hợp, kiểm thử, commit và không có thay đổi chưa commit.
- Đã xóa bảy bản `models.py` cũ trong `.runtime/pending-implementation/src/backend/app/users/`, `preferences/`, `restaurants/`, `menu/`, `orders/`, `reviews/`, `tracking/`. Bản chính của chúng vẫn nằm trong `src/` và lịch sử Git.
- Trước khi dọn tracking đã bảo toàn nguyên lớp BlindEvaluation chưa tích hợp sang bản nháp `src/backend/app/ai/evaluation_models.py` trong `.runtime/pending-implementation/`. Các bản nháp schema/service/router chưa tích hợp và công cụ Python/uv đang dùng để kiểm tra vẫn được giữ lại; API tracking chính đã nằm trong `src/backend/app/tracking/`.
- DB rỗng dùng để sinh migration ở `.runtime/migration-generation/` đã được dọn sau khi sinh xong. Các bản nháp migration cũ chưa được dùng hoặc chép đè vào migration hiện tại.
- Không xóa toàn bộ `.runtime/` trong lúc công cụ ở đó vẫn phục vụ kiểm thử; không thêm bản nháp vào commit.
- Đã dọn sáu file backend auth nháp sau khi bản chính được commit tại `dd97505` và không còn thay đổi chưa commit. Frontend auth mới tích hợp chưa commit nên bản nháp frontend tiếp tục được giữ; mã chạy chính không phụ thuộc chúng.

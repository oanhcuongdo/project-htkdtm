# Frontend Vị Việt

Đã có frontend auth F.8 theo thiết kế cấu trúc: đăng ký/đăng nhập, AuthContext/useAuth, API client, AppShell/Navbar/Footer và RoleGuard. F.12.1 có trang khẩu vị, F.12.2 có tìm món/quán và chọn vị trí gọi API backend; đã có giỏ/checkout/đơn customer, hồ sơ/thực đơn vendor. Đơn vendor và dashboard quán/admin chưa triển khai.

## API công khai đã chuẩn bị — F.11.1

Các module `src/api/restaurants.ts`, `menu.ts`, `search.ts` dùng chung `ApiClient` hiện có. Kiểu response ở `src/types/restaurant.ts`, `menu.ts`, `search.ts`, phân trang dùng `Page<T>` và `PaginationQuery` ở `common.ts`; đã đối chiếu schema backend F.10.1–F.10.3. SearchPage dùng API search ở F.12.2; trang quán/thực đơn và món dùng API chi tiết ở F.12.3.

| Hàm | Endpoint GET dưới `/api/v1` | Kết quả |
| :--- | :--- | :--- |
| `listRestaurants` | `/restaurants/` | `Page<RestaurantPublic>` |
| `getRestaurant` | `/restaurants/{id}` | `RestaurantPublic` |
| `getRestaurantMenu` | `/restaurants/{id}/menu` | `MenuItemPublic[]` |
| `getMenuItem` | `/menu-items/{id}` | `MenuItemPublic` |
| `listCanonicalDishes` | `/canonical-dishes` | `Page<CanonicalDishPublic>` |
| `listIngredients` | `/ingredients` | `Page<IngredientPublic>` |
| `searchDishes` | `/search/dishes` | `Page<DishSearchResult>` |
| `searchRestaurants` | `/search/restaurants` | `Page<RestaurantSearchResult>` |

Hàm danh sách nhận `{ offset?, limit? }`; tìm kiếm nhận `{ lat, lng, q?, radius?, offset?, limit? }`. Vị trí bắt buộc, radius/distance theo km, giá món nguyên VNĐ. Bỏ trường tùy chọn để dùng mặc định backend; query mã hóa bằng URLSearchParams, giữ tọa độ/offset bằng 0. Tất cả hàm nhận tùy chọn `{ signal }` ở đối số cuối để hủy request cũ. Không ghi vị trí/từ khóa vào storage.

Các request công khai đặt `authenticated: false`, dùng được khi chưa đăng nhập và không gửi token dù có phiên. Lỗi nghiệp vụ giữ nguyên `ApiError` (status/code/details) để màn hình xử lý; hủy request trả AbortError. Backend tiếp tục kiểm tra giới hạn, quyền công khai và tình trạng món/quán. TypeScript mô tả hợp đồng lúc biên dịch, chưa kiểm tra cấu trúc JSON khi chạy.

Kiểm thử `tests/publicApi.test.ts` đi qua API client thật với fetch thay thế: tám đường dẫn, query tiếng Việt/ký tự đặc biệt, phân trang, bỏ token, lỗi 404 và hủy tìm kiếm. Toàn bộ 69 kiểm thử frontend đạt (54 trước + 15 mới); TypeScript, ESLint, Prettier và production build đạt. E2E giao diện auth giữ kết quả mốc trước, chưa kiểm thử màn hình nghiệp vụ.

Nội dung dưới đây là đặc tả định hướng, bám theo [đề cương](../../docs/De_cuong_Vi_Viet.docx) (mục 4, 5.3, 6, 7, 8). Phần công nghệ và lệnh chạy đã có được ghi riêng ở mục 6; các đề xuất cho chức năng chưa triển khai cần được chốt theo [thiết kế cấu trúc](../../docs/THIET_KE_CAU_TRUC.md).

Phụ trách dự kiến xem tại [danhsachnhom.md](../../danhsachnhom.md).

## API nghiệp vụ khách hàng đã chuẩn bị — F.11.2

`src/types/preference.ts`, `order.ts`, `review.ts` mô tả payload/response theo backend F.10.5–F.10.7. Các hàm ở `src/api/preferences.ts`, `orders.ts`, `reviews.ts` dùng phiên đăng nhập và cơ chế refresh của API client chung. Khẩu vị đã nối vào F.12.1, checkout COD ở F.12.5; lịch sử/chi tiết đơn đã có ở F.12.6, ReviewForm đã có ở F.12.7.

| Hàm | Endpoint dưới `/api/v1` | Kết quả |
| :--- | :--- | :--- |
| `getPreference` | GET `/preferences/` | `Preference` |
| `savePreference` | PUT `/preferences/` | `Preference` |
| `createOrder` | POST `/orders/` | `OrderDetail` |
| `listOrders` | GET `/orders/` | `OrderDetail[]` |
| `getOrder` | GET `/orders/{id}` | `OrderDetail` |
| `cancelOrder` | PATCH `/orders/{id}/cancel` | `OrderDetail` |
| `createReview` | POST `/orders/{id}/review` | `ReviewOut` |

Khẩu vị PUT yêu cầu đủ năm câu, GET chưa khai báo giữ lỗi 404 cho màn hình quyết định onboarding; không tự tạo hồ sơ. `listOrders` nhận phân trang `{ offset?, limit? }`, trả mảng. Các hàm GET nhận `{ signal }` cuối cùng để hủy tải khi rời trang. Giá và tổng nguyên VNĐ; thời điểm response là chuỗi ISO có múi giờ; lịch sử có reason nullable.

Checkout sau này phải tạo UUID v4 cho session/key, giữ cùng `idempotency_key` và payload khi thử lại cùng ý định đặt đơn. `createOrder` chỉ gửi payload nhận vào, nhận OrderDetail cả khi tạo mới 201 hoặc gửi lại 200; không tự sinh key, tổng hoặc snapshot. Khi refresh sau 401, API client gửi lại nguyên JSON. Lỗi đổi giá/xung đột key/chuyển trạng thái/đánh giá trùng được giữ nguyên với details để UI xử lý. Đánh giá gắn món với đúng đơn; kiểm tra người mua, trạng thái completed và chống trùng nằm ở backend.

21 ca mới trong `tests/customerApi.test.ts` kiểm tra bảy endpoint/method/body/token, chặn request thiếu phiên, retry sau refresh, cùng key cho lần gửi lại, lỗi nghiệp vụ và hủy tải. Toàn bộ 90 kiểm thử frontend đạt (69 trước + 21 mới); TypeScript, ESLint, Prettier và production build đạt. Kiểm thử mới dùng API client thật với fetch thay thế; chưa xác nhận luồng checkout trên trình duyệt.

## API chủ quán đã chuẩn bị — F.11.3

`src/api/vendor.ts` có 15 hàm gọi API hiện có của vendor, tái sử dụng token/refresh/lỗi của ApiClient. Types quản lý nằm trong `types/restaurant.ts`, `types/menu.ts` và dùng chung `OrderDetail` ở `types/order.ts`. Hồ sơ và thực đơn đã nối trang vendor ở F.12.8–F.12.9; xử lý đơn vendor chưa có UI.

| Hàm | Method và đường dẫn dưới `/api/v1/vendor` | Kết quả |
| :--- | :--- | :--- |
| `getVendorRestaurant` | GET `/restaurant` | `RestaurantDetail` |
| `createVendorRestaurant` | POST `/restaurant` | `RestaurantDetail` |
| `updateVendorRestaurant` | PUT `/restaurant` | `RestaurantDetail` |
| `listVendorMenuItems` | GET `/menu-items` | `Page<MenuItemDetail>` |
| `getVendorMenuItem` | GET `/menu-items/{id}` | `MenuItemDetail` |
| `createVendorMenuItem` | POST `/menu-items` | `MenuItemDetail` |
| `updateVendorMenuItem` | PUT `/menu-items/{id}` | `MenuItemDetail` |
| `stopSellingVendorMenuItem` | DELETE `/menu-items/{id}` | `void` (204) |
| `listVendorOrders` | GET `/orders` | `OrderDetail[]` |
| `getVendorOrder` | GET `/orders/{id}` | `OrderDetail` |
| `confirmVendorOrder` | PATCH `/orders/{id}/confirm` | `OrderDetail` |
| `rejectVendorOrder` | PATCH `/orders/{id}/reject` | `OrderDetail` |
| `prepareVendorOrder` | PATCH `/orders/{id}/preparing` | `OrderDetail` |
| `deliverVendorOrder` | PATCH `/orders/{id}/delivering` | `OrderDetail` |
| `completeVendorOrder` | PATCH `/orders/{id}/complete` | `OrderDetail` |

Các hàm danh sách nhận `{ offset?, limit? }`; hàm GET nhận `{ signal }` cuối cùng để hủy tải. PUT hồ sơ bắt buộc bán kính, giờ mở/đóng và cờ nhận đơn; PUT món bắt buộc cờ bán, xác nhận và danh sách nguyên liệu. POST giữ mặc định tại máy chủ khi bỏ trường tùy chọn. Backend suy ra quán từ membership của tài khoản, kiểm tra phạm vi món/đơn; không có tham số chọn quán cho các thao tác vendor.

Ngừng bán dùng DELETE nhưng giữ món và dữ liệu lịch sử; 204 trả `undefined`, không yêu cầu JSON. Từ chối đơn gửi `{ reason }`; các chuyển trạng thái khác không có body. Client trả dữ liệu máy chủ, giữ lỗi 403/404/409 để màn hình xử lý và không tự quyết định quyền/trạng thái.

34 ca mới trong `tests/vendorApi.test.ts` kiểm tra 15 request, token và thiếu phiên, response 204, phân trang, lỗi quyền/phạm vi/trạng thái và hủy tải. Toàn bộ 124 kiểm thử frontend đạt (90 trước + 34 mới); TypeScript, lint, format và production build đạt. Fetch được thay thế trong kiểm thử; luồng giao diện vendor sẽ được kiểm tra khi triển khai ở F.12.

## API quản trị đã chuẩn bị — F.11.4

`src/api/admin.ts` có 11 hàm gọi endpoint admin hiện có. Types catalog được bổ sung trong `types/menu.ts`, bộ lọc quán ở `types/admin.ts`; dùng lại `RestaurantDetail`, `RestaurantStatus` và `Page<T>`. Chưa có giao diện duyệt quán hoặc quản lý danh mục.

| Hàm | Method và đường dẫn dưới `/api/v1/admin` | Kết quả |
| :--- | :--- | :--- |
| `listAdminRestaurants` | GET `/restaurants` | `Page<RestaurantDetail>` |
| `approveAdminRestaurant` | PATCH `/restaurants/{id}/approve` | `RestaurantDetail` |
| `suspendAdminRestaurant` | PATCH `/restaurants/{id}/suspend` | `RestaurantDetail` |
| `listAdminCanonicalDishes` | GET `/canonical-dishes` | `Page<CanonicalDishDetail>` |
| `createAdminCanonicalDish` | POST `/canonical-dishes` | `CanonicalDishDetail` |
| `updateAdminCanonicalDish` | PUT `/canonical-dishes/{id}` | `CanonicalDishDetail` |
| `deleteAdminCanonicalDish` | DELETE `/canonical-dishes/{id}` | `void` (204) |
| `listAdminIngredients` | GET `/ingredients` | `Page<IngredientDetail>` |
| `createAdminIngredient` | POST `/ingredients` | `IngredientDetail` |
| `updateAdminIngredient` | PUT `/ingredients/{id}` | `IngredientDetail` |
| `deleteAdminIngredient` | DELETE `/ingredients/{id}` | `void` (204) |

Danh sách nhận `{ offset?, limit? }`; danh sách quán nhận thêm `status?: "pending" | "approved" | "suspended"`. Bỏ status để lấy mọi trạng thái; các GET nhận `{ signal }` ở đối số cuối. PATCH duyệt/tạm ngừng không có body; dùng cờ nhận đơn từ response vì duyệt không tự bật nhận đơn.

POST món chuẩn cho phép bỏ mức cay/danh sách/source_id để dùng mặc định backend. PUT yêu cầu đủ các trường, gồm `source_id` có thể null; tên, vùng và phương pháp bắt buộc cho cả hai. Nguyên liệu gửi `{ name }`, máy chủ chuẩn hóa và trả bản ghi. Types detail giữ source_id/cờ mô phỏng cho quản trị, khác types công khai. Hai DELETE thành công 204 trả undefined; mục đang được dùng trả `ApiError` 409 `CATALOG_IN_USE`.

Mọi request dùng phiên/refresh của ApiClient; backend xác nhận role admin từ DB. Lỗi 403/404/409 giữ nguyên và không tự xóa phiên. 28 ca mới trong `tests/adminApi.test.ts` kiểm tra 11 request và token/thiếu phiên, bộ lọc, phân trang, response 204, lỗi nghiệp vụ, hủy tải và PUT gửi lại sau refresh giữ source_id null. Toàn bộ 152 kiểm thử frontend đạt (124 trước + 28 mới); TypeScript, lint, format và production build đạt. Fetch được thay thế trong kiểm thử; chưa kiểm thử màn hình quản trị trên trình duyệt.

## Màn hình khẩu vị đã triển khai — F.12.1

Customer mở `/onboarding/taste` từ nút **Khai báo khẩu vị** tại `/account`. RoleGuard chặn vendor/admin và chuyển người chưa đăng nhập về login; đăng nhập lại có thể quay về route này. Sau đăng nhập thông thường vẫn về trang tài khoản, chưa tự kiểm tra/lần đầu chuyển onboarding.

`pages/customer/PreferencePage.tsx` đọc GET `/preferences/`: 404 NOT_FOUND mở hồ sơ mới, dữ liệu có sẵn được điền lại (giữ cả nhãn vùng tùy chỉnh), lỗi khác hiện nút thử lại và không mở form để tránh ghi đè hồ sơ chưa tải được. Năm câu hỏi gồm vùng miền (nhiều lựa chọn), mức cay, nguyên liệu thích/tránh (ngăn cách bằng dấu phẩy), mức khám phá. Vùng và nguyên liệu cho phép trống; hai mức cần được chọn. Validation giới hạn mỗi danh sách 100 mục, mỗi mục 100 ký tự, lỗi dưới trường và focus trường lỗi đầu tiên.

Người dùng cần chọn đồng ý lưu trước PUT. Đây là điều kiện ở client, chưa có lịch sử đồng ý trong DB. Bỏ qua về tài khoản và không gọi PUT; hồ sơ cũ cũng không bị xóa. Khi lưu, khóa trường/nút để ngăn gửi lặp; lỗi giữ câu trả lời, lỗi validation 422 được ánh xạ theo trường. Chỉ hiện thành công sau response backend, sau đó dùng hồ sơ đã chuẩn hóa. Giao diện giải thích dữ liệu phục vụ gợi ý sau này; chưa tạo gợi ý hoặc cam kết lọc dị ứng.

CSS riêng `preferences.css` dùng màu/font hiện có, card 28px, lựa chọn và nút có vùng chạm tối thiểu 48px, focus rõ và giảm chuyển động. Desktop hai cột giới thiệu/biểu mẫu, mobile một cột rút gọn giới thiệu. Không lưu câu trả lời vào localStorage.

Toàn bộ 165 kiểm thử frontend đạt (152 trước + 13 mới). Hai kịch bản Playwright mới đạt trên Edge với API được chặn và trả response kiểm soát trong test: bỏ qua, lỗi/thử lại/tải lại, payload qua API client thật, responsive 360/390/768/1280px và bàn phím. Đã xem ảnh desktop/mobile; chưa chạy luồng khẩu vị với PostgreSQL/backend thật trong trình duyệt. Backend khẩu vị vẫn có bộ kiểm thử SQLite riêng đã ghi tại F.10.7. TypeScript, lint, format và build đạt.

## Chọn vị trí và tìm kiếm đã triển khai — F.12.2

Route công khai `/search`, mở từ **Tìm món, quán** trên thanh điều hướng. `SearchPage` dùng hai API search hiện có, chuyển Món ăn/Quán ăn, tìm theo từ khóa (tối đa 180 ký tự), bán kính 1/3/5/10/20/50 km, phân trang 12 mục. Để trống từ khóa để khám phá gần vị trí đã chọn. Thay bộ lọc/chế độ hoặc vị trí quay về trang đầu; đang gõ chưa gọi API cho đến khi gửi form. Kết quả có khoảng cách đường thẳng, giá VNĐ, trạng thái mở/nhận đơn, địa chỉ/giờ quán hoặc nguyên liệu món. Tên món/quán liên kết tới hai trang công khai ở F.12.3; thêm vào giỏ từ chi tiết món ở F.12.4, checkout COD đã có ở F.12.5.

`LocationProvider` trong AppShell giữ tọa độ/tên địa điểm trong bộ nhớ, chia sẻ qua `useLocation`. `components/map/LocationPicker.tsx` không tự xin quyền; người dùng bấm định vị mới gọi Geolocation API, chờ tối đa 10 giây. Khi bị từ chối/không hỗ trợ/quá hạn có lỗi tiếng Việt và vẫn nhập tay được. Nhập vĩ độ -90..90, kinh độ -180..180, chấp nhận 0; tên địa điểm tùy chọn chỉ là nhãn. Nút xóa xóa vị trí và ô nhập, ẩn kết quả. Không ghi tọa độ/nhãn vào storage hoặc tracking; chỉ gửi tọa độ đến API tìm kiếm. Định vị trả muộn không ghi đè lựa chọn nhập tay mới hơn.

**Giới hạn bản đồ:** chưa có MapView hoặc dịch vụ geocoding. Tên địa điểm/địa chỉ nhập vào không tự đổi thành tọa độ; người dùng cần định vị hoặc lấy tọa độ từ bản đồ bên ngoài rồi nhập. Chức năng nhập địa chỉ để xác định điểm theo thiết kế còn chờ tích hợp dịch vụ bản đồ. Vị trí mất khi tải lại hoặc rời AppShell (ví dụ tới trang login).

Có trạng thái chưa chọn vị trí, tải, rỗng, lỗi/thử lại và phân trang theo total API. Đổi vị trí/truy vấn hủy yêu cầu cũ, không cho phản hồi cũ ghi đè kết quả mới. Không tự nới bán kính, không cá nhân hóa theo khẩu vị. Quán đóng cửa vẫn xuất hiện theo backend và ghi rõ trạng thái; thông tin nguyên liệu không bảo đảm an toàn dị ứng.

188 kiểm thử frontend đạt (165 trước + 23 mới). Hai kịch bản Playwright tìm kiếm mới và hai kịch bản khẩu vị đạt với Edge/API kiểm soát trong test; đã xem ảnh 360/1280px và kiểm tra không tràn ngang ở 360/390/768/1280px. Kiểm tra tọa độ 0/biên/sai, quyền định vị bị từ chối, phản hồi cũ/định vị muộn, từ khóa/bán kính/chế độ, phân trang, lỗi/thử lại/xóa vị trí. Chưa chạy UI search với backend/PostgreSQL thật. TypeScript/lint/format/build đạt.

## Quán, thực đơn và chi tiết món — F.12.3

Hai route công khai `/restaurants/:id`, `/menu-items/:id` nối từ tên món/quán trong kết quả tìm kiếm. Trang quán hiển thị địa chỉ, giờ Việt Nam (cả ngày/qua đêm), bán kính và trạng thái mở/nhận đơn do backend trả. Không cần chọn vị trí để đọc chi tiết; các trang này không kiểm tra khả năng giao đến khách.

`RestaurantPage` tải hồ sơ trước rồi tải thực đơn. Thực đơn 12 món/trang, gọi API với limit=13 và offset tăng 12 để dò còn trang sau vì response không có total. Món thứ 13 được giữ làm dấu, không hiện trong trang trước; trang sau đọc lại từ đúng offset. Rỗng ở trang đầu có thông báo quán chưa có món đang bán; rỗng ở trang sau cho quay lại trang trước. Lỗi thực đơn có retry và giữ hồ sơ quán đã tải.

`DishDetailPage` tải món rồi quán tương ứng để hiển thị trạng thái hiện tại. Tách **Nguyên liệu từ quán** và **Đặc trưng món chuẩn** (vùng, cách chế biến, mức cay, nguyên liệu tham khảo/nhãn). Không dùng nguyên liệu món chuẩn thay cho nguyên liệu thực tế còn thiếu, không coi cờ xác nhận là bảo đảm dị ứng. Giá nguyên VNĐ lấy từ API. Có liên kết về thực đơn quán và thêm món vào giỏ F.12.4; checkout COD đã tích hợp ở F.12.5.

Component dùng chung ở `components/menu/`: DishCard, IngredientInfo, RestaurantInfo; `components/common/PublicResourceState` cho lỗi 404/mạng. Hook `usePublicData` hủy và bỏ phản hồi cũ khi đổi trang, hỗ trợ retry; route kiểm tra ID nguyên dương trong giới hạn backend trước khi gọi API. Lỗi 404 dùng thông báo không tồn tại/chưa công khai, không lộ trạng thái quản lý. CSS `catalog.css` đồng bộ font/màu, card 24–28px, bố cục thích ứng và focus rõ.

206 kiểm thử frontend đạt (188 trước + 18 mới), gồm phân trang dò thêm một món, đổi ID/abort, ID sai, 404/rỗng/lỗi/retry, nguyên liệu, giờ qua đêm/cả ngày và liên kết. Hai kịch bản Playwright mới đạt trên Edge với API kiểm soát trong test; hai kịch bản search cũng đạt. Đã xem ảnh desktop/mobile và không tràn ngang ở 360/390/768/1280px. TypeScript/lint/format/build đạt; chưa kiểm tra luồng quán/món với backend/PostgreSQL thật trong trình duyệt.

## Giỏ hàng một quán — F.12.4

Route `/cart` công khai, mở từ Navbar (kèm tổng số phần) hoặc sau khi thêm món ở trang chi tiết. `CartProvider` bao quanh router để giỏ giữ nguyên khi điều hướng qua trang login/register; `useCart` chia sẻ state, `cartReducer` kiểm tra một quán, giới hạn số lượng và tổng tiền. Khách vãng lai/customer có thể chuẩn bị giỏ; vendor/admin không thêm món như khách hàng.

Giỏ chỉ giữ trong bộ nhớ, không ghi storage hoặc API. Tải lại/đóng ứng dụng làm trống giỏ, có thông báo trên trang. Guest đăng nhập giữ giỏ hiện tại; đăng xuất hoặc đổi từ tài khoản này sang tài khoản khác xóa giỏ. Khôi phục phiên/loading/lỗi kết nối không tự xóa giỏ của tài khoản đang dùng.

`AddToCart` lấy dữ liệu món/quán đang hiển thị, khóa thêm khi món/quán chưa nhận đơn. `QuantityControl` dùng nút +/- (1–99, vùng chạm 48px). Thêm cùng món gộp số lượng, tối đa 99 phần/món và 100 món khác nhau. Giá VNĐ nguyên lưu theo lúc thêm; nếu thêm lại món có giá khác, báo lỗi và yêu cầu xóa dòng cũ trước khi dùng giá mới, không tự đổi giá cả giỏ. Các điều kiện phục vụ/giá thật phải được kiểm tra lại khi đặt đơn.

Thêm quán khác mở dialog xác nhận: giữ giỏ hiện tại hoặc thay toàn bộ bằng món mới. Native dialog giữ focus, Escape hủy và trả focus về nút thêm. `CartPage` có sửa số lượng, xóa từng món, tạm tính, link chi tiết món/quay lại thực đơn và đi tới checkout F.12.5; CartDrawer chưa có.

229 kiểm thử frontend đạt (206 trước + 23 mới), gồm reducer và UI/provider: gộp/tổng tiền, giới hạn số lượng/100 món, giá đổi, đổi quán xác nhận/hủy, giới hạn vai trò, vòng đời guest/login/restore/logout. Hai kịch bản Playwright cart mới và hai catalog đạt với Edge/API đọc kiểm soát; không tạo đơn. Đã xem ảnh desktop/mobile, không tràn ngang ở 360/390/768/1280px; kiểm tra Escape/focus, xóa/sửa/đổi quán và tải lại mất giỏ. TypeScript/lint/format/build đạt.

## Checkout COD — F.12.5

Customer mở `/checkout` từ giỏ; guest đi qua login rồi quay về checkout, vendor/admin bị RoleGuard chặn. `CheckoutForm` nhận địa chỉ 5–500 ký tự, tọa độ từ LocationPicker và xác nhận hai thông tin cùng điểm giao/COD. Tọa độ thay đổi hoặc sửa địa chỉ yêu cầu xác nhận lại. Chưa có geocoding nên client không tự kiểm tra địa chỉ dạng chữ khớp tọa độ.

`CheckoutPage` gọi POST `/orders/` qua API client thật, gửi expected_price của từng dòng, không gửi total/snapshot/trạng thái. Khóa gửi lặp bằng ref và nút disabled. Chỉ hiện ghi nhận đơn sau response 201/200 của server, dùng mã đơn/trạng thái/snapshot/tổng tiền trả về. Chỉ xóa giỏ nếu vẫn trùng nội dung đã gửi; giỏ chỉnh sửa sau đó được giữ. Trang lịch sử và theo dõi đơn đã nối ở F.12.6.

`useIdempotency` giữ một yêu cầu chờ cho mỗi customer trong tab: payload gồm địa chỉ/tọa độ, session UUID v4 và key UUID v4. Lưu payload trong sessionStorage `viviet.checkout.pending.v1.{userId}`, session trong `viviet.session.v1`; localStorage chỉ giữ key dưới `viviet.checkout.key.v1.{userId}.{sessionId}`, không lưu địa chỉ/tọa độ. Cache bộ nhớ giữ cùng yêu cầu qua điều hướng; reload khôi phục từ sessionStorage ngay cả khi giỏ trong bộ nhớ đã mất. Xóa dữ liệu yêu cầu chờ khi thành công, lỗi nghiệp vụ chắc chắn không tạo đơn hoặc khi người dùng chủ động bỏ sau kiểm tra. Yêu cầu chờ chưa rõ kết quả được giữ theo tài khoản qua logout/login để tránh phát sinh key mới. Nếu storage bị chặn, có thông báo giữ trang mở; không bảo đảm khôi phục sau reload/đóng tab trong trường hợp đó.

Lỗi mạng/5xx/401/403 không biết chắc kết quả giữ nguyên payload/key, khóa sửa nội dung và có **Thử lại cùng đơn**. Backend 400/404/422 hoặc 409 nghiệp vụ không tạo đơn mở lại form, giữ địa chỉ/câu trả lời. ORDER_PRICE_CHANGED hiển thị giá cũ/mới, lấy lại giá từ API món và yêu cầu đồng ý cập nhật; cập nhật chưa gửi đơn, phải bấm đặt lại. IDEMPOTENCY_CONFLICT/EXPIRED không tự sinh key; có nút tải 20 đơn gần nhất với mã/thời gian/trạng thái/địa chỉ/món/tổng. Danh sách không tự suy đơn nào khớp key và không thay thế lịch sử đầy đủ. Chỉ sau khi tải danh sách và xác nhận cảnh báo, người dùng mới có thể bỏ yêu cầu cũ để lập lại; thao tác này có thể tạo thêm đơn nếu lần trước đã thành công.

247 kiểm thử frontend đạt (229 trước + 18 mới). Hai Playwright checkout mới và hai cart đạt trên Edge/API kiểm soát, kiểm tra mất phản hồi → reload → retry cùng payload/key và đồng ý giá mới trước gửi lại. Đã xem ảnh desktop/mobile, không tràn ngang ở 360/390/768/1280px; TypeScript/lint/format/build đạt. Chưa kiểm tra UI checkout với backend/PostgreSQL thật; backend orders đã có bộ kiểm thử riêng của F.10.5.

## Lịch sử và chi tiết đơn khách hàng — F.12.6

Customer mở `/orders` từ Navbar/tài khoản, hoặc `/orders/:id` từ receipt sau checkout. Hai route có RoleGuard; đăng nhập có thể quay về đường dẫn đơn hợp lệ. Backend vẫn xác định chủ đơn từ token. Nội dung được tải lại khi đổi tài khoản/ID, hủy request cũ và không lưu danh sách/chi tiết đơn vào storage.

`OrderListPage` gọi GET `/orders/`, mới nhất trước theo backend, 10 đơn/trang với limit11 để dò trang sau vì API trả mảng không có total. Có làm mới, tải/rỗng/lỗi/retry và phân trang. Thẻ đơn dùng tên/giá snapshot, tổng máy chủ, địa chỉ và thời gian theo Việt Nam; link tới chi tiết. Không đọc lại thực đơn để thay snapshot.

`OrderDetailPage` và `useCustomerOrder` đọc GET chi tiết, hiển thị trạng thái, món/giá lúc mua, COD, địa chỉ/tọa độ và timeline thực tế từ history (gồm lý do từ chối nếu có). DTO không có tên người thao tác nên giao diện không tự tạo thông tin này. Tự GET mỗi 15 giây khi tab đang hiển thị và đơn còn xử lý, đọc lại khi trở về tab; dừng sau completed/cancelled/rejected hoặc unmount. Có nút cập nhật thủ công. Lỗi refresh mạng giữ dữ liệu gần nhất kèm thông báo và khóa hủy; lỗi 401/403/404 ẩn dữ liệu cũ.

Chỉ pending có nút hủy. Dialog yêu cầu xác nhận, Escape giữ đơn và trả focus. PATCH hủy khóa gửi lặp, không cập nhật lạc quan; dùng response máy chủ. Nếu hủy lỗi/409, tự GET trạng thái mới và không tự PATCH lại. GET cũ đang chờ bị hủy/bỏ qua để không ghi đè kết quả hủy. Khi quán vừa xác nhận, UI giữ trạng thái confirmed do server trả và bỏ nút hủy. Đánh giá món đã nối ở F.12.7 cho completed.

Component chung: OrderStatusBadge, OrderTimeline, OrderError, CancelOrderDialog ở `components/order/`. `orders.css` đồng bộ font/màu và focus, card 24–28px, bố cục một/hai cột thích ứng. 271 kiểm thử frontend đạt (247 trước + 24 mới), gồm quyền/chủ đơn, ID sai/404, snapshot, phân trang, polling/tab ẩn/trạng thái cuối, thay tài khoản/ID, hủy xác nhận/lỗi/409/gửi lặp và GET không ghi đè PATCH. Hai Playwright orders mới và hai checkout đạt với Edge/API kiểm soát; đã xem ảnh desktop/mobile, không tràn ngang 360/390/768/1280px. TypeScript/lint/format/build đạt; chưa chạy UI đơn với backend/PostgreSQL thật.

## Đánh giá món đã mua — F.12.7

Trong `/orders/:id`, customer chỉ thấy phần đánh giá khi API trả trạng thái `completed`. Mỗi OrderItem có một `components/order/ReviewForm.tsx` độc lập, dùng tên snapshot của lần mua, chọn 1–5 sao và nhận xét tùy chọn tối đa 2000 ký tự. Không có form ở pending/confirmed/preparing/delivering/cancelled/rejected; backend vẫn kiểm tra quyền người mua, trạng thái và món thuộc đúng đơn.

Form dùng radio native với nhãn tiếng Việt, điều khiển được bằng Tab/Space/phím mũi tên, vùng chạm tối thiểu 48px và focus rõ. `reviewValidation.ts` kiểm tra mức sao nguyên/giới hạn nhận xét; nhận xét được trim trước POST `/orders/{id}/review`. Có counter, lỗi theo trường, loading/disabled và ref khóa gửi lặp. Lỗi gửi giữ sao/nhận xét; lỗi 422 ánh xạ rating/comment. Lỗi quyền/món/đơn chưa completed khóa gửi tiếp và yêu cầu tải lại trang. Không lưu nội dung nhận xét trong storage hoặc tracking.

Chỉ hiện đã lưu sau response ReviewOut hợp lệ đúng order/menu item, dùng điểm/nhận xét/thời gian trả về và khóa gửi tiếp trong lần mở trang. Khi nhận `REVIEW_ALREADY_EXISTS` (kể cả thử lại sau mất phản hồi), UI chỉ thông báo món đã được đánh giá, không giả định lần gửi này thành công hoặc tự hiển thị điểm cũ. UNIQUE backend giữ một đánh giá/món/đơn.

**Giới hạn đọc lại:** backend chưa có GET danh sách/chi tiết review, cũng chưa sửa/xóa review. Sau reload không biết sẵn món nào đã đánh giá nên form có thể hiện lại; POST trùng sẽ được chặn và chuyển thông báo. Không hiển thị sao/nhận xét cũ khi chưa có dữ liệu từ API. Review này là cảm nhận sau mua, tách khỏi feedback phù hợp của gợi ý.

297 kiểm thử frontend đạt (271 trước + 26 mới); hai Playwright reviews mới và hai orders đạt với Edge/API kiểm soát. Bao phủ chỉ completed, đúng payload/món, validation/focus, độc lập nhiều form, khóa gửi lặp, lỗi giữ nội dung/422/409, response không hợp lệ và bỏ phản hồi sau unmount. Đã xem ảnh desktop/mobile, không tràn ngang 360/390/768/1280px, chọn sao bằng bàn phím. TypeScript/lint/format/build đạt; chưa chạy UI review với backend/PostgreSQL thật.

## Hồ sơ quán dành cho vendor — F.12.8

Vendor mở `/vendor/profile` từ **Quản lý hồ sơ quán** tại `/vendor`. Route có RoleGuard, login hỗ trợ quay lại đúng đường dẫn; `/vendor` vẫn là trang tài khoản. Backend suy quán từ membership, UI không nhận ID quán để chọn mục tiêu. Đổi tài khoản hủy/bỏ phản hồi cũ và tải lại hồ sơ.

`pages/vendor/ProfilePage.tsx` gọi GET `/vendor/restaurant`. Chỉ 404 NOT_FOUND nghiệp vụ mở form tạo; lỗi mạng/HTTP 404 khác có retry và không bị hiểu là chưa có quán. Form tên 1–160, địa chỉ 1–500 ký tự, tọa độ hữu hạn trong giới hạn, bán kính (0,50] km, giờ HH:MM Việt Nam; giờ bằng nhau là cả ngày, qua nửa đêm được hỗ trợ. Chưa geocode địa chỉ. `vendorProfileValidation.ts` chuẩn hóa/kiểm tra và ánh xạ dữ liệu máy chủ.

POST tạo quán gửi hồ sơ, không gửi status/owner/id/cờ nhận đơn. Quán mới chờ duyệt và không nhận đơn. PUT yêu cầu đủ trường hồ sơ và accepting_orders; chỉ approved mới bật được. Pending/suspended vẫn sửa thông tin với cờ nhận đơn false. Có nút kiểm tra trạng thái duyệt từ GET, giữ các chỉnh sửa khác chưa lưu; quán vừa approved không tự bật nhận đơn. Nếu PUT trả RESTAURANT_NOT_APPROVED, UI tắt/khóa cờ nhận đơn và yêu cầu đọc lại trạng thái, không tự suy quán đang pending hay suspended.

Có loading/lỗi/retry, lỗi theo trường, focus ô sai, ref khóa gửi lặp và giữ dữ liệu khi lưu lỗi. Chỉ báo lưu sau response hồ sơ hợp lệ. Tạo quán lỗi mạng/5xx/response sai hoặc RESTAURANT_ALREADY_LINKED khóa POST tiếp, có nút kiểm tra hồ sơ đã liên kết: GET thấy quán thì chuyển sang sửa, GET xác nhận chưa có mới cho tạo tiếp. Backend membership UNIQUE là chốt chống tạo trùng; UI không giả thành công từ lỗi. PUT thử lại cùng nội dung có tính thay thế hồ sơ, không tạo quán mới.

Không lưu nháp vào storage; reload làm mất chỉnh sửa chưa lưu. Quản lý thực đơn đã nối ở F.12.9; chưa có giao diện duyệt admin, đơn vendor hoặc dashboard. CSS `profile.css` đồng bộ màu/font, focus, vùng chạm, card 24–28px và bố cục thích ứng.

321 kiểm thử frontend đạt (297 trước + 24 mới), hai Playwright vendorProfile đạt với Edge/API kiểm soát. Bao phủ tạo/sửa đủ payload, pending/suspended/approved, GET/retry, dữ liệu lỗi giữ nguyên, 422, 409 chưa duyệt, tạo mất phản hồi/already linked, quyền và đổi tài khoản. Đã xem ảnh desktop/mobile, không tràn ngang 360/390/768/1280px; TypeScript/lint/format/build đạt. Chưa chạy UI profile với backend/PostgreSQL thật. Lượt gọi kèm E2E auth cũ không đạt vì backend 127.0.0.1:8000 không chạy (ECONNREFUSED); đã dừng bộ đó và kiểm tra riêng vendor bằng API kiểm soát, không coi đây là kết quả auth E2E mới.

## Thực đơn và nguyên liệu dành cho vendor — F.12.9

Vendor mở **Quản lý thực đơn** từ `/vendor`. Ba route `/vendor/menu`, `/vendor/menu/new`, `/vendor/menu/:id/edit` có RoleGuard và hỗ trợ quay lại sau đăng nhập. `MenuManagePage` gọi GET danh sách 12 món/trang theo total/offset/limit, gồm món đang bán và ngừng bán; có tải/rỗng/lỗi/retry, liên kết hồ sơ khi chưa có membership. Đổi tài khoản tải dữ liệu mới, không giữ editor của tài khoản trước.

`MenuItemPage` đọc hồ sơ và món riêng qua API vendor khi sửa. ID sai không gọi API; món sai quán/sai ID hoặc response không hợp lệ không mở form tạo mới. Form tên 1–180 ký tự, giá nguyên 1–10.000.000 VNĐ, một món chuẩn, trạng thái bán, danh sách tối đa 100 ID nguyên liệu khác nhau và cờ xác nhận. Xác nhận nguyên liệu cần ít nhất một thành phần thực tế. `CatalogPicker` dùng GET món chuẩn/nguyên liệu công khai, 10 mục/trang, giữ lựa chọn qua nhiều trang và cho bỏ nguyên liệu bằng chip. Không tự dùng JSON nguyên liệu tham khảo của món chuẩn làm nguyên liệu thực tế tại quán.

POST và PUT gửi đủ sáu trường: `canonical_dish_id`, `name`, `price`, `is_available`, `ingredients_verified`, `ingredient_ids`. Không gửi ID quán/tài khoản/trạng thái duyệt/cờ mô phỏng. Quán pending/suspended vẫn chuẩn bị món; công khai và nhận đơn phụ thuộc backend. Validation tiếng Việt dưới trường, focus lỗi, disabled/loading và ref ngăn gửi lặp. Chỉ thông báo lưu sau response hợp lệ đúng quán/món; lỗi giữ draft, không lưu nháp vào storage.

Tạo món chưa có idempotency backend. Khi POST lỗi mạng/5xx/response sai hoặc chưa rõ kết quả, form khóa gửi tiếp và dẫn **Kiểm tra thực đơn đã lưu**; không tự thử POST lại hay giả thành công. Sau đối chiếu danh sách, vendor chủ động quyết định có tạo lại hay không. PUT lỗi cho sửa/thử lại với nội dung thay thế đầy đủ. Native dialog ngừng bán có xác nhận, Escape/hủy và trả focus. DELETE 204 giữ record/liên kết/lịch sử, sau đó GET lại danh sách; lỗi DELETE cũng GET lại để đối chiếu, không tự lặp mutation. Bật bán lại qua form sửa.

Thành phần chung ở `components/menu/CatalogPicker.tsx`, `StopSellingDialog.tsx`; kiểm tra/ánh xạ form ở `utils/vendorMenuValidation.ts`, giao diện ở `pages/vendor/menu.css`. Nguyên liệu được quản lý ngay trong form món; chưa có `IngredientPage` riêng, trang xử lý đơn vendor, catalog admin hoặc dashboard. Không đổi backend/schema/dependencies.

349 kiểm thử frontend đạt (321 trước + 28 mới); hai Playwright vendorMenu mới và hai vendorProfile đạt với Edge/API kiểm soát. Bao phủ payload đủ trường, nguyên liệu thực tế, phân trang/giữ lựa chọn, validation/422, khóa gửi, POST chưa rõ kết quả, ngừng bán, guard/ID và đổi tài khoản. Đã xem ảnh desktop/mobile, không tràn ngang 360/390/768/1280px; TypeScript/lint/format/build đạt. Chưa chạy UI thực đơn với backend/PostgreSQL thật.

## Đọc đơn hàng của quán — F.12.10

`/vendor/orders` và `/vendor/orders/:id` dùng API vendor với RoleGuard, mở từ tài khoản chủ quán. Danh sách 10 mục/trang dùng limit11 để dò trang sau; chi tiết dùng snapshot tên/giá, tổng tiền, địa chỉ/tọa độ giao và OrderTimeline. Có làm mới thủ công, loading/rỗng/lỗi/retry, kiểm tra ID và bỏ dữ liệu cũ khi đổi tài khoản. Dùng lại stylesheet đơn hàng customer; chưa có polling hoặc các nút chuyển trạng thái vendor. Các ghi chú trước đây về chưa có UI xử lý đơn vẫn áp dụng cho thao tác ghi; phần đọc đã có ở mốc này. Chưa kiểm chứng trình duyệt/backend thật trong lượt này.

## Xử lý đơn của quán — F.12.11

Chi tiết đơn vendor có nhận/từ chối pending, bắt đầu chuẩn bị confirmed, giao preparing và hoàn tất delivering. Các nút chỉ hiện cho bước hợp lệ, đều cần xác nhận; từ chối yêu cầu lý do trim 1–500 ký tự. PATCH khóa gửi lặp/làm mới; kết quả phải đúng ID, quán và trạng thái đích. Sau thành công hoặc lỗi đều đọc lại GET, không tự lặp PATCH. Nếu đọc lại lỗi, chỉ cho tải lại dữ liệu trước khi thao tác tiếp. Đơn kết thúc không có nút ghi; chưa có polling. Chưa kiểm chứng trình duyệt/backend thật trong lượt này.

## Kiểm chứng đơn vendor trên trình duyệt — F.12.12

Ba ca `e2e/vendorOrders.spec.ts` kiểm tra mở danh sách/chi tiết, xác nhận đủ bốn bước xử lý, từ chối với lý do và lịch sử, PATCH mất phản hồi rồi GET lỗi/tải lại. Kiểm tra token, không gửi khi hủy xác nhận, không tự PATCH lại và khóa thao tác khi chưa đọc được trạng thái. Đạt trên Edge với API kiểm soát; đã xem ảnh desktop/mobile và kiểm tra không tràn ngang 360/390/768/1280px. TypeScript/lint/format đạt. Đây là kiểm chứng UI bổ sung cho F.12.10–F.12.11; chưa phải kiểm thử backend/PostgreSQL thật.

## Danh sách quán dành cho admin — F.12.13

Admin mở **Danh sách quán** từ tài khoản hoặc `/admin/restaurants`. Trang có RoleGuard và hỗ trợ quay lại sau login. GET `/admin/restaurants` dùng 12 mục/trang, total từ máy chủ, bộ lọc tất cả/chờ duyệt/đã duyệt/tạm ngừng. Đổi bộ lọc về trang đầu, hủy/bỏ phản hồi cũ; đổi tài khoản không giữ danh sách trước. Có tải/rỗng/lỗi/retry và làm mới.

Thẻ quán hiển thị trạng thái nhận đơn máy chủ, địa chỉ; mở thông tin bằng details/summary native để xem giờ Việt Nam/cả ngày/qua đêm, bán kính, tọa độ và cờ mô phỏng. Không gọi API công khai để đọc quán pending/suspended. Đây là UI đọc admin đầu tiên; các ghi chú chưa có UI admin ở mốc cũ vẫn áp dụng cho thao tác duyệt/tạm ngừng và CRUD catalog chưa triển khai.

366 kiểm thử frontend đạt, một Playwright adminRestaurants đạt với Edge/API kiểm soát; kiểm tra không tràn ngang 360/390/768/1280px. TypeScript/lint/build đạt. Chưa kiểm chứng backend/PostgreSQL thật.

## Duyệt và tạm ngừng quán — F.12.14

Danh sách admin đã có duyệt pending/suspended và tạm ngừng pending/approved, xác nhận trước khi gửi và quay lại không gửi. Trong khi PATCH khóa thao tác, bộ lọc/phân trang/làm mới; chỉ ghi nhận thành công khi response đúng ID/trạng thái. Cả thành công và lỗi đều GET lại danh sách, không tự PATCH lại. Duyệt không tự bật nhận đơn; tạm ngừng giữ đơn cũ để tiếp tục xử lý. Các ghi chú chưa có thao tác duyệt ở mốc trước đã được thay thế bởi mốc này; CRUD catalog chưa có UI.

368 unit/UI và hai Playwright adminRestaurants đạt với API kiểm soát; TypeScript/lint/build đạt. Chưa kiểm chứng backend/PostgreSQL thật.

## Danh mục nguyên liệu admin — F.12.15

Route `/admin/ingredients` có RoleGuard và link từ tài khoản admin. Danh sách phân trang 12 mục, total từ máy chủ; thêm/sửa chỉ gửi tên chuẩn hóa trim/chữ thường, giới hạn 1–100 ký tự. Xóa có xác nhận, 409 giữ nguyên liệu đang được tham chiếu. Không chỉnh cờ mô phỏng. Sau DELETE thành công/lỗi tải lại danh sách, không tự gửi lại mutation. Tạo mất phản hồi hoặc lỗi chưa rõ kết quả khóa gửi và yêu cầu tải lại/đối chiếu trước khi chủ động mở form mới; không giả thành công. Lỗi giữ dữ liệu; reload mất nháp. Món chuẩn sẽ triển khai riêng.

368 kiểm thử hồi quy đạt, hai Playwright adminIngredients đạt với API kiểm soát; không tràn ngang 360/390/768/1280px, TypeScript/lint/build đạt. Chưa chạy backend/PostgreSQL thật. Chạy `npx playwright test e2e/adminIngredients.spec.ts` với dev server và biến E2E_BASE_URL/E2E_BROWSER_CHANNEL như các mốc trước.

## Danh mục món chuẩn admin — F.12.16

`/admin/dishes` có RoleGuard, liên kết tài khoản admin, danh sách phân trang và tạo/sửa/xóa món chuẩn. Form tên, vùng miền, cách chế biến, mức cay0–3, nguyên liệu tham khảo/nhãn mỗi dòng một mục, source_id tùy chọn. Validation theo schema backend; PUT gửi đủ bảy trường, nguồn trống gửi null. Không sửa cờ mô phỏng. Nguyên liệu tham khảo không thay nguyên liệu thực tế của quán.

Xóa có xác nhận, 409 giữ món còn được tham chiếu; sau DELETE đọc lại danh sách. Lỗi giữ form, POST mất phản hồi/5xx khóa gửi và cho đối chiếu danh sách trước khi chủ động tạo tiếp. Chưa có lưu nháp qua reload. 375 kiểm thử frontend và một Playwright adminDishes đạt; TypeScript/lint/build đạt. Kiểm tra không tràn ngang 360/1280px; API được kiểm soát trong Playwright, chưa kiểm chứng backend/PostgreSQL thật. Chạy `npx playwright test e2e/adminDishes.spec.ts` với dev server và biến E2E như các mốc trước.

## Khôi phục sau lỗi render — F.12.17

`common/ErrorBoundary` hiển thị thông báo tiếng Việt, mở lại nội dung hoặc về trang chủ khi component lỗi render/lifecycle. `RouteErrorBoundary` bao quanh Outlet bên trong AppShell, reset theo điều hướng và giữ provider/giỏ ở bên ngoài khi chỉ trang lỗi. Boundary ngoài App trong main.tsx bảo vệ lỗi auth/provider/layout; trường hợp này trạng thái bộ nhớ trong cây bị tháo có thể mất. Không gửi exception ra UI hay tự retry mutation; lỗi API/async/event handler vẫn được xử lý tại từng luồng. Có nhắc kiểm tra kết quả giao dịch trước khi gửi lại.

Xem bảng đối chiếu tại [tiến độ F.12.17](../../docs/TIEN_DO_TRIEN_KHAI.md#rà-soát-giao-diện-và-xử-lý-lỗi-render-f1217). Giao diện chưa hoàn tất toàn bộ: còn CartDrawer/bản đồ, dashboard/thống kê, quản lý user/chất lượng dữ liệu và gợi ý/đánh giá ở các bước sau.

## Giỏ hàng nhanh — F.12.18

Nút **Xem giỏ nhanh** trong Navbar mở CartDrawer cho khách/customer. Dialog dùng cùng CartContext, cho đổi số lượng/xóa, xem tạm tính và sang /cart để đặt hàng; không tạo giỏ hay storage riêng. Có giỏ trống, nhắc giá cần kiểm tra lại và giỏ chỉ giữ trong lần mở trang. Escape/đóng trả focus, khóa cuộn nền khi mở; đổi route/tài khoản đóng drawer. Link Giỏ hàng hiện có vẫn hoạt động. CartDrawer đã hoàn thành, thay thế ghi chú chưa có ở các mốc cũ; CartItem chưa tách riêng.

378 unit/UI hồi quy và ba Playwright cart đạt (một ca drawer mới), TypeScript/lint/build đạt. API kiểm soát trong Playwright; kiểm tra không tràn ngang 360/390/768/1280px và đã xem ảnh mobile. Chưa kiểm chứng backend thật trong lượt này.

## Dòng giỏ hàng dùng chung — F.12.19

CartPage và CartDrawer cùng dùng `components/cart/CartItem.tsx` để hiển thị tên/giá/số lượng/tổng dòng, chuyển chi tiết và xóa. Component nhận callback từ nơi dùng, không tạo state giỏ riêng. Compact dùng heading h3 trong drawer và đóng drawer khi mở chi tiết; trang giỏ dùng h2. CartItem đã được tách, thay thế ghi chú chưa tách ở các mốc cũ. Ba Playwright cart, typecheck/lint/build đạt; kiểm thử trình duyệt dùng API kiểm soát.

## Tổng quan vận hành chủ quán — F.12.20

`/vendor/dashboard` mở từ tài khoản vendor, có RoleGuard/returnTo login, dùng GET hồ sơ quán để hiển thị trạng thái duyệt/nhận đơn, giờ và phạm vi giao. Chỉ NOT_FOUND nghiệp vụ hướng dẫn tạo hồ sơ; lỗi khác cho làm mới. Liên kết hồ sơ/thực đơn/đơn hàng giữ khả năng xử lý đơn cũ khi quán tạm ngừng. Không tự bật nhận đơn, không tạo số liệu thống kê từ một trang danh sách. /vendor vẫn là tài khoản; StatsPage/doanh thu/KPI chưa có vì cần API thống kê.

378 unit/UI hồi quy và hai Playwright vendorDashboard đạt với API kiểm soát; không tràn ngang 360/390/768/1280px, TypeScript/lint/build đạt. Chưa kiểm chứng backend/PostgreSQL thật.

## Tổng quan quản trị — F.12.21

`/admin/dashboard` mở từ tài khoản admin, có RoleGuard/returnTo. Bốn ô đọc total của danh sách quán (tất cả/pending), món chuẩn và nguyên liệu với limit1. Tải/lỗi/retry độc lập, số liệu không hợp lệ báo lỗi; không dùng số mục của trang làm tổng hoặc coi lỗi là 0. Các số được đọc riêng, có thể khác thời điểm và bao gồm dữ liệu mô phỏng. Link quản lý luôn hoạt động; link xét duyệt hướng dẫn chọn bộ lọc trong danh sách quán. Không có thống kê doanh thu/người dùng/chất lượng dữ liệu.

378 kiểm thử hồi quy và hai Playwright adminDashboard đạt với API kiểm soát; không tràn ngang 360/390/768/1280px, TypeScript/lint/build đạt. Chưa kiểm chứng backend/PostgreSQL thật.

## Hoàn thiện component chung — F.12.22

OrderCard dùng chung cho hai danh sách đơn, nhận đường chi tiết theo vai trò và dùng snapshot/giá máy chủ. NotFoundPage là trang 404 riêng. AddressFallback giữ form tên địa điểm/tọa độ, validation/focus; LocationPicker vẫn điều phối định vị và xóa vị trí, reset form dự phòng khi xóa. Chưa có geocoding hoặc MapView. Đây là ba việc gom chung một đợt commit.

Tám Playwright search/orders/vendorOrders/commonNavigation đạt với API kiểm soát; TypeScript/lint/build đạt. Unit test lượt này bị chặn khởi động: Windows Application Control không cho nạp native binding Rolldown. Mốc 378 unit/UI thuộc lượt trước; cần chạy lại Vitest trong môi trường cho phép trước khi xác nhận toàn bộ kiểm thử. Không đổi dependencies để vượt chính sách hệ thống.

## Bản đồ quán và chỉ đường — F.12.23

RestaurantInfo ở trang quán/món tích hợp MapView: bấm **Xem bản đồ quán** mới tải iframe OpenStreetMap; có ẩn, địa chỉ/tọa độ và liên kết mở bản đồ ngoài khi không tải. Chỉ đường mở Google Maps với tọa độ đích quán, không gửi origin/vị trí khách hoặc token. Không cần API key/dependency. Đối chiếu [OSM HTML export](https://wiki.openstreetmap.org/wiki/Export) và [Google Maps URLs](https://developers.google.com/maps/documentation/urls/get-started). Nội dung iframe do nhà cung cấp quản lý, fallback luôn có vì không thể kiểm tra tile xuyên origin.

Phần này thay ghi chú chưa có MapView ở mốc cũ nhưng chưa bao gồm geocoding, chọn điểm hoặc bản đồ nhiều kết quả tìm kiếm. Ba Playwright maps/catalog đạt với request API/OSM kiểm soát, typecheck/lint/build đạt; chưa kiểm chứng bản đồ nhà cung cấp trực tiếp/backend thật. Unit URL đã viết nhưng chưa chạy được vì native binding Rolldown bị Windows Application Control chặn như F.12.22.

## Auth đã triển khai

| Route | Nội dung hiện có |
| :--- | :--- |
| `/` | Trang giới thiệu, liên kết đăng ký/đăng nhập hoặc tài khoản |
| `/register` | Đăng ký customer/vendor, xác nhận mật khẩu, chuyển về đăng nhập khi thành công |
| `/login` | Đăng nhập bằng email/mật khẩu, hiển thị lỗi và chuyển đến trang theo vai trò |
| `/account` | Thông tin tài khoản đã đăng nhập |
| `/onboarding/taste` | Customer đọc/lưu năm câu khẩu vị, đồng ý lưu hoặc bỏ qua về tài khoản |
| `/search` | Công khai: chọn vị trí, tìm món/quán theo từ khóa và khoảng cách, phân trang |
| `/restaurants/:id` | Công khai: hồ sơ quán, giờ phục vụ, thực đơn phân trang và liên kết chi tiết món |
| `/menu-items/:id` | Công khai: giá/đặc trưng món, nguyên liệu thực tế/tham khảo và thông tin quán |
| `/cart` | Giỏ hàng một quán: đổi số lượng, xóa món, tạm tính và chuyển checkout |
| `/checkout` | Customer: địa chỉ/tọa độ, gửi đơn COD, retry chống trùng và ghi nhận kết quả máy chủ |
| `/orders`, `/orders/:id` | Customer: danh sách phân trang, snapshot, tiến trình cập nhật và hủy pending có xác nhận |
| `/vendor`, `/admin` | Thông tin tài khoản có guard vai trò tương ứng; chưa có dashboard nghiệp vụ |
| `/vendor/profile` | Vendor: tạo/xem/sửa hồ sơ, trạng thái duyệt, giờ/phạm vi giao và bật/tắt nhận đơn |
| `/vendor/menu` | Vendor: thực đơn phân trang, gồm món ngừng bán, xác nhận ngừng bán và liên kết sửa |
| `/vendor/menu/new`, `/vendor/menu/:id/edit` | Vendor: tạo/sửa món, chọn món chuẩn và nguyên liệu thực tế, trạng thái bán/xác nhận |
| `/forbidden`, route không tồn tại | Thông báo không đủ quyền/trang 404 |

API theo [contract auth](../../docs/API_CONTRACT.md). Mật khẩu giữ nguyên khi gửi, không lưu vào storage; role đăng ký chỉ có customer/vendor. Form có nhãn, autocomplete, validation, trạng thái chờ và khóa gửi lặp. Không thêm đăng nhập xã hội hoặc khôi phục mật khẩu khi backend chưa hỗ trợ.

Token access/refresh được lưu dưới khóa `viviet.auth.v1`: bật “Ghi nhớ đăng nhập” dùng localStorage, tắt dùng sessionStorage của tab hiện tại. Refresh giữ nguyên lựa chọn này; logout xóa cả hai nơi. Không lưu User/role để cấp quyền; khi mở lại trang phải gọi `/auth/me` trước khi hiển thị trang riêng. 401 của API được thử refresh một lần, các request đồng thời dùng chung một refresh; 401/422 từ refresh hoặc 401 sau thử lại xóa phiên. Lỗi mạng/5xx giữ token và cho thử lại; 403 không tự đăng xuất. Logout và đổi phiên vô hiệu hóa phản hồi cũ; sự kiện storage đồng bộ phiên lưu lâu dài giữa các tab. Nếu storage bị chặn, phiên còn trong bộ nhớ và giao diện thông báo có thể cần đăng nhập lại khi tải lại.

### Giao diện Material Design 3

Hai trang auth có khung riêng: desktop hai phần thương hiệu/biểu mẫu, mobile rút gọn thương hiệu để ưu tiên thao tác. Card bo 28px, nút pill, nền ngà và xanh lá trầm; không dùng thư viện UI mới. Be Vietnam Pro và subset Material Symbols Rounded được phục vụ cùng ứng dụng, có giấy phép tại [public/fonts](public/fonts/README.md).

Các vai trò màu `primary`, `on-primary`, `primary-container`, `surface`, `on-surface`, `outline`, `error` và trạng thái bổ sung nằm tập trung trong [auth.css](src/auth.css). Đổi các biến `--md-sys-color-*` để thay theme. Component dùng chung ở `components/auth/`: `AuthField`, `AuthButton`, `MaterialIcon`, `AuthDialog`; `AuthLayout` và `AuthSessionState` quản lý khung/trạng thái phục hồi phiên. CSS auth cũ đã được gỡ khỏi stylesheet chung.

Form validation ở `utils/authValidation.ts` và `useAuthErrors`: lỗi tiếng Việt dưới từng trường, focus trường lỗi đầu tiên, không xóa dữ liệu khi gửi thất bại. Có hiện/ẩn mật khẩu, xác nhận mật khẩu, đồng ý điều khoản, autofill, gửi bằng Enter, khóa gửi lặp, vòng focus/khôi phục focus khi đóng dialog, chuyển động 180ms và giảm chuyển động theo hệ điều hành. Vùng tương tác chính tối thiểu 48px; đã kiểm tra 360px, 390px, 768px và 1280px.

“Quên mật khẩu?” mở hướng dẫn hỗ trợ, không gọi hoặc giả lập API reset chưa có. Điều khoản/chính sách mở nội dung cho bản thử nghiệm, có thể đóng bằng nút hoặc Escape. Checkbox đồng ý được kiểm tra ở frontend, chưa lưu thời điểm/phiên bản chấp thuận trong DB; không gửi trường `consent` vào API đăng ký hiện có. Không hiển thị đăng nhập Google vì backend chưa hỗ trợ.

Logout chỉ xóa phiên trình duyệt, chưa thu hồi token ở máy chủ. localStorage có thể được JavaScript cùng origin đọc; không coi đây là cookie HttpOnly. Backend vẫn kiểm tra quyền mỗi API, RoleGuard không thay thế kiểm tra membership của quán. Sau đăng nhập chỉ nhận đích quay lại thuộc `/account`, `/vendor`, `/admin`, không nhận URL ngoài hoặc đường dẫn có dấu gạch chéo ngược.

## 1. Các màn hình dự kiến

| Vai trò | Nhóm màn hình |
| :--- | :--- |
| Khách hàng | Đăng ký/đăng nhập, khai báo khẩu vị, chọn vị trí, tìm món/quán, danh sách Top 5 gợi ý có lý do, thực đơn quán, giỏ hàng, tạo và theo dõi đơn, phản hồi |
| Chủ quán | Hồ sơ quán, giờ mở/phạm vi phục vụ, thực đơn/nguyên liệu/bật tắt món, danh sách đơn, cập nhật trạng thái và thống kê quán mình |
| Quản trị viên | Duyệt quán, danh mục món chuẩn và nhãn, kiểm tra nội dung, tài khoản, tình trạng xử lý dữ liệu và dashboard |

### Bản đồ route (đề xuất)

| Route | Vai trò | Nội dung |
| :--- | :--- | :--- |
| `/login`, `/register` | Tất cả | Xác thực; điều hướng theo vai trò sau đăng nhập |
| `/onboarding/taste` | Khách | 5 câu khẩu vị: vùng miền, mức cay, nguyên liệu thích, nguyên liệu cần tránh, mức sẵn sàng thử món mới; có nút bỏ qua |
| `/location` | Khách | Cấp quyền vị trí hoặc nhập địa chỉ/chọn điểm thủ công |
| `/` (trang chủ) | Khách | Top 5 gợi ý kèm lý do, ô tìm kiếm, bộ lọc |
| `/search` | Khách | Kết quả tìm món/quán, bản đồ quán |
| `/restaurants/:id` | Khách | Thông tin quán, giờ mở, thực đơn, trạng thái món |
| `/cart`, `/checkout` | Khách | Giỏ hàng một quán, xác nhận địa chỉ giao, thanh toán khi nhận |
| `/orders`, `/orders/:id` | Khách | Lịch sử và tiến trình đơn, hủy đơn, đánh giá sau hoàn tất |
| `/vendor/*` | Chủ quán | Hồ sơ quán, thực đơn, nguyên liệu, đơn hàng, thống kê |
| `/admin/*` | Quản trị viên | Duyệt quán, món chuẩn và nhãn, tài khoản, chất lượng dữ liệu |

Chặn route theo vai trò chỉ để cải thiện trải nghiệm; quyền thật do backend kiểm tra ở mọi API.

## 2. Luồng nghiệp vụ chính

### 2.1. Khách mới và gợi ý

1. Đăng nhập lần đầu → màn hình 5 câu khẩu vị (bỏ qua được).
2. Chọn vị trí hoặc nhập địa chỉ. Bán kính mặc định 5 km.
3. Trang chủ hiển thị tối đa 5 món, mỗi món có tên, quán, giá, khoảng cách và **lý do gợi ý do API trả về** (ví dụ: hợp mức cay, có nguyên liệu yêu thích, gần bạn). Frontend không tự sinh lý do.
4. Nếu khách bỏ qua khai báo: hiển thị danh sách khám phá kèm thông báo "Chưa cá nhân hóa — hãy khai báo khẩu vị để nhận gợi ý phù hợp hơn".
5. Nếu ít hơn 5 ứng viên: hiển thị danh sách ngắn và nguyên nhân từ API (ví dụ: ít quán đang mở trong phạm vi); không tự nới bộ lọc.
6. Mỗi món có nút phản hồi **Phù hợp / Không phù hợp**.

### 2.2. Đặt món và trạng thái đơn

Giỏ hàng chỉ chứa món của một quán; khi thêm món quán khác, hỏi khách có muốn làm trống giỏ hiện tại không.

| Trạng thái | Nhãn hiển thị | Thao tác của khách | Thao tác của chủ quán |
| :--- | :--- | :--- | :--- |
| `PENDING` | Chờ quán xác nhận | Hủy đơn | Xác nhận / Từ chối (kèm lý do) |
| `CONFIRMED` | Quán đã nhận đơn | — | Bắt đầu chuẩn bị |
| `PREPARING` | Đang chuẩn bị | — | Chuyển sang đang giao |
| `DELIVERING` | Đang giao | — | Hoàn tất |
| `COMPLETED` | Hoàn tất | Đánh giá món | — |
| `REJECTED` | Quán từ chối | Xem lý do | — |
| `CANCELLED` | Đã hủy | — | — |

Mã trạng thái cần thống nhất với backend. Giao diện chỉ hiện nút cho chuyển trạng thái hợp lệ; backend vẫn từ chối chuyển sai. Tiến trình đơn hiển thị người thao tác và thời điểm từ lịch sử trạng thái.

## 3. Các tình huống phải thể hiện

- Người dùng có thể nhập địa chỉ khi không cấp quyền vị trí; lỗi tải bản đồ không chặn luồng tìm và đặt món.
- Quán xuất hiện trên bản đồ nhưng chưa tham gia hệ thống không có thao tác đặt món qua Vị Việt.
- Hiển thị lý do gợi ý, danh sách ngắn khi ít ứng viên và thông báo chưa cá nhân hóa khi khách bỏ qua khai báo.
- Thông báo khi món hết bán, quán đóng cửa, ngoài phạm vi phục vụ, đơn bị từ chối hoặc trạng thái thay đổi.
- Khi đặt đơn, nếu backend báo giá/tùy chọn/trạng thái món đã đổi: hiển thị khác biệt và yêu cầu khách xác nhận lại, không tự đặt.
- Không hiển thị thông tin nguyên liệu như cam kết an toàn dị ứng; ghi chú rằng khách nên hỏi quán khi có dị ứng nghiêm trọng.
- Chỉ mở đánh giá món khi đơn ở trạng thái hoàn tất.
- Khóa thao tác gửi lặp trên giao diện kết hợp kiểm soát ở backend; không dựa riêng vào việc ẩn nút để phân quyền.
- Trạng thái rỗng, đang tải và lỗi mạng cho mọi danh sách.

## 4. Ghi sự kiện phục vụ gợi ý và BI

Dữ liệu cho `Fact_RecImpression` và `Fact_Session` ([database](../database/README.md)) phát sinh từ frontend, vì vậy cần ghi đúng ngay từ đầu.

| Sự kiện | Khi nào ghi | Trường tối thiểu |
| :--- | :--- | :--- |
| `impression` | Mục gợi ý thực sự hiển thị trên màn hình | `event_id`, `session_id`, `request_id`, `menu_item_id`, thời điểm |
| `click` | Khách mở chi tiết món từ danh sách gợi ý | `event_id`, `session_id`, `request_id`, `menu_item_id` |
| `add_to_cart` | Thêm món vào giỏ | `event_id`, `session_id`, `menu_item_id`, `request_id` nếu đến từ gợi ý |
| `feedback` | Bấm phù hợp/không phù hợp | `event_id`, `session_id`, `request_id`, `menu_item_id`, giá trị 0/1 |
| `session_start` / `session_end` | Mở phiên / hết phiên | `event_id`, `session_id`, thời điểm |

Quy tắc:

- `event_id` sinh ở client (UUID v4) và giữ nguyên khi gửi lại để backend loại trùng. `occurred_at` là thời điểm phát sinh kèm múi giờ; `received_at` do máy chủ cấp. Service sẽ kiểm tra sai lệch đồng hồ và cửa sổ tiếp nhận khi được triển khai.
- Mã sự kiện thống nhất với model tracking là `impression`, `click`, `add_to_cart`, `feedback`, `session_start`, `session_end`. Thứ hạng lấy từ RecommendationImpression đã lưu tại backend, không cần client gửi lại.
- `request_id` và phiên bản thuật toán do API gợi ý trả về; frontend chỉ chuyển tiếp, không gắn nhãn thuật toán trên giao diện.
- Khi tạo đơn, gửi kèm `session_id` để backend quy thuộc theo quy tắc 30 phút.
- Gom và gửi theo lô, thử lại khi lỗi mạng; không để việc ghi sự kiện làm chậm thao tác người dùng.
- Không gửi tọa độ chi tiết hoặc địa chỉ giao hàng trong sự kiện hành vi.

### Màn hình thử nghiệm đánh giá (tuần 7)

Phục vụ 150 trường hợp so sánh danh sách phổ biến với mô hình cá nhân hóa: hiển thị hợp hai danh sách Top 5 đã lọc trùng, xáo trộn thứ tự, **ẩn tên thuật toán**, người dùng chấm phù hợp/không phù hợp từng món. Dùng mã người tham gia, tách khỏi dữ liệu giao dịch thật.

## 5. Quyền riêng tư và bảo mật

- Xin đồng thuận trước khi lưu hồ sơ khẩu vị và vị trí; giải thích dữ liệu dùng để gợi ý.
- Không lưu tọa độ chính xác lâu dài trong `localStorage`; ưu tiên giữ trong phiên.
- Không đưa khóa bí mật vào mã nguồn trình duyệt. Khóa Google Maps phía trình duyệt luôn bị lộ, nên phải giới hạn theo HTTP referrer và chỉ bật API cần dùng.
- Auth F.8 nhận/trả JWT trong JSON và header Bearer, frontend persist token trong localStorage theo thiết kế; không ghi token ra log. Cookie `HttpOnly` là hướng có thể bổ sung sau khi thống nhất luồng cookie/CSRF với backend.

## 6. Công nghệ, lệnh chạy và cấu trúc

### Bộ khung hiện có

Node.js 20.19+, 22.12+ hoặc 24+ theo `engines` của package; React 18, Vite 5, TypeScript 5.6 và React Router. Đã có `package.json`, `package-lock.json`, cấu hình môi trường mẫu và Dockerfile. Vitest dùng Vite riêng trong dependencies để chạy bộ kiểm thử.

Từ thư mục `src/frontend/`:

```powershell
npm ci
npm run dev
```

Frontend chạy tại `http://localhost:5173`. `npm run build` kiểm tra TypeScript của nguồn, tests/config và tạo bản production; `npm run lint`, `npm run format:check` kiểm tra mã/định dạng. `npm test` chạy 54 ca API client và React UI với Vitest/Testing Library, không cần backend. `npm run test:e2e` chạy bốn kịch bản trình duyệt với backend thật; cần khởi động riêng backend/DB tạm và frontend theo [hướng dẫn](../../docs/HUONG_DAN_CAI_DAT.md#kiểm-thử-auth-trên-trình-duyệt).

`VITE_API_BASE_URL` trong cấu hình mẫu là `/api/v1`. Vite chuyển `/api` và `/health` tới backend local ở `http://127.0.0.1:8000`; Docker đặt `API_PROXY_TARGET=http://backend:8000`.

Xem [hướng dẫn cài đặt](../../docs/HUONG_DAN_CAI_DAT.md) và [tiến độ từng phần](../../docs/TIEN_DO_TRIEN_KHAI.md).

### Cấu trúc auth hiện có

Đường dẫn theo F.8 và bước 11–12 của [thiết kế cấu trúc chung](../../docs/THIET_KE_CAU_TRUC.md). Đã có khẩu vị, tìm kiếm, trang quán/món, giỏ hàng và checkout COD; cache truy vấn, bản đồ và dashboard chưa triển khai.

```text
src/frontend/
├── package.json
├── .env.example          # chỉ chứa tên biến và giá trị mẫu
├── src/
│   ├── api/client.ts, auth.ts
│   ├── types/auth.ts
│   ├── contexts/AuthContext.tsx, authState.ts
│   ├── hooks/useAuth.ts
│   ├── components/layout/  # AppShell, Navbar, Footer, RoleGuard
│   ├── pages/auth/         # AuthLayout, LoginPage, RegisterPage
│   ├── pages/HomePage.tsx, AccountPage.tsx
│   ├── utils/auth.ts       # nhãn vai trò, đích điều hướng nội bộ
│   ├── router.tsx
│   └── styles.css
├── tests/                 # client/session và React UI
├── e2e/auth.spec.ts        # backend thật và bố cục desktop/mobile
├── vitest.config.ts
└── playwright.config.ts
```

### Biến môi trường (đề xuất)

| Biến | Ý nghĩa | Ví dụ |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Địa chỉ API backend trong cấu hình mẫu | `/api/v1` |
| `API_PROXY_TARGET` | Đích proxy của Vite dev server | Local: `http://127.0.0.1:8000`; Docker: `http://backend:8000` |
| `VITE_GOOGLE_MAPS_API_KEY` | Khóa Maps phía trình duyệt, đã giới hạn referrer | *(không commit)* |
| `VITE_DEFAULT_CENTER_LAT`, `VITE_DEFAULT_CENTER_LNG` | Tâm khu vực thử nghiệm, chốt tuần 1 | — |
| `VITE_DEFAULT_RADIUS_KM` | Bán kính tìm kiếm mặc định | `5` |

Mọi biến `VITE_*` đều lộ ra trình duyệt, vì vậy không đặt bí mật vào đây.

## 7. Tích hợp API

Danh sách endpoint, định dạng lỗi và mã trạng thái cần thống nhất với [backend](../backend/README.md) và ghi lại khi triển khai. Yêu cầu tối thiểu từ phía frontend:

- API gợi ý trả về `request_id`, danh sách món theo thứ hạng, lý do cho từng món, cờ chưa cá nhân hóa và nguyên nhân khi thiếu ứng viên.
- API tạo đơn sẽ nhận `idempotency_key` trong body theo thiết kế E.4 và trả lỗi riêng cho các trường hợp món hết bán, giá thay đổi, ngoài phạm vi, quán đóng cửa.
- Định dạng lỗi thống nhất có mã lỗi máy đọc được để hiển thị thông báo tiếng Việt phù hợp.
- Có cơ chế cập nhật trạng thái đơn (polling định kỳ là đủ cho bản mẫu).

## 8. Kiểm thử và tiêu chí nghiệm thu liên quan

| Tiêu chí (đề cương mục 7) | Phần việc của frontend |
| :--- | :--- |
| Chức năng giao dịch: 30 ca tạo, hủy, từ chối, gửi lặp, đổi trạng thái sai | Kịch bản thao tác trên giao diện cho cả khách và chủ quán; bấm đặt nhiều lần không tạo đơn trùng |
| Tuân thủ điều kiện | Không hiển thị nút đặt cho món hết bán, quán đóng cửa hoặc ngoài phạm vi |
| Trải nghiệm: ≥ 90% hoàn thành nhiệm vụ, điểm hài lòng ≥ 4/5 | Kịch bản nhiệm vụ cố định, giao diện dùng tốt trên điện thoại |
| Độ tin cậy BI: khớp 100% sau ETL | Sự kiện hiển thị/nhấp ghi đủ, không trùng `event_id` |

Kiểm tra thêm: giao diện co giãn trên điện thoại, điều hướng bằng bàn phím, nhãn cho trường nhập liệu và độ tương phản chữ đủ đọc.

## 9. Mốc thực hiện liên quan

| Tuần | Đầu ra frontend |
| :-: | :--- |
| 2 | Wireframe các màn hình chính, luồng đơn và route |
| 3 | Khởi tạo dự án, đăng nhập, chặn route theo vai trò |
| 4 | Thực đơn, giỏ hàng, đặt món, theo dõi trạng thái, chọn vị trí |
| 5 | Khai báo khẩu vị, hiển thị Top 5 và lý do, phản hồi |
| 6 | Ghi sự kiện, màn hình chủ quán/quản trị hoàn chỉnh |
| 7 | Màn hình thử nghiệm đánh giá mù; kiểm thử giao dịch và trải nghiệm |
| 8 | Sửa lỗi, hướng dẫn cài đặt, kịch bản demo |

## 10. Đầu ra cần bổ sung khi lập trình

- Đã có `package.json`, lockfile, `.env.example` và lệnh cài phụ thuộc/chạy/biên dịch; cập nhật khi thêm module hoặc thay đổi môi trường.
- Tài liệu tích hợp API và danh sách sự kiện đã chốt.
- Ảnh chụp hoặc wireframe các màn hình chính.
- Cập nhật mục khởi chạy trong [README nhóm](../../README.md) và [danhsachnhom.md](../../danhsachnhom.md).

Xem thêm [README nhóm](../../README.md), [backend](../backend/README.md), [cơ sở dữ liệu](../database/README.md) và [đề cương](../../docs/De_cuong_Vi_Viet.docx).

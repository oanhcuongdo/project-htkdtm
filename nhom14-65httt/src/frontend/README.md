# Frontend Vị Việt

Đã có frontend auth F.8 theo thiết kế cấu trúc: đăng ký/đăng nhập, AuthContext/useAuth, API client, AppShell/Navbar/Footer và RoleGuard. Giao diện gọi API backend thật; chưa có chức năng tìm món, đặt hàng hoặc dashboard quán/admin.

## API công khai đã chuẩn bị — F.11.1

Các module `src/api/restaurants.ts`, `menu.ts`, `search.ts` dùng chung `ApiClient` hiện có. Kiểu response ở `src/types/restaurant.ts`, `menu.ts`, `search.ts`, phân trang dùng `Page<T>` và `PaginationQuery` ở `common.ts`; đã đối chiếu schema backend F.10.1–F.10.3. Đây là lớp gọi API để màn hình ở F.12 sử dụng; chưa có SearchPage hoặc trang thực đơn.

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

## Auth đã triển khai

| Route | Nội dung hiện có |
| :--- | :--- |
| `/` | Trang giới thiệu, liên kết đăng ký/đăng nhập hoặc tài khoản |
| `/register` | Đăng ký customer/vendor, xác nhận mật khẩu, chuyển về đăng nhập khi thành công |
| `/login` | Đăng nhập bằng email/mật khẩu, hiển thị lỗi và chuyển đến trang theo vai trò |
| `/account` | Thông tin tài khoản đã đăng nhập |
| `/vendor`, `/admin` | Thông tin tài khoản có guard vai trò tương ứng; chưa có dashboard nghiệp vụ |
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

Đường dẫn theo F.8 của [thiết kế cấu trúc chung](../../docs/THIET_KE_CAU_TRUC.md). Chưa có cache truy vấn, bản đồ, giỏ hàng hoặc các trang nghiệp vụ.

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

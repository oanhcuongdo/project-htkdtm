# Cài đặt và tạo cơ sở dữ liệu Vị Việt

Hướng dẫn khởi chạy backend có `/health`, OpenAPI, API auth/quán/thực đơn/danh mục/tìm kiếm/đơn COD/đánh giá/khẩu vị/tracking và frontend đăng ký/đăng nhập. Đã có migration `001` tạo 15 bảng OLTP; chưa có seed, dashboard hoặc frontend nghiệp vụ.

## Cấu hình khóa JWT

Sau khi tạo `.env` từ `.env.example`, thay `SECRET_KEY` mẫu bằng khóa ngẫu nhiên riêng. Có thể chạy lệnh sau với Python đã cài và lưu kết quả vào `SECRET_KEY` trong `.env` một lần:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Giữ nguyên khóa giữa các lần khởi động nếu muốn token tiếp tục hợp lệ; không commit `.env` hoặc đưa khóa vào frontend. Các thao tác cần JWT trả 503 `AUTH_NOT_CONFIGURED` nếu khóa dưới 32 byte hoặc còn bắt đầu bằng `changeme`; health/docs vẫn chạy. `ALGORITHM` chỉ nhận HS256, access mặc định 60 phút và refresh 7 ngày; cấu hình ở `.env.example`. Khi chạy lại phần local bên dưới, không ghi đè `.env` đã chỉnh bằng file mẫu.

## Chạy local trên Windows

Cần Python 3.11 trở lên; Node.js 20.19+, 22.12+ hoặc 24+ theo `engines` frontend. Với PostgreSQL, DB/tài khoản trong `.env` cần tồn tại và máy chủ DB đang chạy; có thể chạy riêng DB bằng `docker compose up db -d` từ thư mục nhóm nếu có Docker. Để thử local chưa có PostgreSQL, dùng lựa chọn SQLite được chú thích trong đoạn lệnh dưới. Từ thư mục `nhom14-65httt/`:

```powershell
# Chỉ copy ở lần đầu; sau đó cấu hình SECRET_KEY như hướng dẫn phía trên:
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -m venv src/backend/.venv
src/backend/.venv/Scripts/python.exe -m pip install -r src/backend/requirements.txt -r src/backend/requirements-dev.txt
Set-Location src/backend
# Chỉ bỏ chú thích dòng này nếu muốn dùng SQLite local thay PostgreSQL:
# $env:DATABASE_URL = 'sqlite:///./viviet.db'
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m alembic current
.venv/Scripts/python.exe -m alembic check
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend: `http://localhost:8000/health`; tài liệu API: `http://localhost:8000/docs`.

Trong `/docs`, thử lần lượt `POST /api/v1/auth/register`, `/login`, nhập access token vào nút Authorize rồi gọi `GET /api/v1/auth/me`. `/refresh` nhận refresh token trong JSON. Mật khẩu/role và mã lỗi xem [API contract](API_CONTRACT.md). Refresh chưa thu hồi token cũ; chưa có logout phía máy chủ. Chưa có tài khoản admin mẫu hoặc seed quán.

Sau khi đăng nhập bằng vendor, có thể tạo quán qua POST `/api/v1/vendor/restaurant`, xem/sửa hồ sơ bằng GET/PUT cùng đường dẫn. Quán mới chờ duyệt và chưa nhận đơn. Admin được cấp hợp lệ dùng GET `/api/v1/admin/restaurants`, PATCH `/{restaurant_id}/approve` hoặc `/suspend` dưới prefix đó; duyệt xong vendor mới bật `accepting_orders=true` qua PUT được. Xem payload đầy đủ và các giới hạn ở API contract. API công khai `/api/v1/restaurants/` và `/{restaurant_id}` chỉ trả quán approved; frontend quản lý quán chưa được tích hợp ở lượt này.

Để thử thực đơn trong `/docs`, dùng admin đã được cấp hợp lệ tạo nguyên liệu qua POST `/api/v1/admin/ingredients`, tạo món chuẩn qua POST `/api/v1/admin/canonical-dishes`, ghi lại ID trả về. Đổi sang access token vendor có quán, POST `/api/v1/vendor/menu-items` với canonical_dish_id/name/price; món mặc định chưa bán/chưa xác nhận nguyên liệu. PUT `/{item_id}` với đủ sáu trường theo [API contract F.10.2](API_CONTRACT.md#thực-đơn-món-chuẩn-và-nguyên-liệu--f102), đặt is_available=true và ingredient_ids thực tế. Với quán approved, GET công khai `/api/v1/restaurants/{restaurant_id}/menu` và `/api/v1/menu-items/{item_id}` sẽ trả món đó. DELETE vendor ngừng bán, món vẫn còn trong GET vendor; xóa catalog đang dùng trả 409. Chưa có seed hoặc giao diện quản lý thực đơn; không đăng ký công khai được tài khoản admin.

Thử tìm kiếm công khai qua `/api/v1/search/dishes?q=pho&lat=21.0285&lng=105.8542&radius=5` và `/api/v1/search/restaurants?q=&lat=21.0285&lng=105.8542`. Thay tọa độ bằng điểm trong phạm vi giao của quán đã tạo. Chỉ quán approved/món đang bán trong phạm vi mới xuất hiện; quán đóng cửa vẫn hiện trạng thái để khách cân nhắc. Kiểm tra thêm q tiếng Việt không dấu, radius nhỏ và offset vượt tổng để thấy kết quả lọc/phân trang. Không có dữ liệu phù hợp trả page rỗng; thiếu vị trí trả 422. [API contract F.10.3](API_CONTRACT.md#tìm-kiếm-món-và-quán--f103) mô tả đầy đủ response và giới hạn; chưa có SearchPage hoặc bản đồ.

Sau migrate, `current` cần báo `001 (head)`, `check` không báo thay đổi schema mới. File SQLite local là dữ liệu phát sinh và được Git bỏ qua. Nếu dùng biến môi trường DATABASE_URL cho SQLite, cần giữ cùng giá trị khi chạy backend và các lệnh Alembic. Không cần seed ở bước này vì chưa có dữ liệu mẫu.

Mở terminal khác tại thư mục nhóm:

```powershell
Set-Location src/frontend
npm ci
npm run dev
```

Frontend: `http://localhost:5173`. Vite chuyển `/api` và `/health` sang backend local. `.env` backend luôn được đọc từ thư mục nhóm, không phụ thuộc thư mục chạy lệnh. Frontend dùng cấu hình riêng tại `src/frontend/.env.local` nếu cần; xem `.env.example` bên cạnh.

Mở `/register` để tạo customer/vendor, sau đó đăng nhập ở `/login`. Khách đến `/account`, chủ quán đến `/vendor`, admin đã được cấp hợp lệ đến `/admin`; hiện các trang này chỉ hiển thị tài khoản và kiểm tra vai trò, chưa có dashboard. Tải lại trang để kiểm tra phục hồi qua `/me`; logout chỉ xóa phiên trình duyệt. Chưa có tài khoản admin mẫu; đăng ký công khai không nhận admin.

## Chạy bằng Docker

Từ thư mục nhóm, sau khi copy `.env.example` thành `.env`:

```powershell
docker compose up --build
```

Compose chạy PostgreSQL 16, backend ở cổng 8000 và frontend ở cổng 5173. Backend dùng hostname `db`; Vite proxy tới `backend:8000` trong mạng Docker. Mở terminal khác tại thư mục nhóm để tạo/kiểm tra schema:

```powershell
docker compose exec backend python -m alembic upgrade head
docker compose exec backend python -m alembic current
docker compose exec backend python -m alembic check
```

Nếu có Make, các lệnh tương ứng là `make migrate`, `make migrate-status`, `make migrate-check`. Chưa chạy `make seed` hoặc `make etl` vì các module đó chưa được tích hợp. Backend không tự chạy migration lúc khởi động.

Docker chưa được kiểm chứng trong phiên phát triển này vì máy không có Docker CLI trong PATH. Cần thử lại trên máy có Docker Desktop trước khi đánh dấu nghiệm thu.

## Kiểm tra

Mốc F.11.1: **69 kiểm thử frontend đạt**, gồm 15 ca API công khai mới và 54 ca trước. TypeScript, ESLint, Prettier và Vite production build đạt. Các ca mới dùng fetch thay thế để kiểm tra URL/query, token, lỗi và hủy request; chưa có màn hình nghiệp vụ để chạy E2E. Chạy `npm test` và `npm run build` từ `src/frontend/`. Trong phiên này chạy Vitest/Vite trực tiếp bằng Node hiện có vì lệnh npm test gặp lỗi nạp native binding từ môi trường; không đổi dependencies hoặc lockfile.

Mốc F.10.8: **1133 kiểm thử backend đạt**, gồm 31 ca API tracking mới và 1102 ca trước. Ruff/format đạt. Kiểm thử dùng SQLite tạm để kiểm tra quyền, ngữ cảnh sự kiện, idempotency, hiển thị trước tương tác, cửa sổ thời gian và rollback batch. PostgreSQL thực tế chưa kiểm chứng.

POST `/api/v1/tracking/events` nhận batch 1–100 sự kiện từ customer theo [API contract F.10.8](API_CONTRACT.md#ghi-nhận-sự-kiện-tương-tác--f108). Để thử `impression`/`click`/`feedback`, cần có RecommendationRequest và RecommendationImpression đúng tài khoản/phiên/món từ luồng tạo gợi ý; luồng đó chưa có API nên hiện kiểm thử tự tạo dữ liệu trong SQLite tạm. Sự kiện phiên và `add_to_cart` không có request không cần dữ liệu gợi ý. Không dùng UUID request mẫu trong tài liệu như dữ liệu tồn tại sẵn.

Mốc F.10.7: **1102 kiểm thử backend đạt**, gồm 36 ca API khẩu vị mới và 1066 ca trước. Ruff/format đạt. Kiểm thử API dùng SQLite tạm do migration tạo: quyền riêng tư, đủ năm câu, chuẩn hóa, ghi đè, rollback và mô phỏng tranh chấp tạo lần đầu. PostgreSQL thực tế chưa kiểm chứng.

Thử hồ sơ khẩu vị bằng access token customer: GET `/api/v1/preferences/` trước khi khai báo trả 404; PUT cùng đường dẫn với đủ năm câu trong [API contract F.10.7](API_CONTRACT.md#hồ-sơ-khẩu-vị--f107) trả hồ sơ đã chuẩn hóa; GET lại thấy dữ liệu đó. Vendor/admin nhận 403. Bỏ qua onboarding không gọi PUT nên không tạo bản ghi. Chưa có màn hình PreferencePage.

Mốc F.10.6: **1066 kiểm thử backend đạt**, gồm 30 ca đánh giá mới và 1036 ca đã có. Ruff/format đạt. Các ca mới kiểm tra quyền người mua, trạng thái completed, món thực sự có trong đơn, chống trùng, snapshot và rollback trên SQLite tạm. PostgreSQL thực tế/chạy đồng thời chưa kiểm chứng.

Để thử đánh giá, tạo đơn customer và cho vendor đúng quán chuyển đến completed, sau đó dùng access token của customer gọi POST `/api/v1/orders/{order_id}/review` với `{"menu_item_id":1,"rating":5,"comment":"Rất ngon"}`. ID món phải thuộc OrderItem của đơn đó; gửi lại cùng đơn/món trả 409. Response trả tên/giá snapshot của lần mua. Xem [API contract F.10.6](API_CONTRACT.md#đánh-giá-món-đã-mua--f106).

Mốc hiện tại F.10.5: **1036 kiểm thử backend đạt**, gồm 86 ca API đơn COD mới và 950 ca trước; Ruff/format đạt. Kiểm thử API dùng SQLite tạm tạo bằng migration, gồm scope, validation, snapshot, idempotency 24 giờ, mô phỏng tranh chấp UNIQUE và rollback. Chưa kiểm chứng PostgreSQL thực tế. Các đoạn dưới giữ kết quả của mốc trước.

Để thử đơn hàng trong Swagger: tạo quán approved đang mở/bật nhận đơn và món đang bán; đăng nhập customer, gọi POST `/api/v1/orders/` với payload tại [API contract F.10.5](API_CONTRACT.md#đơn-cod-và-chống-gửi-lặp--f105). Dùng UUID v4 mới cho session/key và giá hiện tại cho expected_price. Gửi nguyên payload lần hai nhận 200/cùng ID; sửa quantity với cùng key nhận 409. Đổi sang vendor đúng quán, gọi GET `/api/v1/vendor/orders`, PATCH confirm → preparing → delivering → complete; thử customer hủy một đơn pending khác. Chưa có giao diện checkout hoặc xử lý đơn.

Ở lượt chuyển trạng thái đơn F.10.4, toàn bộ **950 kiểm thử backend đạt**, gồm 167 ca mới và 783 ca trước. Ruff/format đạt. Phần mới là service nội bộ, chưa có endpoint đơn hàng để thử trong Swagger; chạy `python -m pytest tests/test_order_state_machine.py -q` từ backend để kiểm tra riêng. Bộ kiểm thử dùng SQLite tạm, chưa xác nhận khóa hàng/cạnh tranh thực tế trên PostgreSQL. Chi tiết mốc API trước được giữ bên dưới.

```powershell
# Từ src/backend
.venv/Scripts/python.exe -m pytest tests -q

# Từ src/frontend
npm run build
npm run lint
npm run format:check
npm test
```

Toàn bộ 783 kiểm thử backend đạt, gồm 99 ca tìm kiếm, 167 ca thực đơn/catalog, 92 ca quán/phân quyền, 84 ca auth, các model OLTP và 23 ca migration. Kiểm thử dùng production app với DB SQLite tạm do migration tạo: tạo/duyệt/tạm ngừng quán, membership, giờ qua đêm, phân trang, validation, CRUD catalog, cô lập thực đơn, ngừng bán giữ snapshot và rollback món/liên kết nguyên liệu khi lỗi ghi. Tìm kiếm kiểm tra tiếng Việt có/không dấu, literal, Haversine, cả hai bán kính, sát biên, vùng cực/kinh tuyến 180°, total sau lọc, thứ tự ổn định, không ghi DB và tránh truy vấn theo từng món. OpenAPI đã đối chiếu hai endpoint search; Ruff/format đạt trên các file Python thay đổi. Migration kiểm tra nâng/hạ/nâng lại, lệch schema, constraint, đường dẫn, URL và mặc định JSON. PostgreSQL mới kiểm tra SQL offline; chưa xác nhận PostgreSQL/Docker, khóa hàng cạnh tranh thực tế hoặc API giao dịch/tracking.

Frontend có 54 kiểm thử Vitest/React UI và bốn kịch bản Playwright đạt với backend thật trên SQLite tạm; đã kiểm tra ảnh login/register Material Design 3 ở 360/390/768/1280px, bàn phím, hiện/ẩn mật khẩu, dialog và lựa chọn ghi nhớ đăng nhập. Build, TypeScript (gồm tests/config), lint và format check đạt. Kết quả 425 ca backend là mốc của commit backend auth; lượt frontend không đổi mã Python. npm audit còn bốn cảnh báo thuộc Vite 5/React Router 6 đã có; chưa nâng major toolchain trong phần auth này.

## Kiểm thử auth trên trình duyệt

Các kịch bản E2E tạo tài khoản thử qua giao diện, vì vậy chạy backend với DB SQLite riêng. Sau khi đã cài dependencies, mở terminal tại thư mục nhóm:

```powershell
New-Item -ItemType Directory -Force .runtime | Out-Null
$testDatabase = Join-Path (Get-Location).Path '.runtime/auth-e2e.db'
$backendPython = Join-Path (Get-Location).Path 'src/backend/.venv/Scripts/python.exe'
$env:DATABASE_URL = 'sqlite:///' + $testDatabase.Replace('\', '/')
$env:SECRET_KEY = & $backendPython -c "import secrets; print(secrets.token_urlsafe(48))"
Set-Location src/backend
& $backendPython -m alembic upgrade head
& $backendPython -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Terminal thứ hai, từ `src/frontend/`:

```powershell
$env:API_PROXY_TARGET = 'http://127.0.0.1:8001'
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Terminal thứ ba, từ `src/frontend/` trên Windows có Microsoft Edge:

```powershell
$env:E2E_BASE_URL = 'http://127.0.0.1:5174'
$env:E2E_BROWSER_CHANNEL = 'msedge'
npm run test:e2e
```

Nếu chưa có Edge, có thể cài Chromium dành cho Playwright bằng `npx playwright install chromium`, bỏ biến `E2E_BROWSER_CHANNEL` và chạy lại. Bộ test không tự khởi động server hay chọn DB thay bạn. Không trỏ E2E vào DB ứng dụng cần giữ; dùng Ctrl+C để dừng hai server thử sau khi kiểm tra. Ảnh kiểm tra nằm trong `.runtime/playwright-results/`, không đưa vào Git. Trên Windows bị chặn `npm.ps1`, dùng `npm.cmd` thay `npm`.

## Thay đổi schema sau này

Chạy `alembic revision --autogenerate -m "mo ta thay doi"` rồi review thao tác và kiểm thử trước khi áp dụng. Revision `001` là bản khởi tạo cố định; không sửa để thay cho việc tạo revision mới sau khi nó đã được commit/áp dụng. Các bảng BI/đánh giá mù sẽ được bổ sung ở các phần sau bằng migration mới.

Lệnh `alembic downgrade base` xóa 15 bảng và dữ liệu của chúng. Chỉ dùng để kiểm tra trên DB tạm có thể bỏ, không dùng trên DB cần giữ dữ liệu. Bộ test migration đã kiểm tra rollback trong DB tạm; chưa chạy rollback trên DB ứng dụng của bạn.

Các bước chạy và kiểm tra ở trên không cần `.runtime/pending-implementation/`. Khi clone trên máy khác, cài lại môi trường từ requirements và `package-lock.json`; không cần sao chép bản nháp cục bộ.

Không đưa `.env`, `.venv/`, `node_modules/`, `dist/` hay `.runtime/` vào commit.

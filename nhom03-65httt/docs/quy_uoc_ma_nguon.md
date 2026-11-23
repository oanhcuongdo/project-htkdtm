# Quy ước mã nguồn, API, migration và dữ liệu (Nhóm 03)

Bổ sung cho [CONTRIBUTING.md](../CONTRIBUTING.md). Mục tiêu: nhiều người viết song song mà ghép lại không xung đột.

## 1. Nguyên tắc chung

- Ngôn ngữ: mã (tên biến, hàm, tệp) bằng tiếng Anh không dấu; chú thích, tài liệu, thông báo lỗi người dùng bằng tiếng Việt.
- Tên tệp và thư mục: chữ thường, không dấu, không khoảng trắng (`snake_case` cho Python, `kebab-case` cho trang React).
- Mỗi chức năng đi kèm cách kiểm tra: lệnh chạy được và kết quả mong đợi (đưa vào mô tả PR).
- Không để mật khẩu, khóa, đường dẫn máy cá nhân trong mã. Cấu hình lấy từ biến môi trường (`src/backend/app/core/config.py`) hoặc `config/`.
- Không sửa mã của người khác trong PR của mình. Cần sửa thì báo chủ sở hữu hoặc tạo PR riêng.

## 2. Chủ sở hữu từng phần

Mỗi người **tự viết API cho mô hình mình phụ trách**. Thay đổi phần của người khác phải có người đó (hoặc nhóm trưởng) đồng ý.

| Phần | Chủ sở hữu | Tệp router đề xuất (`src/backend/app/api/`) |
|---|---|---|
| Mô hình cảm xúc M1, chatbot, khuyến nghị và cảnh báo tự sinh | Tùng | `sentiment.py`, `chat.py`, `recommendations.py` |
| Mô hình khía cạnh M2 | Thái Anh | `aspects.py` |
| Dự báo M3, phát hiện bất thường | Ngọc Anh | `forecast.py`, `anomaly.py` |
| Xác thực JWT, cập nhật dữ liệu, quản lý nguồn và sự kiện, tìm kiếm đánh giá, guest token Superset | Hoàng Anh | `auth.py`, `refresh.py`, `sources.py`, `reviews.py`, `embed.py` |
| KPI và BHI, xem cảnh báo, đánh dấu đã xử lý | Hưng | `kpi.py`, `alerts.py` |
| Khung backend, Docker, Alembic, cấu hình chung | Tùng | `main.py`, `core/`, `Dockerfile`, `docker-compose.yml` |

## 3. API (FastAPI)

- **Mỗi người một tệp router riêng**, không dồn vào `predict.py`. Hiện `predict.py` chứa các điểm cuối khung trả 501. Khi làm thật, chuyển điểm cuối của mình sang tệp riêng, xóa phần khung tương ứng trong `predict.py` và đăng ký router trong `main.py` (`app.include_router(...)`). Mỗi PR chỉ chạm hai nơi này ở dòng của mình để dễ gộp.
- **Đường dẫn:** tiền tố `/api/v1/`, danh từ số nhiều, chữ thường. Hợp đồng đã chốt (đường dẫn, dữ liệu vào) không đổi nếu chưa báo website và n8n.
- **Dữ liệu vào ra** khai báo bằng Pydantic trong `app/schemas/`; lỗi trả theo `ErrorOut`. Không trả dữ liệu thô khi chưa che thông tin nhạy cảm.
- **Mã trạng thái:** 200 thành công, 422 dữ liệu vào sai, 401 và 403 cho xác thực và phân quyền, 404 không có, 501 chỉ cho phần chưa làm.
- **Kiểm thử:** thêm bài kiểm thử trong `src/backend/tests/` (pytest). PR chỉ được merge khi `pytest` xanh và các điểm cuối cũ không hỏng.
- **Mô hình AI:** nạp trọng số từ thư mục `models/` (ngoài Git, xem `models/README.md`), không bao giờ commit trọng số. Tải mô hình một lần khi khởi động, không tải lại mỗi yêu cầu.
- **Tài liệu API:** tóm tắt (`summary`) tiếng Việt cho từng điểm cuối để trang `/docs` dùng được làm tài liệu.

## 4. Cơ sở dữ liệu và migration (Alembic)

- Schema viết bằng SQL thuần trong `src/database/schema/`; mỗi migration chỉ chạy một tệp SQL.
- **Không sửa** tệp SQL hay migration đã merge. Thay đổi mới là một tệp SQL mới (`03_...sql`) cộng một migration mới (`0003_...py`).
- **Số phiên bản là tài nguyên chung.** Hai người cùng thêm `0003` sẽ xung đột. Trước khi tạo migration, báo trong nhóm chat để nhận số kế tiếp; người merge sau phải đổi `down_revision` cho khớp.
- Mọi lệnh tạo phải chạy lại được (`IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`). Thử `upgrade head` hai lần, rồi `downgrade` một bước và `upgrade head` lại.
- Tên bảng và cột: chữ thường, `snake_case`. Bảng sự kiện `fact_*`, bảng chiều `dim_*`, đúng schema `raw`, `clean`, `dw`.
- Không có dữ liệu thật trong migration hay seed. Seed chỉ là dữ liệu mẫu nhỏ do nhóm tự tạo (`src/database/seed/`).

## 5. Dữ liệu và mô hình

- Dữ liệu thật (đánh giá thu thập, tệp gán nhãn) **chỉ nằm ở máy hoặc ổ lưu trữ riêng của nhóm**, không đưa lên Git, không đính kèm vào PR. Chia sẻ qua kênh riêng của nhóm.
- Mô tả cách tái tạo kết quả bằng lệnh và tham số, không bằng tệp dữ liệu. Đặt hạt ngẫu nhiên (`seed`) cố định khi huấn luyện.
- Mỗi mô hình ghi kết quả đánh giá vào `docs/` hoặc `models/README.md`: tập kiểm định, baseline so sánh, chỉ số (F1, MAE, MAPE...), thời điểm huấn luyện. Phải có baseline đơn giản để so sánh.
- Phải tuân thủ `docs/dao_duc_phap_ly.md` khi thu thập (điều khoản nguồn, tần suất gọi, che thông tin cá nhân).

## 6. Giao diện (React, TypeScript, Tailwind, shadcn/ui)

- Màu và kiểu chữ dùng token của giao diện (`bg-card`, `text-foreground`...), không dùng màu cố định hoặc biến thể `dark:`.
- Dữ liệu mẫu để ở `src/services/mock-data.ts` cho tới khi có API; khi nối API thật thì thay lớp trong `src/services/`, không viết `fetch` rải rác trong trang.
- Trang mới là một thư mục trong `src/pages/<ten>/index.tsx`, khai báo trong `src/routes.tsx` (nạp lười).
- Trước khi tạo PR: `npm run typecheck` và `npm run build` phải qua. Không commit `node_modules/` hay `dist/`.

## 7. Dashboard Superset và SQL

- Truy vấn dataset lưu trong `src/bi/superset/queries/`, mỗi tệp một chỉ số, có chú thích định nghĩa và đơn vị.
- Công thức BHI và KPI chỉ có một nơi định nghĩa (`docs/kpi_bhi.md` và `src/bi/bhi.py`). SQL phải cho kết quả trùng hàm Python trên cùng dữ liệu mẫu.
- Truy vấn có bộ lọc thời gian phải dùng biến lọc của Superset, không viết cứng ngày.

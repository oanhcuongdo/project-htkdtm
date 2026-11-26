# Apache Superset (T5)

Dashboard của EduVision BI chạy bằng Apache Superset trong Docker Compose, đọc kho dữ liệu PostgreSQL (schema `dw`).
Người dựng dashboard: Hưng (dashboard 1 đến 4), Ngọc Anh (dashboard 5, 6). Nhúng vào website: Hoàng Anh (HA5).

## Chạy

Superset là dịch vụ **tùy chọn** (profile `bi`), vì nặng (ảnh khoảng 1,3 GB, cần khoảng 1 GB RAM). Lần đầu mất vài phút để khởi tạo.

```bash
cd nhom03-65httt
# 1. Thêm các biến SUPERSET_* vào .env (xem .env.example). Tạo giá trị ngẫu nhiên:
python -c "import secrets; print(secrets.token_urlsafe(48))"
# 2. Chạy
docker compose --profile bi up -d --build
# 3. Mở http://localhost:8088, đăng nhập bằng SUPERSET_ADMIN_USER / SUPERSET_ADMIN_PASSWORD trong .env
```

Kiểm tra: `docker compose ps` thấy `eduvision-superset` ở trạng thái `healthy`; `curl http://localhost:8088/health` trả `OK`.
Tắt: `docker compose --profile bi down` (thêm `-v` để xóa cả dữ liệu Superset và PostgreSQL).

## Biến môi trường (trong `.env`, không commit)

| Biến | Ý nghĩa |
|---|---|
| `SUPERSET_SECRET_KEY` | Khóa bí mật của Superset. Bắt buộc, không có giá trị mặc định |
| `SUPERSET_GUEST_TOKEN_SECRET` | Khóa ký guest token khi nhúng dashboard (HA5). Bắt buộc |
| `SUPERSET_ADMIN_USER`, `SUPERSET_ADMIN_PASSWORD`, `SUPERSET_ADMIN_EMAIL` | Tài khoản quản trị tạo lúc khởi tạo |
| `SUPERSET_DB_PASSWORD` | Mật khẩu của tài khoản PostgreSQL chỉ đọc `superset_ro` (tự tạo) |
| `SUPERSET_PORT` | Cổng trên máy (mặc định 8088, chỉ mở cho `127.0.0.1`) |

## Kết nối dữ liệu

Khi container khởi động, `register_dw.py` tự:
1. Tạo vai trò PostgreSQL **`superset_ro`**: chỉ `SELECT` trên schema `dw`, giao dịch mặc định chỉ đọc, giới hạn mỗi truy vấn 60 giây. Bảng hoặc view tạo sau này trong `dw` cũng tự được cấp quyền đọc.
2. Đăng ký kết nối **"EduVision DW"** trong Superset bằng vai trò đó (không dùng tài khoản quản trị, không cho chạy lệnh ghi từ SQL Lab).

Chỉ thấy schema `dw`. Lớp `raw` và `clean` (chứa văn bản đánh giá gốc) không đọc được từ Superset.

## Dựng dashboard

- Truy vấn dataset lưu trong [queries/](queries/): mỗi tệp một chỉ số, có chú thích định nghĩa. Trong Superset: Datasets, thêm dataset bằng SQL, dán nội dung tệp.
- Truy vấn có bộ lọc thời gian phải dùng biến lọc của Superset (`from_dttm`, `to_dttm`), không viết cứng ngày.
- Xuất dashboard (Settings, Export) rồi lưu tệp zip vào `dashboards/` để người khác nhập lại (Import). Kiểm tra tệp xuất không chứa mật khẩu trước khi commit.

## Giới hạn hiện tại

- Metadata Superset lưu SQLite trong volume `superset_home`: đủ cho học tập và demo, không dùng cho môi trường thật.
- Cấu hình cho phép website nhúng (`frame-ancestors`) và vai trò guest sẽ làm ở HA5.
- Tài khoản quản trị chỉ tạo lần đầu; đổi `SUPERSET_ADMIN_PASSWORD` sau đó không đổi mật khẩu đã tạo (đổi trong giao diện Superset).

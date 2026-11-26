"""Cấu hình Superset cho EduVision BI. Mọi giá trị bí mật lấy từ biến môi trường (docker-compose, .env), không viết cứng."""

import os


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Thiếu biến môi trường {name}. Đặt trong tệp .env (xem .env.example), không ghi vào mã."
        )
    return value


# Khóa bí mật của Superset (mã hóa mật khẩu kết nối, phiên đăng nhập). Bắt buộc, không có giá trị mặc định.
SECRET_KEY = _required("SUPERSET_SECRET_KEY")

# Metadata của Superset (người dùng, dataset, dashboard) lưu SQLite trong volume Docker: đủ cho học tập và demo.
# Dữ liệu phân tích nằm ở PostgreSQL (schema dw), Superset chỉ đọc qua tài khoản chỉ đọc.
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

# Nhúng dashboard vào website bằng guest token (người làm: Hoàng Anh, HA5).
# Phần frame-ancestors (cho phép website nhúng) sẽ cấu hình ở HA5.
FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}
GUEST_TOKEN_JWT_SECRET = _required("SUPERSET_GUEST_TOKEN_SECRET")
GUEST_ROLE_NAME = "Gamma"

# Không gửi thống kê ẩn danh và không bật CSRF-exempt: giữ mặc định an toàn.
SUPERSET_WEBSERVER_TIMEOUT = 120
ROW_LIMIT = 50000

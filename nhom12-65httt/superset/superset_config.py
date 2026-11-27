import os

# Cấu hình bảo mật & cho phép nhúng iframe vào React (http://localhost:5173)
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "nhom12-65httt-smartrent-superset-secret-key")

# Tắt Talisman / X-Frame-Options để React localhost:5173 nhúng được iframe Superset
TALISMAN_ENABLED = False
HTTP_HEADERS = {}

# Bật CORS cho Frontend React
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
}

# Cho phép nhúng Dashboard công khai (standalone=true) hoặc Guest Token
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "DASHBOARD_CROSS_FILTERS": True,
}

# Cho phép vai trò Public xem Dashboard đã publish (phục vụ demo nhúng iframe không cần login lại)
PUBLIC_ROLE_LIKE = "Gamma"
GUEST_ROLE_NAME = "Gamma"
WTF_CSRF_ENABLED = False

import os

# Cấu hình Secret key cho Superset
SECRET_KEY = os.getenv('SUPERSET_SECRET_KEY', 'SecureSupersetSecretKey2026FinanceApp123!')

# Lưu metadata của Superset trong SQLite riêng biệt
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

# Tắt Talisman CSP trong môi trường phát triển để tránh chặn script/style
TALISMAN_ENABLED = False
WTF_CSRF_ENABLED = False

# Hỗ trợ cả tiếng Anh và tiếng Việt
LANGUAGES = {
    'en': {'flag': 'us', 'name': 'English'},
    'vi': {'flag': 'vn', 'name': 'Vietnamese'}
}
BABEL_DEFAULT_LOCALE = 'en'

# Cấu hình webserver
SUPERSET_WEBSERVER_TIMEOUT = 120
ROW_LIMIT = 50000

# Cho phép xử lý template SQL
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

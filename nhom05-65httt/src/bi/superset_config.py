"""
Apache Superset Configuration - Hệ thống quản lý đào tạo thông minh (Nhóm 05)
Phụ trách: Nguyễn Quang Đức (Data Warehouse & BI)
"""

import os

SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "htkdtm-nhom05-superset-secret-key")

# Sử dụng Redis cho Cache và Celery results
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": 1,
}

DATA_CACHE_CONFIG = {
    **CACHE_CONFIG,
    "CACHE_KEY_PREFIX": "superset_data_",
    "CACHE_REDIS_DB": 2,
}

# Bật các Feature Flags phục vụ 3 Dashboard BI
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "EMBEDDED_SUPERSET": True,
    "ALERT_REPORTS": False,
}

# Cho phép nhúng iframe hoặc truy cập từ Django Backend nếu cần
ENABLE_CORS = True
WTF_CSRF_ENABLED = False
TALISMAN_ENABLED = False

# Ngôn ngữ hỗ trợ
LANGUAGES = {
    "en": {"flag": "us", "name": "English"},
    "vi": {"flag": "vn", "name": "Vietnamese"},
}

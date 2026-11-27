"""Apache Superset configuration reading secrets and metadata DB URI from environment."""

import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me-superset-secret")

_pg_user = os.environ.get("POSTGRES_USER", "erp")
_pg_password = os.environ.get("POSTGRES_PASSWORD", "erp")
_pg_host = os.environ.get("POSTGRES_HOST", "postgres")
_pg_port = os.environ.get("POSTGRES_PORT", "5432")
_superset_db = os.environ.get("SUPERSET_DB", "superset")

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DATABASE_URI",
    f"postgresql+psycopg2://{_pg_user}:{_pg_password}@{_pg_host}:{_pg_port}/{_superset_db}",
)

WTF_CSRF_ENABLED = True
ENABLE_PROXY_FIX = True
